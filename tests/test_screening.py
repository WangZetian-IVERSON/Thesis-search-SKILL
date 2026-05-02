from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.screening import screen_papers
from deep_read_selected import parse_rank


class ScreeningTests(unittest.TestCase):
    def test_screening_assigns_ranks_and_actions(self) -> None:
        metadata = {
            "query": "agent literature review",
            "papers": [
                {
                    "paper_id": "p1",
                    "title": "Agent Literature Review Benchmark",
                    "authors": ["Ada Lovelace"],
                    "year": 2026,
                    "venue": "arXiv",
                    "url": "https://arxiv.org/pdf/1234.5678",
                    "abstract": "We propose a benchmark dataset for agent literature review evaluation.",
                    "fulltext_status": "open-access",
                    "score": 0.9,
                }
            ],
        }
        result = screen_papers(metadata)
        self.assertEqual(result["screening_mode"], "metadata-and-abstract-only")
        self.assertEqual(result["papers"][0]["rank"], 1)
        self.assertEqual(result["papers"][0]["natural_language_prompt"], "帮我精读第1篇")
        self.assertIn("摘要总结", result["papers"][0]["zh_takeaway"])
        self.assertIn("数据集", result["papers"][0]["zh_takeaway"])
        self.assertIn("preliminarily classified", result["papers"][0]["en_takeaway"])
        self.assertIn("该论文", result["papers"][0]["screening_reason_zh"])
        self.assertIn("title matches", result["papers"][0]["screening_reason_en"])
        self.assertIn("PDF", result["papers"][0]["next_action_zh"])
        self.assertIn("benchmark dataset", result["papers"][0]["english_digest"])
        self.assertIn("does not claim full-text", result["limits"][0])
        self.assertIn("download", result["papers"][0]["next_action"])

    def test_parse_rank_accepts_natural_language(self) -> None:
        self.assertEqual(parse_rank("3"), 3)
        self.assertEqual(parse_rank("第3篇"), 3)
        self.assertEqual(parse_rank("帮我精读第三篇"), 3)
        self.assertEqual(parse_rank("第十二篇"), 12)


if __name__ == "__main__":
    unittest.main()
