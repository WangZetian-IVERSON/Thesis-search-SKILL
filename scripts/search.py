from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.dedupe import dedupe_papers
from lib.score import score_papers
from lib.utils import ensure_dir, now_stamp, slugify, write_json, write_text
from sources import source_arxiv, source_crossref, source_openalex, source_semantic_scholar


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def write_csv(path: Path, rows: list[dict]) -> None:
    ensure_dir(path.parent)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_find_html(query: str, papers: list[dict]) -> str:
    cards = []
    for paper in papers:
        authors = ", ".join(paper.get("authors") or []) or "Unknown author"
        doi = paper.get("doi") or ""
        link = paper.get("url") or (f"https://doi.org/{doi}" if doi else "")
        link_html = f'<a href="{link}">source</a>' if link else "no source link"
        cards.append(
            f"""
            <article class=\"paper-card\">
              <h2>{paper.get('title')}</h2>
              <p class=\"meta\">{authors} · {paper.get('year') or 'n.d.'} · {paper.get('venue') or 'Unknown venue'}</p>
              <p><strong>Source:</strong> {paper.get('source')} · <strong>Score:</strong> {paper.get('score')} · <strong>Citations:</strong> {paper.get('cited_by_count') or 0}</p>
              <p><strong>DOI:</strong> {doi or 'None'} · {link_html}</p>
              <p>{paper.get('abstract') or 'No abstract available from this source.'}</p>
            </article>
            """
        )
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <title>Find Results - {query}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; background: #f7f7f4; color: #1f2933; }}
    header {{ background: #243b53; color: white; padding: 24px 32px; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .paper-card {{ background: white; border: 1px solid #d9e2ec; border-radius: 6px; padding: 18px; margin-bottom: 16px; }}
    h1, h2 {{ margin-top: 0; }}
    .meta {{ color: #52606d; }}
    a {{ color: #0b69a3; }}
  </style>
</head>
<body>
<header><h1>Paper Find Results</h1><p>{query}</p></header>
<main>{''.join(cards)}</main>
</body>
</html>"""


def search_sources(query: str, source: str, limit: int) -> list:
    load_env_file(Path.cwd() / ".env")
    openalex_email = os.getenv("OPENALEX_EMAIL") or None
    semantic_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY") or None

    source_plan = []
    if source in {"all", "openalex"}:
        source_plan.append(("OpenAlex", lambda: source_openalex.search(query, limit, openalex_email)))
    if source in {"all", "crossref"}:
        source_plan.append(("CrossRef", lambda: source_crossref.search(query, limit)))
    if source in {"all", "semantic-scholar"}:
        source_plan.append(("Semantic Scholar", lambda: source_semantic_scholar.search(query, limit, semantic_key)))
    if source in {"all", "arxiv"}:
        source_plan.append(("arXiv", lambda: source_arxiv.search(query, limit)))

    papers = []
    for source_name, runner in source_plan:
        try:
            found = runner()
            papers.extend(found)
            print(f"{source_name}: {len(found)} results")
        except Exception as exc:
            print(f"warning: {source_name} skipped: {exc}", file=sys.stderr)
    return papers


def main() -> int:
    parser = argparse.ArgumentParser(description="Search public academic metadata sources.")
    parser.add_argument("query", help="Research topic or paper query")
    parser.add_argument("--top", type=int, default=10, help="Number of ranked papers to keep")
    parser.add_argument("--source", choices=["all", "openalex", "crossref", "semantic-scholar", "arxiv"], default="all")
    parser.add_argument("--output", default="outputs/evidence", help="Output directory")
    args = parser.parse_args()

    output_dir = ensure_dir(args.output)
    raw_papers = search_sources(args.query, args.source, max(args.top * 2, 20))
    papers = score_papers(dedupe_papers(raw_papers))[: args.top]
    rows = [paper.to_dict() for paper in papers]

    stamp = now_stamp()
    slug = slugify(args.query, 48)
    json_path = output_dir / f"find-{stamp}-{slug}.json"
    csv_path = output_dir / f"find-{stamp}-{slug}.csv"
    html_path = output_dir / f"find-{stamp}-{slug}.html"
    write_json(json_path, {"query": args.query, "source": args.source, "papers": rows})
    write_csv(csv_path, rows)
    write_text(html_path, render_find_html(args.query, rows))

    print(f"Saved JSON: {json_path}")
    print(f"Saved CSV:  {csv_path}")
    print(f"Saved HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
