from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.schema import FigureRecord
from lib.utils import ensure_dir, slugify, stable_paper_id, write_json

CAPTION_RE = re.compile(r"^\s*(fig(?:ure)?|table)\s*\.?\s*(\d+[a-z]?)\b[:.\- ]*(.*)", re.IGNORECASE)


def find_caption_lines(text: str) -> list[tuple[str, str, str]]:
    matches = []
    for line in text.splitlines():
        line = " ".join(line.split())
        match = CAPTION_RE.search(line)
        if match:
            kind = "table" if match.group(1).lower().startswith("table") else "figure"
            number = match.group(2)
            caption = match.group(3).strip() or line
            matches.append((kind, number, caption))
    return matches


def capture(pdf_path: Path, output_dir: Path, max_pages: int | None = None) -> Path:
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit("PyMuPDF is required. Install with: pip install -r requirements.txt") from exc

    document = fitz.open(pdf_path)
    title = (document.metadata or {}).get("title") or pdf_path.stem
    paper_id = stable_paper_id(title) or slugify(pdf_path.stem)
    screenshot_dir = ensure_dir(output_dir / "screenshots" / paper_id)
    records: list[FigureRecord] = []
    page_limit = min(max_pages or len(document), len(document))

    for page_index in range(page_limit):
        page = document[page_index]
        text = page.get_text("text")
        captions = find_caption_lines(text)
        if not captions:
            continue
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        page_image = screenshot_dir / f"page-{page_index + 1}.png"
        pixmap.save(page_image)
        for item_index, (kind, number, caption) in enumerate(captions, start=1):
            figure_id = f"{kind}{number}"
            records.append(
                FigureRecord(
                    paper_id=paper_id,
                    figure_id=figure_id,
                    kind=kind,
                    page=page_index + 1,
                    caption=caption,
                    screenshot=str(page_image),
                    extraction_method="full-page-caption-detected",
                    confidence="medium",
                )
            )

    manifest = {
        "paper_id": paper_id,
        "source_pdf": str(pdf_path.resolve()),
        "records": [record.to_dict() for record in records],
    }
    manifest_path = ensure_dir(output_dir / "evidence") / f"{paper_id}.figures_manifest.json"
    write_json(manifest_path, manifest)
    print(f"Figure manifest saved: {manifest_path}")
    print(f"Detected figure/table captions: {len(records)}")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture page screenshots for figure/table captions in a PDF.")
    parser.add_argument("pdf", help="Path to local PDF")
    parser.add_argument("--output", default="outputs", help="Output root directory")
    parser.add_argument("--max-pages", type=int, default=None, help="Only scan the first N pages")
    args = parser.parse_args()
    capture(Path(args.pdf), Path(args.output), args.max_pages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
