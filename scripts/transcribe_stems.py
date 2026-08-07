#!/usr/bin/env python3
"""Create quantized pitch/onset evidence from separated song stems."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import librosa
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
STEMS = ROOT / "analysis" / "separated" / "htdemucs" / "reference"
OUT = ROOT / "analysis"
SR = 22050
HOP = 256
GRID_OFFSET = 0.648
SECONDS_PER_BEAT = 60.0 / 77.733


def midi_name(value: int) -> str:
    return librosa.midi_to_note(value, octave=True, unicode=False)


def pitch_track(path: Path, fmin: float, fmax: float, frame_length: int) -> tuple[np.ndarray, ...]:
    y, _ = librosa.load(path, sr=SR, mono=True)
    f0, voiced, probability = librosa.pyin(
        y,
        fmin=fmin,
        fmax=fmax,
        sr=SR,
        frame_length=frame_length,
        hop_length=HOP,
        fill_na=np.nan,
    )
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=HOP)[0]
    times = librosa.times_like(f0, sr=SR, hop_length=HOP)
    return y, times, f0, voiced, probability, rms[: len(f0)]


def quantize_bins(
    times: np.ndarray,
    f0: np.ndarray,
    voiced: np.ndarray,
    probability: np.ndarray,
    rms: np.ndarray,
    subdivisions: int,
    total_beats: int,
    min_voiced_fraction: float,
    min_probability: float,
    rms_floor_db: float,
    tuning_correction_semitones: float = 0.0,
) -> list[dict[str, object]]:
    step = SECONDS_PER_BEAT / subdivisions
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    rows: list[dict[str, object]] = []
    for index in range(total_beats * subdivisions):
        start = GRID_OFFSET + index * step
        end = start + step
        inside = (times >= start) & (times < end)
        good = (
            inside
            & voiced
            & np.isfinite(f0)
            & (probability >= min_probability)
            & (rms_db >= rms_floor_db)
        )
        denominator = max(1, int(np.count_nonzero(inside)))
        fraction = float(np.count_nonzero(good) / denominator)
        midi = None
        pitch_name = ""
        confidence = 0.0
        if fraction >= min_voiced_fraction:
            midi_values = librosa.hz_to_midi(f0[good]) + tuning_correction_semitones
            midi = int(np.rint(np.median(midi_values)))
            pitch_name = midi_name(midi)
            confidence = float(np.mean(probability[good]))
        beat = index / subdivisions
        rows.append(
            {
                "index": index,
                "beat": round(beat, 4),
                "bar": int(beat // 4) + 1,
                "beat_in_bar": round(beat % 4 + 1, 4),
                "start_seconds": round(start, 6),
                "end_seconds": round(end, 6),
                "midi": midi,
                "note": pitch_name,
                "voiced_fraction": round(fraction, 4),
                "confidence": round(confidence, 4),
            }
        )
    return rows


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def onset_evidence(path: Path) -> list[dict[str, object]]:
    y, _ = librosa.load(path, sr=SR, mono=True)
    bands = {
        "low": (35, 180),
        "mid": (180, 2500),
        "high": (2500, 10000),
    }
    envelopes: dict[str, np.ndarray] = {}
    for name, (low, high) in bands.items():
        filtered = librosa.effects.preemphasis(y) if name == "high" else y
        envelopes[name] = librosa.onset.onset_strength(
            y=filtered, sr=SR, hop_length=HOP, fmin=low, fmax=high
        )
    combined = sum(envelopes.values())
    peaks = librosa.onset.onset_detect(
        onset_envelope=combined,
        sr=SR,
        hop_length=HOP,
        backtrack=True,
        units="frames",
    )
    rows: list[dict[str, object]] = []
    for frame in peaks:
        time = float(librosa.frames_to_time(frame, sr=SR, hop_length=HOP))
        beat = (time - GRID_OFFSET) / SECONDS_PER_BEAT
        if beat < 0 or beat >= 320:
            continue
        values = {name: float(env[min(frame, len(env) - 1)]) for name, env in envelopes.items()}
        dominant = max(values, key=values.get)
        rows.append(
            {
                "time_seconds": round(time, 6),
                "beat": round(beat, 4),
                "bar": int(beat // 4) + 1,
                "beat_in_bar": round(beat % 4 + 1, 4),
                "dominant_band": dominant,
                **{f"{name}_strength": round(value, 5) for name, value in values.items()},
            }
        )
    return rows


def main() -> None:
    OUT.mkdir(exist_ok=True)
    print("Tracking isolated vocal pitch...", flush=True)
    _, times, f0, voiced, probability, rms = pitch_track(
        STEMS / "vocals.wav", librosa.note_to_hz("A3"), librosa.note_to_hz("C6"), 2048
    )
    vocal_rows = quantize_bins(
        times,
        f0,
        voiced,
        probability,
        rms,
        subdivisions=2,
        total_beats=320,
        min_voiced_fraction=0.24,
        min_probability=0.48,
        rms_floor_db=-38.0,
        tuning_correction_semitones=0.0,
    )
    write_rows(OUT / "vocal_melody_eighth_bins.csv", vocal_rows)

    print("Tracking isolated bass pitch...", flush=True)
    _, times, f0, voiced, probability, rms = pitch_track(
        STEMS / "bass.wav", librosa.note_to_hz("E1"), librosa.note_to_hz("C4"), 4096
    )
    bass_rows = quantize_bins(
        times,
        f0,
        voiced,
        probability,
        rms,
        subdivisions=2,
        total_beats=320,
        min_voiced_fraction=0.34,
        min_probability=0.52,
        rms_floor_db=-34.0,
        tuning_correction_semitones=0.05,
    )
    write_rows(OUT / "bass_eighth_bins.csv", bass_rows)

    print("Detecting isolated drum onsets...", flush=True)
    drum_rows = onset_evidence(STEMS / "drums.wav")
    write_rows(OUT / "drum_onsets.csv", drum_rows)

    vocal_hist = Counter(row["note"] for row in vocal_rows if row["note"])
    bass_hist = Counter(row["note"] for row in bass_rows if row["note"])
    report = {
        "grid_offset_seconds": GRID_OFFSET,
        "seconds_per_beat": SECONDS_PER_BEAT,
        "bpm": 60 / SECONDS_PER_BEAT,
        "bars": 80,
        "vocal_voiced_eighth_bins": sum(bool(row["note"]) for row in vocal_rows),
        "vocal_range": [
            midi_name(min(int(row["midi"]) for row in vocal_rows if row["midi"] is not None)),
            midi_name(max(int(row["midi"]) for row in vocal_rows if row["midi"] is not None)),
        ],
        "vocal_pitch_histogram": vocal_hist.most_common(),
        "bass_voiced_eighth_bins": sum(bool(row["note"]) for row in bass_rows),
        "bass_range": [
            midi_name(min(int(row["midi"]) for row in bass_rows if row["midi"] is not None)),
            midi_name(max(int(row["midi"]) for row in bass_rows if row["midi"] is not None)),
        ],
        "bass_pitch_histogram": bass_hist.most_common(),
        "drum_onset_count": len(drum_rows),
    }
    (OUT / "stem_transcription_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
