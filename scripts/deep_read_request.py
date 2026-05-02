from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from deep_read_selected import deep_read
from lib.library import DEFAULT_LIBRARY_JSON, pick_by_request


def run_request(selection: str, topic: str = "", questions: str | None = None, output_root: Path = Path("outputs")) -> dict:
    paper = pick_by_request(selection, DEFAULT_LIBRARY_JSON)
    screening_json = paper.get("screening_json")
    rank = int(paper.get("rank") or 0)
    if not screening_json or rank <= 0:
        raise SystemExit(f"无法从文献库记录定位 screening JSON 或序号：{selection}")
    return deep_read(Path(screening_json), rank, topic or "", questions, output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Use a natural-language date/order request to deep read a paper from the unified library.")
    parser.add_argument("selection", help="例如：给我4.29号抓取的第一个论文的精读")
    parser.add_argument("--topic", default="", help="User research topic")
    parser.add_argument("--questions", default=None, help="Reading questions")
    parser.add_argument("--output", default="outputs", help="Output root directory")
    args = parser.parse_args()
    run_request(args.selection, args.topic, args.questions, Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
