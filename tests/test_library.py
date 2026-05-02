from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.library import parse_date, parse_order, pick_by_request, upsert_screening
from lib.utils import write_json


class LibraryTests(unittest.TestCase):
    def test_parse_date_and_order_from_natural_language(self) -> None:
        self.assertEqual(parse_date("给我2026-04-29抓取的第一个论文的精读"), "2026-04-29")
        self.assertEqual(parse_date("给我4.29号抓取的第2篇论文"), "2026-04-29")
        self.assertEqual(parse_order("给我4.29号抓取的第一个论文的精读"), 1)
        self.assertEqual(parse_order("给我4.29号抓取的第12篇论文"), 12)

    def test_upsert_and_pick_by_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            screening = root / "screen-topic.json"
            library = root / "library.json"
            dashboard = root / "index.html"
            write_json(
                screening,
                {
                    "topic": "agent review",
                    "captured_at": "2026-04-29T09:00:00",
                    "captured_date": "2026-04-29",
                    "screening_mode": "metadata-and-abstract-only",
                    "papers": [
                        {
                            "rank": 1,
                            "title": "Agent Review",
                            "authors": ["Ada"],
                            "venue": "arXiv",
                            "source": "arXiv",
                            "score": 0.9,
                            "zh_takeaway": "中文总结",
                        }
                    ],
                },
            )
            upsert_screening(screening, library, dashboard)
            picked = pick_by_request("给我2026-04-29抓取的第一个论文的精读", library)
            self.assertEqual(picked["title"], "Agent Review")
            self.assertTrue(dashboard.exists())


if __name__ == "__main__":
    unittest.main()
