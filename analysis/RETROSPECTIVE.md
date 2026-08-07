# Studio retrospective — structure, automation, and KPI

## Executive result

The musical delivery already satisfied the core reconstruction requirements, but the production system did not: the project state was split across Markdown, task history, filenames, and manual GarageBand actions. This retrospective moved those decisions into code and made the verified artifacts the only active versions.

The generated structure audit now passes with no failures or warnings. See `analysis/STRUCTURE_AUDIT.md`.

## STUDIO.md contract review

| Requirement | Before retrospective | Result now |
|---|---|---|
| Confirmed identity and exact recording | Documented | Pass; canonicalized in `studio/project.json` |
| BPM, key, meter, form, arrangement | Documented in several files | Pass; one machine-readable source of truth |
| Full and per-part MIDI | Present and validated | Pass; canonical filenames preserved |
| Direct rendered MIDI A/B | Present after seven attempts | Pass; selected report renamed `analysis/midi_comparison.json` |
| Native `.band` | Created and manually verified | Pass; project, patches, faders, metadata, and fingerprint are machine-verifiable |
| Native export A/B | Present | Pass; canonical report and render remain active |
| Save/close/reopen verification | Performed but stored only in task history | Pass; recorded in `analysis/native_verification.json` |
| Minimal user instructions | Present | Pass |
| Organized generated files | Trial artifacts mixed with active deliverables | Fixed; only two promoted WAVs remain in `renders/` |
| Reusable workflow | Manual exploration required | Fixed; one native `sync` command performs the complete cycle |
| Learning across projects | Lessons existed only in prose/history | Fixed; reusable evidence is stored in `studio/knowledge.json` |

## Structure correction

Active artifacts now use canonical names. Historical trial reports and approximately 8.5 GB of trial renders were moved to `archive/iterations/`; they no longer compete with the delivery files. GarageBand research packages were moved to `fixtures/garageband/`. The divergent live session found during this retrospective was preserved in `archive/live_sessions/` before the canonical project was reopened.

The active control plane is:

- `studio/project.json`: complete project specification and KPI policy;
- `studio/knowledge.json`: reusable evidence-backed rules;
- `analysis/accepted_state.json`: promoted artifact hashes and KPI baseline;
- `analysis/iteration_ledger.jsonl`: every evaluated hypothesis and decision;
- `analysis/native_verification.json`: persisted post-reopen native evidence;
- `scripts/audit_project.py`: delivery and KPI contract audit;
- `scripts/studio_pipeline.py`: advice, evaluation, rejection, and promotion;
- `scripts/garageband_native.py`: native bootstrap/synchronization/verification/export;
- `tests/test_studio_system.py`: promotion and control-mapping regression tests.

## Manual/computer-use removal

The native workflow is now:

```sh
.analysis-venv/bin/python scripts/garageband_native.py preflight
.analysis-venv/bin/python scripts/garageband_native.py sync \
  --hypothesis "<one measurable hypothesis>" \
  --primary-change "<one variable group>" \
  --promote
```

`sync` applies the spec, performs persistent slider drags, saves, closes, reopens, verifies every track/patch/fader and the project metadata, exports a temporary WAV, compares it with the reference, invokes the KPI gate, records the decision, and removes the temporary candidate. No manual GarageBand action is part of the normal path.

An end-to-end no-change replay completed successfully with `manual_actions_required: false`. The quality gate rejected it because its weighted score was `0.002075` below the accepted render. This is the intended behavior: reproducibility was proven without creating another “final” version or replacing a slightly better canonical artifact.

`studio/MANUAL_FALLBACK.md` remains for a new machine whose GarageBand version, installed sound library, or macOS Accessibility state fails preflight. Any newly discovered UI shape must be encoded in the automation before production continues.

## Version-count and precision policy

Before rendering a candidate, the operator must state one hypothesis and one primary change. Promotion requires:

- every target-specific KPI minimum;
- at least `0.003` weighted-score gain;
- no individual protected metric regression greater than `0.01`;
- a complete reference comparison, not an opening-section check.

Failed candidate audio is temporary. Its metrics and decision remain in the compact JSONL ledger, which retains learning without retaining gigabytes of indistinguishable WAV versions.

## Brain update policy

Every new pass begins with `scripts/studio_pipeline.py advise`. A learning enters `studio/knowledge.json` only when it has a reusable trigger, action, evidence, scope, and confidence. Song-specific facts remain in the project spec or comparison report. This prevents the “brain” from growing through duplicated narrative while preserving the decisions that materially improved later work.

The first reusable rules include exact-grid-first timing, separate MIDI/native comparisons, imported-fader inspection, patch-name skepticism, post-reopen export, user-confirmed baseline preservation, and diagnosis before candidate generation.

## Remaining engineering risk

GarageBand still exposes its full editing surface through macOS Accessibility rather than a supported project API. The automation therefore validates the tested app version, discovers exact patch search results, verifies every persisted value, and stops safely on an unknown UI. The bootstrap-from-MIDI path shares the now-tested Save dialog handling, but a new GarageBand release or missing sound-library patch can still trigger the documented manual fallback until its new behavior is encoded and tested.
