#!/usr/bin/env python3
"""Compare the rendered reconstruction with the exact reference and its stems."""

from __future__ import annotations

import json
import os
import argparse
from pathlib import Path

import librosa
import numpy as np

from studio_common import ROOT

ANALYSIS = ROOT / "analysis"
RENDERS = ROOT / "renders"
STEMS = ANALYSIS / "separated" / "htdemucs" / "reference"
SR = 22050
HOP = 512
REFERENCE_GRID_OFFSET = 0.648

os.environ.setdefault("MPLCONFIGDIR", str(ANALYSIS / ".matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path: Path) -> np.ndarray:
    audio, _ = librosa.load(path, sr=SR, mono=True)
    return audio.astype(np.float32)


def crop_reference(audio: np.ndarray, target_length: int) -> np.ndarray:
    start = round(REFERENCE_GRID_OFFSET * SR)
    result = audio[start : start + target_length]
    if len(result) < target_length:
        result = np.pad(result, (0, target_length - len(result)))
    return result


def feature_cosine(a: np.ndarray, b: np.ndarray) -> float:
    count = min(a.shape[1], b.shape[1])
    a = a[:, :count]
    b = b[:, :count]
    numerator = np.sum(a * b, axis=0)
    denominator = np.linalg.norm(a, axis=0) * np.linalg.norm(b, axis=0)
    valid = denominator > 1e-9
    return float(np.mean(numerator[valid] / denominator[valid])) if np.any(valid) else 0.0


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    count = min(len(a), len(b))
    a = a[:count]
    b = b[:count]
    if np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def onset_f1(reference: np.ndarray, rendered: np.ndarray, tolerance: float = 0.12) -> dict[str, float]:
    reference_times = librosa.onset.onset_detect(
        y=reference, sr=SR, hop_length=HOP, units="time", backtrack=True
    )
    rendered_times = librosa.onset.onset_detect(
        y=rendered, sr=SR, hop_length=HOP, units="time", backtrack=True
    )
    used: set[int] = set()
    matches = 0
    for time in rendered_times:
        if not len(reference_times):
            break
        distances = np.abs(reference_times - time)
        for index in np.argsort(distances):
            if int(index) not in used and distances[index] <= tolerance:
                used.add(int(index))
                matches += 1
                break
    precision = matches / len(rendered_times) if len(rendered_times) else 0.0
    recall = matches / len(reference_times) if len(reference_times) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "reference_onsets": int(len(reference_times)),
        "rendered_onsets": int(len(rendered_times)),
        "precision": round(precision, 5),
        "recall": round(recall, 5),
        "f1": round(f1, 5),
    }


def compare_pair(reference: np.ndarray, rendered: np.ndarray) -> dict[str, object]:
    count = min(len(reference), len(rendered))
    reference = reference[:count]
    rendered = rendered[:count]
    reference /= max(float(np.max(np.abs(reference))), 1e-9)
    rendered /= max(float(np.max(np.abs(rendered))), 1e-9)

    rms_ref = librosa.feature.rms(y=reference, hop_length=HOP)[0]
    rms_render = librosa.feature.rms(y=rendered, hop_length=HOP)[0]
    onset_ref = librosa.onset.onset_strength(y=reference, sr=SR, hop_length=HOP)
    onset_render = librosa.onset.onset_strength(y=rendered, sr=SR, hop_length=HOP)
    chroma_ref = librosa.feature.chroma_cqt(y=reference, sr=SR, hop_length=HOP)
    chroma_render = librosa.feature.chroma_cqt(y=rendered, sr=SR, hop_length=HOP)
    mfcc_ref = librosa.feature.mfcc(y=reference, sr=SR, n_mfcc=20, hop_length=HOP)[1:]
    mfcc_render = librosa.feature.mfcc(y=rendered, sr=SR, n_mfcc=20, hop_length=HOP)[1:]
    centroid_ref = librosa.feature.spectral_centroid(y=reference, sr=SR, hop_length=HOP)[0]
    centroid_render = librosa.feature.spectral_centroid(y=rendered, sr=SR, hop_length=HOP)[0]

    scale = float(np.dot(reference, rendered) / max(np.dot(rendered, rendered), 1e-12))
    estimate = scale * rendered
    residual = reference - estimate
    si_sdr = 10 * np.log10(
        max(float(np.dot(estimate, estimate)), 1e-12)
        / max(float(np.dot(residual, residual)), 1e-12)
    )
    return {
        "rms_envelope_correlation": round(correlation(rms_ref, rms_render), 5),
        "onset_envelope_correlation": round(correlation(onset_ref, onset_render), 5),
        "chroma_cosine_similarity": round(feature_cosine(chroma_ref, chroma_render), 5),
        "mfcc_timbre_similarity": round(feature_cosine(mfcc_ref, mfcc_render), 5),
        "median_spectral_centroid_reference_hz": round(float(np.median(centroid_ref)), 2),
        "median_spectral_centroid_render_hz": round(float(np.median(centroid_render)), 2),
        "si_sdr_db": round(float(si_sdr), 4),
        "onset_match": onset_f1(reference, rendered),
    }


def rms_db(audio: np.ndarray) -> float:
    return float(20 * np.log10(max(np.sqrt(np.mean(np.square(audio))), 1e-12)))


def section_metrics(reference: np.ndarray, rendered: np.ndarray) -> list[dict[str, object]]:
    sections = [
        ("Intro", 0, 32),
        ("Chorus 1", 32, 80),
        ("Interlude 1", 80, 92),
        ("Verse 1", 92, 144),
        ("Chorus 2", 144, 192),
        ("Instrumental", 192, 220),
        ("Verse 2", 220, 248),
        ("Chorus 3", 248, 300),
        ("Outro", 300, 320),
    ]
    seconds_per_beat = 60 / 77.733
    rows: list[dict[str, object]] = []
    for name, start_beat, end_beat in sections:
        start = round(start_beat * seconds_per_beat * SR)
        end = round(end_beat * seconds_per_beat * SR)
        metrics = compare_pair(reference[start:end], rendered[start:end])
        rows.append(
            {
                "section": name,
                "chroma": metrics["chroma_cosine_similarity"],
                "onset": metrics["onset_envelope_correlation"],
                "rms": metrics["rms_envelope_correlation"],
                "timbre": metrics["mfcc_timbre_similarity"],
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", required=True, help="Render filename prefix, for example iteration2")
    args = parser.parse_args()
    prefix = args.prefix

    reference_full_raw = load(ANALYSIS / "reference.wav")
    render_full = load(RENDERS / f"{prefix}_full.wav")
    reference_full = crop_reference(reference_full_raw, len(render_full))

    pairs = {
        "full_mix": (reference_full, render_full),
        "bass": (
            crop_reference(load(STEMS / "bass.wav"), len(load(RENDERS / f"{prefix}_02_bass.wav"))),
            load(RENDERS / f"{prefix}_02_bass.wav"),
        ),
        "drums": (
            crop_reference(load(STEMS / "drums.wav"), len(load(RENDERS / f"{prefix}_03_drums.wav"))),
            load(RENDERS / f"{prefix}_03_drums.wav"),
        ),
        "vocals_vs_guide": (
            crop_reference(load(STEMS / "vocals.wav"), len(load(RENDERS / f"{prefix}_04_vocal.wav"))),
            load(RENDERS / f"{prefix}_04_vocal.wav"),
        ),
    }
    keys = load(RENDERS / f"{prefix}_01_keys.wav")
    lead = load(RENDERS / f"{prefix}_05_lead.wav")
    other_render = keys[: min(len(keys), len(lead))] + lead[: min(len(keys), len(lead))]
    pairs["accompaniment_other"] = (
        crop_reference(load(STEMS / "other.wav"), len(other_render)),
        other_render,
    )

    metrics = {name: compare_pair(reference, rendered) for name, (reference, rendered) in pairs.items()}
    metrics["full_mix"]["sections"] = section_metrics(reference_full, render_full)

    reference_stems = {name: load(STEMS / f"{name}.wav") for name in ("bass", "drums", "vocals", "other")}
    reference_total_rms = rms_db(reference_full_raw)
    render_parts = {
        "bass": load(RENDERS / f"{prefix}_02_bass.wav"),
        "drums": load(RENDERS / f"{prefix}_03_drums.wav"),
        "vocal_guide": load(RENDERS / f"{prefix}_04_vocal.wav"),
        "keys": keys,
        "lead": lead,
    }
    render_total_rms = rms_db(render_full)
    level_balance = {
        "reference_stems_db_relative_to_mix": {
            name: round(rms_db(audio) - reference_total_rms, 3)
            for name, audio in reference_stems.items()
        },
        "rendered_parts_db_relative_to_mix": {
            name: round(rms_db(audio) - render_total_rms, 3)
            for name, audio in render_parts.items()
        },
    }

    report = {
        "reference_alignment_seconds_removed": REFERENCE_GRID_OFFSET,
        "renderer": "Apple DLS General MIDI via AVAudioUnitSampler",
        "metrics": metrics,
        "level_balance": level_balance,
    }
    (ANALYSIS / f"{prefix}_comparison.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    time_ref = np.arange(len(reference_full)) / SR
    fig, axes = plt.subplots(3, 1, figsize=(16, 10), constrained_layout=True)
    axes[0].plot(time_ref, reference_full, linewidth=0.15, label="Reference", alpha=0.8)
    axes[0].plot(np.arange(len(render_full)) / SR, render_full, linewidth=0.15, label="MIDI render", alpha=0.65)
    axes[0].set(title="Aligned waveform overview", xlim=(0, min(len(reference_full), len(render_full)) / SR))
    axes[0].legend(loc="upper right")
    rms_ref = librosa.feature.rms(y=reference_full, hop_length=HOP)[0]
    rms_render = librosa.feature.rms(y=render_full, hop_length=HOP)[0]
    rms_time = librosa.times_like(rms_ref, sr=SR, hop_length=HOP)
    axes[1].plot(rms_time, librosa.amplitude_to_db(rms_ref, ref=np.max), label="Reference")
    axes[1].plot(rms_time[: len(rms_render)], librosa.amplitude_to_db(rms_render, ref=np.max), label="MIDI render")
    axes[1].set(title="Relative loudness envelope", ylabel="dB", ylim=(-60, 3))
    axes[1].legend(loc="lower right")
    sections = metrics["full_mix"]["sections"]
    names = [row["section"] for row in sections]
    x = np.arange(len(names))
    width = 0.22
    axes[2].bar(x - width, [row["chroma"] for row in sections], width, label="Chroma")
    axes[2].bar(x, [row["onset"] for row in sections], width, label="Onset")
    axes[2].bar(x + width, [row["timbre"] for row in sections], width, label="Timbre")
    axes[2].set_xticks(x, names, rotation=25, ha="right")
    axes[2].set(title="Section similarity (1.0 is identical)", ylim=(-0.2, 1.0))
    axes[2].legend()
    fig.savefig(ANALYSIS / f"{prefix}_comparison.png", dpi=150)
    plt.close(fig)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
