from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.synthesis import build_paper_analysis


class SynthesisTests(unittest.TestCase):
    def test_build_paper_analysis_extracts_sections(self) -> None:
        reading = {
            "paper_id": "sample",
            "title": "Sample",
            "annotations": [
                {"page": 1, "role": "methodology", "text": "We propose a method for evaluating language model agents with a dataset of literature review tasks."},
                {"page": 2, "role": "evidence", "text": "The result shows improved performance and higher evidence grounding accuracy."},
                {"page": 3, "role": "concession", "text": "However, the study is limited by a small dataset and future work should test more disciplines."},
            ],
        }
        analysis = build_paper_analysis(reading, topic="language model agents")
        self.assertEqual(analysis["paper_id"], "sample")
        self.assertIn("method", analysis["sections"])
        self.assertIn("dataset", analysis["sections"]["method"]["summary"].lower())
        self.assertIn("方法线索", analysis["sections"]["method"]["summary_zh"])
        self.assertIn("主要证据", analysis["sections"]["method"]["deep_summary_zh"])
        self.assertGreaterEqual(len(analysis["sections"]["method"]["deep_points_zh"]), 4)
        self.assertIn("This passage", analysis["sections"]["method"]["summary_en"])
        self.assertIn("language model agents", analysis["relevance"]["summary"])
        self.assertGreaterEqual(len(analysis["relevance"]["deep_points_zh"]), 3)
        self.assertIn("language model agents", analysis["relevance"]["summary_en"])


if __name__ == "__main__":
    unittest.main()
