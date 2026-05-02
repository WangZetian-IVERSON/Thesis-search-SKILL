from __future__ import annotations

from lib.http_client import get_json
from lib.schema import PaperMetadata
from lib.utils import stable_paper_id


def search(query: str, limit: int = 20, email: str | None = None) -> list[PaperMetadata]:
    params = {
        "search": query,
        "per-page": min(limit, 50),
        "select": "title,authorships,publication_year,cited_by_count,primary_location,doi,open_access",
    }
    if email:
        params["mailto"] = email
    data = get_json("https://api.openalex.org/works", params=params)
    papers: list[PaperMetadata] = []
    for item in data.get("results", []):
        title = item.get("title") or "Untitled"
        authors = [
            author.get("author", {}).get("display_name", "")
            for author in item.get("authorships", [])
            if author.get("author", {}).get("display_name")
        ]
        year = item.get("publication_year")
        location = item.get("primary_location") or {}
        source = location.get("source") or {}
        venue = source.get("display_name")
        doi = item.get("doi")
        pdf_url = (item.get("open_access") or {}).get("oa_url")
        paper_id = stable_paper_id(title, year, authors[0] if authors else None)
        papers.append(
            PaperMetadata(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                doi=doi,
                url=pdf_url or doi,
                source="OpenAlex",
                cited_by_count=item.get("cited_by_count"),
                fulltext_status="open-access" if pdf_url else "metadata-only",
            )
        )
    return papers
