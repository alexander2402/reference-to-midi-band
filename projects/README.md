# Track projects

Each non-template directory here is one independent track project. A new track is added with:

```sh
make new-project NAME=<track-slug>
```

The producer commands select a project with `PROJECT=<track-slug>`; `gorodok` is the default while it is the only active track.

Every project owns:

- `project.json` — machine-readable musical, delivery, GarageBand, and KPI contract;
- `PROJECT.md` — current human-readable project state;
- `midi/`, `renders/`, `analysis/`, and `sources/` — active track artifacts;
- `.studio/candidates/` — temporary gated candidates;
- `archive/` — rejected or historical material.

Shared scripts, rules, knowledge, tests, and GarageBand fixtures belong at the repository root.
