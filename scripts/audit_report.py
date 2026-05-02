from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.schema import AuditFinding
from lib.dedupe import title_similarity
from lib.utils import ensure_dir, read_json, write_text
from sources.source_crossref import verify_doi


def finding(severity: str, code: str, message: str, target: str | None = None, suggestion: str | None = None) -> AuditFinding:
    return AuditFinding(severity=severity, code=code, message=message, target=target, suggestion=suggestion)


def audit(
    metadata_path: Path | None,
    manifest_paths: list[Path],
    reading_paths: list[Path],
    analysis_paths: list[Path],
    report_path: Path | None,
    output_path: Path,
    verify_online: bool = False,
) -> list[AuditFinding]:
    findings: list[AuditFinding] = []

    if metadata_path:
        data = read_json(metadata_path, {})
        papers = data.get("papers", []) if isinstance(data, dict) else []
        if not papers:
            findings.append(finding("error", "META-EMPTY", "No papers found in metadata file.", str(metadata_path)))
        for index, paper in enumerate(papers, start=1):
            target = paper.get("paper_id") or f"paper-{index}"
            if not paper.get("title"):
                findings.append(finding("error", "META-TITLE", "Paper is missing a title.", target))
            if not paper.get("doi") and not paper.get("url"):
                findings.append(finding("warning", "META-SOURCE", "Paper has no DOI or source URL.", target, "Verify manually before claiming it as real."))
            if paper.get("fulltext_status") == "metadata-only":
                findings.append(finding("info", "FULLTEXT-MISSING", "Only metadata is available; do not label this as full-text reading.", target))
            if verify_online and paper.get("doi"):
                try:
                    crossref = verify_doi(paper["doi"])
                    title_values = crossref.get("title") or [] if crossref else []
                    crossref_title = title_values[0] if title_values else ""
                    if crossref_title and title_similarity(crossref_title, paper.get("title") or "") < 0.82:
                        findings.append(
                            finding(
                                "error",
                                "DOI-TITLE-MISMATCH",
                                "DOI resolves, but CrossRef title differs from metadata title.",
                                target,
                                f"CrossRef title: {crossref_title}",
                            )
                        )
                except Exception as exc:
                    findings.append(finding("warning", "DOI-VERIFY-FAILED", f"DOI online verification failed: {exc}", target))

    for reading_path in reading_paths:
        reading = read_json(reading_path, {})
        if not reading:
            findings.append(finding("error", "READING-EMPTY", "Reading manifest is empty or unreadable.", str(reading_path)))
            continue
        html_path = reading.get("output_html")
        if not html_path or not Path(html_path).exists():
            findings.append(finding("error", "READING-HTML-MISSING", "Reading HTML file does not exist.", reading.get("paper_id"), html_path))
        if not reading.get("annotation_count"):
            findings.append(finding("warning", "READING-NO-ANNOTATIONS", "Reading manifest has no paragraph annotations.", reading.get("paper_id")))
        if reading.get("mode") == "question" and not reading.get("questions"):
            findings.append(finding("warning", "READING-QUESTIONS-MISSING", "Question mode has no stored questions.", reading.get("paper_id")))

    for analysis_path in analysis_paths:
        analysis = read_json(analysis_path, {})
        if not analysis:
            findings.append(finding("error", "ANALYSIS-EMPTY", "Analysis file is empty or unreadable.", str(analysis_path)))
            continue
        sections = analysis.get("sections") or {}
        for key in ["research_problem", "core_claim", "method", "evidence", "limitations"]:
            section = sections.get(key)
            if not section:
                findings.append(finding("error", "ANALYSIS-SECTION-MISSING", f"Missing analysis section: {key}", analysis.get("paper_id")))
                continue
            if not section.get("summary"):
                findings.append(finding("error", "ANALYSIS-SUMMARY-MISSING", f"Section has no summary: {key}", analysis.get("paper_id")))
            if section.get("status") == "needs-review":
                findings.append(finding("warning", "ANALYSIS-NEEDS-REVIEW", f"Section still needs review: {key}", analysis.get("paper_id")))
        if analysis.get("analysis_status") == "heuristic-draft":
            findings.append(finding("info", "ANALYSIS-DRAFT", "Analysis is a heuristic draft; review before final submission.", analysis.get("paper_id")))

    for manifest_path in manifest_paths:
        manifest = read_json(manifest_path, {})
        records = manifest.get("records", []) if isinstance(manifest, dict) else []
        if not records:
            findings.append(finding("warning", "FIG-EMPTY", "No figure/table records were found in manifest.", str(manifest_path)))
        for record in records:
            screenshot = record.get("screenshot")
            if not screenshot or not Path(screenshot).exists():
                findings.append(finding("error", "FIG-MISSING-FILE", "Screenshot file does not exist.", record.get("figure_id"), screenshot))
            if not record.get("page"):
                findings.append(finding("error", "FIG-PAGE", "Figure/table record has no page number.", record.get("figure_id")))
            if not record.get("caption"):
                findings.append(finding("warning", "FIG-CAPTION", "Figure/table record has no caption.", record.get("figure_id")))

    if report_path:
        if not report_path.exists():
            findings.append(finding("error", "REPORT-MISSING", "Report file does not exist.", str(report_path)))
        elif report_path.stat().st_size < 1000:
            findings.append(finding("warning", "REPORT-SMALL", "Report file is unusually small.", str(report_path)))

    error_count = sum(1 for item in findings if item.severity == "error")
    warning_count = sum(1 for item in findings if item.severity == "warning")
    status = "pass" if error_count == 0 else "fail"
    lines = ["# Final Audit", "", f"Status: {status}", f"Errors: {error_count}", f"Warnings: {warning_count}", ""]
    if not findings:
        lines.append("No blocking issues found by deterministic checks.")
    else:
        for item in findings:
            lines.append(f"## [{item.severity.upper()}] {item.code}")
            lines.append(item.message)
            if item.target:
                lines.append(f"Target: {item.target}")
            if item.suggestion:
                lines.append(f"Suggestion: {item.suggestion}")
            lines.append("")
    ensure_dir(output_path.parent)
    write_text(output_path, "\n".join(lines))
    print(f"Audit saved: {output_path}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic checks against paper metadata, figure manifests, and reports.")
    parser.add_argument("--metadata", default=None, help="find-*.json metadata file")
    parser.add_argument("--manifest", action="append", default=[], help="Figure manifest JSON. Can be repeated.")
    parser.add_argument("--reading", action="append", default=[], help="Reading manifest JSON. Can be repeated.")
    parser.add_argument("--analysis", action="append", default=[], help="Analysis JSON. Can be repeated.")
    parser.add_argument("--report", default=None, help="Generated HTML/PDF report path")
    parser.add_argument("--output", default="outputs/checks/final_audit.md", help="Audit markdown output")
    parser.add_argument("--verify-doi", action="store_true", help="Verify DOI/title pairs through CrossRef. Uses network.")
    args = parser.parse_args()
    findings = audit(
        Path(args.metadata) if args.metadata else None,
        [Path(path) for path in args.manifest],
        [Path(path) for path in args.reading],
        [Path(path) for path in args.analysis],
        Path(args.report) if args.report else None,
        Path(args.output),
        args.verify_doi,
    )
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
