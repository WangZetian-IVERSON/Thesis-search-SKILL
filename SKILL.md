---
name: thesis-reading-skill
description: "Use when: searching academic papers, screening abstracts, deeply reading PDFs, extracting figure/table evidence, generating Chinese-first literature review reports, or auditing paper evidence."
argument-hint: "research topic, uploaded PDFs, reading questions, output format, paper count"
---

# Thesis Reading Skill

> **Design principle**: Users speak in **short, natural language**. The skill must figure out everything else — which screening file, which papers, where to put output. NEVER ask the user for paths, slugs, or filenames.

Project root: `f:\thesis-reading-skill`
Run scripts with: `python scripts/xxx.py` (venv already active)

---

## Intent → Action Routing

Detect the user's intent from natural language, then run the **complete** corresponding pipeline. Do NOT stop halfway.

### Intent A — "搜一下 / 找几篇 / 帮我看看 XXX 方向的论文"

Run search + screen + build_library. Do NOT deep-read yet.

```bash
python scripts/search.py "TOPIC" --top 20
python scripts/screen_papers.py outputs/evidence/find-<slug>.json --topic "TOPIC" --top 10
python scripts/build_library.py --screening outputs/screening/screen-<slug>.json
```

Reply: `outputs/library/index.html` 路径 + "已加入论文库初筛，N 篇待精读。如需精读请直接说『精读第 1、3 篇』"

### Intent B — "精读 / 深度阅读 / 详细看一下 第 N 篇 / 前 K 篇"

> **Critical: never stop after `screen_papers.py` when the user asked for 精读.** That leaves `deep_read: {}` and the user sees only abstract-level cards — this is the #1 historical failure mode.

**Step 1 — Auto-locate the latest screening file** (never ask the user):

```bash
LATEST=$(ls -t outputs/screening/screen-*.json | head -1)
```

If user said "刚才那批 / 上次搜的 XXX 方向"，match by topic substring in filename instead.

**Step 2 — Parse rank list from natural language**:

- "第 1、2、3 篇" → ranks `1 2 3`
- "前 3 篇 / top 3" → ranks `1 2 3`
- 仅说"精读"不带数字 → 默认 `1 2 3`
- "第 2 篇" → rank `2`

**Step 3 — Deep read each rank** (script auto-downloads the PDF):

```bash
for R in <RANKS>; do
  python scripts/deep_read_selected.py "$LATEST" "帮我精读第${R}篇" --topic "TOPIC"
done
```

Some papers are paywalled and will fail — that is expected; continue with the next rank.

**Step 4 — Rebuild dashboard**:

```bash
python scripts/build_library.py --screening "$LATEST"
```

**Step 5 — Verify before replying**: open `outputs/library/library.json` and confirm at least one targeted rank has a non-empty `deep_read` object. If all are `{}`, the pipeline is broken — debug rather than give the user a placeholder link.

**Step 6 — Reply** with the file path and a one-line Chinese summary, e.g.:
> 已完成精读：第 1、3 篇（第 2 篇 PDF 不可用，已跳过）
> 仪表盘：`outputs/library/index.html`
> 一句话：[从 research_problem.deep_summary_zh 取第一篇结论]

### Intent C — "继续 / 再加几篇 / 追加 XXX 方向"

Same as Intent A but with a new topic. `build_library.py --screening` appends a new session to the existing dashboard. Do NOT recreate or wipe the library.

### Intent D — "重新生成 HTML / 刷新仪表盘"

Just run Step 4 of Intent B. No re-search, no re-read.

---

## Hard Rules

1. **Never ask the user for file paths, slugs, or shell args.** Auto-locate via `ls -t outputs/screening/*.json` or topic match.
2. **Never stop after `screen_papers.py` when the user asked for 精读.** Complete the full Intent B pipeline.
3. **Always run `build_library.py --screening <file>`** after deep reading so the new session is upserted into the existing library.
4. **Never invent papers, DOIs, authors, page numbers, figures, tables, or quotations.**
5. **Never bypass paywalls, CAPTCHA, login, or institutional access controls.**
6. **Audit silently** before replying; mention failed papers but still link to the successful ones.
7. **Clearly distinguish full-text reading from metadata-only analysis.** If full text is unavailable, label it metadata-only or ask the user to upload the PDF.

---

## Non-Negotiable Evidence Rules

- Every figure/table screenshot must have provenance metadata: paper id, page, caption, screenshot path, extraction method, confidence.
- Run a final audit before presenting any HTML/PDF as complete.

---

## Reading Modes

### Logic Mode
Use when the user gives a topic or paper without specific questions. Summarize each paper through research problem, core claim, method, evidence, limitations, and relation to the user's topic.

### Question Mode
Use when the user provides reading questions. Organize notes around up to six questions and bind each answer to original text, page numbers, or figure/table evidence.

### Figure Evidence Mode
Use when the user asks for diagrams, tables, experimental results, model architecture, or data evidence. Extract or screenshot figures/tables and record every item in a manifest.

---

## Output Standards

- HTML is the primary output format.
- PDF is exported from HTML only after the HTML report is generated.
- Use `outputs/library/index.html` as the main persistent entry point.
- User-facing interpretation must be Chinese-first. Source quotations and figure captions can stay in the source language as folded evidence.
- If an item is metadata-only, it must not appear as a fully-read paper.

---

## Tool Files

- Search: [scripts/search.py](../../../scripts/search.py)
- Screen papers: [scripts/screen_papers.py](../../../scripts/screen_papers.py)
- Deep read selected paper: [scripts/deep_read_selected.py](../../../scripts/deep_read_selected.py)
- Deep read by dashboard request: [scripts/deep_read_request.py](../../../scripts/deep_read_request.py)
- Library dashboard: [scripts/build_library.py](../../../scripts/build_library.py)
- Fetch full text: [scripts/fetch_fulltext.py](../../../scripts/fetch_fulltext.py)
- Parse PDF: [scripts/parse_pdf.py](../../../scripts/parse_pdf.py)
- Read PDF: [scripts/read_paper.py](../../../scripts/read_paper.py)
- Analyze reading: [scripts/analyze_paper.py](../../../scripts/analyze_paper.py)
- Capture figures/tables: [scripts/capture_figures.py](../../../scripts/capture_figures.py)
- Build report: [scripts/build_report.py](../../../scripts/build_report.py)
- Export PDF: [scripts/export_pdf.py](../../../scripts/export_pdf.py)
- Audit report: [scripts/audit_report.py](../../../scripts/audit_report.py)
