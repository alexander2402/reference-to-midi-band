#!/usr/bin/env python3
"""Shared data and quality-gate helpers for the studio pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = REPO_ROOT / "projects"
DEFAULT_PROJECT = os.environ.get("STUDIO_PROJECT", "gorodok")
ROOT = PROJECTS_ROOT / DEFAULT_PROJECT
DEFAULT_SPEC = ROOT / "project.json"
KNOWLEDGE = REPO_ROOT / "studio" / "knowledge.json"
ACCEPTED_STATE = ROOT / "analysis" / "accepted_state.json"
ITERATION_LEDGER = ROOT / "analysis" / "iteration_ledger.jsonl"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_spec(path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    spec = load_json(path)
    if spec.get("schema_version") != 1:
        raise ValueError(f"Unsupported project spec schema: {spec.get('schema_version')}")
    return spec


def resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def report_metrics(report: dict[str, Any], kind: str) -> dict[str, float]:
    if kind == "direct_midi":
        source = report["metrics"]["full_mix"]
    elif kind == "native":
        source = report["metrics"]
    else:
        raise ValueError(f"Unknown comparison kind: {kind}")
    return {
        "rms_envelope_correlation": float(source["rms_envelope_correlation"]),
        "onset_envelope_correlation": float(source["onset_envelope_correlation"]),
        "chroma_cosine_similarity": float(source["chroma_cosine_similarity"]),
        "mfcc_timbre_similarity": float(source["mfcc_timbre_similarity"]),
        "onset_f1": float(source["onset_match"]["f1"]),
    }


def weighted_score(metrics: dict[str, float], weights: dict[str, float]) -> float:
    missing = set(weights) - set(metrics)
    if missing:
        raise ValueError(f"Metrics missing from report: {sorted(missing)}")
    total_weight = sum(float(weight) for weight in weights.values())
    if total_weight <= 0:
        raise ValueError("Quality weights must sum to a positive value")
    return sum(metrics[name] * float(weight) for name, weight in weights.items()) / total_weight


def promotion_decision(
    candidate: dict[str, float],
    baseline: dict[str, float] | None,
    quality: dict[str, Any],
    promotion: dict[str, Any],
    hypothesis: str,
    primary_change: str,
) -> dict[str, Any]:
    minimum_failures = {
        name: {"actual": candidate[name], "minimum": float(minimum)}
        for name, minimum in quality["minimums"].items()
        if candidate[name] < float(minimum)
    }
    candidate_score = weighted_score(candidate, quality["weights"])
    baseline_score = weighted_score(baseline, quality["weights"]) if baseline else None
    regressions: dict[str, dict[str, float]] = {}
    if baseline:
        allowed = float(promotion["maximum_single_metric_regression"])
        for name, old_value in baseline.items():
            regression = old_value - candidate[name]
            if regression > allowed:
                regressions[name] = {
                    "baseline": old_value,
                    "candidate": candidate[name],
                    "regression": round(regression, 6),
                    "allowed": allowed,
                }
    gain = candidate_score - baseline_score if baseline_score is not None else None
    process_failures: list[str] = []
    if promotion.get("require_hypothesis") and not hypothesis.strip():
        process_failures.append("A candidate hypothesis is required")
    if promotion.get("require_single_primary_change") and not primary_change.strip():
        process_failures.append("One primary change must be named")
    insufficient_gain = (
        gain is not None and gain < float(promotion["minimum_weighted_gain"])
    )
    accepted = not minimum_failures and not regressions and not process_failures and not insufficient_gain
    return {
        "accepted": accepted,
        "candidate_score": round(candidate_score, 6),
        "baseline_score": round(baseline_score, 6) if baseline_score is not None else None,
        "weighted_gain": round(gain, 6) if gain is not None else None,
        "minimum_failures": minimum_failures,
        "protected_regressions": regressions,
        "process_failures": process_failures,
        "insufficient_gain": insufficient_gain,
    }
