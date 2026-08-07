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

- [`projects/gorodok/`](projects/gorodok/) — Анжелика Варум, “Городок”. Open [`Gorodok_Matched.band`](projects/gorodok/Gorodok_Matched.band), or listen to [`Gorodok_Matched_GarageBand_verified.wav`](projects/gorodok/renders/Gorodok_Matched_GarageBand_verified.wav).

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

Large generated audio, native `.band` packages, references, candidates, archives, and fixtures are intentionally excluded from Git. The reproducible producer code, rules, tests, specifications, MIDI, and compact evidence are tracked.
