from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.synthesis import build_paper_analysis, load_figures
from lib.utils import ensure_dir, read_json, slugify, write_json, write_text


def render_markdown(analysis: dict) -> str:
    lines = [f"# {analysis.get('title') or analysis.get('paper_id')}", "", f"Status: {analysis.get('analysis_status')}", ""]
    for key in ["research_problem", "core_claim", "method", "evidence", "limitations"]:
        section = analysis["sections"][key]
        lines.append(f"## {section.get('label_zh') or section['label']} / {section.get('label_en') or key}")
        page = f"（page {section['page']}）" if section.get("page") else ""
        lines.append(f"详细解读：{section.get('deep_summary_zh') or section.get('summary_zh') or section.get('summary')}{page}")
        if section.get("deep_points_zh"):
            lines.append("")
            lines.append("精读要点：")
            for point in section.get("deep_points_zh", []):
                lines.append(f"- {point}")
        lines.append(f"English Summary: {section.get('summary_en') or section.get('summary')}{page}")
        if section.get("evidence"):
            lines.append("")
            lines.append("证据摘录 / Source evidence:")
            for item in section["evidence"]:
                lines.append(f"- page {item.get('page')}: {item.get('quote')}")
        lines.append("")
    lines.append(f"## {analysis['relevance'].get('label_zh') or analysis['relevance']['label']} / {analysis['relevance'].get('label_en') or 'Relation to the User Topic'}")
    lines.append(f"详细解读：{analysis['relevance'].get('summary_zh') or analysis['relevance'].get('summary')}")
    if analysis["relevance"].get("deep_points_zh"):
        lines.append("")
        lines.append("精读要点：")
        for point in analysis["relevance"].get("deep_points_zh", []):
            lines.append(f"- {point}")
    lines.append(f"English Summary: {analysis['relevance'].get('summary_en') or analysis['relevance'].get('summary')}")
    lines.append("")
    if analysis.get("figure_table_notes"):
        lines.append("## 图表证据")
        for item in analysis["figure_table_notes"]:
            lines.append(f"- {item.get('figure_id')} page {item.get('page')}: {item.get('caption')} | {item.get('screenshot')}")
        lines.append("")
    lines.append("## 审计提示 / Audit Notes")
    for note in analysis.get("audit_notes", []):
        lines.append(f"- {note}")
    for note in analysis.get("audit_notes_en", []):
        lines.append(f"- {note}")
    return "\n".join(lines)


def analyze(reading_manifest_path: Path, manifest_paths: list[Path], output_dir: Path, topic: str = "") -> tuple[Path, Path]:
    reading = read_json(reading_manifest_path, {})
    if not reading:
        raise SystemExit(f"Reading manifest is empty or unreadable: {reading_manifest_path}")
    analysis = build_paper_analysis(reading, topic=topic, figure_records=load_figures(manifest_paths))
    paper_id = analysis.get("paper_id") or slugify(analysis.get("title") or reading_manifest_path.stem)
    ensure_dir(output_dir)
    json_path = output_dir / f"{paper_id}.analysis.json"
    md_path = output_dir / f"{paper_id}.analysis.md"
    write_json(json_path, analysis)
    write_text(md_path, render_markdown(analysis))
    print(f"Analysis JSON saved: {json_path}")
    print(f"Analysis Markdown saved: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a structured deep-reading analysis draft from a reading manifest.")
    parser.add_argument("reading", help="*.reading_manifest.json file")
    parser.add_argument("--manifest", action="append", default=[], help="Figure manifest JSON. Can be repeated.")
    parser.add_argument("--topic", default="", help="User research topic for relevance analysis")
    parser.add_argument("--output", default="outputs/analyses", help="Output directory")
    args = parser.parse_args()
    analyze(Path(args.reading), [Path(path) for path in args.manifest], Path(args.output), args.topic)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
