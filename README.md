# Reference-to-MIDI producer

This repository is a reusable producer system. It does not represent one song: every track is an isolated module under `projects/<track>/`, while shared analysis, GarageBand automation, KPI gates, tests, and accumulated knowledge live at the root.

## Project layout

```text
reference-to-midi-band/
├── projects/
│   └── gorodok/
│       ├── project.json
│       ├── PROJECT.md
│       ├── Gorodok_Matched.band
│       ├── midi/
│       ├── renders/
│       ├── analysis/
│       ├── sources/
│       ├── .studio/candidates/
│       └── archive/
├── scripts/                  shared producer engine
├── studio/                   shared knowledge and fallback
├── fixtures/                 shared GarageBand research fixtures
├── tests/                    producer regression tests
├── PRODUCER_RULES.md         cumulative non-negotiable rules
└── STUDIO.md                 operating workflow
```

See [`projects/README.md`](projects/README.md) for the per-track contract and [`PRODUCER_RULES.md`](PRODUCER_RULES.md) for the cumulative rules.

## Current projects

- [`projects/gorodok/`](projects/gorodok/) — Анжелика Варум, “Городок”. The preserved [`Gorodok_Matched.band`](projects/gorodok/Gorodok_Matched.band) and separate [`Gorodok_Matched-lisiy-final.band`](projects/gorodok/Gorodok_Matched-lisiy-final.band) are both retained and Git-tracked as binary project artifacts.

## Add a track

```sh
make new-project NAME=<track-slug>
```

This creates the complete isolated project shell. Fill its `project.json`, then select it for every producer command:

```sh
make audit PROJECT=<track-slug>
make validate PROJECT=<track-slug>
make native-preflight PROJECT=<track-slug>
```

`PROJECT=gorodok` is the current default.

## Precision workflow

Before a candidate, state one measurable hypothesis and one primary change. The native synchronization performs the save/reopen verification, full-reference export and comparison, KPI gate, decision ledger update, and cleanup of rejected candidate audio.

```sh
make native-sync \
  PROJECT=<track-slug> \
  HYPOTHESIS="<one measurable hypothesis>" \
  PRIMARY_CHANGE="<one variable group>" \
  PROMOTE=--promote
```

Master and track volume are immutable. The producer never writes them; runtime automation records the current track values and stops if they change. Balance is shaped with EQ, arrangement, velocity, articulation, register, density, or patch choice.

## Navigate project history

Meaningful native-project states use immutable checkpoints rather than `v2` filenames:

```sh
make history PROJECT=gorodok
make history-show PROJECT=gorodok REVISION=HEAD
STUDIO_PROJECT=gorodok .analysis-venv/bin/python scripts/project_history.py diff <older> <newer>
STUDIO_PROJECT=gorodok .analysis-venv/bin/python scripts/project_history.py materialize <revision-or-tag> /tmp/history-view
```

Git tracks revision manifests, refs, summaries, and hashes. Immutable checkpoint snapshots also remain in the local `.history/objects/` store and can later be mirrored through Git LFS or an artifact backend without changing the history model.

The active user-saved `.band` packages and named user exports are tracked directly as binary Git artifacts. Large references, generated candidates, archives, fixtures, and local history objects remain excluded. Git LFS is preferred for future remote scaling but was unavailable during the current setup.
