from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.dedupe import dedupe_papers, normalize_doi
from lib.schema import PaperMetadata


class DedupeTests(unittest.TestCase):
    def test_normalize_doi_strips_prefix(self) -> None:
        self.assertEqual(normalize_doi("https://doi.org/10.1000/ABC"), "10.1000/abc")

    def test_dedupe_merges_by_doi(self) -> None:
        papers = [
            PaperMetadata(paper_id="a", title="A Study", doi="10.1000/abc", cited_by_count=1),
            PaperMetadata(paper_id="b", title="A Study Duplicate", doi="https://doi.org/10.1000/ABC", cited_by_count=5, abstract="x"),
        ]
        merged = dedupe_papers(papers)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].cited_by_count, 5)
        self.assertEqual(merged[0].abstract, "x")


if __name__ == "__main__":
    unittest.main()
