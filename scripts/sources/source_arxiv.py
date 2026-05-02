from __future__ import annotations

import xml.etree.ElementTree as ET
import time

import requests

from lib.schema import PaperMetadata
from lib.utils import stable_paper_id

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def search(query: str, limit: int = 20) -> list[PaperMetadata]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 50),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    response = None
    for delay in [0, 2, 5, 10]:
        if delay:
            time.sleep(delay)
        response = requests.get("https://export.arxiv.org/api/query", params=params, timeout=30)
        if response.status_code != 429:
            response.raise_for_status()
            break
    if response is None or response.status_code == 429:
        raise requests.HTTPError("arXiv rate limit did not clear after retries")
    root = ET.fromstring(response.text)
    papers: list[PaperMetadata] = []
    for entry in root.findall(f"{ATOM}entry"):
        title = " ".join((entry.findtext(f"{ATOM}title") or "Untitled").split())
        authors = [author.findtext(f"{ATOM}name") or "" for author in entry.findall(f"{ATOM}author")]
        authors = [author for author in authors if author]
        published = entry.findtext(f"{ATOM}published") or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        abstract = " ".join((entry.findtext(f"{ATOM}summary") or "").split())
        arxiv_id = entry.findtext(f"{ATOM}id")
        doi = entry.findtext(f"{ARXIV}doi")
        pdf_url = None
        for link in entry.findall(f"{ATOM}link"):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href")
                break
        paper_id = stable_paper_id(title, year, authors[0] if authors else None)
        papers.append(
            PaperMetadata(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue="arXiv",
                doi=doi,
                url=pdf_url or arxiv_id,
                source="arXiv",
                abstract=abstract,
                fulltext_status="open-access" if pdf_url else "metadata-only",
            )
        )
    return papers
