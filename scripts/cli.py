from __future__ import annotations

import argparse
import importlib
import sys


COMMANDS = {
    "search": "scripts.search",
    "screen": "scripts.screen_papers",
    "library": "scripts.build_library",
    "fetch": "scripts.fetch_fulltext",
    "parse": "scripts.parse_pdf",
    "read": "scripts.read_paper",
    "analyze": "scripts.analyze_paper",
    "capture": "scripts.capture_figures",
    "report": "scripts.build_report",
    "export-pdf": "scripts.export_pdf",
    "audit": "scripts.audit_report",
    "deep-read": "scripts.deep_read_selected",
    "deep-request": "scripts.deep_read_request",
    "cite": "scripts.cite",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="thesis-reading",
        description="Run the thesis-reading-skill paper search, reading, reporting, and audit commands.",
    )
    parser.add_argument("command", nargs="?", choices=sorted(COMMANDS), help="Command to run")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the selected command")
    return parser


def main() -> int:
    parser = build_parser()
    parsed = parser.parse_args()
    if not parsed.command:
        parser.print_help()
        return 0

    module = importlib.import_module(COMMANDS[parsed.command])
    original_argv = sys.argv[:]
    try:
        sys.argv = [f"thesis-reading {parsed.command}", *parsed.args]
        return int(module.main())
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
