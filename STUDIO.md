# Reference-to-MIDI / GarageBand Studio Rules

## Analysis failure handling

- If beat tracking is unstable, try independent beat trackers, inspect onset patterns, and test half- and double-time interpretations.
- If polyphonic transcription is poor, separate the source before transcription and analyze vocals, bass, drums, and accompaniment independently.
- If bass is difficult to detect, isolate low-frequency/bass content and transcribe it independently.
- If harmony is ambiguous, combine chroma analysis, separated harmonic content, web evidence, bass motion, and musical reasoning.
- If an instrument is ambiguous, describe its functional or timbral class instead of inventing an exact instrument name.
- If a `.band` package becomes corrupted, preserve the evidence, lower confidence in the generation method, and fall back to a controlled GarageBand import workflow. Do not pretend that a directory ending in `.band` is a valid project.

## Canonical project structure

Every project uses one machine-readable source of truth at `studio/project.json`. Tempo, key, meter, form, deliverable paths, MIDI programs, native track names, patches, faders, quality thresholds, and promotion rules belong there instead of being duplicated as untracked task memory.

Active workspace structure:

- `studio/`: canonical project specification, reusable knowledge, and the new-machine manual fallback;
- `midi/`: one promoted full MIDI plus useful promoted part files;
- `renders/`: one promoted direct-MIDI render and one promoted native-project render;
- `analysis/`: canonical validation, comparison, maps, and current reports;
- `scripts/`: deterministic analysis, generation, rendering, native automation, audit, and promotion code;
- `sources/`: reference acquisition evidence;
- `fixtures/`: deliberately named research/test projects;
- `tests/`: regression tests for the studio system;
- `archive/`: rejected historical artifacts that are not active deliverables.

Do not use `v2`, `final2`, or numbered trial filenames in the active deliverable directories. Candidates are temporary. Only a candidate that passes the promotion gate replaces a canonical artifact.

## Definition of Done — First Usable Reconstruction

A reconstruction is ready only when:

- reference identity is confirmed;
- the exact analyzed recording is known;
- BPM is established;
- key is established;
- meter is established;
- structure is mapped;
- core arrangement is identified;
- important harmony is reconstructed;
- important instrumental parts have MIDI;
- MIDI files pass technical validation;
- the generated arrangement has been rendered to audio;
- the rendered audio has been aligned and compared with the reference;
- material sound differences have been corrected through repeated render/compare iterations;
- significant uncertainties are documented;
- web/audio discrepancies have been reconciled where practical;
- `README.md` contains minimal GarageBand setup instructions;
- `PROJECT.md` reflects the current state;
- generated files are organized and clearly named.

The objective is first usable playback before optional polish, but technical MIDI validity alone is never sufficient.

## Mandatory rendered-audio A/B loop

Every reconstruction must use this loop:

1. Render the actual current deliverable to audio. Prefer the target GarageBand project and its selected patches; use a clearly identified substitute renderer only while the native project is not yet available.
2. Time-align the render with the exact reference recording.
3. Compare the complete track and every section, not only the opening bars.
4. Measure and inspect at least:
   - tempo, downbeat, bar-grid, and section-boundary alignment;
   - melody pitch, rhythm, phrasing, range, and rests;
   - chord identity, inversions, harmonic rhythm, and bass motion;
   - drum onsets, pattern, fills, density, and section changes;
   - instrumentation, register, stereo placement, spectral balance, dynamics, and fade behavior.
5. Perform a perceptual A/B check in addition to numeric validation.
6. Write the observed differences to `analysis/COMPARISON.md` or an equivalent current report.
7. Correct the largest audible mismatch, render again, and repeat.

When both a portable MIDI file and a native project are deliverables, run this loop twice: once on a deterministic render of the MIDI itself and once on an export of the saved native project. Report their results separately. A good substitute-renderer result does not prove that the native patches sound correct, and a good native export does not prove that the portable MIDI will render similarly elsewhere.

Do not mark a project ready because the MIDI parses, contains the expected number of bars, or has plausible chords. Do not stop after one render. Continue until the render matches the reference with no material audible difference, or until the user explicitly accepts a documented remaining limitation.

When user feedback identifies which parts are closest, preserve those parts as the baseline and prioritize the parts the user says are wrong. Store project-specific feedback in `studio/project.json` or the iteration ledger; store only reusable evidence-backed lessons in `studio/knowledge.json`.

## Precision-first iteration and promotion

Before creating a candidate:

1. Read `studio/knowledge.json` through `scripts/studio_pipeline.py advise`.
2. State one measurable hypothesis and one primary variable group to change.
3. Predict which KPI should improve and which metrics must not regress.
4. Render the complete target once after the change.
5. Evaluate it through `scripts/studio_pipeline.py evaluate`.

A candidate is promoted only when it meets every declared minimum, improves the weighted score by the configured amount, and does not exceed the allowed regression in any protected metric. An unchanged or ambiguous candidate is rejected automatically. Rejected candidate audio is temporary and is not retained as another active version; its hypothesis, metrics, and decision remain in `analysis/iteration_ledger.jsonl`.

This policy reduces version count by improving diagnosis before rendering, not by hiding failed measurements.

## Definition of Done — Native `.band`

When the user expects a GarageBand project, a native project is a required deliverable. It must not be silently omitted or replaced by MIDI-only instructions.

Native GarageBand project support is demonstrated only when controlled tests show that the delivered project:

- opens successfully in GarageBand;
- preserves the expected tempo, key, and meter;
- contains the expected named tracks;
- contains the expected musical regions and events;
- uses intentionally selected patches or clearly documented functional substitutes;
- plays from bar 1 without manual repair;
- can be saved, closed, and reopened without corruption;
- can be rendered or exported for comparison;
- reproduces reliably across repeated tests;
- does not depend on unexplained accidental state from a template.

Patch names alone are insufficient. After the final patch and mix edits, save the project, close it, reopen it, and re-read both patch assignments and fader values. The final verification render must be exported from that freshly reopened state. This catches edits that were audible in one session but were not actually persisted in the `.band` package.

Direct binary `.band` mutation remains experimental. Prefer a controlled workflow in which GarageBand opens a valid MIDI arrangement, creates native tracks, assigns patches, saves a new project, reopens it, and exports a verification render. A project is not delivered merely because a `.band` directory was created.

## Automation-first native workflow

Normal GarageBand work is code-driven through `scripts/garageband_native.py` and the canonical spec. The automation can bootstrap a project from the full MIDI, assign exact patches, set persistent faders with real slider events, save, close, reopen, verify metadata/patches/faders, export, compare, and invoke the promotion gate.

Use one `sync` command for a diagnosed native change. Do not reproduce the accessibility clicks interactively during ordinary work. Computer-use exploration is allowed only when GarageBand changes its UI or a previously unseen dialog makes the automation fail; once solved, encode the behavior and a regression test before continuing.

On a new machine, run `preflight` first. If GarageBand, its sound library, or macOS Accessibility blocks automation, use `studio/MANUAL_FALLBACK.md`. The fallback is a portability escape hatch, not the production default.

## Studio learning loop

The system must become more informed after every accepted or informative rejected pass:

- `analysis/iteration_ledger.jsonl` records the hypothesis, primary change, artifact hash, metrics, and decision;
- `analysis/accepted_state.json` records the exact promoted artifacts and KPI baseline;
- `studio/knowledge.json` stores reusable rules with trigger, action, evidence, scope, and confidence;
- `scripts/audit_project.py` verifies the delivery contract and KPI thresholds from the same spec;
- regression tests protect the promotion logic and known GarageBand control mappings.

Add a knowledge rule only when evidence generalizes beyond the current song. Keep song-specific facts in the project spec or comparison report. Review and deduplicate knowledge before starting a new project so the brain grows in signal rather than in prose volume.

## Required delivery set

Unless the user requests otherwise, the finished workspace should contain:

- a verified native GarageBand `.band` project when GarageBand output is expected;
- the full multi-track MIDI and useful per-part MIDI files;
- a render of the delivered arrangement for immediate A/B review;
- `README.md` with minimal open/import/play instructions;
- `PROJECT.md` with the current evidence and confidence;
- a current comparison report describing the render/reference differences and the iterations used to correct them;
- technical validation results.

## User interaction philosophy

Keep user-facing interaction concise. Do the complex work internally and document it on disk.

Target interaction:

```text
User:
<song URL>

Codex:
I understand this as “[Song]” by [Artist], [specific version if relevant].
Correct?

User:
Yes.

Codex:
<autonomous analysis, reconstruction, rendering, comparison, iteration, and project creation>

Codex:
Ready.

GarageBand:
1. Open the delivered project.
2. Confirm BPM/key/meter if needed.
3. Press Play.

Important uncertainties:
...
```

That is the target UX.
