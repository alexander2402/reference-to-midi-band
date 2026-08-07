# Project state — Анжелика Варум, “Городок”

## Status

**User-authored native revision preserved as the preferred initial sound direction; previous full-song render remains the promoted comparison baseline.**

The first reconstruction was rejected after rendered comparison confirmed that its block-chord accompaniment and simplified melody did not follow the recording closely enough. The rebuilt arrangement passed seven direct-MIDI iterations and five native passes. The user then simplified the native palette, added Bright Vocal audio, and saved two partial demonstrations. That exact state is retained as project-history tag `better-initial-output-example` and analyzed in `analysis/USER_INITIAL_OUTPUT_REVIEW.md`.

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
| Previous verified GarageBand export | 0.429 | 0.644 | 0.934 | 0.841 | 0.752 |

The direct MIDI render is `renders/00_full_arrangement.wav`. The promoted full-song native baseline remains `renders/Gorodok_Matched_GarageBand_verified.wav`; it predates the user's saved sound-direction example. The two partial user exports are under `renders/examples/user-simplified-instruments/`. Canonical results are in `analysis/midi_comparison.json`, `analysis/garageband_comparison.json`, and `analysis/COMPARISON.md`; the same-window example comparison is in `analysis/USER_INITIAL_OUTPUT_REVIEW.md`.

## Native GarageBand project

Primary project: `Gorodok_Matched.band`

Current saved project metadata:

- GarageBand 10.4.3, build 5433
- `77.733 BPM`, A minor, `4/4`
- 44.1 kHz
- seven active tracks
- all expected MIDI regions and track names

Saved patches and read-only volume observations:

| Track | GarageBand patch | Observed track-volume value |
|---|---|---:|
| Accompaniment | Classic Electric Piano | 233 |
| Bass | Upright Studio Bass | 233 |
| Drums | SoCal | 233 |
| Vocal guide | Female Chamber Choir | 233 |
| Bright Vocal 1 | Bright Vocal | 203 |
| Bright Vocal 2 | Bright Vocal | 203 |
| High line | Steinway Grand Piano | 233 |

The user-authored state was saved, closed, reopened, and inspected without modifying it. All patch names and the embedded Bright Vocal media persisted. The volume values above are historical read-only observations; producer rule PR-002 prohibits writing track or master volume. The partial MP3s are directional examples and do not replace the previous full-song export until a complete render passes the promotion gate. The degraded first native attempt remains only in `archive/Gorodok_Reconstruction_first_attempt.band`.

## Reproduction

```sh
make validate PROJECT=gorodok
make native-sync PROJECT=gorodok HYPOTHESIS="<measurable hypothesis>" PRIMARY_CHANGE="<one variable group>" PROMOTE=--promote
make audit PROJECT=gorodok
```

The native `sync` command applies `project.json`, protects existing volume values from mutation, saves, closes, reopens, verifies patches and metadata, exports a temporary candidate, compares it, records the result, and promotes it only when the KPI gate passes. The current control state is in `analysis/accepted_state.json`, `analysis/native_verification.json`, and `analysis/iteration_ledger.jsonl`.

## Remaining physical limitation

The reconstruction is not sample-identical to the mastered commercial recording. A MIDI choir cannot reproduce the original human vocal, and the original synthesizer programs, outboard processing, and mastering are unavailable. The current ceiling is therefore an aligned, editable reconstruction whose notes, harmony, structure, rhythm, and practical balance have been rendered and corrected against the source; it does not substitute the copyrighted source audio for MIDI parts.
