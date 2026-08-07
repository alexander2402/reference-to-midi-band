#!/usr/bin/env python3
"""Promote only measured improvements and retain reusable studio knowledge."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from studio_common import (
    ACCEPTED_STATE,
    DEFAULT_SPEC,
    ITERATION_LEDGER,
    KNOWLEDGE,
    ROOT,
    append_jsonl,
    atomic_write_json,
    load_json,
    load_spec,
    promotion_decision,
    report_metrics,
    resolve,
    sha256,
    weighted_score,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_paths(spec: dict[str, Any], kind: str) -> tuple[Path, Path]:
    deliverables = spec["deliverables"]
    if kind == "direct_midi":
        return resolve(deliverables["midi_comparison"]), resolve(deliverables["midi_render"])
    return resolve(deliverables["native_comparison"]), resolve(deliverables["native_render"])


def seed(spec: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema_version": 1,
        "project_id": spec["project_id"],
        "updated_at": now(),
        "targets": {},
    }
    for kind in ("direct_midi", "native"):
        report_path, artifact_path = canonical_paths(spec, kind)
        report = load_json(report_path)
        metrics = report_metrics(report, kind)
        quality = spec["quality"][kind]
        state["targets"][kind] = {
            "report": str(report_path.relative_to(ROOT)),
            "artifact": str(artifact_path.relative_to(ROOT)),
            "artifact_sha256": sha256(artifact_path),
            "metrics": metrics,
            "weighted_score": round(weighted_score(metrics, quality["weights"]), 6),
            "accepted_at": now(),
            "hypothesis": "Seeded from the verified retrospective delivery state",
            "primary_change": "canonicalize-current-state"
        }
    atomic_write_json(ACCEPTED_STATE, state)
    return state


def load_or_seed(spec: dict[str, Any]) -> dict[str, Any]:
    return load_json(ACCEPTED_STATE) if ACCEPTED_STATE.exists() else seed(spec)


def copy_atomically(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.candidate")
    shutil.copy2(source, temporary)
    temporary.replace(destination)


def learn(text: str, action: str, evidence: str, scope: str, confidence: float) -> str:
    knowledge = load_json(KNOWLEDGE)
    normalized = "-".join(text.lower().split())[:64].strip("-") or "learned-rule"
    existing_ids = {rule["id"] for rule in knowledge["rules"]}
    identifier = normalized
    suffix = 2
    while identifier in existing_ids:
        identifier = f"{normalized}-{suffix}"
        suffix += 1
    knowledge["rules"].append(
        {
            "id": identifier,
            "scope": scope,
            "trigger": text,
            "action": action,
            "evidence": evidence,
            "confidence": confidence,
            "updated_at": now(),
        }
    )
    atomic_write_json(KNOWLEDGE, knowledge)
    return identifier


def evaluate(args: argparse.Namespace, spec: dict[str, Any]) -> dict[str, Any]:
    report_path = resolve(args.report)
    artifact_path = resolve(args.artifact)
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    if not artifact_path.is_file():
        raise FileNotFoundError(artifact_path)

    report = load_json(report_path)
    candidate = report_metrics(report, args.kind)
    state = load_or_seed(spec)
    baseline = state["targets"].get(args.kind, {}).get("metrics")
    decision = promotion_decision(
        candidate,
        baseline,
        spec["quality"][args.kind],
        spec["quality"]["promotion"],
        args.hypothesis,
        args.primary_change,
    )
    ledger_entry = {
        "timestamp": now(),
        "project_id": spec["project_id"],
        "kind": args.kind,
        "hypothesis": args.hypothesis,
        "primary_change": args.primary_change,
        "report": str(report_path.relative_to(ROOT)) if report_path.is_relative_to(ROOT) else str(report_path),
        "artifact": str(artifact_path.relative_to(ROOT)) if artifact_path.is_relative_to(ROOT) else str(artifact_path),
        "artifact_sha256": sha256(artifact_path),
        "metrics": candidate,
        "decision": decision,
    }
    append_jsonl(ITERATION_LEDGER, ledger_entry)

    promoted = False
    if decision["accepted"] and args.promote:
        canonical_report, canonical_artifact = canonical_paths(spec, args.kind)
        if report_path.resolve() != canonical_report.resolve():
            copy_atomically(report_path, canonical_report)
        if artifact_path.resolve() != canonical_artifact.resolve():
            copy_atomically(artifact_path, canonical_artifact)
        state["targets"][args.kind] = {
            "report": str(canonical_report.relative_to(ROOT)),
            "artifact": str(canonical_artifact.relative_to(ROOT)),
            "artifact_sha256": sha256(canonical_artifact),
            "metrics": candidate,
            "weighted_score": decision["candidate_score"],
            "accepted_at": now(),
            "hypothesis": args.hypothesis,
            "primary_change": args.primary_change,
        }
        state["updated_at"] = now()
        atomic_write_json(ACCEPTED_STATE, state)
        promoted = True

    learned_rule = None
    if args.learning_trigger:
        learned_rule = learn(
            args.learning_trigger,
            args.learning_action,
            args.learning_evidence,
            args.learning_scope,
            args.learning_confidence,
        )
    return {
        "kind": args.kind,
        "decision": decision,
        "promoted": promoted,
        "ledger": str(ITERATION_LEDGER.relative_to(ROOT)),
        "learned_rule": learned_rule,
    }


def advise(spec: dict[str, Any], scope: str | None) -> list[dict[str, Any]]:
    rules = load_json(KNOWLEDGE)["rules"]
    if scope:
        rules = [rule for rule in rules if rule["scope"] == scope]
    return sorted(rules, key=lambda rule: float(rule["confidence"]), reverse=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--spec", default=str(DEFAULT_SPEC))
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("seed", help="Record the current verified canonical state")
    commands.add_parser("status", help="Print the accepted state")
    advice = commands.add_parser("advise", help="Print reusable rules before a new pass")
    advice.add_argument("--scope")
    candidate = commands.add_parser("evaluate", help="Gate and optionally promote a candidate")
    candidate.add_argument("--kind", choices=("direct_midi", "native"), required=True)
    candidate.add_argument("--report", required=True)
    candidate.add_argument("--artifact", required=True)
    candidate.add_argument("--hypothesis", required=True)
    candidate.add_argument("--primary-change", required=True)
    candidate.add_argument("--promote", action="store_true")
    candidate.add_argument("--learning-trigger", default="")
    candidate.add_argument("--learning-action", default="")
    candidate.add_argument("--learning-evidence", default="")
    candidate.add_argument("--learning-scope", default="iteration")
    candidate.add_argument("--learning-confidence", type=float, default=0.8)
    return result


def main() -> None:
    args = parser().parse_args()
    spec = load_spec(Path(args.spec))
    if args.command == "seed":
        output = seed(spec)
    elif args.command == "status":
        output = load_or_seed(spec)
    elif args.command == "advise":
        output = advise(spec, args.scope)
    else:
        output = evaluate(args, spec)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
