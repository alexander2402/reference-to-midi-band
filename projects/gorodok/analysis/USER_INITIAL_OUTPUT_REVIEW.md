# User-authored initial-output review

## Preserved state

The saved GarageBand project and both user exports are preserved as immutable history revision `20260807T131140Z-user-simplified-instruments-e1505efe`, tagged `better-initial-output-example`.

This revision is the preferred **initial sound direction**, not yet a promoted full-song replacement. Both demonstrations cover `131.291` seconds—intro, first chorus, interlude, first verse, and roughly half of chorus 2.

## What changed

| Role | Previous native state | User-authored state | Reusable interpretation |
|---|---|---|---|
| Conductor placeholder | Steinway Grand Piano track | Removed | Do not expose a technical/conductor track in the first listening mix |
| Accompaniment | Classic Electric Piano | Classic Electric Piano | Keep the clear, familiar harmonic anchor |
| Bass | Fingerstyle Bass | Upright Studio Bass | Prefer the simpler acoustic identity when it reads more naturally |
| Drums | SoCal | SoCal | Preserve the user-confirmed rhythmic baseline |
| Melody guide | Female Chamber Choir | Female Chamber Choir | Retain as a MIDI guide rather than asking it to sound like the singer |
| Vocal sound | No audio vocal | Two Bright Vocal audio tracks | Introduce a human-like vocal cue earlier in the first output |
| High line | Glass Bells | Steinway Grand Piano | Replace decorative synthetic brightness with a familiar core instrument first |

The saved project contains seven active tracks. Its existing volume observations are `233` for the five instrument/guide tracks and `203` for both Bright Vocal tracks. They are preserved as historical state, but they are **not** part of the reusable recipe: producer rule PR-002 prohibits changing master or track volume. Future balance work uses EQ and musical/spectral decisions.

## Same-window audio comparison

All three rows below use the same first `131.291` seconds of the aligned reference. Higher is better except spectral centroid, where closeness to the reference value (`1547.83 Hz`) is the useful comparison.

| Output | RMS envelope | Onset envelope | Chroma | Timbre | Onset F1 | Centroid |
|---|---:|---:|---:|---:|---:|---:|
| Previous accepted native render | 0.45366 | 0.67971 | 0.92872 | 0.83245 | 0.74537 | 863.66 Hz |
| User vocal test 1 | 0.47157 | 0.19742 | 0.93048 | 0.83313 | 0.76574 | 1177.14 Hz |
| User vocal test 2 | **0.48140** | 0.18504 | 0.93038 | 0.82123 | 0.75971 | **1335.19 Hz** |

The measurements support the user's perceptual judgment in several useful ways:

- both examples improve the broad loudness contour, harmonic identity, onset F1, and reference-like brightness over the same time window;
- test 1 slightly improves timbre similarity as well;
- test 2 moves the spectral center substantially closer to the recording and has the best loudness-envelope match, which helps explain why the simpler sound feels clearer and more present;
- onset-envelope correlation falls sharply even though onset F1 rises. Events remain plausibly timed, but their strength contour differs from the recording. This is the main diagnostic to address after adopting the better palette.

The detailed reports are `analysis/user_vocal_test_1_comparison.json`, `analysis/user_vocal_test_2_comparison.json`, and `analysis/accepted_native_first_131s_comparison.json`.

## Better initial-output recipe

For the next track, the first native output should:

1. establish the exact grid, form, harmony, bass motion, and drum identity;
2. use the smallest credible palette for the core roles;
3. prefer familiar acoustic/electric patches before decorative or highly synthetic substitutes;
4. include a credible human-like vocal cue early when one is available;
5. keep optional high lines and ear-candy out until the core A/B is convincing;
6. compare a representative early sample for fast sound-direction feedback, then require a full-song comparison before promotion;
7. preserve volume controls and solve balance through EQ, register, arrangement, articulation, density, velocity, and patch selection.

The two Bright Vocal tracks are preserved exactly in the checkpoint. They should not automatically become a duplication pattern for new projects; one vocal source is the initial default unless duplication has an intentional arrangement or stereo purpose rather than a loudness purpose.
