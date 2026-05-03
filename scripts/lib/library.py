from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.utils import ensure_dir, read_json, slugify, write_json, write_text

SCRIPT_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = SCRIPT_DIR.parent
DEFAULT_LIBRARY_JSON = ROOT_DIR / "outputs" / "library" / "library.json"
DEFAULT_LIBRARY_HTML = ROOT_DIR / "outputs" / "library" / "index.html"

CHINESE_ORDER_NUMBERS = {
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


def now_local() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def local_date(value: str | None = None) -> str:
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            pass
    return datetime.now().date().isoformat()


def relative_to_html(path: str | Path | None, html_path: Path = DEFAULT_LIBRARY_HTML) -> str:
    if not path:
        return ""
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = (ROOT_DIR / resolved).resolve()
    try:
        return Path(os.path.relpath(resolved, html_path.parent.resolve())).as_posix()
    except ValueError:
        return resolved.as_uri()


def load_library(path: Path = DEFAULT_LIBRARY_JSON) -> dict[str, Any]:
    data = read_json(path, None)
    if isinstance(data, dict):
        data.setdefault("version", 1)
        data.setdefault("sessions", [])
        return data
    return {"version": 1, "created_at": now_local(), "updated_at": now_local(), "sessions": []}


def save_library(data: dict[str, Any], path: Path = DEFAULT_LIBRARY_JSON) -> Path:
    data["updated_at"] = now_local()
    return write_json(path, data)


def paper_identity(paper: dict[str, Any]) -> str:
    if paper.get("doi"):
        return "doi:" + str(paper.get("doi")).lower()
    if paper.get("paper_id"):
        return "paper:" + str(paper.get("paper_id"))
    return "title:" + slugify(str(paper.get("title") or "untitled"), 96)


def make_paper_record(paper: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    rank = int(paper.get("rank") or 0)
    session_id = session["session_id"]
    record_id = f"{session_id}-{rank:03d}"
    return {
        "record_id": record_id,
        "identity": paper_identity(paper),
        "session_id": session_id,
        "captured_at": session["captured_at"],
        "captured_date": session["captured_date"],
        "rank": rank,
        "title": paper.get("title") or "Untitled",
        "authors": paper.get("authors") or [],
        "year": paper.get("year"),
        "venue": paper.get("venue"),
        "source": paper.get("source"),
        "score": paper.get("score"),
        "doi": paper.get("doi"),
        "url": paper.get("url"),
        "paper_type": paper.get("paper_type"),
        "abstract": paper.get("abstract"),
        "zh_takeaway": paper.get("zh_takeaway"),
        "screening_reason_zh": paper.get("screening_reason_zh") or paper.get("screening_reason"),
        "next_action_zh": paper.get("next_action_zh") or paper.get("next_action"),
        "natural_language_prompt": f"给我{session['captured_date']}抓取的第{rank}篇论文的精读",
        "fulltext_status": paper.get("fulltext_status"),
        "pdf_path": paper.get("pdf_path"),
        "screening_json": session.get("screening_json"),
        "deep_read": paper.get("deep_read") or {},
    }


def upsert_screening(screening_path: Path, library_path: Path = DEFAULT_LIBRARY_JSON, dashboard_path: Path = DEFAULT_LIBRARY_HTML) -> dict[str, Any]:
    screening = read_json(screening_path, {})
    if not isinstance(screening, dict) or not screening.get("papers"):
        raise ValueError(f"Screening file is empty or invalid: {screening_path}")

    library = load_library(library_path)
    captured_at = screening.get("captured_at") or now_local()
    session = {
        "session_id": slugify(screening_path.stem, 96),
        "topic": screening.get("topic") or screening.get("source_metadata") or "未命名主题",
        "source_metadata": screening.get("source_metadata"),
        "screening_mode": screening.get("screening_mode"),
        "captured_at": captured_at,
        "captured_date": screening.get("captured_date") or local_date(captured_at),
        "screening_json": str(screening_path),
        "count": len(screening.get("papers", [])),
        "papers": [],
    }
    existing_session = next((item for item in library.get("sessions", []) if item.get("session_id") == session["session_id"]), None)
    existing_deep_reads = {}
    if existing_session:
        for paper in existing_session.get("papers", []):
            key = paper.get("identity") or f"rank:{paper.get('rank')}"
            if paper.get("deep_read"):
                existing_deep_reads[key] = paper.get("deep_read")

    records = [make_paper_record(paper, session) for paper in screening.get("papers", [])]
    for record in records:
        deep_read = existing_deep_reads.get(record.get("identity")) or existing_deep_reads.get(f"rank:{record.get('rank')}")
        if deep_read:
            record["deep_read"] = deep_read
    session["papers"] = records

    sessions = [item for item in library.get("sessions", []) if item.get("session_id") != session["session_id"]]
    sessions.append(session)
    sessions.sort(key=lambda item: (item.get("captured_at") or "", item.get("session_id") or ""), reverse=True)
    library["sessions"] = sessions
    save_library(library, library_path)
    render_dashboard(library_path, dashboard_path)
    return session


def update_deep_read_record(
    screening_path: Path,
    rank: int,
    summary: dict[str, Any],
    library_path: Path = DEFAULT_LIBRARY_JSON,
    dashboard_path: Path = DEFAULT_LIBRARY_HTML,
) -> None:
    library = load_library(library_path)
    session_id = slugify(screening_path.stem, 96)
    for session in library.get("sessions", []):
        if session.get("session_id") != session_id:
            continue
        for paper in session.get("papers", []):
            if int(paper.get("rank") or 0) == int(rank):
                paper["deep_read"] = {
                    "report_html": summary.get("report_html"),
                    "reading_html": summary.get("reading_html"),
                    "audit": summary.get("audit"),
                    "analysis_json": summary.get("analysis_json"),
                    "updated_at": now_local(),
                }
                # Refresh zh_takeaway from deep-reading analysis if available
                analysis_path = summary.get("analysis_json")
                if analysis_path:
                    analysis = read_json(Path(analysis_path), {})
                    sections = analysis.get("sections", {})
                    parts = []
                    for key in ("research_problem", "core_claim"):
                        zh = (sections.get(key) or {}).get("deep_summary_zh", "")
                        if zh and len(zh) > 10:
                            parts.append(zh)
                    if parts:
                        paper["zh_takeaway"] = " ".join(parts)
                save_library(library, library_path)
                render_dashboard(library_path, dashboard_path)
                return


def flattened_papers(library: dict[str, Any], html_path: Path = DEFAULT_LIBRARY_HTML) -> list[dict[str, Any]]:
    rows = []
    date_counts: dict[str, int] = {}
    for session in sorted(library.get("sessions", []), key=lambda item: item.get("captured_at") or ""):
        for paper in sorted(session.get("papers", []), key=lambda item: int(item.get("rank") or 0)):
            date_key = paper.get("captured_date") or session.get("captured_date") or "unknown"
            date_counts[date_key] = date_counts.get(date_key, 0) + 1
            row = dict(paper)
            row["date_rank"] = date_counts[date_key]
            row["authors_text"] = ", ".join(row.get("authors") or []) or "未知作者"
            row["report_href"] = relative_to_html(row.get("deep_read", {}).get("report_html"), html_path)
            row["reading_href"] = relative_to_html(row.get("deep_read", {}).get("reading_html"), html_path)
            row["screening_json_href"] = relative_to_html(row.get("screening_json"), html_path)
            row["pdf_href"] = relative_to_html(row.get("pdf_path"), html_path)
            row["has_deep_read"] = bool(row.get("report_href"))
            row["date_prompt"] = f"给我{date_key}抓取的第{row['date_rank']}篇论文的精读"
            search_text = " ".join(
                str(part or "")
                for part in [
                    row.get("title"),
                    row.get("authors_text"),
                    row.get("zh_takeaway"),
                    row.get("abstract"),
                    row.get("source"),
                    row.get("venue"),
                ]
            ).lower()
            row["search_text"] = re.sub(r"[\"'<>&]+", " ", search_text)
            rows.append(row)
    return sorted(rows, key=lambda item: (item.get("captured_date") or "", item.get("date_rank") or 0), reverse=True)


def render_dashboard(library_path: Path = DEFAULT_LIBRARY_JSON, dashboard_path: Path = DEFAULT_LIBRARY_HTML) -> Path:
    library = load_library(library_path)
    papers = flattened_papers(library, dashboard_path)
    env = Environment(loader=FileSystemLoader(ROOT_DIR / "templates"), autoescape=select_autoescape(["html", "xml"]))
    template = env.get_template("library.html.j2")
    html = template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        updated_at=library.get("updated_at"),
        sessions=library.get("sessions", []),
        papers=papers,
        paper_count=len(papers),
        deep_read_count=sum(1 for paper in papers if paper.get("has_deep_read")),
    )
    ensure_dir(dashboard_path.parent)
    write_text(dashboard_path, html)
    return dashboard_path


def parse_order(selection: str) -> int:
    match = re.search(r"第\s*(\d{1,3})\s*(篇|个|项|篇论文)?", selection)
    if match:
        return int(match.group(1))
    for chinese, value in sorted(CHINESE_ORDER_NUMBERS.items(), key=lambda item: len(item[0]), reverse=True):
        if f"第{chinese}" in selection or chinese == selection.strip():
            return value
    raise ValueError(f"无法解析序号：{selection}")


def parse_date(selection: str, current_year: int | None = None) -> str:
    year = current_year or datetime.now().year
    iso = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", selection)
    if iso:
        return f"{int(iso.group(1)):04d}-{int(iso.group(2)):02d}-{int(iso.group(3)):02d}"
    md = re.search(r"(?<!\d)(\d{1,2})\s*[./月]\s*(\d{1,2})\s*(号|日)?", selection)
    if md:
        return f"{year:04d}-{int(md.group(1)):02d}-{int(md.group(2)):02d}"
    raise ValueError(f"无法解析日期：{selection}")


def pick_by_request(selection: str, library_path: Path = DEFAULT_LIBRARY_JSON) -> dict[str, Any]:
    date_key = parse_date(selection)
    order = parse_order(selection)
    library = load_library(library_path)
    papers = [paper for paper in flattened_papers(library) if paper.get("captured_date") == date_key]
    papers.sort(key=lambda item: int(item.get("date_rank") or 0))
    for paper in papers:
        if int(paper.get("date_rank") or 0) == order:
            return paper
    raise ValueError(f"{date_key} 没有第 {order} 篇抓取记录。")
