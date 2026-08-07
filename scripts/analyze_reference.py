#!/usr/bin/env python3
"""Extract reproducible timing, tonal, and structural diagnostics from the reference."""

from __future__ import annotations

import json
import os

from studio_common import ROOT

import librosa
os.environ.setdefault(
    "MPLCONFIGDIR", str(ROOT / "analysis" / ".matplotlib")
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


AUDIO = ROOT / "analysis" / "reference.wav"
OUT_DIR = ROOT / "analysis"
HOP = 512


def key_correlations(chroma_mean: np.ndarray) -> list[dict[str, float | str]]:
    major = np.array(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )
    minor = np.array(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )
    names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    out: list[dict[str, float | str]] = []
    for tonic, name in enumerate(names):
        for mode, profile in (("major", major), ("minor", minor)):
            rolled = np.roll(profile, tonic)
            corr = float(np.corrcoef(chroma_mean, rolled)[0, 1])
            out.append({"key": f"{name} {mode}", "correlation": corr})
    return sorted(out, key=lambda item: item["correlation"], reverse=True)


def beat_run(y: np.ndarray, sr: int, start_bpm: float) -> dict[str, object]:
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
    tempo, beats = librosa.beat.beat_track(
        onset_envelope=onset,
        sr=sr,
        hop_length=HOP,
        start_bpm=start_bpm,
        bpm=None,
        sparse=True,
    )
    times = librosa.frames_to_time(beats, sr=sr, hop_length=HOP)
    intervals = np.diff(times)
    return {
        "start_bpm": start_bpm,
        "tempo": float(np.atleast_1d(tempo)[0]),
        "beat_count": int(len(times)),
        "first_beats_seconds": [round(float(x), 4) for x in times[:24]],
        "last_beat_seconds": round(float(times[-1]), 4) if len(times) else None,
        "median_interval_seconds": round(float(np.median(intervals)), 6) if len(intervals) else None,
        "times": times,
        "onset": onset,
    }


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    y, sr = librosa.load(AUDIO, sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=HOP)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=HOP)
    active = np.flatnonzero(rms_db > -45.0)
    active_start = float(rms_times[active[0]]) if len(active) else 0.0
    active_end = float(rms_times[active[-1]]) if len(active) else duration

    harmonic, percussive = librosa.effects.hpss(y, margin=(1.5, 3.0))
    runs = {
        "full_start_75": beat_run(y, sr, 75.0),
        "full_start_150": beat_run(y, sr, 150.0),
        "percussive_start_75": beat_run(percussive, sr, 75.0),
        "percussive_start_150": beat_run(percussive, sr, 150.0),
    }

    chroma = librosa.feature.chroma_cqt(y=harmonic, sr=sr, hop_length=HOP)
    weights = np.maximum(rms, 1e-9)
    weights = weights[: chroma.shape[1]]
    chroma_mean = np.average(chroma[:, : len(weights)], axis=1, weights=weights)
    chroma_mean /= np.sum(chroma_mean)
    keys = key_correlations(chroma_mean)

    # Tonal centroid change provides a useful, reproducible set of section-change candidates.
    tonnetz = librosa.feature.tonnetz(chroma=chroma, sr=sr)
    smooth_width = max(3, int(round(2.0 * sr / HOP)))
    kernel = np.ones(smooth_width) / smooth_width
    smooth = np.vstack([np.convolve(row, kernel, mode="same") for row in tonnetz])
    novelty = np.linalg.norm(np.diff(smooth, axis=1), axis=0)
    novelty_times = librosa.frames_to_time(np.arange(len(novelty)), sr=sr, hop_length=HOP)
    peaks = librosa.util.peak_pick(
        novelty,
        pre_max=int(2.0 * sr / HOP),
        post_max=int(2.0 * sr / HOP),
        pre_avg=int(4.0 * sr / HOP),
        post_avg=int(4.0 * sr / HOP),
        delta=float(np.std(novelty) * 0.65),
        wait=int(4.0 * sr / HOP),
        sparse=True,
    )
    ranked = sorted(
        ((float(novelty[p]), float(novelty_times[p])) for p in peaks), reverse=True
    )[:30]

    serializable_runs = {
        name: {k: v for k, v in run.items() if k not in {"times", "onset"}}
        for name, run in runs.items()
    }
    report = {
        "audio": str(AUDIO.relative_to(ROOT)),
        "sample_rate": sr,
        "duration_seconds": round(float(duration), 6),
        "active_start_seconds_minus_45db": round(active_start, 4),
        "active_end_seconds_minus_45db": round(active_end, 4),
        "beat_tracking": serializable_runs,
        "chroma_pitch_class_distribution_C_to_B": [round(float(x), 6) for x in chroma_mean],
        "key_rankings": keys[:12],
        "section_change_candidates_seconds": [
            round(time, 4) for _, time in sorted(ranked, key=lambda item: item[1])
        ],
    }
    (OUT_DIR / "analysis_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    best_run = runs["percussive_start_75"]
    fig, axes = plt.subplots(3, 1, figsize=(16, 10), constrained_layout=True)
    axes[0].plot(np.arange(len(y)) / sr, y, linewidth=0.25, color="#304a6e")
    axes[0].set(title="Reference waveform", xlim=(0, duration), ylabel="Amplitude")
    onset_times = librosa.frames_to_time(
        np.arange(len(best_run["onset"])), sr=sr, hop_length=HOP
    )
    axes[1].plot(onset_times, best_run["onset"], color="#b14d38", linewidth=0.7)
    for beat in best_run["times"]:
        axes[1].axvline(beat, color="#263238", alpha=0.12, linewidth=0.5)
    axes[1].set(title="Percussive onset strength and 77-BPM beat grid", xlim=(0, duration))
    img = librosa.display.specshow(
        chroma,
        x_axis="time",
        y_axis="chroma",
        sr=sr,
        hop_length=HOP,
        ax=axes[2],
        cmap="magma",
    )
    axes[2].set(title="Harmonic chromagram")
    fig.colorbar(img, ax=axes[2], format="%+2.0f")
    fig.savefig(OUT_DIR / "reference_diagnostics.png", dpi=150)
    plt.close(fig)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
