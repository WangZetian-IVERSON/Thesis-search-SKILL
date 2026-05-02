from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lib.utils import ensure_dir, read_json, write_text


def load_papers(metadata_path: Path | None) -> list[dict]:
    if not metadata_path:
        return []
    data = read_json(metadata_path, {})
    if isinstance(data, dict):
        return data.get("papers", [])
    return []


def load_parsed(paths: list[Path]) -> list[dict]:
    parsed = []
    for path in paths:
        data = read_json(path, {})
        if not data:
            continue
        excerpt_parts = []
        for page in data.get("pages", [])[:3]:
            text = " ".join((page.get("text") or "").split())
            if text:
                excerpt_parts.append(f"Page {page.get('page')}: {text[:900]}")
        data["excerpt"] = "\n\n".join(excerpt_parts) or "No extractable text found."
        parsed.append(data)
    return parsed


def make_report_relative(path: str, report_dir: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return Path(os.path.relpath(resolved, report_dir.resolve())).as_posix()
    except ValueError:
        return resolved.as_uri()


def load_figures(paths: list[Path], report_dir: Path) -> list[dict]:
    figures = []
    for path in paths:
        data = read_json(path, {})
        records = data.get("records", []) if isinstance(data, dict) else []
        for record in records:
            screenshot = record.get("screenshot")
            if screenshot:
                record["screenshot"] = make_report_relative(screenshot, report_dir)
            figures.append(record)
    return figures


def load_readings(paths: list[Path], report_dir: Path) -> list[dict]:
    readings = []
    for path in paths:
        data = read_json(path, {})
        if not data:
            continue
        output_html = data.get("output_html")
        if output_html:
            data["output_html"] = make_report_relative(output_html, report_dir)
        readings.append(data)
    return readings


def load_analyses(paths: list[Path]) -> list[dict]:
    analyses = []
    for path in paths:
        data = read_json(path, {})
        if data:
            analyses.append(data)
    return analyses


def build_report(title: str, metadata: Path | None, parsed: list[Path], manifests: list[Path], readings: list[Path], analyses: list[Path], output: Path) -> Path:
    report_dir = output.parent
    env = Environment(
        loader=FileSystemLoader(ROOT_DIR / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")
    html = template.render(
        title=title,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        papers=load_papers(metadata),
        parsed_papers=load_parsed(parsed),
        figures=load_figures(manifests, report_dir),
        readings=load_readings(readings, report_dir),
        analyses=load_analyses(analyses),
    )
    ensure_dir(output.parent)
    write_text(output, html)
    print(f"Report saved: {output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an HTML reading report from search, PDF parse, and figure manifest artifacts.")
    parser.add_argument("--title", default="论文精读报告")
    parser.add_argument("--metadata", default=None, help="find-*.json metadata file")
    parser.add_argument("--parsed", action="append", default=[], help="*.parsed.json file. Can be repeated.")
    parser.add_argument("--manifest", action="append", default=[], help="*.figures_manifest.json file. Can be repeated.")
    parser.add_argument("--reading", action="append", default=[], help="*.reading_manifest.json file. Can be repeated.")
    parser.add_argument("--analysis", action="append", default=[], help="*.analysis.json file. Can be repeated.")
    parser.add_argument("--output", default="outputs/report.html")
    args = parser.parse_args()
    build_report(
        args.title,
        Path(args.metadata) if args.metadata else None,
        [Path(path) for path in args.parsed],
        [Path(path) for path in args.manifest],
        [Path(path) for path in args.reading],
        [Path(path) for path in args.analysis],
        Path(args.output),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
