from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.citation import format_apa, format_bibtex
from lib.schema import PaperMetadata
from lib.text_analysis import annotate_paragraphs, parse_questions
from lib.utils import ensure_dir, read_json, slugify, stable_paper_id, write_json, write_text


def parse_pdf_direct(pdf_path: Path) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit("PyMuPDF is required. Install with: pip install -r requirements.txt") from exc

    document = fitz.open(pdf_path)
    metadata = document.metadata or {}
    title = metadata.get("title") or pdf_path.stem
    author_text = metadata.get("author") or ""
    authors = [part.strip() for part in author_text.replace(";", ",").split(",") if part.strip()]
    paper_id = stable_paper_id(title, None, authors[0] if authors else None) or slugify(pdf_path.stem)
    pages = [{"page": index, "text": page.get_text("text")} for index, page in enumerate(document, start=1)]
    return {
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "source_pdf": str(pdf_path.resolve()),
        "page_count": len(document),
        "pages": pages,
    }


def load_input(path: Path) -> dict:
    if path.suffix.lower() == ".json":
        data = read_json(path, {})
        if not data:
            raise SystemExit(f"Parsed JSON is empty or unreadable: {path}")
        return data
    if path.suffix.lower() == ".pdf":
        return parse_pdf_direct(path)
    raise SystemExit("Input must be a PDF or a *.parsed.json file.")


def build_reading_page(input_path: Path, output_dir: Path, questions_raw: str | None = None, lang: str = "zh", max_paragraphs: int = 80) -> Path:
    data = load_input(input_path)
    questions = parse_questions(questions_raw)
    page_texts = [(page.get("page"), page.get("text") or "") for page in data.get("pages", [])]
    annotations = annotate_paragraphs(page_texts, questions=questions, lang=lang, max_paragraphs=max_paragraphs, title=data.get("title") or "")

    paper = PaperMetadata(
        paper_id=data.get("paper_id") or slugify(data.get("title") or input_path.stem),
        title=data.get("title") or input_path.stem,
        authors=data.get("authors") or [],
        pdf_path=data.get("source_pdf"),
        fulltext_status="parsed-fulltext",
    )

    env = Environment(loader=FileSystemLoader(ROOT_DIR / "templates"), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("reading.html.j2")
    html = template.render(
        title=paper.title,
        source_pdf=paper.pdf_path or str(input_path),
        page_count=data.get("page_count") or len(data.get("pages", [])),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        mode="question" if questions else "logic",
        annotations=[item.to_dict() for item in annotations],
        apa=format_apa(paper),
        bibtex=format_bibtex(paper),
    )

    output_dir = ensure_dir(output_dir)
    html_path = output_dir / f"{paper.paper_id}.reading.html"
    manifest_path = output_dir / f"{paper.paper_id}.reading_manifest.json"
    write_text(html_path, html)
    write_json(
        manifest_path,
        {
            "paper_id": paper.paper_id,
            "title": paper.title,
            "source": str(input_path.resolve()),
            "output_html": str(html_path),
            "mode": "question" if questions else "logic",
            "questions": questions,
            "annotation_count": len(annotations),
            "annotations": [item.to_dict() for item in annotations],
        },
    )
    print(f"Reading HTML saved: {html_path}")
    print(f"Reading manifest saved: {manifest_path}")
    return html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Paperwise-style dual-column reading HTML for a local PDF or parsed JSON.")
    parser.add_argument("input", help="PDF file or *.parsed.json file")
    parser.add_argument("--questions", default=None, help="Reading questions separated by commas, semicolons, newlines, or Q1: labels")
    parser.add_argument("--lang", default="zh", choices=["zh", "en"], help="Annotation language")
    parser.add_argument("--max-paragraphs", type=int, default=80, help="Maximum paragraphs to annotate")
    parser.add_argument("--output", default="outputs/readings", help="Output directory")
    args = parser.parse_args()
    build_reading_page(Path(args.input), Path(args.output), args.questions, args.lang, args.max_paragraphs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
