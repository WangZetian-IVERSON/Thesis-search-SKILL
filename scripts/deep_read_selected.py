from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from analyze_paper import analyze
from audit_report import audit
from build_report import build_report
from capture_figures import capture
from fetch_fulltext import download_pdf
from parse_pdf import parse_pdf
from read_paper import build_reading_page
from lib.library import update_deep_read_record
from lib.utils import ensure_dir, read_json, slugify, write_json


CHINESE_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
    "十三": 13,
    "十四": 14,
    "十五": 15,
    "十六": 16,
    "十七": 17,
    "十八": 18,
    "十九": 19,
    "二十": 20,
}


def parse_rank(selection: str) -> int:
    text = selection.strip()
    if text.isdigit():
        return int(text)
    match = __import__("re").search(r"第\s*(\d{1,3})\s*(篇|个|项|篇论文)?", text)
    if match:
        return int(match.group(1))
    for chinese, value in sorted(CHINESE_NUMBERS.items(), key=lambda item: len(item[0]), reverse=True):
        if f"第{chinese}" in text or chinese == text:
            return value
    raise SystemExit(f"Could not parse paper rank from selection: {selection}")


def pick_paper(screening_path: Path, rank: int) -> dict:
    screening = read_json(screening_path, {})
    papers = screening.get("papers", []) if isinstance(screening, dict) else []
    for paper in papers:
        if paper.get("rank") == rank:
            return paper
    raise SystemExit(f"No paper with rank {rank} in {screening_path}")


def direct_pdf_url(url: str | None) -> bool:
    if not url:
        return False
    lower = url.lower()
    return lower.endswith(".pdf") or "arxiv.org/pdf" in lower


def ensure_pdf(paper: dict, papers_dir: Path) -> Path:
    existing = paper.get("pdf_path")
    if existing and Path(existing).exists():
        return Path(existing)

    url = paper.get("url")
    if not direct_pdf_url(url):
        raise SystemExit(
            "Selected paper has no direct open PDF URL. Upload the PDF to papers/ and run read_paper.py directly, "
            "or choose a paper with an open PDF link."
        )

    title = paper.get("title") or paper.get("paper_id") or "paper"
    target = ensure_dir(papers_dir) / f"{slugify(title, 92)}.pdf"
    if not target.exists():
        ok = download_pdf(url, target)
        if not ok:
            raise SystemExit(f"URL did not return a PDF: {url}")
    paper["pdf_path"] = str(target)
    return target


def deep_read(screening_path: Path, rank: int, topic: str, questions: str | None, output_root: Path) -> dict:
    paper = pick_paper(screening_path, rank)
    pdf_path = ensure_pdf(paper, Path("papers"))

    evidence_dir = ensure_dir(output_root / "evidence")
    readings_dir = ensure_dir(output_root / "readings")
    analyses_dir = ensure_dir(output_root / "analyses")

    parsed_path = parse_pdf(pdf_path, evidence_dir)
    reading_html = build_reading_page(parsed_path, readings_dir, questions, "zh", 100)
    reading_manifest = readings_dir / f"{Path(reading_html).stem.replace('.reading', '')}.reading_manifest.json"
    figure_manifest = capture(pdf_path, output_root, None)
    analysis_json, analysis_md = analyze(reading_manifest, [figure_manifest], analyses_dir, topic)
    reports_dir = ensure_dir(output_root / "reports")
    checks_dir = ensure_dir(output_root / "checks")
    report_slug = slugify(f"{screening_path.stem}-rank-{rank}", 96)
    report_path = reports_dir / f"deep-read-{report_slug}.html"
    audit_path = checks_dir / f"deep-read-{report_slug}-audit.md"
    build_report(
        f"深度精读第 {rank} 篇：{paper.get('title') or paper.get('paper_id')}",
        None,
        [parsed_path],
        [figure_manifest],
        [reading_manifest],
        [analysis_json],
        report_path,
    )
    audit(None, [figure_manifest], [reading_manifest], [analysis_json], report_path, audit_path)

    summary = {
        "rank": rank,
        "title": paper.get("title"),
        "pdf_path": str(pdf_path),
        "parsed": str(parsed_path),
        "reading_html": str(reading_html),
        "reading_manifest": str(reading_manifest),
        "figure_manifest": str(figure_manifest),
        "analysis_json": str(analysis_json),
        "analysis_md": str(analysis_md),
        "report_html": str(report_path),
        "audit": str(audit_path),
    }
    summary_path = output_root / "checks" / f"deep-read-{report_slug}.json"
    write_json(summary_path, summary)
    update_deep_read_record(screening_path, rank, summary)
    print(f"Deep read summary saved: {summary_path}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep read one selected paper by rank from a screening JSON file.")
    parser.add_argument("screening", help="screen-*.json from scripts/screen_papers.py")
    parser.add_argument("selection", help="Paper rank or natural language selection, e.g. 3, 第3篇, 帮我精读第三篇")
    parser.add_argument("--topic", default="", help="User research topic")
    parser.add_argument("--questions", default=None, help="Reading questions for read_paper.py")
    parser.add_argument("--output", default="outputs", help="Output root directory")
    args = parser.parse_args()
    deep_read(Path(args.screening), parse_rank(args.selection), args.topic, args.questions, Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
