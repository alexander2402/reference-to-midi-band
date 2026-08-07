from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from garageband_native import fader_x  # noqa: E402
from studio_common import load_spec, promotion_decision, report_metrics  # noqa: E402


class StudioSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = load_spec()

    def test_sections_cover_the_complete_song_once(self) -> None:
        bars = [
            bar
            for section in self.spec["sections"]
            for bar in range(section["start_bar"], section["end_bar"] + 1)
        ]
        self.assertEqual(bars, list(range(1, self.spec["music"]["bars"] + 1)))

    def test_deliverables_are_canonical_not_versioned(self) -> None:
        deliverables = self.spec["deliverables"]
        artifact_keys = {
            "native_project",
            "full_midi",
            "part_midis",
            "midi_render",
            "native_render",
            "midi_comparison",
            "native_comparison",
        }
        names = []
        for key in artifact_keys:
            value = deliverables[key]
            names.extend(value if isinstance(value, list) else [value])
        self.assertFalse(any("_v2" in name or "iteration" in name or "baseline" in name for name in names))

    def test_current_reports_meet_declared_thresholds(self) -> None:
        targets = {
            "direct_midi": ROOT / self.spec["deliverables"]["midi_comparison"],
            "native": ROOT / self.spec["deliverables"]["native_comparison"],
        }
        for kind, path in targets.items():
            report = json.loads(path.read_text(encoding="utf-8"))
            metrics = report_metrics(report, kind)
            for name, minimum in self.spec["quality"][kind]["minimums"].items():
                self.assertGreaterEqual(metrics[name], minimum, f"{kind} {name}")

    def test_unchanged_candidate_is_not_promoted(self) -> None:
        baseline = {
            "rms_envelope_correlation": 0.50,
            "onset_envelope_correlation": 0.71,
            "chroma_cosine_similarity": 0.95,
            "mfcc_timbre_similarity": 0.87,
            "onset_f1": 0.76,
        }
        decision = promotion_decision(
            baseline,
            baseline,
            self.spec["quality"]["direct_midi"],
            self.spec["quality"]["promotion"],
            "No-op reproducibility check",
            "no-op",
        )
        self.assertFalse(decision["accepted"])
        self.assertTrue(decision["insufficient_gain"])

    def test_broad_regression_blocks_a_higher_weighted_score(self) -> None:
        baseline = {
            "rms_envelope_correlation": 0.50,
            "onset_envelope_correlation": 0.71,
            "chroma_cosine_similarity": 0.95,
            "mfcc_timbre_similarity": 0.87,
            "onset_f1": 0.76,
        }
        candidate = dict(baseline)
        candidate["chroma_cosine_similarity"] = 0.99
        candidate["rms_envelope_correlation"] = 0.48
        decision = promotion_decision(
            candidate,
            baseline,
            self.spec["quality"]["direct_midi"],
            self.spec["quality"]["promotion"],
            "Increase harmonic clarity",
            "accompaniment-voicing",
        )
        self.assertFalse(decision["accepted"])
        self.assertIn("rms_envelope_correlation", decision["protected_regressions"])

    def test_fader_geometry_matches_verified_garageband_mapping(self) -> None:
        self.assertEqual(fader_x(375, 128, 233, 233), 500)
        self.assertEqual(fader_x(375, 128, 233, 173), 440)
        self.assertEqual(fader_x(375, 128, 233, 153), 420)


if __name__ == "__main__":
    unittest.main()
