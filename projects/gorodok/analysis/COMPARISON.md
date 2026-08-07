# Rendered comparison — “Городок”

## Reference and alignment

- Reference: the official album recording of Анжелика Варум — “Городок” from *Ля-Ля-Фа*.
- Reference file: `analysis/reference.wav`.
- Grid: `77.733 BPM`, `4/4`, A minor, 80 bars.
- Alignment: `0.648 s` of leading reference audio is removed before comparison.
- Direct MIDI renderer: Apple DLS through `AVAudioUnitSampler`, 44.1 kHz.
- Native renderer: GarageBand 10.4.3 project export, PCM WAV, 44.1 kHz, 16-bit stereo.
- Delivered native project: `Gorodok_Matched.band`.

The direct render tests the actual current MIDI independently of GarageBand patch choice. The native render separately tests the saved `.band` project. Full-song metrics and every form section are computed for both.

## Why the first pass was rejected

The original MIDI passed file-format checks but had not been rendered and compared. The first real A/B test supported the user's report:

- the drum pattern was the closest part;
- block chords replaced most reference accompaniment attacks and inner voices;
- the vocal guide incorrectly forced several chromatic pitches upward;
- the bass patch was too bright and its level was too low;
- the slightly wrong tempo accumulated timing drift over four minutes;
- no native GarageBand project had been created.

The drums were therefore retained as the baseline while the grid, accompaniment, melody, bass, high synth, patches, and mix were rebuilt.

## Direct MIDI render iterations

Higher is better for every similarity column.

| Pass | RMS envelope | Onset envelope | Chroma | MFCC timbre | Onset F1 | Main change |
|---|---:|---:|---:|---:|---:|---|
| Rejected baseline | 0.293 | 0.126 | 0.832 | 0.792 | 0.643 | Sparse block chords; no rendered correction loop |
| Iteration 2 | 0.532 | 0.399 | 0.946 | 0.819 | 0.713 | Reference-derived accompaniment and restored chromatic melody |
| Iteration 3 | 0.646 | 0.688 | 0.946 | 0.879 | 0.741 | Exact grid/downbeat; darker bass; patch search |
| Iteration 4, rejected | 0.253 | 0.697 | 0.932 | 0.863 | 0.770 | Deliberate level over-boost test |
| Iteration 5 | 0.522 | 0.697 | 0.946 | 0.875 | 0.759 | Reference-relative stem balance restored |
| Iteration 6 | 0.533 | 0.709 | 0.948 | 0.870 | 0.759 | Choir-like guide tested in the complete mix |
| Iteration 7, selected | 0.509 | 0.707 | 0.947 | 0.868 | 0.761 | Vocal level corrected to the separated reference balance |

Iteration 7 is the selected direct-MIDI state. Its file is `renders/00_full_arrangement.wav`.

## Selected MIDI part comparison

| Part | RMS envelope | Onset envelope | Chroma | MFCC timbre | Onset F1 | Finding |
|---|---:|---:|---:|---:|---:|---|
| Bass | 0.562 | 0.603 | 0.968 | 0.910 | 0.757 | Strong pitch agreement; a darker fingered-bass render fixed the first pass |
| Drums | 0.596 | 0.769 | — | 0.336 | 0.736 | Timing/pattern remain the strongest rhythmic result; the kit spectrum is still darker than the master |
| Vocal guide | 0.619 | 0.202 | 0.720 | 0.508 | 0.515 | Pitch/rhythm guide improved; a MIDI choir cannot model the singer's consonants and timbre |
| Accompaniment | 0.160 | 0.746 | 0.898 | 0.851 | 0.808 | Reference attacks and harmony are dense and aligned; the amplitude envelope still differs |

Selected reference-relative part levels are approximately: drums `-12.26 dB`, vocal `-4.41 dB`, and combined accompaniment `-5 dB`, all relative to bass.

## Native GarageBand iterations

The first native project existed but initially assigned the same animated pad to most melodic tracks. Each saved state below was exported and compared before the next change.

| Native pass | RMS envelope | Onset envelope | Chroma | MFCC timbre | Onset F1 | Median centroid | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Initial native | 0.524 | 0.406 | 0.845 | 0.881 | 0.581 | 1,849 Hz | Distinct MIDI notes, but nearly all tracks shared Epic Cloud Formation |
| Patch pass 2 | 0.776 | 0.641 | 0.578 | 0.845 | 0.764 | 499 Hz | Dynamics improved, but Deep Sub Bass at maximum level masked harmony |
| Patch pass 3 | 0.686 | 0.650 | 0.573 | 0.830 | 0.765 | 542 Hz | Female choir and brighter bell; bass masking remained |
| Mix pass 4 | 0.402 | 0.643 | 0.933 | 0.841 | 0.757 | 837 Hz | Fingerstyle Bass plus normalized faders restored harmonic clarity |
| Post-reopen verified | 0.429 | 0.644 | 0.934 | 0.841 | 0.752 | 859 Hz | Persisted patches; final export from freshly reopened project |

The verified native file is `renders/Gorodok_Matched_GarageBand_verified.wav`. Its strongest full-song evidence is harmonic alignment (`0.934`) and onset matching (`0.752` F1). It remains darker than the reference master: median centroid `859 Hz` versus `1,591 Hz`.

## Native project verification

The delivered `Gorodok_Matched.band` passed all required checks:

- opens in GarageBand 10.4.3;
- preserves `77.733 BPM`, A minor, `4/4`, 44.1 kHz, and six imported tracks;
- retains every expected track name and MIDI region;
- plays from the start;
- saves without corruption;
- closes and reopens;
- preserves final patches: Classic Electric Piano, Fingerstyle Bass, SoCal, Female Chamber Choir, and Glass Bells;
- records the then-current track-volume values as read-only verification evidence; current producer policy forbids changing them;
- exports a complete WAV after reopening;
- produces the documented verified comparison result.

The earlier degraded native attempt was moved to `archive/Gorodok_Reconstruction_first_attempt.band` so it cannot be confused with the delivery project.

## Remaining physical limitation

The commercial master contains a specific human performance, original 1993 synthesizer programs, studio effects, mix automation, and mastering. An editable MIDI reconstruction cannot be sample-identical without embedding the source recording itself. The reference is used only for analysis and A/B measurement; it is not substituted for the MIDI parts. The remaining largest audible difference is therefore the human vocal and original production timbre, not the song grid or overall harmonic structure.
