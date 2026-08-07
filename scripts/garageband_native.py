#!/usr/bin/env python3
"""Reproduce, verify, export, compare, and gate a GarageBand project from its spec.

GarageBand has no complete public project-editing API. This driver uses macOS
Accessibility deterministically and verifies the persisted `.band` state after a
close/reopen cycle. The manual document is used only when a new machine blocks
Accessibility or presents an unrecognized GarageBand UI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from studio_common import DEFAULT_SPEC, ROOT, load_spec, resolve


SCRIPT_DIR = Path(__file__).resolve().parent
CGCLICK = SCRIPT_DIR / "cgclick"
GARAGEBAND_APP = Path("/Applications/GarageBand.app")


class AutomationError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrackState:
    index: int
    name: str
    patch: str
    fader: int


def apple_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def run(command: list[str], *, input_text: str | None = None, timeout: int = 30) -> str:
    completed = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise AutomationError(f"{' '.join(command)} failed: {message}")
    return completed.stdout.strip()


def osascript(source: str, timeout: int = 30) -> str:
    return run(["osascript"], input_text=source, timeout=timeout)


def ensure_helpers() -> None:
    for executable, source in ((CGCLICK, SCRIPT_DIR / "cgclick.m"),):
        if executable.exists() and executable.stat().st_mtime >= source.stat().st_mtime:
            continue
        run(
            [
                "clang",
                "-fobjc-arc",
                "-framework",
                "Foundation",
                "-framework",
                "ApplicationServices",
                str(source),
                "-o",
                str(executable),
            ],
            timeout=60,
        )


def project_window(project: Path) -> str:
    return f"{project.stem} - Tracks"


def activate(window_name: str | None = None) -> None:
    raise_window = ""
    if window_name:
        raise_window = (
            f'if exists window {apple_string(window_name)} then '
            f'perform action "AXRaise" of window {apple_string(window_name)}\n'
        )
    osascript(
        'tell application "GarageBand" to activate\n'
        'tell application "System Events" to tell process "GarageBand"\n'
        'set frontmost to true\n'
        f"{raise_window}"
        "end tell"
    )


def wait_for_window(window_name: str, timeout: int = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            found = osascript(
                'tell application "System Events" to tell process "GarageBand"\n'
                f'return exists window {apple_string(window_name)}\n'
                "end tell"
            )
            if found.lower() == "true":
                return
        except AutomationError:
            pass
        time.sleep(1)
    raise AutomationError(f"GarageBand window did not appear: {window_name}")


def wait_for_window_absent(window_name: str, timeout: int = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            found = osascript(
                'tell application "System Events" to tell process "GarageBand"\n'
                f'return exists window {apple_string(window_name)}\n'
                "end tell"
            )
            if found.lower() == "false":
                return
        except AutomationError:
            return
        time.sleep(1)
    raise AutomationError(f"GarageBand window did not close: {window_name}")


def open_project(project: Path) -> str:
    run(["open", "-a", "GarageBand", str(project)], timeout=20)
    window_name = project_window(project)
    wait_for_window(window_name)
    activate(window_name)
    return window_name


def preflight(spec: dict[str, Any], *, require_project: bool = True) -> dict[str, Any]:
    ensure_helpers()
    accessibility = False
    try:
        accessibility = osascript(
            'tell application "System Events" to get UI elements enabled'
        ).lower() == "true"
    except AutomationError:
        accessibility = False
    project = resolve(spec["deliverables"]["native_project"])
    source_midi = resolve(spec["deliverables"]["full_midi"])
    result = {
        "platform": sys.platform,
        "garageband_installed": GARAGEBAND_APP.exists(),
        "accessibility_enabled": accessibility,
        "project_exists": project.exists(),
        "source_midi_exists": source_midi.exists(),
        "cgclick": CGCLICK.exists(),
        "manual_fallback": "studio/MANUAL_FALLBACK.md",
    }
    required_checks = [
        "garageband_installed",
        "accessibility_enabled",
        "source_midi_exists",
        "cgclick",
    ]
    if require_project:
        required_checks.append("project_exists")
    failures = [
        name
        for name in required_checks
        if not result[name]
    ]
    result["status"] = "PASS" if sys.platform == "darwin" and not failures else "BLOCKED"
    result["failures"] = failures
    return result


def wait_for_any_tracks_window(timeout: int = 90) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            output = osascript(
                'tell application "System Events" to tell process "GarageBand"\n'
                'return name of every window\n'
                'end tell'
            )
            for name in (part.strip() for part in output.split(",")):
                if name.endswith(" - Tracks"):
                    return name
        except AutomationError:
            pass
        time.sleep(1)
    raise AutomationError("GarageBand did not open an imported MIDI Tracks window")


def bootstrap_project(spec: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    project = resolve(spec["deliverables"]["native_project"])
    source_midi = resolve(spec["deliverables"]["full_midi"])
    if project.exists():
        return {
            "status": "SKIPPED",
            "reason": "Native project already exists",
            "project": str(project.relative_to(ROOT)),
        }
    if not spec.get("garageband", {}).get("bootstrap_from_midi", True):
        raise AutomationError(
            "This native project contains user-authored audio and cannot be rebuilt from MIDI alone; "
            "materialize a project-history checkpoint instead"
        )
    steps = [
        f"Open {source_midi.relative_to(ROOT)} in GarageBand",
        f"Save the imported Tracks window as {project.name} in {ROOT}",
        "Apply the canonical patches through sync without changing volume",
    ]
    if dry_run:
        return {"status": "DRY_RUN", "steps": steps, "manual_actions_required": False}
    check = preflight(spec, require_project=False)
    if check["status"] != "PASS":
        raise AutomationError(f"Bootstrap preflight blocked: {check}")
    run(["open", "-a", "GarageBand", str(source_midi)], timeout=20)
    imported_window = wait_for_any_tracks_window()
    activate(imported_window)
    save_script = f'''
tell application "System Events" to tell process "GarageBand"
    set frontmost to true
    keystroke "s" using command down
    delay 1
    if not (exists window "Save") then error "GarageBand save dialog did not appear"
    keystroke "g" using {{command down, shift down}}
    delay 1
    keystroke {apple_string(str(ROOT))}
    key code 36
    delay 2
    set d to splitter group 1 of window "Save"
    set value of text field "Save As:" of d to {apple_string(project.stem)}
    click button "Save" of d
end tell
'''
    osascript(save_script, timeout=30)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline and not project.exists():
        time.sleep(1)
    if not project.exists():
        raise AutomationError(f"GarageBand did not create {project}")
    wait_for_window(project_window(project), timeout=90)
    return {
        "status": "PASS",
        "project": str(project.relative_to(ROOT)),
        "manual_actions_required": False,
    }


def save_as(window_name: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise AutomationError(f"Refusing to overwrite Save As destination: {destination}")
    activate(window_name)
    osascript(
        'tell application "System Events" to tell process "GarageBand"\n'
        'set frontmost to true\n'
        'click menu item "Save As…" of menu 1 of menu bar item "File" of menu bar 1\n'
        'delay 1\n'
        'if not (exists window "Save") then error "GarageBand Save As dialog did not appear"\n'
        'keystroke "g" using {command down, shift down}\n'
        'delay 1\n'
        f'keystroke {apple_string(str(destination.parent))}\n'
        'key code 36\n'
        'delay 2\n'
        'set d to splitter group 1 of window "Save"\n'
        f'set value of text field "Save As:" of d to {apple_string(destination.stem)}\n'
        'click button "Save" of d\n'
        'end tell',
        timeout=30,
    )
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline and not destination.exists():
        time.sleep(1)
    if not destination.exists():
        raise AutomationError(f"GarageBand did not create Save As copy: {destination}")


def quarantine_live_session(spec: dict[str, Any]) -> dict[str, Any]:
    project = resolve(spec["deliverables"]["native_project"])
    window_name = project_window(project)
    wait_for_window(window_name, timeout=5)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    quarantine = ROOT / "archive" / "live_sessions" / f"{project.stem}_live_session_{timestamp}.band"
    save_as(window_name, quarantine)
    time.sleep(4)
    close_project()
    wait_for_window_absent(window_name)
    reopened = open_project(project)
    return {
        "status": "PASS",
        "quarantined_copy": str(quarantine.relative_to(ROOT)),
        "reopened_window": reopened,
        "manual_actions_required": False,
    }


def inspect_tracks(window_name: str, track_count: int) -> list[TrackState]:
    source = f'''
tell application "System Events" to tell process "GarageBand"
    set w to window {apple_string(window_name)}
    set regionArea to group 1 of scroll area 2 of splitter group 2 of splitter group 1 of group 3 of w
    set headerArea to group 1 of scroll area 1 of splitter group 2 of splitter group 1 of group 3 of w
    set outputLines to {{}}
    repeat with i from 1 to {track_count}
        set trackRegion to UI element i of regionArea
        set trackName to ""
        try
            set trackName to name of button 1 of UI element 1 of trackRegion
        end try
        set patchDescription to description of trackRegion
        set faderValue to value of slider 2 of UI element i of headerArea
        set end of outputLines to (i as text) & tab & trackName & tab & patchDescription & tab & (faderValue as text)
    end repeat
end tell
set AppleScript's text item delimiters to linefeed
set resultText to outputLines as text
set AppleScript's text item delimiters to ""
return resultText
'''
    lines = osascript(source).splitlines()
    states: list[TrackState] = []
    for line in lines:
        index_text, name, description, fader_text = line.split("\t")
        match = re.search(r"[“\"](.+?)[”\"]", description)
        patch = match.group(1) if match else description
        states.append(TrackState(int(index_text), name, patch, int(float(fader_text))))
    return states


def project_metadata(project: Path) -> dict[str, Any]:
    path = project / "Alternatives" / "000" / "MetaData.plist"
    with path.open("rb") as handle:
        return plistlib.load(handle)


def project_fingerprint(project: Path) -> str:
    digest = hashlib.sha256()
    critical = [
        Path("projectData"),
        Path("Alternatives/000/ProjectData"),
        Path("Alternatives/000/MetaData.plist"),
        Path("Resources/ProjectInformation.plist"),
    ]
    media = sorted(
        path.relative_to(project)
        for path in (project / "Media").rglob("*")
        if path.is_file()
    )
    for relative in [*critical, *media]:
        path = project / relative
        if not path.exists():
            continue
        digest.update(str(relative).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def verify(
    spec: dict[str, Any],
    *,
    open_if_needed: bool = True,
    project_override: Path | None = None,
) -> dict[str, Any]:
    project = project_override or resolve(spec["deliverables"]["native_project"])
    window_name = project_window(project)
    if open_if_needed:
        try:
            wait_for_window(window_name, timeout=2)
        except AutomationError:
            open_project(project)
    expected_tracks = spec["garageband"]["tracks"]
    actual_tracks = inspect_tracks(window_name, len(expected_tracks))
    errors: list[str] = []
    track_rows: list[dict[str, Any]] = []
    for expected, actual in zip(expected_tracks, actual_tracks, strict=True):
        row_errors: list[str] = []
        if actual.name and expected["name"] != actual.name:
            row_errors.append(f"name expected {expected['name']!r}, found {actual.name!r}")
        if expected["patch"] != actual.patch:
            row_errors.append(f"patch expected {expected['patch']!r}, found {actual.patch!r}")
        errors.extend(f"Track {actual.index}: {error}" for error in row_errors)
        track_rows.append(
            {
                "index": actual.index,
                "name": actual.name,
                "patch": actual.patch,
                "fader": actual.fader,
                "status": "PASS" if not row_errors else "FAIL",
            }
        )

    metadata = project_metadata(project)
    music = spec["music"]
    metadata_checks = {
        "tempo_bpm": abs(float(metadata["BeatsPerMinute"]) - float(music["tempo_bpm"])) < 0.001,
        "key": metadata["SongKey"] == "A" and metadata["SongGenderKey"] == "minor",
        "meter": (
            int(metadata["SongSignatureNumerator"]) == 4
            and int(metadata["SongSignatureDenominator"]) == 4
        ),
        "track_count": int(metadata["NumberOfTracks"]) == len(expected_tracks),
        "sample_rate": int(metadata["SampleRate"]) == 44100,
    }
    errors.extend(f"Metadata failed: {name}" for name, passed in metadata_checks.items() if not passed)
    project_data_path = project / "Alternatives" / "000" / "ProjectData"
    project_data = project_data_path.read_bytes()
    for expected in expected_tracks:
        if expected["name"].encode("utf-8") not in project_data:
            errors.append(f"Saved project data is missing track name: {expected['name']}")
        if expected["patch"].encode("utf-8") not in project_data:
            errors.append(f"Saved project data is missing patch: {expected['patch']}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "project": str(project.relative_to(ROOT)),
        "window": window_name,
        "tracks": track_rows,
        "metadata": metadata_checks,
        "errors": errors,
    }


def verification_report_path() -> Path:
    return ROOT / "analysis" / "native_verification.json"


def write_verification_report(spec: dict[str, Any], verification: dict[str, Any]) -> None:
    project = resolve(spec["deliverables"]["native_project"])
    report = {
        "schema_version": 1,
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": str(project.relative_to(ROOT)),
        "project_fingerprint": project_fingerprint(project),
        "verification": verification,
    }
    temporary = verification_report_path().with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(verification_report_path())


def verify_saved_package(spec: dict[str, Any]) -> dict[str, Any]:
    project = resolve(spec["deliverables"]["native_project"])
    metadata = project_metadata(project)
    project_data = (project / "Alternatives" / "000" / "ProjectData").read_bytes()
    errors: list[str] = []
    music = spec["music"]
    if abs(float(metadata["BeatsPerMinute"]) - float(music["tempo_bpm"])) >= 0.001:
        errors.append("Saved tempo differs from spec")
    if metadata["SongKey"] != "A" or metadata["SongGenderKey"] != "minor":
        errors.append("Saved key differs from spec")
    if int(metadata["NumberOfTracks"]) != len(spec["garageband"]["tracks"]):
        errors.append("Saved track count differs from spec")
    for track in spec["garageband"]["tracks"]:
        if track["name"].encode("utf-8") not in project_data:
            errors.append(f"Missing saved track name: {track['name']}")
        if track["patch"].encode("utf-8") not in project_data:
            errors.append(f"Missing saved patch: {track['patch']}")

    persisted_report = verification_report_path()
    persisted = None
    if persisted_report.exists():
        persisted = json.loads(persisted_report.read_text(encoding="utf-8"))
        if persisted.get("project_fingerprint") != project_fingerprint(project):
            errors.append("Project changed after the last post-reopen verification")
    else:
        errors.append("No post-reopen native verification report exists")
    return {
        "status": "PASS" if not errors else "FAIL",
        "project": str(project.relative_to(ROOT)),
        "project_fingerprint": project_fingerprint(project),
        "post_reopen_verification": str(persisted_report.relative_to(ROOT)),
        "errors": errors,
        "manual_actions_required": False,
    }


def click(x: float, y: float) -> None:
    run([str(CGCLICK), str(round(x)), str(round(y))], timeout=10)


def track_region_geometry(window_name: str, index: int) -> tuple[int, int, int, int]:
    output = osascript(
        'tell application "System Events" to tell process "GarageBand"\n'
        f'set w to window {apple_string(window_name)}\n'
        'set regionArea to group 1 of scroll area 2 of splitter group 2 of splitter group 1 of group 3 of w\n'
        f'set e to UI element 1 of UI element {index} of regionArea\n'
        'set p to position of e\n'
        'set z to size of e\n'
        'return {item 1 of p, item 2 of p, item 1 of z, item 2 of z}\n'
        'end tell'
    )
    return tuple(int(float(part.strip())) for part in output.split(","))  # type: ignore[return-value]


def ensure_library(window_name: str) -> None:
    value = osascript(
        'tell application "System Events" to tell process "GarageBand"\n'
        f'set w to window {apple_string(window_name)}\n'
        'return value of checkbox "Library" of group 1 of w\n'
        'end tell'
    )
    if value.strip() == "0":
        osascript(
            'tell application "System Events" to tell process "GarageBand"\n'
            f'set w to window {apple_string(window_name)}\n'
            'perform action "AXPress" of checkbox "Library" of group 1 of w\n'
            'end tell'
        )
        time.sleep(1)


def search_results(window_name: str, query: str) -> list[dict[str, Any]]:
    osascript(
        'tell application "System Events" to tell process "GarageBand"\n'
        f'set w to window {apple_string(window_name)}\n'
        'set s to splitter group 1 of group 1 of group 1 of group 2 of w\n'
        'set f to text field 1 of group 2 of s\n'
        'set focused of f to true\n'
        'keystroke "a" using command down\n'
        'key code 51\n'
        f'keystroke {apple_string(query)}\n'
        'end tell'
    )
    time.sleep(3)
    source = f'''
tell application "System Events" to tell process "GarageBand"
    set w to window {apple_string(window_name)}
    set s to splitter group 1 of group 1 of group 1 of group 2 of w
    set t to table 1 of scroll area 1 of group 3 of s
    set outputLines to {{}}
    repeat with i from 1 to count rows of t
        set r to row i of t
        set resultName to name of UI element 1 of r
        set resultPosition to position of r
        set resultSize to size of r
        set end of outputLines to (i as text) & tab & resultName & tab & (item 1 of resultPosition as text) & tab & (item 2 of resultPosition as text) & tab & (item 1 of resultSize as text) & tab & (item 2 of resultSize as text)
    end repeat
end tell
set AppleScript's text item delimiters to linefeed
set resultText to outputLines as text
set AppleScript's text item delimiters to ""
return resultText
'''
    output = osascript(source)
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        index, name, x, y, width, height = line.split("\t")
        rows.append(
            {
                "index": int(index),
                "name": name,
                "x": int(float(x)),
                "y": int(float(y)),
                "width": int(float(width)),
                "height": int(float(height)),
            }
        )
    return rows


def apply_patch(window_name: str, track: dict[str, Any]) -> None:
    activate(window_name)
    ensure_library(window_name)
    x, y, width, height = track_region_geometry(window_name, int(track["index"]))
    click(x + min(90, max(20, width // 10)), y + height // 2)
    time.sleep(1)
    rows = search_results(window_name, track["search"])
    matches = [row for row in rows if row["name"] == track["patch"]]
    if len(matches) != 1:
        names = [row["name"] for row in rows]
        raise AutomationError(
            f"Expected one result for {track['patch']!r} using {track['search']!r}; found {names}"
        )
    row = matches[0]
    activate(window_name)
    click(row["x"] + min(80, row["width"] // 2), row["y"] + row["height"] // 2)
    time.sleep(5)
    actual = inspect_tracks(window_name, int(track["index"]))[-1]
    if actual.patch != track["patch"]:
        raise AutomationError(
            f"Patch did not apply to track {track['index']}: expected {track['patch']}, found {actual.patch}"
        )


def assert_volume_unchanged(
    baseline: dict[int, int], current: list[TrackState], *, stage: str
) -> None:
    changed = [
        f"track {state.index}: {baseline.get(state.index)} -> {state.fader}"
        for state in current
        if baseline.get(state.index) != state.fader
    ]
    if changed:
        raise AutomationError(
            f"Volume changed during {stage}; producer policy forbids track/master volume edits: "
            + "; ".join(changed)
        )


def save_project() -> None:
    osascript(
        'tell application "GarageBand" to activate\n'
        'tell application "System Events" to tell process "GarageBand"\n'
        'set frontmost to true\n'
        'keystroke "s" using command down\n'
        'end tell'
    )
    time.sleep(5)


def close_project() -> None:
    osascript(
        'tell application "GarageBand" to activate\n'
        'tell application "System Events" to tell process "GarageBand"\n'
        'set frontmost to true\n'
        'keystroke "w" using command down\n'
        'end tell'
    )
    time.sleep(4)


def export_wave(window_name: str, basename: str, timeout: int = 180) -> Path:
    candidate = ROOT / f"{basename}.wav"
    candidate.unlink(missing_ok=True)
    osascript(
        'tell application "GarageBand" to activate\n'
        'tell application "System Events" to tell process "GarageBand"\n'
        'set frontmost to true\n'
        f'perform action "AXRaise" of window {apple_string(window_name)}\n'
        'click menu item "Export Song to Disk…" of menu 1 of menu bar item "Share" of menu bar 1\n'
        'delay 1\n'
        'keystroke "g" using {command down, shift down}\n'
        'delay 1\n'
        f'keystroke {apple_string(str(ROOT))}\n'
        'key code 36\n'
        'delay 2\n'
        'set d to splitter group 1 of window "Export Song to Disk"\n'
        f'set value of text field "Save As:" of d to {apple_string(basename)}\n'
        'click radio button "WAVE" of radio group 1 of d\n'
        'set destinationName to value of pop up button "Where:" of d\n'
        f'if destinationName is not {apple_string(ROOT.name)} then error "Unexpected export destination: " & destinationName\n'
        'click button "Export" of d\n'
        'end tell',
        timeout=30,
    )
    deadline = time.monotonic() + timeout
    last_size = -1
    stable = 0
    while time.monotonic() < deadline:
        if candidate.exists():
            size = candidate.stat().st_size
            stable = stable + 1 if size == last_size and size > 1024 else 0
            last_size = size
            if stable >= 3:
                return candidate
        time.sleep(2)
    raise AutomationError(f"GarageBand export did not finish: {candidate}")


def synchronize(spec: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    check = preflight(spec, require_project=False)
    if check["status"] != "PASS":
        raise AutomationError(f"Preflight blocked: {check}")
    project = resolve(spec["deliverables"]["native_project"])
    if not project.exists():
        bootstrap_project(spec)
    window_name = open_project(project)
    current = {state.index: state for state in inspect_tracks(window_name, len(spec["garageband"]["tracks"]))}
    locked_volumes = {index: state.fader for index, state in current.items()}
    changes: list[str] = []
    for track in spec["garageband"]["tracks"]:
        actual = current[int(track["index"])]
        if actual.patch != track["patch"]:
            if track.get("preserve") and not args.apply_preserved:
                raise AutomationError(
                    f"Preserved track {track['index']} differs: {actual.patch} != {track['patch']}"
                )
            apply_patch(window_name, track)
            changes.append(f"track {track['index']} patch -> {track['patch']}")
    assert_volume_unchanged(
        locked_volumes,
        inspect_tracks(window_name, len(spec["garageband"]["tracks"])),
        stage="patch application",
    )
    save_project()
    close_project()
    window_name = open_project(project)
    verification = verify(spec, open_if_needed=False)
    if verification["status"] != "PASS":
        raise AutomationError(f"Post-reopen verification failed: {verification['errors']}")
    reopened = [
        TrackState(
            int(row["index"]),
            str(row["name"]),
            str(row["patch"]),
            int(row["fader"]),
        )
        for row in verification["tracks"]
    ]
    assert_volume_unchanged(locked_volumes, reopened, stage="save/reopen")
    write_verification_report(spec, verification)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    basename = f".studio_native_candidate_{timestamp}"
    exported = export_wave(window_name, basename)
    candidate_dir = ROOT / ".studio" / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    candidate_audio = candidate_dir / f"native-{timestamp}.wav"
    exported.replace(candidate_audio)

    report_path = candidate_dir / f"native-{timestamp}.json"
    run(
        [
            sys.executable,
            str(SCRIPT_DIR / "compare_garageband_render.py"),
            "--spec",
            str(args.spec),
            "--render-path",
            str(candidate_audio),
            "--output-path",
            str(report_path),
        ],
        timeout=120,
    )
    gate_command = [
        sys.executable,
        str(SCRIPT_DIR / "studio_pipeline.py"),
        "--spec",
        str(args.spec),
        "evaluate",
        "--kind",
        "native",
        "--report",
        str(report_path),
        "--artifact",
        str(candidate_audio),
        "--hypothesis",
        args.hypothesis,
        "--primary-change",
        args.primary_change,
    ]
    if args.promote:
        gate_command.append("--promote")
    decision = json.loads(run(gate_command, timeout=60))
    if spec["quality"]["promotion"].get("retained_rejected_artifacts", 0) == 0:
        candidate_audio.unlink(missing_ok=True)
        report_path.unlink(missing_ok=True)
    return {
        "status": "PASS",
        "changes": changes,
        "verification": verification,
        "quality_gate": decision,
        "manual_actions_required": False,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--spec", default=str(DEFAULT_SPEC))
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("preflight")
    bootstrap = commands.add_parser("bootstrap", help="Create the native project from the full MIDI")
    bootstrap.add_argument("--dry-run", action="store_true")
    commands.add_parser(
        "quarantine-live",
        help="Save the current live session to archive and reopen the canonical saved project",
    )
    verification = commands.add_parser("verify")
    verification.add_argument("--live", action="store_true", help="Inspect the open project instead of the saved package report")
    verification.add_argument("--record", action="store_true", help="Record a passing live post-reopen verification")
    commands.add_parser("export")
    sync = commands.add_parser("sync", help="Apply spec, save/reopen, verify, export, compare, and gate")
    sync.add_argument("--hypothesis", required=True)
    sync.add_argument("--primary-change", required=True)
    sync.add_argument("--promote", action="store_true")
    sync.add_argument("--apply-preserved", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    spec = load_spec(Path(args.spec))
    try:
        if args.command == "preflight":
            output = preflight(spec)
        elif args.command == "bootstrap":
            output = bootstrap_project(spec, dry_run=args.dry_run)
        elif args.command == "quarantine-live":
            check = preflight(spec)
            if check["status"] != "PASS":
                raise AutomationError(f"Preflight blocked: {check}")
            output = quarantine_live_session(spec)
        elif args.command == "verify":
            if args.live:
                check = preflight(spec)
                if check["status"] != "PASS":
                    raise AutomationError(f"Preflight blocked: {check}")
                output = verify(spec)
                if args.record:
                    if output["status"] != "PASS":
                        raise AutomationError(f"Cannot record failed verification: {output['errors']}")
                    write_verification_report(spec, output)
            else:
                if args.record:
                    raise AutomationError("--record requires --live")
                output = verify_saved_package(spec)
        elif args.command == "export":
            check = preflight(spec)
            if check["status"] != "PASS":
                raise AutomationError(f"Preflight blocked: {check}")
            project = resolve(spec["deliverables"]["native_project"])
            window_name = open_project(project)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            output = {"candidate": str(export_wave(window_name, f".studio_native_candidate_{timestamp}"))}
        else:
            output = synchronize(spec, args)
    except AutomationError as error:
        output = {
            "status": "BLOCKED",
            "error": str(error),
            "manual_fallback": "studio/MANUAL_FALLBACK.md",
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        raise SystemExit(2)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
