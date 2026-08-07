#!/usr/bin/env python3
"""Build alternate monophonic vocal guides for rendered A/B selection."""

from __future__ import annotations

import csv

from generate_reconstruction import (
    ANALYSIS_DIR,
    GRID_OFFSET_SECONDS,
    SECONDS_PER_BEAT,
    NoteEvent,
    chord_map,
    conductor_track,
    load_vocal_events,
    note_track,
    save_midi,
)


OUT = ANALYSIS_DIR / "vocal_candidates"
VOCAL_RANGES = [(31.0, 79.0), (90.0, 138.0), (143.0, 191.0), (218.0, 244.0), (248.0, 297.0)]


def in_vocal_range(beat: float) -> bool:
    return any(start <= beat <= end for start, end in VOCAL_RANGES)


def pyin_guide() -> list[int | None]:
    rows = csv.DictReader((ANALYSIS_DIR / "vocal_melody_eighth_bins.csv").open(encoding="utf-8"))
    return [int(row["midi"]) if row["midi"] else None for row in rows]


def pyin_grid_events(filename: str, subdivisions: int) -> list[NoteEvent]:
    rows = csv.DictReader((ANALYSIS_DIR / filename).open(encoding="utf-8"))
    sequence: list[int | None] = [int(row["midi"]) if row["midi"] else None for row in rows]
    for index in range(1, len(sequence) - 1):
        previous, current, following = sequence[index - 1 : index + 2]
        if current is None and previous == following:
            sequence[index] = previous
        elif current is not None and previous == following and previous is not None:
            if abs(current - previous) <= 2:
                sequence[index] = previous
    step = 1.0 / subdivisions
    events: list[NoteEvent] = []
    index = 0
    while index < len(sequence):
        pitch = sequence[index]
        if pitch is None:
            index += 1
            continue
        end = index + 1
        while end < len(sequence) and sequence[end] == pitch:
            end += 1
        events.append(NoteEvent(index * step, max(0.10, (end - index) * step - 0.04), pitch, 82))
        index = end
    return events


def basic_pitch_rows() -> list[tuple[float, float, int, int]]:
    rows = csv.DictReader(
        (ANALYSIS_DIR / "basic_pitch" / "vocals_basic_pitch.csv").open(encoding="utf-8")
    )
    out: list[tuple[float, float, int, int]] = []
    for row in rows:
        start_seconds = float(row["start_time_s"])
        end_seconds = float(row["end_time_s"])
        start = (start_seconds - GRID_OFFSET_SECONDS) / SECONDS_PER_BEAT
        end = (end_seconds - GRID_OFFSET_SECONDS) / SECONDS_PER_BEAT
        pitch = int(row["pitch_midi"])
        velocity = int(row["velocity"])
        if (
            in_vocal_range((start + end) / 2)
            and 59 <= pitch <= 76
            and velocity >= 38
            and end - start >= 0.10
        ):
            out.append((start, end, pitch, velocity))
    return sorted(out)


def grid_candidate(subdivisions: int, guide_weight: float, fill_from_guide: bool) -> list[NoteEvent]:
    guide = pyin_guide()
    source = basic_pitch_rows()
    step = 1.0 / subdivisions
    sequence: list[tuple[int, int] | None] = []
    for index in range(round(320 * subdivisions)):
        start = index * step
        center = start + step / 2
        if not in_vocal_range(center):
            sequence.append(None)
            continue
        guide_index = min(len(guide) - 1, max(0, round(center * 2)))
        target = guide[guide_index]
        candidates: list[tuple[float, int, int]] = []
        for event_start, event_end, pitch, velocity in source:
            overlap = max(0.0, min(start + step, event_end) - max(start, event_start))
            if overlap <= 0:
                continue
            distance = abs(pitch - target) if target is not None else 0
            score = overlap / step * 45 + velocity
            if target is not None:
                score += guide_weight * max(-2, 2 - distance)
            candidates.append((score, pitch, velocity))
        if candidates:
            _, pitch, velocity = max(candidates)
            if target is not None and abs(pitch - target) > 4:
                pitch = target
            sequence.append((pitch, max(64, min(96, velocity))))
        elif fill_from_guide and target is not None:
            sequence.append((target, 78))
        else:
            sequence.append(None)

    # Suppress isolated pitch fragments and bridge a single empty bin between
    # identical pitches.  Both operations reduce transcription artefacts while
    # retaining syllabic articulation.
    for index in range(1, len(sequence) - 1):
        previous = sequence[index - 1]
        current = sequence[index]
        following = sequence[index + 1]
        if current is None and previous and following and previous[0] == following[0]:
            sequence[index] = (previous[0], min(previous[1], following[1]))
        elif current and previous and following and previous[0] == following[0]:
            if abs(current[0] - previous[0]) <= 2:
                sequence[index] = (previous[0], current[1])

    events: list[NoteEvent] = []
    index = 0
    while index < len(sequence):
        current = sequence[index]
        if current is None:
            index += 1
            continue
        end = index + 1
        velocities = [current[1]]
        while end < len(sequence) and sequence[end] and sequence[end][0] == current[0]:
            velocities.append(sequence[end][1])
            end += 1
        events.append(
            NoteEvent(
                index * step,
                max(0.10, (end - index) * step - 0.04),
                current[0],
                round(sum(velocities) / len(velocities)),
            )
        )
        index = end
    return events


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chords = chord_map()
    candidates = {
        "pyin_raw": load_vocal_events(),
        "pyin16_raw": pyin_grid_events("vocal_melody_sixteenth_bins.csv", 4),
        "basic_grid8": grid_candidate(2, guide_weight=0, fill_from_guide=False),
        "fused_grid8": grid_candidate(2, guide_weight=24, fill_from_guide=True),
        "fused_grid16": grid_candidate(4, guide_weight=24, fill_from_guide=True),
    }
    for name, events in candidates.items():
        track = note_track(f"Vocal Candidate: {name}", 68, events)
        path = OUT / f"04_{name}.mid"
        save_midi(path, [conductor_track(chords), track])
        print(name, len(events), path)


if __name__ == "__main__":
    main()
