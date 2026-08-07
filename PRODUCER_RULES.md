# Producer rules

This is the cumulative rulebook for the repository. Add new durable rules here as they are learned. Project-specific facts belong in `projects/<track>/project.json`; reusable evidence belongs in `studio/knowledge.json`.

Rules are mandatory unless the user explicitly replaces one. When automation changes, protect the rule with an audit check or regression test whenever possible.

## PR-001 — Every track is a project

Each new song or track must live in its own `projects/<track>/` directory. The repository root is the producer system, not a song workspace.

A project owns its `project.json`, `PROJECT.md`, native project, MIDI, sources, renders, analysis, candidates, and archive. Shared automation, tests, templates, and producer knowledge remain at the repository root. Track-specific artifacts must never leak back into root-level `analysis/`, `midi/`, `renders/`, `sources/`, or `archive/` directories.

## PR-002 — Never change volume

Never change master volume, master gain, track volume, or track gain—manually or through automation. These controls are read-only. Capture existing track-volume values only to detect accidental mutation.

Shape tonal balance and perceived prominence with equalization. If EQ cannot solve a balance problem, diagnose arrangement, octave, velocity, articulation, patch choice, density, or masking; do not reach for a volume control.

## PR-003 — Track completed producer changes in Git

Producer code, rules, tests, project specifications, MIDI, and compact analysis evidence must be committed as coherent checkpoints after validation. When the user explicitly requires Git protection for active native packages, track only the active `projects/<track>/*.band` packages and named user exports as binary artifacts; keep candidates, fixtures, local history objects, and archives ignored. Prefer Git LFS when it is available.

## PR-004 — Version projects with checkpoints, not filenames

Never create `final2`, `v7`, or similar copies to represent the history of one track. Before a meaningful user edit or automated experiment, create an immutable project checkpoint with a parent, content hash, author, concise summary, and optional tag.

Git tracks the checkpoint manifests and refs. Large `.band` and audio objects live in the project's `.history/objects/` store. Navigate with `HEAD`, tags, revision prefixes, `list`, `show`, and `diff`. Looking into the past must use `materialize` to a separate destination; it must never overwrite the active project implicitly.
