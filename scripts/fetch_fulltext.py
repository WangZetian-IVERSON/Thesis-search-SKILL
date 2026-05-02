from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.utils import ensure_dir, read_json, slugify, write_json


def looks_like_pdf_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.path.lower().endswith(".pdf") or "arxiv.org/pdf" in url.lower()


def download_pdf(url: str, output_path: Path) -> bool:
    if not looks_like_pdf_url(url):
        return False
    response = requests.get(url, timeout=60, headers={"User-Agent": "thesis-reading-skill/0.1"})
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    if "pdf" not in content_type and not response.content.startswith(b"%PDF"):
        return False
    ensure_dir(output_path.parent)
    output_path.write_bytes(response.content)
    return True


def fetch(metadata_path: Path, output_dir: Path, manifest_output: Path) -> Path:
    data = read_json(metadata_path, {})
    papers = data.get("papers", []) if isinstance(data, dict) else []
    results = []
    for paper in papers:
        url = paper.get("url") or ""
        title = paper.get("title") or paper.get("paper_id") or "paper"
        target = output_dir / f"{slugify(title, 72)}.pdf"
        status = "skipped"
        if url:
            try:
                if download_pdf(url, target):
                    paper["pdf_path"] = str(target)
                    paper["fulltext_status"] = "downloaded-open-access"
                    status = "downloaded"
                else:
                    status = "not-a-direct-pdf"
            except Exception as exc:
                status = f"failed: {exc}"
        results.append({"paper_id": paper.get("paper_id"), "title": title, "url": url, "status": status, "pdf_path": paper.get("pdf_path")})
    data["papers"] = papers
    manifest_path = manifest_output
    write_json(manifest_path, {"source_metadata": str(metadata_path), "results": results})
    write_json(metadata_path, data)
    print(f"Fulltext fetch manifest saved: {manifest_path}")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download legal direct open-access PDFs from metadata URLs.")
    parser.add_argument("metadata", help="find-*.json metadata file")
    parser.add_argument("--output", default="papers", help="PDF output directory")
    parser.add_argument("--manifest-output", default="outputs/evidence/fulltext_fetch_manifest.json", help="Download manifest output path")
    args = parser.parse_args()
    fetch(Path(args.metadata), Path(args.output), Path(args.manifest_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
