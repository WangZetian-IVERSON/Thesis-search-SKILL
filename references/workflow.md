# Workflow

## 1. Clarify

Collect the user's topic, discipline, time range, paper count, reading questions, language, and output format.

## 2. Search

Run public metadata search. Keep source information and never present metadata-only papers as full-text reading.

```bash
python scripts/search.py "<query>" --top 10
```

## 3. Select

Rank by relevance, citation signal, recency, venue, and full-text availability. If the list is noisy, ask the user to choose papers before deep reading.

## 4. Acquire Full Text

Use direct open-access PDFs only, or ask the user to upload local PDFs.

```bash
python scripts/fetch_fulltext.py <metadata.json>
```

## 5. Parse

Parse every local PDF into page-level JSON.

```bash
python scripts/parse_pdf.py papers/example.pdf
```

## 6. Capture Figures and Tables

Capture figure/table pages and create manifest records.

```bash
python scripts/capture_figures.py papers/example.pdf
```

## 7. Read

For each paper, write a structured reading: problem, claim, method, evidence, figures/tables, limitations, and relation to the user's task.

## 8. Synthesize

Compare papers across themes, methods, evidence strength, disagreements, and research gaps.

## 9. Build and Export

Generate HTML first, then export PDF when needed.

## 10. Audit

Run deterministic checks and report unresolved risks before presenting the final output.
