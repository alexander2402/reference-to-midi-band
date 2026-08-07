#!/usr/bin/env python3
"""Validate generated MIDI files structurally and musically."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import mido
import pretty_midi


ROOT = Path(__file__).resolve().parents[1]
MIDI_DIR = ROOT / "midi"
OUT = ROOT / "analysis" / "midi_validation.json"
EXPECTED_BPM = 77.733
EXPECTED_BEATS = 320


def validate(path: Path) -> dict[str, object]:
    midi = mido.MidiFile(path)
    assert midi.type == 1, f"{path.name}: expected format 1"
    assert midi.ticks_per_beat == 480, f"{path.name}: unexpected PPQ"

    tempo_values: list[int] = []
    signatures: list[tuple[int, int]] = []
    keys: list[str] = []
    track_reports: list[dict[str, object]] = []
    absolute_end = 0
    all_errors: list[str] = []

    for track_index, track in enumerate(midi.tracks):
        tick = 0
        active: dict[tuple[int, int], list[int]] = defaultdict(list)
        pitches: list[int] = []
        note_count = 0
        track_name = f"Track {track_index}"
        for message in track:
            tick += message.time
            if message.type == "track_name":
                track_name = message.name
            elif message.type == "set_tempo":
                tempo_values.append(message.tempo)
            elif message.type == "time_signature":
                signatures.append((message.numerator, message.denominator))
            elif message.type == "key_signature":
                keys.append(message.key)
            elif message.type == "note_on" and message.velocity > 0:
                active[(message.channel, message.note)].append(tick)
                pitches.append(message.note)
                note_count += 1
            elif message.type in {"note_off", "note_on"}:
                key = (message.channel, message.note)
                if not active[key]:
                    all_errors.append(f"{track_name}: unmatched note-off at tick {tick}: {key}")
                else:
                    start = active[key].pop(0)
                    if tick <= start:
                        all_errors.append(f"{track_name}: non-positive note duration at tick {tick}: {key}")
        for key, starts in active.items():
            for start in starts:
                all_errors.append(f"{track_name}: stuck note from tick {start}: {key}")
        absolute_end = max(absolute_end, tick)
        track_reports.append(
            {
                "name": track_name,
                "note_count": note_count,
                "pitch_min": min(pitches) if pitches else None,
                "pitch_max": max(pitches) if pitches else None,
                "end_tick": tick,
            }
        )

    assert not all_errors, f"{path.name}: " + "; ".join(all_errors[:5])
    assert tempo_values, f"{path.name}: no tempo"
    bpms = [mido.tempo2bpm(value) for value in tempo_values]
    assert abs(bpms[0] - EXPECTED_BPM) < 0.001, f"{path.name}: tempo mismatch"
    assert (4, 4) in signatures, f"{path.name}: missing 4/4 signature"
    assert "Am" in keys, f"{path.name}: missing A-minor key signature"
    assert absolute_end == EXPECTED_BEATS * midi.ticks_per_beat, (
        f"{path.name}: expected {EXPECTED_BEATS} beats, got {absolute_end / midi.ticks_per_beat}"
    )

    pretty = pretty_midi.PrettyMIDI(str(path))
    change_times, tempi = pretty.get_tempo_changes()
    assert len(tempi) >= 1
    assert abs(float(tempi[0]) - EXPECTED_BPM) < 0.001

    return {
        "file": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "format": midi.type,
        "ticks_per_beat": midi.ticks_per_beat,
        "tempo_bpm": round(bpms[0], 6),
        "time_signature": "4/4",
        "key": "A minor",
        "duration_beats": absolute_end / midi.ticks_per_beat,
        "duration_seconds": round(pretty.get_end_time(), 6),
        "tracks": track_reports,
        "status": "PASS",
    }


def main() -> None:
    files = sorted(MIDI_DIR.glob("*.mid"))
    assert len(files) == 6, f"Expected 6 MIDI files, found {len(files)}"
    report = {
        "expected_bpm": EXPECTED_BPM,
        "expected_meter": "4/4",
        "expected_key": "A minor",
        "expected_bars": 80,
        "files": [validate(path) for path in files],
        "status": "PASS",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
