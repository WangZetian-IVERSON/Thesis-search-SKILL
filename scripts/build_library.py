from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.library import DEFAULT_LIBRARY_HTML, DEFAULT_LIBRARY_JSON, render_dashboard, upsert_screening


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or refresh the unified paper library dashboard.")
    parser.add_argument("--screening", action="append", default=[], help="screen-*.json to import. Can be repeated.")
    parser.add_argument("--library", default=str(DEFAULT_LIBRARY_JSON), help="Library JSON path")
    parser.add_argument("--output", default=str(DEFAULT_LIBRARY_HTML), help="Dashboard HTML path")
    args = parser.parse_args()
    library_path = Path(args.library)
    output_path = Path(args.output)
    for screening in args.screening:
        upsert_screening(Path(screening), library_path, output_path)
    dashboard = render_dashboard(library_path, output_path)
    print(f"Library dashboard saved: {dashboard}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
