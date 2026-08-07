#!/usr/bin/env python3
"""Extract a higher-resolution monophonic pitch grid from the isolated vocal."""

from __future__ import annotations

import librosa

from transcribe_stems import OUT, STEMS, pitch_track, quantize_bins, write_rows


def main() -> None:
    _, times, f0, voiced, probability, rms = pitch_track(
        STEMS / "vocals.wav", librosa.note_to_hz("A3"), librosa.note_to_hz("C6"), 2048
    )
    rows = quantize_bins(
        times,
        f0,
        voiced,
        probability,
        rms,
        subdivisions=4,
        total_beats=320,
        min_voiced_fraction=0.22,
        min_probability=0.48,
        rms_floor_db=-38.0,
        tuning_correction_semitones=0.0,
    )
    path = OUT / "vocal_melody_sixteenth_bins.csv"
    write_rows(path, rows)
    print(path, sum(bool(row["note"]) for row in rows))


if __name__ == "__main__":
    main()
