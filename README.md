# Городок — compared MIDI and verified GarageBand project

This workspace contains a rebuilt reconstruction of **“Городок” by Анжелика Варум**, matched against the official 1993 album recording from *Ля-Ля-Фа*.

## Play the native project

1. Open [`Gorodok_Matched.band`](Gorodok_Matched.band) in GarageBand.
2. Press Play.

The project is already set to **77.733 BPM**, **A minor**, **4/4**, and **80 bars**. It was saved, played, closed, reopened, inspected, and exported successfully in GarageBand 10.4.3. The final saved tracks are:

- Classic Electric Piano accompaniment
- Fingerstyle Bass
- SoCal drums
- Female Chamber Choir melody guide
- Glass Bells high synth

For an immediate listen without opening GarageBand, use [`renders/Gorodok_Matched_GarageBand_verified.wav`](renders/Gorodok_Matched_GarageBand_verified.wav). This WAV was exported after the final close/reopen verification, so it corresponds to the delivered `.band` state.

## Play or import the MIDI

The full arrangement is [`midi/00_full_arrangement.mid`](midi/00_full_arrangement.mid). Its direct Apple DLS render is [`renders/00_full_arrangement.wav`](renders/00_full_arrangement.wav); that render is the closest controlled test of the MIDI notes themselves.

Separate parts are also available:

- [`midi/01_accompaniment_transcribed.mid`](midi/01_accompaniment_transcribed.mid)
- [`midi/02_bass_transcribed.mid`](midi/02_bass_transcribed.mid)
- [`midi/03_electronic_drums.mid`](midi/03_electronic_drums.mid)
- [`midi/04_vocal_melody_guide.mid`](midi/04_vocal_melody_guide.mid)
- [`midi/05_high_synth_transcribed.mid`](midi/05_high_synth_transcribed.mid)

If importing the MIDI into another project, use **77.733 BPM**, **A minor**, **4/4**, and place it at bar 1.

## Musical map

| Bars | Section | Approximate reference time |
|---:|---|---:|
| 1–8 | Intro | 0:00.65 |
| 9–20 | Chorus 1 | 0:25.36 |
| 21–23 | Interlude 1 | 1:02.42 |
| 24–36 | Verse 1 | 1:11.69 |
| 37–48 | Chorus 2 | 1:51.84 |
| 49–55 | Instrumental | 2:28.91 |
| 56–62 | Verse 2, short | 2:50.53 |
| 63–75 | Chorus 3, extended | 3:12.15 |
| 76–80 | Outro | 3:52.30 |

## What changed after the rejected first attempt

The drums were preserved as the baseline. The accompaniment, bass, melody guide, high synth, exact tempo, levels, and GarageBand patches were rebuilt from separated reference parts and repeatedly rendered and compared.

The rejected MIDI render scored `0.832` for harmonic similarity and `0.126` for onset-envelope similarity. The selected MIDI render scores `0.947` and `0.707`. The verified native GarageBand export scores `0.934` and `0.644`; GarageBand's patches are darker than the direct MIDI renderer, but the notes, structure, and timing remain closely aligned.

See [`analysis/COMPARISON.md`](analysis/COMPARISON.md) for the full A/B history and [`PROJECT.md`](PROJECT.md) for validation and native-project evidence.

## Reusable studio workflow

The project is now driven by [`studio/project.json`](studio/project.json), not by remembered GarageBand clicks. The complete native verification/export/comparison gate is one command:

```sh
.analysis-venv/bin/python scripts/garageband_native.py sync \
  --hypothesis "<one measurable hypothesis>" \
  --primary-change "<one variable group>" \
  --promote
```

Before a new pass, run `scripts/studio_pipeline.py advise`. After changes, `scripts/audit_project.py` verifies the full STUDIO.md contract. Rejected candidates are recorded in `analysis/iteration_ledger.jsonl` but their temporary WAV files are not retained as more `v2`/`final2` versions.

The full retrospective and current structural result are in [`analysis/RETROSPECTIVE.md`](analysis/RETROSPECTIVE.md) and [`analysis/STRUCTURE_AUDIT.md`](analysis/STRUCTURE_AUDIT.md).

## Remaining limitation

MIDI instruments cannot reproduce the original singer, exact 1993 synthesizer patches, mix processing, and mastering sample-for-sample. The vocal track is therefore a pitch/rhythm guide rather than a replacement for Анжелика Варум's recorded performance. The original audio is retained only as analysis evidence and is not embedded in the reconstruction.
