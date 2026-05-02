from __future__ import annotations

import re
from difflib import SequenceMatcher

from lib.schema import PaperMetadata


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip().lower()
    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    return doi or None


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def dedupe_papers(papers: list[PaperMetadata]) -> list[PaperMetadata]:
    results: list[PaperMetadata] = []
    seen_doi: dict[str, PaperMetadata] = {}

    for paper in papers:
        doi = normalize_doi(paper.doi)
        if doi and doi in seen_doi:
            existing = seen_doi[doi]
            if (paper.cited_by_count or 0) > (existing.cited_by_count or 0):
                existing.cited_by_count = paper.cited_by_count
            if not existing.abstract and paper.abstract:
                existing.abstract = paper.abstract
            if not existing.url and paper.url:
                existing.url = paper.url
            continue

        duplicate = None
        for existing in results:
            if title_similarity(existing.title, paper.title) >= 0.94 and existing.year == paper.year:
                duplicate = existing
                break
        if duplicate:
            if not duplicate.doi and paper.doi:
                duplicate.doi = paper.doi
            if not duplicate.url and paper.url:
                duplicate.url = paper.url
            if not duplicate.source and paper.source:
                duplicate.source = paper.source
            duplicate.cited_by_count = max(duplicate.cited_by_count or 0, paper.cited_by_count or 0)
            continue

        paper.doi = doi
        results.append(paper)
        if doi:
            seen_doi[doi] = paper

    return results
