from __future__ import annotations

from lib.http_client import get_json
from lib.schema import PaperMetadata
from lib.utils import stable_paper_id


def search(query: str, limit: int = 20) -> list[PaperMetadata]:
    params = {
        "query.bibliographic": query,
        "rows": min(limit, 50),
        "select": "title,author,issued,container-title,DOI,URL,is-referenced-by-count",
    }
    data = get_json("https://api.crossref.org/works", params=params)
    papers: list[PaperMetadata] = []
    for item in data.get("message", {}).get("items", []):
        title_values = item.get("title") or []
        title = title_values[0] if title_values else "Untitled"
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            name = " ".join(part for part in [given, family] if part).strip()
            if name:
                authors.append(name)
        date_parts = item.get("issued", {}).get("date-parts") or []
        year = date_parts[0][0] if date_parts and date_parts[0] else None
        venues = item.get("container-title") or []
        venue = venues[0] if venues else None
        doi = item.get("DOI")
        paper_id = stable_paper_id(title, year, authors[0] if authors else None)
        papers.append(
            PaperMetadata(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                doi=doi,
                url=item.get("URL"),
                source="CrossRef",
                cited_by_count=item.get("is-referenced-by-count"),
            )
        )
    return papers


def verify_doi(doi: str) -> dict | None:
    data = get_json(f"https://api.crossref.org/works/{doi}")
    return data.get("message")
