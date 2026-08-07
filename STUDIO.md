# Reference-to-MIDI / GarageBand Studio Rules

`PRODUCER_RULES.md` is the cumulative non-negotiable rulebook. This document defines the operating workflow; if the two conflict, the producer rules win.

## Analysis failure handling

- If beat tracking is unstable, try independent beat trackers, inspect onset patterns, and test half- and double-time interpretations.
- If polyphonic transcription is poor, separate the source before transcription and analyze vocals, bass, drums, and accompaniment independently.
- If bass is difficult to detect, isolate low-frequency/bass content and transcribe it independently.
- If harmony is ambiguous, combine chroma analysis, separated harmonic content, web evidence, bass motion, and musical reasoning.
- If an instrument is ambiguous, describe its functional or timbral class instead of inventing an exact instrument name.
- If a `.band` package becomes corrupted, preserve the evidence, lower confidence in the generation method, and fall back to a controlled GarageBand import workflow. Do not pretend that a directory ending in `.band` is a valid project.

## Canonical project structure

The repository is a projects producer. Every track uses one machine-readable source of truth at `projects/<track>/project.json`. Tempo, key, meter, form, deliverable paths, MIDI programs, native track names, patches, EQ intent, quality thresholds, and promotion rules belong there instead of being duplicated as untracked task memory.

Active workspace structure:

- `projects/<track>/`: the complete isolated track project—specification, project notes, native project, MIDI, renders, analysis, sources, candidates, and archive;
- `scripts/`: shared deterministic analysis, generation, rendering, native automation, audit, promotion, and project-scaffolding code;
- `studio/`: reusable producer knowledge and the new-machine manual fallback;
- `fixtures/`: deliberately named shared research/test projects;
- `tests/`: producer regression tests;
- `PRODUCER_RULES.md`: cumulative mandatory rules.

Never create root-level `analysis/`, `midi/`, `renders/`, `sources/`, or `archive/` directories. A new track is a new folder under `projects/`, analogous to adding a new page to an application.

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
- the root `README.md` describes the producer and project selection;
- the selected project's `PROJECT.md` reflects the current state;
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
6. Write the observed differences to `projects/<track>/analysis/COMPARISON.md` or an equivalent current report.
7. Correct the largest audible mismatch, render again, and repeat.

When both a portable MIDI file and a native project are deliverables, run this loop twice: once on a deterministic render of the MIDI itself and once on an export of the saved native project. Report their results separately. A good substitute-renderer result does not prove that the native patches sound correct, and a good native export does not prove that the portable MIDI will render similarly elsewhere.

Do not mark a project ready because the MIDI parses, contains the expected number of bars, or has plausible chords. Do not stop after one render. Continue until the render matches the reference with no material audible difference, or until the user explicitly accepts a documented remaining limitation.

When user feedback identifies which parts are closest, preserve those parts as the baseline and prioritize the parts the user says are wrong. Store project-specific feedback in `projects/<track>/project.json` or its iteration ledger; store only reusable evidence-backed lessons in `studio/knowledge.json`.

## Precision-first iteration and promotion

Before creating a candidate:

1. Read `studio/knowledge.json` through `scripts/studio_pipeline.py advise`.
2. State one measurable hypothesis and one primary variable group to change.
3. Predict which KPI should improve and which metrics must not regress.
4. Render the complete target once after the change.
5. Evaluate it through `scripts/studio_pipeline.py evaluate`.

A candidate is promoted only when it meets every declared minimum, improves the weighted score by the configured amount, and does not exceed the allowed regression in any protected metric. An unchanged or ambiguous candidate is rejected automatically. Rejected candidate audio is temporary and is not retained as another active version; its hypothesis, metrics, and decision remain in `projects/<track>/analysis/iteration_ledger.jsonl`.

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

Patch names alone are insufficient. After the final patch and EQ edits, save the project, close it, reopen it, and re-read patch assignments. Track-volume values may be read only as a mutation guard; the automation must stop if any value changes. The final verification render must be exported from that freshly reopened state.

Direct binary `.band` mutation remains experimental. Prefer a controlled workflow in which GarageBand opens a valid MIDI arrangement, creates native tracks, assigns patches, saves a new project, reopens it, and exports a verification render. A project is not delivered merely because a `.band` directory was created.

## Automation-first native workflow

Normal GarageBand work is code-driven through `scripts/garageband_native.py` and the selected project's canonical spec. The automation can bootstrap a project from the full MIDI, assign exact patches, guard volume values against mutation, save, close, reopen, verify metadata and patches, export, compare, and invoke the promotion gate. It contains no volume-writing action.

Master volume, master gain, track volume, and track gain are immutable. Balance must be approached through EQ first, followed when necessary by arrangement, register, velocity, articulation, density, and patch choice. Volume controls are never an optimization variable.

Use one `sync` command for a diagnosed native change. Do not reproduce the accessibility clicks interactively during ordinary work. Computer-use exploration is allowed only when GarageBand changes its UI or a previously unseen dialog makes the automation fail; once solved, encode the behavior and a regression test before continuing.

On a new machine, run `preflight` first. If GarageBand, its sound library, or macOS Accessibility blocks automation, use `studio/MANUAL_FALLBACK.md`. The fallback is a portability escape hatch, not the production default.

## Studio learning loop

The system must become more informed after every accepted or informative rejected pass:

- `projects/<track>/analysis/iteration_ledger.jsonl` records the hypothesis, primary change, artifact hash, metrics, and decision;
- `projects/<track>/analysis/accepted_state.json` records the exact promoted artifacts and KPI baseline;
- `studio/knowledge.json` stores reusable rules with trigger, action, evidence, scope, and confidence;
- `scripts/audit_project.py` verifies the delivery contract and KPI thresholds from the same spec;
- regression tests protect promotion logic, project isolation, and the immutable-volume rule.

Add a knowledge rule only when evidence generalizes beyond the current song. Keep song-specific facts in the project spec or comparison report. Review and deduplicate knowledge before starting a new project so the brain grows in signal rather than in prose volume.

## Project history

Use `scripts/project_history.py` for meaningful saved states of the same track. Each checkpoint stores immutable heavy artifacts locally and a small Git-tracked revision manifest containing the parent, hash, author, summary, and related Git commit. `history/refs.json` provides `HEAD` and human tags.

Create a checkpoint before changing a user-authored native project. Use `list`, `show`, and `diff` for navigation. Use `materialize` to open a past revision as a separate copy; do not silently replace the active project. This provides Git-like past/future navigation without polluting active deliverables with versioned filenames.

A user-authored checkpoint may be retained as an initial-output example without being promoted as the full-song canonical render. Record its comparison scope and separate reusable arrangement/sound lessons from one-off volume settings.

## Required delivery set

Unless the user requests otherwise, the finished workspace should contain:

- a verified native GarageBand `.band` project when GarageBand output is expected;
- the full multi-track MIDI and useful per-part MIDI files;
- a render of the delivered arrangement for immediate A/B review;
- a root `README.md` that explains project selection and minimal open/import/play discovery;
- a project-local `PROJECT.md` with the current evidence and confidence;
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
