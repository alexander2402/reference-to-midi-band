# Gorodok project history

This directory is the tracked index for immutable project checkpoints. Revision manifests and refs are committed to Git; large snapshot objects live in the ignored `.history/objects/` store.

```sh
make history PROJECT=gorodok
make history-show PROJECT=gorodok REVISION=HEAD
STUDIO_PROJECT=gorodok .analysis-venv/bin/python scripts/project_history.py diff <older> <newer>
STUDIO_PROJECT=gorodok .analysis-venv/bin/python scripts/project_history.py materialize <revision-or-tag> /tmp/gorodok-history-view
```

`materialize` never overwrites the active project. It creates a separate readable copy, so looking into the past cannot destroy the present. A future remote artifact backend or Git LFS can mirror `.history/objects/`; the tracked hashes make missing or corrupted objects detectable.
