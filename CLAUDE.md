# Claude Code Instructions

This repository is a command-driven academic paper reading skill. Use it when the user asks to search papers, screen abstracts, deep read PDFs, extract figure/table evidence, build Chinese-first HTML/PDF reports, or audit paper-report consistency.

## Primary Workflow

Read [SKILL.md](SKILL.md) first and follow its procedure. The executable entry points are Python scripts under [scripts](scripts), templates are under [templates](templates), and policy/reference notes are under [references](references).

## Operating Rules

- Never invent papers, DOI values, authors, page numbers, figures, tables, quotations, or search results.
- Never bypass paywalls, CAPTCHA, login, institutional access controls, or anti-automation rules.
- Keep metadata-only screening separate from full-text reading.
- Download PDFs only when an open legal PDF URL is available, or ask the user to upload the PDF.
- Every figure/table screenshot must keep provenance metadata in a manifest.
- Run the audit step before presenting a report as complete.
- User-facing summaries and report structure should be Chinese-first; source evidence can remain folded in the original language.

## Common Commands

```bash
python scripts/search.py "LLM agents literature review" --top 20
python scripts/screen_papers.py outputs/evidence/find-xxx.json --top 20
python scripts/deep_read_request.py "给我5.2号抓取的第一个论文的精读" --topic "LLM agents literature review"
python scripts/deep_read_selected.py outputs/screening/screen-topic.json "帮我精读第3篇" --topic "LLM agents literature review"
python scripts/build_library.py
python scripts/audit_report.py --metadata outputs/evidence/find-xxx.json --reading outputs/readings/example.reading_manifest.json --analysis outputs/analyses/example.analysis.json --manifest outputs/evidence/example.figures_manifest.json --report outputs/reports/example.report.html
```

## Outputs

- Use `outputs/library/index.html` as the main user-facing dashboard.
- Store downloaded or uploaded PDFs in `papers/`.
- Store generated evidence, readings, analyses, reports, screenshots, and checks under `outputs/`.
