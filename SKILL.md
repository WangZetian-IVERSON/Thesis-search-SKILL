---
name: thesis-reading-skill
description: "Use when: searching academic papers, verifying real papers, deeply reading PDFs, extracting figures and tables, creating literature review reports, auditing academic report accuracy, generating HTML/PDF paper reading outputs."
argument-hint: "research topic, uploaded PDFs, reading questions, output format, paper count"
---

# Thesis Reading Skill

## When to Use

Use this skill when the user asks to find papers, deeply read academic papers, summarize PDFs, extract figures or tables, build a literature review report, generate citations, or verify whether papers and report evidence are real.

## Non-Negotiable Rules

1. Never invent papers, DOI values, authors, page numbers, figures, tables, quotations, or database results.
2. Do not bypass paywalls, CAPTCHA, login systems, institutional access controls, or database anti-automation rules.
3. Clearly distinguish full-text reading from metadata-only analysis.
4. Every figure/table screenshot must have provenance metadata: paper id, page, caption if available, screenshot path, extraction method, and confidence.
5. Run a final audit before presenting generated HTML/PDF as complete.
6. If full text is unavailable, ask the user to upload the PDF or label the item as metadata-only.

## Procedure

1. Clarify the task: topic, discipline, time range, paper count, output language, output format, and user reading questions.
2. Search public metadata sources with `python scripts/search.py "<query>" --top 20`.
3. Create a ranked screening list without downloading PDFs: `python scripts/screen_papers.py <metadata.json> --top 20`.
4. Sync every screening result into the unified dashboard at `outputs/library/index.html`. Prefer this dashboard over creating many standalone screening HTML files. The dashboard should support date, keyword, status, and favorite filtering.
5. Present the dashboard path to the user. Each card should show a Chinese concise guide, Chinese screening reason/action, source metadata, and a natural-language prompt such as "给我4.29号抓取的第一个论文的精读". Do not claim full-text reading at this stage.
6. If the user asks to deep read a paper by date/order, run `python scripts/deep_read_request.py "给我4.29号抓取的第一个论文的精读" --topic "<topic>"`. If the user gives a screening-rank prompt, run `python scripts/deep_read_selected.py <screening.json> "帮我精读第N篇" --topic "<topic>"`.
7. For manual workflows, download only legal direct open-access PDFs with `python scripts/fetch_fulltext.py <metadata.json>`.
8. Parse local PDFs with `python scripts/parse_pdf.py <paper.pdf>`.
9. Create a Chinese-first block reading page with `python scripts/read_paper.py <paper.pdf>` or `python scripts/read_paper.py <parsed.json>`. The source text can be kept as folded evidence, but the visible interpretation should be Chinese.
10. Build a structured analysis draft with `python scripts/analyze_paper.py <reading_manifest.json> --topic "<topic>"`.
11. Capture figure/table evidence with `python scripts/capture_figures.py <paper.pdf>`.
12. Build the HTML report with `python scripts/build_report.py` using metadata, parsed JSON, reading manifests, analysis JSON, and figure manifests.
13. Export PDF when needed with `python scripts/export_pdf.py outputs/report.html`.
14. Run final audit with `python scripts/audit_report.py` and fix blocking errors.
15. Present the dashboard path, selected report path, audit result, unresolved limitations, and any manual verification needed.

## Reading Modes

### Logic Mode

Use when the user gives a topic or paper without specific questions. Summarize each paper through research problem, core claim, method, evidence, limitations, and relation to the user's topic.

### Question Mode

Use when the user provides reading questions. Organize notes around up to six questions and bind each answer to original text, page numbers, or figure/table evidence.

### Figure Evidence Mode

Use when the user asks for diagrams, tables, experimental results, model architecture, or data evidence. Extract or screenshot figures/tables and record every item in a manifest.

## Output Standards

- HTML is the primary output because it can contain source links, screenshots, tables, and audit notes.
- PDF is exported from HTML only after the HTML report is generated.
- The report must include a source overview, per-paper reading sections, figure/table evidence, cross-paper synthesis, citations, and audit appendix.
- User-facing interpretation should be Chinese-first. Source quotations and figure captions can stay in the source language as folded evidence, but the visible summaries, reading notes, recommendations, and report structure should be Chinese.
- Use `outputs/library/index.html` as the main persistent entry point. Standalone HTML files are optional and should be generated only when useful for sharing or archival snapshots.
- If an item is metadata-only, it must not appear as a fully read paper.

## Tool Files

- Search: [scripts/search.py](./scripts/search.py)
- Screen papers: [scripts/screen_papers.py](./scripts/screen_papers.py)
- Deep read selected paper: [scripts/deep_read_selected.py](./scripts/deep_read_selected.py)
- Deep read by dashboard request: [scripts/deep_read_request.py](./scripts/deep_read_request.py)
- Library dashboard: [scripts/build_library.py](./scripts/build_library.py)
- Fetch full text: [scripts/fetch_fulltext.py](./scripts/fetch_fulltext.py)
- Parse PDF: [scripts/parse_pdf.py](./scripts/parse_pdf.py)
- Read PDF: [scripts/read_paper.py](./scripts/read_paper.py)
- Analyze reading: [scripts/analyze_paper.py](./scripts/analyze_paper.py)
- Capture figures/tables: [scripts/capture_figures.py](./scripts/capture_figures.py)
- Build report: [scripts/build_report.py](./scripts/build_report.py)
- Export PDF: [scripts/export_pdf.py](./scripts/export_pdf.py)
- Audit report: [scripts/audit_report.py](./scripts/audit_report.py)
- Workflow reference: [references/workflow.md](./references/workflow.md)
- Search strategy: [references/search-strategy.md](./references/search-strategy.md)
- Reading template: [references/paper-reading-template.md](./references/paper-reading-template.md)
- Analysis template: [references/analysis-template.md](./references/analysis-template.md)
- Figure/table policy: [references/figure-table-policy.md](./references/figure-table-policy.md)
- Audit rules: [references/audit-rules.md](./references/audit-rules.md)
