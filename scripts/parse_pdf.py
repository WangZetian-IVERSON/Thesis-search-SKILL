from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.schema import ParsedPage
from lib.utils import ensure_dir, slugify, stable_paper_id, write_json


def parse_pdf(path: Path, output_dir: Path) -> Path:
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit("PyMuPDF is required. Install with: pip install -r requirements.txt") from exc

    document = fitz.open(path)
    metadata = document.metadata or {}
    title = metadata.get("title") or path.stem
    author_text = metadata.get("author") or ""
    authors = [part.strip() for part in author_text.replace(";", ",").split(",") if part.strip()]
    paper_id = stable_paper_id(title, None, authors[0] if authors else None) or slugify(path.stem)

    pages = []
    for index, page in enumerate(document, start=1):
        pages.append(ParsedPage(page=index, text=page.get_text("text")).to_dict())

    result = {
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "source_pdf": str(path.resolve()),
        "page_count": len(document),
        "pages": pages,
    }
    output_path = ensure_dir(output_dir) / f"{paper_id}.parsed.json"
    write_json(output_path, result)
    print(f"Parsed PDF saved: {output_path}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a local PDF into page-level JSON.")
    parser.add_argument("pdf", help="Path to local PDF")
    parser.add_argument("--output", default="outputs/evidence", help="Output directory")
    args = parser.parse_args()
    parse_pdf(Path(args.pdf), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
