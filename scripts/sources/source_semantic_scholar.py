from __future__ import annotations

from lib.http_client import get_json
from lib.schema import PaperMetadata
from lib.utils import stable_paper_id


def search(query: str, limit: int = 20, api_key: str | None = None) -> list[PaperMetadata]:
    headers = {"x-api-key": api_key} if api_key else None
    params = {
        "query": query,
        "limit": min(limit, 20),
        "fields": "title,authors,year,citationCount,venue,externalIds,url,abstract,openAccessPdf",
    }
    data = get_json("https://api.semanticscholar.org/graph/v1/paper/search", params=params, headers=headers)
    papers: list[PaperMetadata] = []
    for item in data.get("data", []):
        title = item.get("title") or "Untitled"
        authors = [author.get("name", "") for author in item.get("authors", []) if author.get("name")]
        year = item.get("year")
        external_ids = item.get("externalIds") or {}
        doi = external_ids.get("DOI")
        pdf = (item.get("openAccessPdf") or {}).get("url")
        paper_id = stable_paper_id(title, year, authors[0] if authors else None)
        papers.append(
            PaperMetadata(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                venue=item.get("venue"),
                doi=doi,
                url=pdf or item.get("url"),
                source="Semantic Scholar",
                cited_by_count=item.get("citationCount"),
                abstract=item.get("abstract"),
                fulltext_status="open-access" if pdf else "metadata-only",
            )
        )
    return papers
