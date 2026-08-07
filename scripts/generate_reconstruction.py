#!/usr/bin/env python3
"""Generate the reference-compared MIDI reconstruction for Анжелика Варум — Городок."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import mido

from studio_common import ROOT

MIDI_DIR = ROOT / "midi"
ANALYSIS_DIR = ROOT / "analysis"
TPB = 480
BPM = 77.733
TOTAL_BEATS = 320.0
GRID_OFFSET_SECONDS = 0.648
SECONDS_PER_BEAT = 60.0 / BPM


@dataclass(frozen=True)
class ChordEvent:
    start: float
    duration: float
    name: str


@dataclass(frozen=True)
class NoteEvent:
    start: float
    duration: float
    note: int
    velocity: int
    channel: int = 0


SECTIONS = [
    (1, "Intro"),
    (9, "Chorus 1"),
    (21, "Interlude 1"),
    (24, "Verse 1"),
    (37, "Chorus 2"),
    (49, "Instrumental"),
    (56, "Verse 2 (short)"),
    (63, "Chorus 3 (extended)"),
    (76, "Outro"),
]


VOICINGS = {
    "Am": [57, 60, 64, 69],
    "G7/B": [59, 62, 65, 67],
    "C": [55, 60, 64, 67],
    "Bdim": [59, 62, 65],
    "G7": [55, 59, 62, 65],
    "F/A": [57, 60, 65, 69],
    "G": [55, 59, 62, 67],
    "E7": [52, 56, 59, 62, 64],
    "A/E": [52, 57, 61, 64],
    "Dm": [50, 57, 62, 65, 69],
    "G/B": [59, 62, 67],
    "E/B": [59, 62, 64, 68],
    "A/C#": [49, 57, 61, 64, 69],
    "Dm7": [50, 57, 60, 62, 65],
    "Bm7b5": [47, 53, 57, 59, 62],
    "F": [53, 57, 60, 65],
    "Am/E": [52, 57, 60, 64],
    "Em": [52, 55, 59, 64],
    "Gm6/Bb": [46, 55, 58, 62, 64],
    "A7": [45, 55, 57, 61, 64],
    "Esus4": [52, 57, 59, 64],
    "E": [52, 56, 59, 64],
    "Am/B": [47, 57, 60, 64],
    "Fm7": [53, 56, 60, 63],
    "Gm/Bb": [46, 55, 58, 62],
    "A": [45, 52, 57, 61, 64],
    "Am/C": [48, 57, 60, 64],
    "C6": [48, 57, 60, 64, 69],
    "Am/D": [50, 57, 60, 64],
    "Dm6": [50, 57, 59, 62, 65],
}


def chord_map() -> list[ChordEvent]:
    by_bar: dict[int, list[tuple[str, float]]] = {
        1: [("Am", 2), ("G7/B", 2)],
        2: [("C", 2), ("Am", 2)],
        3: [("Bdim", 2), ("C", 2)],
        4: [("Am", 2), ("G7", 2)],
        5: [("C", 2), ("G7", 2)],
        6: [("F/A", 2), ("Am", 2)],
        7: [("G", 2), ("C", 2)],
        8: [("E7", 4)],
        9: [("Am", 4)],
        10: [("A/E", 4)],
        11: [("Dm", 4)],
        12: [("G", 4)],
        13: [("G/B", 4)],
        14: [("C", 2), ("E/B", 2)],
        15: [("Am", 4)],
        16: [("A/C#", 4)],
        17: [("Dm", 2), ("Dm7", 2)],
        18: [("Bm7b5", 2), ("C", 2)],
        19: [("Dm", 2), ("E7", 2)],
        20: [("F", 2), ("Am/E", 2)],
        21: [("Am", 4)],
        22: [("Dm", 4)],
        23: [("Em", 2), ("E7", 2)],
        24: [("Am", 4)],
        25: [("Dm", 2), ("G7", 2)],
        26: [("C", 2), ("E/B", 2)],
        27: [("Am", 4)],
        28: [("Dm", 2), ("G7", 2)],
        29: [("C", 4)],
        30: [("Gm6/Bb", 4)],
        31: [("A7", 4)],
        32: [("Dm", 4)],
        33: [("Bm7b5", 2), ("C", 2)],
        34: [("Dm", 2), ("E7", 2)],
        35: [("F", 4)],
        36: [("Esus4", 2), ("E", 2)],
        37: [("Am", 2), ("Am/B", 2)],
        38: [("C", 2), ("A/C#", 2)],
        39: [("Dm", 4)],
        40: [("G", 4)],
        41: [("G/B", 4)],
        42: [("C", 2), ("E/B", 2)],
        43: [("Am", 4)],
        44: [("C", 2), ("A/C#", 2)],
        45: [("Dm", 4)],
        46: [("Bm7b5", 2), ("C", 2)],
        47: [("Dm", 2), ("E7", 2)],
        48: [("Fm7", 2), ("Am/E", 2)],
        49: [("Am", 4)],
        50: [("F", 2), ("F/A", 2)],
        51: [("F", 2), ("Am/E", 2)],
        52: [("Am", 4)],
        53: [("F", 2), ("Am/E", 2)],
        54: [("Am", 2), ("F", 2)],
        55: [("Am/E", 2), ("Am", 2)],
        56: [("Gm/Bb", 4)],
        57: [("A", 4)],
        58: [("Dm", 4)],
        59: [("Bm7b5", 2), ("Am/C", 2)],
        60: [("Dm", 2), ("Esus4", 2)],
        61: [("Fm7", 4)],
        62: [("Esus4", 2), ("E7", 2)],
        63: [("Am", 2), ("C6", 2)],
        64: [("A/C#", 4)],
        65: [("Dm", 4)],
        66: [("G", 4)],
        67: [("G/B", 4)],
        68: [("C", 2), ("E/B", 2)],
        69: [("Am", 4)],
        70: [("A7", 4)],
        71: [("Dm", 4)],
        72: [("G/B", 2), ("C", 2)],
        73: [("Dm", 2), ("Am/D", 2)],
        74: [("Dm6", 2), ("E7", 2)],
        75: [("Fm7", 4)],
        76: [("Am", 4)],
        77: [("Fm7", 4)],
        78: [("Esus4", 4)],
        79: [("E7", 4)],
        80: [("Am", 4)],
    }
    events: list[ChordEvent] = []
    for bar in range(1, 81):
        cursor = (bar - 1) * 4.0
        entries = by_bar[bar]
        assert abs(sum(duration for _, duration in entries) - 4.0) < 1e-9
        for name, duration in entries:
            events.append(ChordEvent(cursor, duration, name))
            cursor += duration
    return events


def conductor_track(chords: list[ChordEvent]) -> mido.MidiTrack:
    events: list[tuple[int, int, mido.Message | mido.MetaMessage]] = [
        (0, 0, mido.MetaMessage("track_name", name="Conductor")),
        (0, 1, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM))),
        (0, 2, mido.MetaMessage("time_signature", numerator=4, denominator=4)),
        (0, 3, mido.MetaMessage("key_signature", key="Am")),
        (0, 4, mido.MetaMessage("text", text="Approximate reconstruction; 80 bars")),
    ]
    for bar, name in SECTIONS:
        tick = round((bar - 1) * 4 * TPB)
        events.append((tick, 5, mido.MetaMessage("marker", text=f"Bar {bar}: {name}")))
    for chord in chords:
        tick = round(chord.start * TPB)
        events.append((tick, 6, mido.MetaMessage("marker", text=f"Chord: {chord.name}")))
    return finalize_meta(events)


def finalize_meta(
    events: list[tuple[int, int, mido.Message | mido.MetaMessage]],
) -> mido.MidiTrack:
    track = mido.MidiTrack()
    previous = 0
    for tick, order, message in sorted(events, key=lambda item: (item[0], item[1])):
        message.time = tick - previous
        track.append(message)
        previous = tick
    track.append(mido.MetaMessage("end_of_track", time=max(0, round(TOTAL_BEATS * TPB) - previous)))
    return track


def note_track(
    name: str,
    program: int,
    events: list[NoteEvent],
    channel: int = 0,
) -> mido.MidiTrack:
    timeline: list[tuple[int, int, mido.Message | mido.MetaMessage]] = [
        (0, 0, mido.MetaMessage("track_name", name=name)),
        (0, 1, mido.Message("program_change", program=program, channel=channel)),
    ]
    for event in events:
        start = max(0, round(event.start * TPB))
        end = max(start + 1, round((event.start + event.duration) * TPB))
        timeline.append(
            (start, 3, mido.Message("note_on", note=event.note, velocity=event.velocity, channel=event.channel))
        )
        timeline.append(
            (end, 2, mido.Message("note_off", note=event.note, velocity=0, channel=event.channel))
        )
    return finalize_meta(timeline)


def load_accompaniment_events() -> tuple[list[NoteEvent], list[NoteEvent]]:
    """Load the polyphonic transcription of the isolated accompaniment.

    The first pass reduced the accompaniment to one block chord per harmony
    change.  The rendered A/B showed that this reproduced only 16% of the
    reference's accompaniment onsets.  Basic Pitch events retain the performed
    rhythmic figures, inner voices, and high synth line.  Low-register events
    are excluded because the dedicated bass stem is more reliable there.
    """

    rows = csv.DictReader(
        (ANALYSIS_DIR / "basic_pitch" / "other_basic_pitch.csv").open(encoding="utf-8")
    )
    keys: list[NoteEvent] = []
    lead: list[NoteEvent] = []
    for row in rows:
        start_seconds = float(row["start_time_s"])
        end_seconds = float(row["end_time_s"])
        note = int(row["pitch_midi"])
        if not 48 <= note <= 84:
            continue
        start = (start_seconds - GRID_OFFSET_SECONDS) / SECONDS_PER_BEAT
        duration = (end_seconds - start_seconds) / SECONDS_PER_BEAT
        if start < 0 or start >= TOTAL_BEATS or duration < 0.10:
            continue
        duration = min(duration, TOTAL_BEATS - start)
        source_velocity = int(row["velocity"])
        velocity = max(34, min(96, round(source_velocity * 0.92)))
        event = NoteEvent(start, duration, note, velocity)
        (lead if note >= 72 else keys).append(event)
    return keys, lead


def load_bass_events() -> list[NoteEvent]:
    rows = list(csv.DictReader((ANALYSIS_DIR / "bass_eighth_bins.csv").open(encoding="utf-8")))
    sequence: list[int | None] = [int(row["midi"]) if row["midi"] else None for row in rows]
    out: list[NoteEvent] = []
    index = 0
    while index < len(sequence):
        note = sequence[index]
        if note is None:
            index += 1
            continue
        end = index + 1
        while end < len(sequence) and sequence[end] == note:
            end += 1
        duration = (end - index) * 0.5
        out.append(NoteEvent(index * 0.5, max(0.2, duration - 0.04), note, 104))
        index = end
    return out


def load_vocal_events() -> list[NoteEvent]:
    rows = list(
        csv.DictReader((ANALYSIS_DIR / "vocal_melody_sixteenth_bins.csv").open(encoding="utf-8"))
    )
    # Preserve the detected chromatic melody.  The original generator blindly
    # changed C#, D#, and A# to neighbouring scale notes; the stem comparison
    # proved those alterations made the guide less like the sung performance.
    sequence: list[int | None] = [int(row["midi"]) if row["midi"] else None for row in rows]
    for index in range(1, len(sequence) - 1):
        if sequence[index] is None and sequence[index - 1] == sequence[index + 1]:
            sequence[index] = sequence[index - 1]
        elif (
            sequence[index] is not None
            and sequence[index - 1] is not None
            and sequence[index - 1] == sequence[index + 1]
            and abs(sequence[index] - sequence[index - 1]) <= 2
        ):
            sequence[index] = sequence[index - 1]
    out: list[NoteEvent] = []
    index = 0
    while index < len(sequence):
        note = sequence[index]
        if note is None:
            index += 1
            continue
        end = index + 1
        while end < len(sequence) and sequence[end] == note:
            end += 1
        duration = (end - index) * 0.25
        out.append(NoteEvent(index * 0.25, max(0.10, duration - 0.04), note, 82))
        index = end
    return out


def drum_events() -> list[NoteEvent]:
    out: list[NoteEvent] = []
    chorus_bars = set(range(9, 21)) | set(range(37, 49)) | set(range(63, 76))
    sparse_bars = set(range(1, 5)) | set(range(76, 81))
    section_starts = {9, 21, 24, 37, 49, 56, 63, 76}
    for bar in range(1, 81):
        start = (bar - 1) * 4.0
        if bar <= 2:
            continue
        if bar in section_starts and bar not in sparse_bars:
            out.append(NoteEvent(start, 0.15, 49, 70 if bar in chorus_bars else 56, channel=9))
        if bar in sparse_bars:
            if bar >= 76:
                out.append(NoteEvent(start, 0.12, 36, 45, channel=9))
            continue
        for eighth in range(8):
            velocity = 48 if eighth % 2 == 0 else 36
            if bar in chorus_bars:
                velocity += 8
            out.append(NoteEvent(start + eighth * 0.5, 0.1, 42, velocity, channel=9))
        for beat in (0.0, 2.0):
            out.append(NoteEvent(start + beat, 0.12, 36, 72 if bar in chorus_bars else 62, channel=9))
        for beat in (1.0, 3.0):
            out.append(NoteEvent(start + beat, 0.12, 38, 74 if bar in chorus_bars else 64, channel=9))
        if bar in chorus_bars:
            out.append(NoteEvent(start + 2.5, 0.12, 36, 54, channel=9))
        if bar in {8, 23, 36, 48, 55, 62, 75}:
            for beat, note in ((3.0, 45), (3.5, 47), (3.75, 50)):
                out.append(NoteEvent(start + beat, 0.1, note, 62, channel=9))
    return out


def scale_velocities(events: list[NoteEvent], factor: float) -> list[NoteEvent]:
    return [
        NoteEvent(event.start, event.duration, event.note, min(127, round(event.velocity * factor)), event.channel)
        for event in events
    ]


def save_midi(path: Path, tracks: list[mido.MidiTrack]) -> None:
    midi = mido.MidiFile(type=1, ticks_per_beat=TPB)
    midi.tracks.extend(tracks)
    midi.save(path)


def write_analysis_csvs(chords: list[ChordEvent]) -> None:
    with (ANALYSIS_DIR / "chord_map.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["bar", "beat_in_bar", "absolute_beat", "duration_beats", "chord"])
        for chord in chords:
            writer.writerow(
                [int(chord.start // 4) + 1, chord.start % 4 + 1, chord.start, chord.duration, chord.name]
            )
    with (ANALYSIS_DIR / "structure.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["start_bar", "end_bar", "section"])
        for index, (bar, name) in enumerate(SECTIONS):
            end = SECTIONS[index + 1][0] - 1 if index + 1 < len(SECTIONS) else 80
            writer.writerow([bar, end, name])


def main() -> None:
    MIDI_DIR.mkdir(exist_ok=True)
    chords = chord_map()
    write_analysis_csvs(chords)
    accompaniment, lead_events = load_accompaniment_events()

    conductor = conductor_track(chords)
    keys = note_track("Poly Synth Accompaniment (Transcribed)", 90, accompaniment)
    bass = note_track("Fingered Bass (Transcribed)", 33, load_bass_events())
    drums = note_track("Electronic Drums", 0, drum_events(), channel=9)
    vocal = note_track(
        "Vocal Melody Guide", 52, scale_velocities(load_vocal_events(), 1.22)
    )
    lead = note_track("Crystal Synth Line (Transcribed)", 98, lead_events)

    save_midi(MIDI_DIR / "00_full_arrangement.mid", [conductor, keys, bass, drums, vocal, lead])
    save_midi(MIDI_DIR / "01_accompaniment_transcribed.mid", [conductor_track(chords), keys])
    save_midi(MIDI_DIR / "02_bass_transcribed.mid", [conductor_track(chords), bass])
    save_midi(MIDI_DIR / "03_electronic_drums.mid", [conductor_track(chords), drums])
    save_midi(MIDI_DIR / "04_vocal_melody_guide.mid", [conductor_track(chords), vocal])
    save_midi(MIDI_DIR / "05_high_synth_transcribed.mid", [conductor_track(chords), lead])

    print(f"Generated {len(list(MIDI_DIR.glob('*.mid')))} MIDI files at {BPM:.3f} BPM.")


if __name__ == "__main__":
    main()
