#!/usr/bin/env python3
"""Create an isolated track project inside projects/."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from studio_common import PROJECTS_ROOT


DIRECTORIES = (
    "analysis",
    "archive",
    "midi",
    "renders",
    "sources",
    ".studio/candidates",
)


def project_spec(slug: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "project_id": slug,
        "project_slug": slug,
        "title": "TODO",
        "artist": "TODO",
        "reference": {"path": "analysis/reference.wav", "url": "TODO"},
        "music": {
            "tempo_bpm": None,
            "key": None,
            "meter": None,
            "bars": None,
            "ticks_per_beat": 480,
        },
        "sections": [],
        "deliverables": {},
        "mix_policy": {
            "master_volume": "do_not_touch",
            "track_volume": "do_not_touch",
            "balance_method": "equalizer",
            "runtime_guard": "capture track-volume values before automation and fail if any value changes",
        },
        "garageband": {"application": "GarageBand", "tracks": []},
        "quality": {},
        "documentation": ["PROJECT.md"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Lowercase project slug, for example midnight-train")
    args = parser.parse_args()
    slug = args.name.strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise SystemExit("Project name must contain only lowercase letters, digits, and hyphens")

    destination = PROJECTS_ROOT / slug
    if destination.exists():
        raise SystemExit(f"Project already exists: {destination}")
    for relative in DIRECTORIES:
        path = destination / relative
        path.mkdir(parents=True, exist_ok=False)
        (path / ".gitkeep").touch()

    (destination / "project.json").write_text(
        json.dumps(project_spec(slug), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (destination / "PROJECT.md").write_text(
        f"# Project — {slug}\n\nStatus: initialized; reference confirmation pending.\n",
        encoding="utf-8",
    )
    print(destination)


if __name__ == "__main__":
    main()
