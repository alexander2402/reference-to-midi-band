#!/usr/bin/env python3
"""Compare the exported native GarageBand project with the exact reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_render import ANALYSIS, REFERENCE_GRID_OFFSET, RENDERS, compare_pair, crop_reference, load, section_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--render",
        default="Gorodok_Matched_GarageBand_verified.wav",
        help="WAV filename inside renders/",
    )
    parser.add_argument(
        "--output",
        default="garageband_comparison.json",
        help="JSON filename inside analysis/",
    )
    parser.add_argument(
        "--render-path",
        help="Explicit candidate WAV path; overrides --render",
    )
    parser.add_argument(
        "--output-path",
        help="Explicit report path; overrides --output",
    )
    args = parser.parse_args()

    render_path = Path(args.render_path) if args.render_path else RENDERS / args.render
    output_path = Path(args.output_path) if args.output_path else ANALYSIS / args.output
    rendered = load(render_path)
    reference = crop_reference(load(ANALYSIS / "reference.wav"), len(rendered))
    metrics = compare_pair(reference, rendered)
    metrics["sections"] = section_metrics(reference, rendered)
    report = {
        "reference_alignment_seconds_removed": REFERENCE_GRID_OFFSET,
        "renderer": "GarageBand 10.4.3 native project export, PCM WAV 44.1 kHz / 16-bit / stereo",
        "project": "Gorodok_Matched.band",
        "render": str(render_path),
        "metrics": metrics,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
