from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.screening import render_html, render_markdown, screen_papers
from lib.library import DEFAULT_LIBRARY_HTML, upsert_screening
from lib.utils import ensure_dir, read_json, slugify, write_json, write_text


def screen(metadata_path: Path, output_dir: Path, topic: str = "", limit: int | None = None, standalone_html: bool = False) -> tuple[Path, Path, Path | None]:
    metadata = read_json(metadata_path, {})
    if not metadata:
        raise SystemExit(f"Metadata file is empty or unreadable: {metadata_path}")
    screening = screen_papers(metadata, topic=topic, limit=limit)
    screening["captured_at"] = datetime.now().replace(microsecond=0).isoformat()
    screening["captured_date"] = screening["captured_at"][:10]
    slug = slugify(screening.get("topic") or metadata_path.stem, 64)
    ensure_dir(output_dir)
    json_path = output_dir / f"screen-{slug}.json"
    md_path = output_dir / f"screen-{slug}.md"
    html_path = output_dir / f"screen-{slug}.html" if standalone_html else None
    write_json(json_path, screening)
    write_text(md_path, render_markdown(screening))
    if html_path:
        write_text(html_path, render_html(screening))
    upsert_screening(json_path)
    print(f"Screening JSON saved: {json_path}")
    print(f"Screening Markdown saved: {md_path}")
    if html_path:
        print(f"Screening HTML saved: {html_path}")
    print(f"Library dashboard updated: {DEFAULT_LIBRARY_HTML.relative_to(Path.cwd()) if DEFAULT_LIBRARY_HTML.is_relative_to(Path.cwd()) else DEFAULT_LIBRARY_HTML}")
    return json_path, md_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a ranked screening list from search metadata without downloading PDFs.")
    parser.add_argument("metadata", help="find-*.json from scripts/search.py")
    parser.add_argument("--topic", default="", help="Topic used for screening reasons. Defaults to search query.")
    parser.add_argument("--top", type=int, default=None, help="Limit number of papers in the screening list")
    parser.add_argument("--output", default="outputs/screening", help="Output directory")
    parser.add_argument("--standalone-html", action="store_true", help="Also write a standalone screening HTML. The unified library dashboard is always updated.")
    args = parser.parse_args()
    screen(Path(args.metadata), Path(args.output), args.topic, args.top, args.standalone_html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
