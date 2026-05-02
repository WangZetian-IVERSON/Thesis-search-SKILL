from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.text_analysis import annotate_paragraphs, parse_questions


class TextAnalysisTests(unittest.TestCase):
    def test_parse_questions_accepts_multiple_separators(self) -> None:
        questions = parse_questions("Q1: method?; dataset size, limitations")
        self.assertEqual(questions, ["method?", "dataset size", "limitations"])

    def test_annotate_detects_methodology(self) -> None:
        annotations = annotate_paragraphs(
            [(1, "We propose a method and evaluate the model on a dataset. The experiment shows improved performance over baselines.")],
            questions=["method"],
            max_paragraphs=5,
        )
        self.assertEqual(len(annotations), 1)
        self.assertIn(annotations[0].role, {"methodology", "evidence"})
        self.assertEqual(annotations[0].matched_questions, ["method"])
        self.assertTrue(annotations[0].paragraph_function_zh)
        self.assertTrue(annotations[0].paragraph_function_en)
        self.assertIn("中文译读", annotations[0].translation_zh)


if __name__ == "__main__":
    unittest.main()
