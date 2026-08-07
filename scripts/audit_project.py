#!/usr/bin/env python3
"""Audit the workspace against STUDIO.md and the canonical project spec."""

from __future__ import annotations

import json
import plistlib
import re
from pathlib import Path
from typing import Any

from studio_common import DEFAULT_SPEC, ROOT, atomic_write_json, load_json, load_spec, report_metrics, resolve, sha256


OUTPUT_JSON = ROOT / "analysis" / "structure_audit.json"
OUTPUT_MD = ROOT / "analysis" / "STRUCTURE_AUDIT.md"


def check(condition: bool, name: str, evidence: str, required: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if condition else ("FAIL" if required else "WARN"),
        "required": required,
        "evidence": evidence,
    }


def metric_checks(spec: dict[str, Any], kind: str, report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return [check(False, f"{kind} comparison", f"Missing {report_path.relative_to(ROOT)}")]
    metrics = report_metrics(load_json(report_path), kind)
    return [
        check(
            metrics[name] >= float(minimum),
            f"{kind} KPI: {name}",
            f"actual={metrics[name]:.5f}, minimum={float(minimum):.5f}",
        )
        for name, minimum in spec["quality"][kind]["minimums"].items()
    ]


def audit(spec: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.append(check((ROOT / "STUDIO.md").exists(), "Studio rules", "STUDIO.md exists"))
    checks.append(check(DEFAULT_SPEC.exists(), "Canonical project spec", "studio/project.json exists"))
    checks.append(check((ROOT / "studio" / "knowledge.json").exists(), "Reusable knowledge", "studio/knowledge.json exists"))
    checks.append(check((ROOT / "studio" / "MANUAL_FALLBACK.md").exists(), "New-machine fallback", "Manual fallback exists"))

    for name, relative in spec["deliverables"].items():
        paths = relative if isinstance(relative, list) else [relative]
        for path_text in paths:
            path = resolve(path_text)
            checks.append(
                check(path.exists(), f"Deliverable: {name}", str(path.relative_to(ROOT)))
            )
    for document in spec["documentation"]:
        path = resolve(document)
        checks.append(check(path.exists(), "Documentation", str(path.relative_to(ROOT))))

    sections = spec["sections"]
    covered_bars = [bar for section in sections for bar in range(section["start_bar"], section["end_bar"] + 1)]
    expected_bars = list(range(1, int(spec["music"]["bars"]) + 1))
    checks.append(
        check(covered_bars == expected_bars, "Section coverage", "Sections cover bars 1–80 exactly once")
    )

    validation_path = resolve(spec["deliverables"]["midi_validation"])
    validation = load_json(validation_path) if validation_path.exists() else {}
    checks.append(check(validation.get("status") == "PASS", "MIDI technical validation", str(validation_path.relative_to(ROOT))))
    if validation:
        checks.append(
            check(
                abs(float(validation["expected_bpm"]) - float(spec["music"]["tempo_bpm"])) < 0.001,
                "MIDI tempo matches spec",
                f"{validation['expected_bpm']} BPM",
            )
        )
        checks.append(
            check(
                int(validation["expected_bars"]) == int(spec["music"]["bars"]),
                "MIDI length matches spec",
                f"{validation['expected_bars']} bars",
            )
        )

    checks.extend(metric_checks(spec, "direct_midi", resolve(spec["deliverables"]["midi_comparison"])))
    checks.extend(metric_checks(spec, "native", resolve(spec["deliverables"]["native_comparison"])))

    accepted_path = resolve(spec["deliverables"]["accepted_state"])
    accepted = load_json(accepted_path) if accepted_path.exists() else {}
    checks.append(check(accepted.get("project_id") == spec["project_id"], "Accepted-state project identity", str(accepted_path.relative_to(ROOT))))
    for kind, target in accepted.get("targets", {}).items():
        artifact = resolve(target["artifact"])
        checks.append(
            check(
                artifact.exists() and sha256(artifact) == target["artifact_sha256"],
                f"Accepted artifact hash: {kind}",
                str(artifact.relative_to(ROOT)),
            )
        )

    native_verification_path = resolve(spec["deliverables"]["native_verification"])
    native_verification = load_json(native_verification_path) if native_verification_path.exists() else {}
    checks.append(
        check(
            native_verification.get("verification", {}).get("status") == "PASS",
            "Post-reopen native verification",
            str(native_verification_path.relative_to(ROOT)),
        )
    )
    verified_tracks = {
        int(track["index"]): track
        for track in native_verification.get("verification", {}).get("tracks", [])
    }
    for expected in spec["garageband"]["tracks"]:
        target = expected.get("fader")
        if target is None:
            continue
        actual = verified_tracks.get(int(expected["index"]), {}).get("fader")
        checks.append(
            check(
                actual is not None and abs(int(actual) - int(target)) <= 1,
                f"Persisted fader evidence: track {expected['index']}",
                f"actual={actual}, expected={target}",
            )
        )

    ledger_path = resolve(spec["deliverables"]["iteration_ledger"])
    ledger_entries: list[dict[str, Any]] = []
    if ledger_path.exists():
        ledger_entries = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    checks.append(
        check(bool(ledger_entries), "Iteration decision ledger", f"entries={len(ledger_entries)}")
    )

    project = resolve(spec["deliverables"]["native_project"])
    metadata_path = project / "Alternatives" / "000" / "MetaData.plist"
    if metadata_path.exists():
        with metadata_path.open("rb") as handle:
            metadata = plistlib.load(handle)
        music = spec["music"]
        checks.extend(
            [
                check(abs(float(metadata["BeatsPerMinute"]) - float(music["tempo_bpm"])) < 0.001, "Native tempo", str(metadata["BeatsPerMinute"])),
                check(metadata["SongKey"] == "A" and metadata["SongGenderKey"] == "minor", "Native key", "A minor"),
                check(int(metadata["SongSignatureNumerator"]) == 4 and int(metadata["SongSignatureDenominator"]) == 4, "Native meter", "4/4"),
                check(int(metadata["NumberOfTracks"]) == len(spec["garageband"]["tracks"]), "Native track count", str(metadata["NumberOfTracks"])),
                check(int(metadata["SampleRate"]) == 44100, "Native sample rate", str(metadata["SampleRate"])),
            ]
        )
        data_path = project / "Alternatives" / "000" / "ProjectData"
        data = data_path.read_bytes() if data_path.exists() else b""
        for track in spec["garageband"]["tracks"]:
            checks.append(
                check(
                    track["patch"].encode("utf-8") in data,
                    f"Persisted native patch: track {track['index']}",
                    track["patch"],
                )
            )
            checks.append(
                check(
                    track["name"].encode("utf-8") in data,
                    f"Persisted native name: track {track['index']}",
                    track["name"],
                )
            )
    else:
        checks.append(check(False, "Native metadata", str(metadata_path.relative_to(ROOT))))

    expected_directories = {"analysis", "archive", "fixtures", "midi", "renders", "scripts", "sources", "studio", "tests"}
    present_directories = {path.name for path in ROOT.iterdir() if path.is_dir() and not path.name.startswith(".") and not path.name.endswith(".band")}
    missing_directories = expected_directories - present_directories
    checks.append(
        check(not missing_directories, "Workspace organization", f"missing={sorted(missing_directories)}", required=False)
    )

    version_pattern = re.compile(r"(?:baseline|iteration\d+|_v\d+|search_)")
    visible_versions = [
        str(path.relative_to(ROOT))
        for folder in (ROOT / "analysis", ROOT / "renders")
        for path in folder.iterdir()
        if version_pattern.search(path.name)
    ]
    checks.append(
        check(
            not visible_versions,
            "Canonical artifact naming",
            "No trial versions in active analysis/renders" if not visible_versions else ", ".join(visible_versions[:12]),
            required=False,
        )
    )

    root_audio = [path.name for path in ROOT.iterdir() if path.suffix.lower() in {".wav", ".mp3", ".aiff", ".m4a"}]
    checks.append(
        check(not root_audio, "Root directory cleanliness", f"root audio={root_audio}", required=False)
    )
    failures = [item for item in checks if item["status"] == "FAIL"]
    warnings = [item for item in checks if item["status"] == "WARN"]
    return {
        "schema_version": 1,
        "project_id": spec["project_id"],
        "status": "PASS" if not failures else "FAIL",
        "summary": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "failed": len(failures),
            "warnings": len(warnings),
        },
        "checks": checks,
    }


def markdown(report: dict[str, Any]) -> str:
    rows = [
        "# Project structure audit",
        "",
        f"Overall status: **{report['status']}**. Passed: {report['summary']['passed']}; failed: {report['summary']['failed']}; warnings: {report['summary']['warnings']}.",
        "",
        "| Status | Check | Evidence |",
        "|---|---|---|",
    ]
    for item in report["checks"]:
        evidence = str(item["evidence"]).replace("|", "\\|")
        rows.append(f"| {item['status']} | {item['name']} | {evidence} |")
    rows.extend(
        [
            "",
            "This audit is generated from `studio/project.json`; it verifies both the STUDIO.md delivery contract and the promoted KPI thresholds.",
            "",
        ]
    )
    return "\n".join(rows)


def main() -> None:
    spec = load_spec()
    report = audit(spec)
    atomic_write_json(OUTPUT_JSON, report)
    OUTPUT_MD.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
