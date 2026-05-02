from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def find_browser() -> str | None:
    candidates = [
        shutil.which("msedge"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def export_pdf(html_path: Path, output_path: Path) -> Path:
    browser = find_browser()
    if not browser:
        raise SystemExit("No Edge/Chrome executable found. Open the HTML report directly or install a Chromium browser.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        browser,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={output_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    subprocess.run(command, check=True)
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise SystemExit("PDF export failed: output file is empty or missing.")
    print(f"PDF saved: {output_path}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export an HTML report to PDF using local Edge/Chrome headless mode.")
    parser.add_argument("html", help="HTML report path")
    parser.add_argument("--output", default="outputs/report.pdf", help="PDF output path")
    args = parser.parse_args()
    export_pdf(Path(args.html), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
