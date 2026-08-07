# Project state — Анжелика Варум, “Городок”

## Status

**Ready for review: rebuilt MIDI, verified native GarageBand project, and post-reopen export.**

The first reconstruction was rejected after rendered comparison confirmed that its block-chord accompaniment and simplified melody did not follow the recording closely enough. The current deliverable was rebuilt from separated reference parts, passed seven direct-MIDI render iterations, and then passed five native GarageBand patch/mix iterations.

## Confirmed reference

- Song: **Городок**
- Artist: **Анжелика Варум**
- Album: **Ля-Ля-Фа**
- Release: **1993**
- Exact analyzed recording: [official album upload](https://www.youtube.com/watch?v=CMU7_d6xSqQ)
- User-supplied identity page: [Russian Wikipedia](https://ru.wikipedia.org/wiki/%D0%93%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%BA_%28%D0%BF%D0%B5%D1%81%D0%BD%D1%8F_%D0%90%D0%BD%D0%B6%D0%B5%D0%BB%D0%B8%D0%BA%D0%B8_%D0%92%D0%B0%D1%80%D1%83%D0%BC%29)
- Reference file: `analysis/reference.wav`
- Reference duration: approximately `4:14`

## Musical grid and form

- Working tempo: `77.733 BPM`
- Meter: `4/4`
- Key: `A minor`
- Length: `80 bars`, `320 quarter-note beats`
- First aligned downbeat: `0.648 s` into the reference
- Form: intro 1–8; chorus 9–20; interlude 21–23; verse 24–36; chorus 37–48; instrumental 49–55; short verse 56–62; extended chorus 63–75; outro 76–80

Detailed maps are in `analysis/structure.csv` and `analysis/chord_map.csv`.

## Rebuilt arrangement

| MIDI track | Notes | Range | Source/function |
|---|---:|---:|---|
| Poly Synth Accompaniment (Transcribed) | 1,861 | C3–B4 | Dense reference-derived accompaniment attacks, inner voices, and harmony |
| Fingered Bass (Transcribed) | 209 | E1–C3 | Separated bass stem, pitch-tracked and quantized |
| Electronic Drums | 922 | GM 36–50 | Preserved rhythmic baseline with corrected long-form grid |
| Vocal Melody Guide | 257 | B-flat3–C5 | Sixteenth-note guide derived from the separated vocal |
| Crystal Synth Line (Transcribed) | 368 | C5–C6 | Separated high accompaniment/synth line |

The complete file has a conductor track plus the five musical tracks.

## MIDI validation

All six files pass `analysis/midi_validation.json`:

- Standard MIDI File format 1
- `480` ticks per quarter note
- tempo `77.732995 BPM`
- `4/4` time signature and A-minor key metadata
- exactly `320` quarter-note beats
- valid note ranges and positive durations
- no stuck notes

Files:

- `midi/00_full_arrangement.mid`
- `midi/01_accompaniment_transcribed.mid`
- `midi/02_bass_transcribed.mid`
- `midi/03_electronic_drums.mid`
- `midi/04_vocal_melody_guide.mid`
- `midi/05_high_synth_transcribed.mid`

## Rendered comparison

Higher is better in the following comparison. The reference and every render were aligned to the same downbeat and assessed over the complete song and each section.

| Render | RMS envelope | Onset envelope | Chroma | MFCC timbre | Onset F1 |
|---|---:|---:|---:|---:|---:|
| Rejected first MIDI render | 0.293 | 0.126 | 0.832 | 0.792 | 0.643 |
| Selected direct MIDI render | 0.509 | 0.707 | 0.947 | 0.868 | 0.761 |
| Verified GarageBand export | 0.429 | 0.644 | 0.934 | 0.841 | 0.752 |

The direct MIDI render is `renders/00_full_arrangement.wav`. The post-reopen native export is `renders/Gorodok_Matched_GarageBand_verified.wav`. Canonical results are in `analysis/midi_comparison.json`, `analysis/garageband_comparison.json`, and `analysis/COMPARISON.md`; rejected historical reports are under `archive/iterations/analysis/`.

## Native GarageBand project

Primary project: `Gorodok_Matched.band`

Verified project metadata:

- GarageBand 10.4.3, build 5433
- `77.733 BPM`, A minor, `4/4`
- 44.1 kHz
- six imported tracks including the conductor track
- all expected MIDI regions and track names

Verified saved patches:

| Track | GarageBand patch | Saved fader value |
|---|---|---:|
| Accompaniment | Classic Electric Piano | 173 |
| Bass | Fingerstyle Bass | 153 |
| Drums | SoCal | 173 |
| Vocal guide | Female Chamber Choir | 173 |
| High synth | Glass Bells | 163 |

The final state was saved, played, closed, reopened, and re-inspected. All patch names and fader values persisted. The verified WAV was exported from that reopened state. The degraded first native attempt is retained only as `archive/Gorodok_Reconstruction_first_attempt.band` and is not a deliverable.

## Reproduction

```sh
.analysis-venv/bin/python scripts/generate_reconstruction.py
.analysis-venv/bin/python scripts/validate_midis.py
scripts/render_midi midi/00_full_arrangement.mid renders/00_full_arrangement.wav 90,33,0,52,98
.analysis-venv/bin/python scripts/compare_garageband_render.py --render Gorodok_Matched_GarageBand_verified.wav --output garageband_comparison.json
.analysis-venv/bin/python scripts/garageband_native.py sync --hypothesis "<measurable hypothesis>" --primary-change "<one variable group>" --promote
.analysis-venv/bin/python scripts/audit_project.py
```

The native `sync` command applies `studio/project.json`, saves, closes, reopens, verifies patches/faders/metadata, exports a temporary candidate, compares it, records the result, and promotes it only when the KPI gate passes. The current control state is in `analysis/accepted_state.json`, `analysis/native_verification.json`, and `analysis/iteration_ledger.jsonl`.

## Remaining physical limitation

The reconstruction is not sample-identical to the mastered commercial recording. A MIDI choir cannot reproduce the original human vocal, and the original synthesizer programs, outboard processing, and mastering are unavailable. The current ceiling is therefore an aligned, editable reconstruction whose notes, harmony, structure, rhythm, and practical balance have been rendered and corrected against the source; it does not substitute the copyrighted source audio for MIDI parts.
