#!/usr/bin/env python3
"""Create and navigate immutable, Git-like checkpoints for a track project."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from studio_common import DEFAULT_SPEC, REPO_ROOT, ROOT, atomic_write_json, load_json, load_spec


HISTORY = ROOT / "history"
REVISIONS = HISTORY / "revisions"
REFS = HISTORY / "refs.json"
OBJECTS = ROOT / ".history" / "objects"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not result:
        raise ValueError("A checkpoint label must contain a letter or digit")
    return result[:64]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_hash(path: Path) -> str:
    if path.is_file():
        return file_hash(path)
    digest = hashlib.sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        relative = item.relative_to(path)
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash(item).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def artifact_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def project_path(value: str | Path) -> Path:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise ValueError(f"Checkpoint artifacts must remain inside {ROOT}: {resolved}")
    return resolved


def git_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def read_refs() -> dict[str, Any]:
    if REFS.exists():
        return load_json(REFS)
    return {"schema_version": 1, "head": None, "tags": {}}


def resolve_revision(value: str) -> str:
    refs = read_refs()
    if value.upper() == "HEAD":
        if not refs.get("head"):
            raise ValueError("Project history has no HEAD")
        return str(refs["head"])
    if value in refs.get("tags", {}):
        return str(refs["tags"][value])
    matches = sorted(path.stem for path in REVISIONS.glob(f"{value}*.json"))
    if len(matches) != 1:
        raise ValueError(f"Revision {value!r} resolved to {len(matches)} matches")
    return matches[0]


def copy_artifact(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        clone = subprocess.run(
            ["cp", "-cR", str(source), str(destination)],
            text=True,
            capture_output=True,
            check=False,
        )
        if clone.returncode != 0:
            shutil.rmtree(destination, ignore_errors=True)
            shutil.copytree(source, destination)
    else:
        try:
            subprocess.run(
                ["cp", "-c", str(source), str(destination)],
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            destination.unlink(missing_ok=True)
            shutil.copy2(source, destination)


def artifact_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "kind": "directory" if path.is_dir() else "file",
        "sha256": artifact_hash(path),
        "bytes": artifact_size(path),
    }


def checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    spec = load_spec(Path(args.spec))
    native = project_path(spec["deliverables"]["native_project"])
    paths = [native, *(project_path(value) for value in args.include)]
    unique: list[Path] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        if path not in unique:
            unique.append(path)

    artifacts = [artifact_record(path) for path in unique]
    content = hashlib.sha256(
        json.dumps(artifacts, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    revision = f"{timestamp}-{slug(args.label)}-{content[:8]}"
    revision_file = REVISIONS / f"{revision}.json"
    object_destination = OBJECTS / revision
    if revision_file.exists() or object_destination.exists():
        raise FileExistsError(revision)

    refs = read_refs()
    temporary_root = ROOT / ".history" / "tmp"
    temporary_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f"{revision}-", dir=temporary_root))
    try:
        for path in unique:
            copy_artifact(path, stage / "artifacts" / path.relative_to(ROOT))
        object_destination.parent.mkdir(parents=True, exist_ok=True)
        stage.replace(object_destination)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    manifest = {
        "schema_version": 1,
        "revision": revision,
        "project_id": spec["project_id"],
        "created_at": now(),
        "author": args.author,
        "label": args.label,
        "summary": args.summary,
        "parent": refs.get("head"),
        "content_sha256": content,
        "git_commit": git_commit(),
        "artifacts": artifacts,
        "object_store": f".history/objects/{revision}/artifacts",
    }
    revision_file.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(revision_file, manifest)
    refs["head"] = revision
    if args.tag:
        refs.setdefault("tags", {})[args.tag] = revision
    atomic_write_json(REFS, refs)
    return manifest


def list_revisions(as_json: bool) -> Any:
    rows = [load_json(path) for path in sorted(REVISIONS.glob("*.json"), reverse=True)]
    refs = read_refs()
    tags_by_revision: dict[str, list[str]] = {}
    for tag, revision in refs.get("tags", {}).items():
        tags_by_revision.setdefault(str(revision), []).append(tag)
    for row in rows:
        row["is_head"] = row["revision"] == refs.get("head")
        row["tags"] = sorted(tags_by_revision.get(row["revision"], []))
    if as_json:
        return rows
    return [
        {
            "revision": row["revision"],
            "head": row["is_head"],
            "tags": row["tags"],
            "author": row["author"],
            "summary": row["summary"],
        }
        for row in rows
    ]


def show(value: str) -> dict[str, Any]:
    revision = resolve_revision(value)
    return load_json(REVISIONS / f"{revision}.json")


def diff(left: str, right: str) -> dict[str, Any]:
    before = show(left)
    after = show(right)
    old = {item["path"]: item for item in before["artifacts"]}
    new = {item["path"]: item for item in after["artifacts"]}
    return {
        "from": before["revision"],
        "to": after["revision"],
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "changed": sorted(path for path in set(old) & set(new) if old[path]["sha256"] != new[path]["sha256"]),
        "unchanged": sorted(path for path in set(old) & set(new) if old[path]["sha256"] == new[path]["sha256"]),
    }


def materialize(value: str, destination: Path) -> dict[str, Any]:
    revision = resolve_revision(value)
    source = OBJECTS / revision / "artifacts"
    if not source.exists():
        raise FileNotFoundError(f"Local object store is missing for {revision}")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    copy_artifact(source, destination)
    return {"revision": revision, "destination": str(destination)}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--spec", default=str(DEFAULT_SPEC))
    commands = result.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--json", action="store_true")
    show_command = commands.add_parser("show")
    show_command.add_argument("revision")
    difference = commands.add_parser("diff")
    difference.add_argument("left")
    difference.add_argument("right")
    create = commands.add_parser("checkpoint")
    create.add_argument("--label", required=True)
    create.add_argument("--summary", required=True)
    create.add_argument("--author", default="producer")
    create.add_argument("--tag")
    create.add_argument("--include", action="append", default=[])
    materialize_command = commands.add_parser("materialize")
    materialize_command.add_argument("revision")
    materialize_command.add_argument("destination", type=Path)
    return result


def main() -> None:
    args = parser().parse_args()
    if args.command == "checkpoint":
        output = checkpoint(args)
    elif args.command == "list":
        output = list_revisions(args.json)
    elif args.command == "show":
        output = show(args.revision)
    elif args.command == "diff":
        output = diff(args.left, args.right)
    else:
        output = materialize(args.revision, args.destination)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
