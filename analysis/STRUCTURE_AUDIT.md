# Project structure audit

Overall status: **PASS**. Passed: 70; failed: 0; warnings: 0.

| Status | Check | Evidence |
|---|---|---|
| PASS | Studio rules | STUDIO.md exists |
| PASS | Canonical project spec | studio/project.json exists |
| PASS | Reusable knowledge | studio/knowledge.json exists |
| PASS | New-machine fallback | Manual fallback exists |
| PASS | Deliverable: native_project | Gorodok_Matched.band |
| PASS | Deliverable: full_midi | midi/00_full_arrangement.mid |
| PASS | Deliverable: part_midis | midi/01_accompaniment_transcribed.mid |
| PASS | Deliverable: part_midis | midi/02_bass_transcribed.mid |
| PASS | Deliverable: part_midis | midi/03_electronic_drums.mid |
| PASS | Deliverable: part_midis | midi/04_vocal_melody_guide.mid |
| PASS | Deliverable: part_midis | midi/05_high_synth_transcribed.mid |
| PASS | Deliverable: midi_render | renders/00_full_arrangement.wav |
| PASS | Deliverable: native_render | renders/Gorodok_Matched_GarageBand_verified.wav |
| PASS | Deliverable: midi_comparison | analysis/midi_comparison.json |
| PASS | Deliverable: native_comparison | analysis/garageband_comparison.json |
| PASS | Deliverable: midi_validation | analysis/midi_validation.json |
| PASS | Deliverable: native_verification | analysis/native_verification.json |
| PASS | Deliverable: accepted_state | analysis/accepted_state.json |
| PASS | Deliverable: iteration_ledger | analysis/iteration_ledger.jsonl |
| PASS | Deliverable: structure_audit | analysis/STRUCTURE_AUDIT.md |
| PASS | Deliverable: comparison_report | analysis/COMPARISON.md |
| PASS | Documentation | STUDIO.md |
| PASS | Documentation | README.md |
| PASS | Documentation | PROJECT.md |
| PASS | Documentation | analysis/COMPARISON.md |
| PASS | Documentation | studio/MANUAL_FALLBACK.md |
| PASS | Section coverage | Sections cover bars 1–80 exactly once |
| PASS | MIDI technical validation | analysis/midi_validation.json |
| PASS | MIDI tempo matches spec | 77.733 BPM |
| PASS | MIDI length matches spec | 80 bars |
| PASS | direct_midi KPI: rms_envelope_correlation | actual=0.50935, minimum=0.48000 |
| PASS | direct_midi KPI: onset_envelope_correlation | actual=0.70695, minimum=0.70000 |
| PASS | direct_midi KPI: chroma_cosine_similarity | actual=0.94744, minimum=0.94000 |
| PASS | direct_midi KPI: mfcc_timbre_similarity | actual=0.86843, minimum=0.86000 |
| PASS | direct_midi KPI: onset_f1 | actual=0.76108, minimum=0.75000 |
| PASS | native KPI: rms_envelope_correlation | actual=0.42903, minimum=0.40000 |
| PASS | native KPI: onset_envelope_correlation | actual=0.64350, minimum=0.62000 |
| PASS | native KPI: chroma_cosine_similarity | actual=0.93434, minimum=0.92000 |
| PASS | native KPI: mfcc_timbre_similarity | actual=0.84141, minimum=0.83000 |
| PASS | native KPI: onset_f1 | actual=0.75225, minimum=0.74000 |
| PASS | Accepted-state project identity | analysis/accepted_state.json |
| PASS | Accepted artifact hash: direct_midi | renders/00_full_arrangement.wav |
| PASS | Accepted artifact hash: native | renders/Gorodok_Matched_GarageBand_verified.wav |
| PASS | Post-reopen native verification | analysis/native_verification.json |
| PASS | Persisted fader evidence: track 2 | actual=173, expected=173 |
| PASS | Persisted fader evidence: track 3 | actual=153, expected=153 |
| PASS | Persisted fader evidence: track 4 | actual=173, expected=173 |
| PASS | Persisted fader evidence: track 5 | actual=173, expected=173 |
| PASS | Persisted fader evidence: track 6 | actual=163, expected=163 |
| PASS | Iteration decision ledger | entries=1 |
| PASS | Native tempo | 77.73300170898438 |
| PASS | Native key | A minor |
| PASS | Native meter | 4/4 |
| PASS | Native track count | 6 |
| PASS | Native sample rate | 44100 |
| PASS | Persisted native patch: track 1 | Steinway Grand Piano |
| PASS | Persisted native name: track 1 | Conductor |
| PASS | Persisted native patch: track 2 | Classic Electric Piano |
| PASS | Persisted native name: track 2 | Poly Synth Accompaniment (Transcribed) |
| PASS | Persisted native patch: track 3 | Fingerstyle Bass |
| PASS | Persisted native name: track 3 | Fingered Bass (Transcribed) |
| PASS | Persisted native patch: track 4 | SoCal |
| PASS | Persisted native name: track 4 | Electronic Drums |
| PASS | Persisted native patch: track 5 | Female Chamber Choir |
| PASS | Persisted native name: track 5 | Vocal Melody Guide |
| PASS | Persisted native patch: track 6 | Glass Bells |
| PASS | Persisted native name: track 6 | Crystal Synth Line (Transcribed) |
| PASS | Workspace organization | missing=[] |
| PASS | Canonical artifact naming | No trial versions in active analysis/renders |
| PASS | Root directory cleanliness | root audio=[] |

This audit is generated from `studio/project.json`; it verifies both the STUDIO.md delivery contract and the promoted KPI thresholds.
