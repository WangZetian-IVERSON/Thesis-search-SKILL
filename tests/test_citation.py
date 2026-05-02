from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.citation import format_apa, format_bibtex
from lib.schema import PaperMetadata


class CitationTests(unittest.TestCase):
    def test_formats_include_doi(self) -> None:
        paper = PaperMetadata(paper_id="x", title="Useful Paper", authors=["Ada Lovelace"], year=2026, venue="Journal", doi="10.1000/test")
        self.assertIn("https://doi.org/10.1000/test", format_apa(paper))
        self.assertIn("doi = {10.1000/test}", format_bibtex(paper))


if __name__ == "__main__":
    unittest.main()
