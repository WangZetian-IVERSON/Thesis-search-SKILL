from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.citation import format_apa, format_bibtex
from lib.schema import PaperMetadata
from lib.utils import read_json


def load_paper(metadata_path: Path, query: str) -> PaperMetadata:
    data = read_json(metadata_path, {})
    papers = data.get("papers", []) if isinstance(data, dict) else []
    query_lower = query.lower()
    for paper in papers:
        haystack = " ".join([paper.get("paper_id") or "", paper.get("title") or "", paper.get("doi") or ""]).lower()
        if query_lower in haystack:
            return PaperMetadata(**paper)
    raise SystemExit(f"No matching paper found for: {query}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate APA and BibTeX from a metadata JSON file.")
    parser.add_argument("metadata", help="find-*.json metadata file")
    parser.add_argument("query", help="Paper id, title substring, or DOI substring")
    args = parser.parse_args()
    paper = load_paper(Path(args.metadata), args.query)
    print("APA 7:")
    print(format_apa(paper))
    print("\nBibTeX:")
    print(format_bibtex(paper))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
