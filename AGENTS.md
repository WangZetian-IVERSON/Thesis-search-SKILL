# Agent Instructions

This repository provides a portable academic paper reading workflow for coding agents such as Codex-style agents, OpenAI agents, and other terminal-capable assistants.

## What This Agent Should Do

Use this project when the user asks for literature search, paper screening, PDF deep reading, figure/table evidence extraction, Chinese-first literature review reports, or final consistency audits.

The canonical workflow is in [SKILL.md](SKILL.md). Do not duplicate or reinterpret the workflow if [SKILL.md](SKILL.md) has more specific instructions.

## Non-Negotiable Rules

- Do not fabricate scholarly sources or evidence.
- Do not bypass paywalls, login systems, CAPTCHA, institutional access, or anti-automation controls.
- Treat abstract screening as metadata-only until a PDF is legally downloaded or uploaded by the user.
- Keep report claims traceable to metadata, PDF text, page screenshots, or figure/table manifests.
- Run tests or audit commands when changing code or producing final reports.
- Prefer Chinese for user-facing summaries, dashboard cards, report headings, and reading notes.

## Useful Commands

```bash
python scripts/search.py "<topic>" --top 20
python scripts/screen_papers.py outputs/evidence/find-xxx.json --topic "<topic>" --top 20
python scripts/deep_read_request.py "给我5.2号抓取的第一个论文的精读" --topic "<topic>"
python scripts/deep_read_selected.py outputs/screening/screen-topic.json "帮我精读第3篇" --topic "<topic>"
python scripts/fetch_fulltext.py outputs/evidence/find-xxx.json
python scripts/read_paper.py papers/example.pdf --questions "方法是什么; 数据集是什么; 局限是什么"
python scripts/capture_figures.py papers/example.pdf
python scripts/build_report.py --metadata outputs/evidence/find-xxx.json --parsed outputs/evidence/example.parsed.json --reading outputs/readings/example.reading_manifest.json --analysis outputs/analyses/example.analysis.json --manifest outputs/evidence/example.figures_manifest.json
python scripts/audit_report.py --metadata outputs/evidence/find-xxx.json --reading outputs/readings/example.reading_manifest.json --analysis outputs/analyses/example.analysis.json --manifest outputs/evidence/example.figures_manifest.json --report outputs/reports/example.report.html
```

## Data Hygiene

Generated data lives in `outputs/`, `papers/`, and root `evidence/`. Source code, templates, tests, and reference documents should not be removed when cleaning generated data.
