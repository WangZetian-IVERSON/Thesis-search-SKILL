from __future__ import annotations

import math
from datetime import datetime

from lib.schema import PaperMetadata


def score_papers(papers: list[PaperMetadata]) -> list[PaperMetadata]:
    current_year = datetime.now().year
    total = max(len(papers), 1)
    for rank, paper in enumerate(papers, start=1):
        relevance = 1.0 - ((rank - 1) / total)
        citations = math.log((paper.cited_by_count or 0) + 1) / 10
        if paper.year:
            recency = max(0.0, 1.0 - max(current_year - paper.year, 0) / 12)
        else:
            recency = 0.0
        fulltext = 0.1 if paper.pdf_path or paper.fulltext_status == "open-access" else 0.0
        paper.score = round((0.5 * relevance) + (0.3 * citations) + (0.2 * recency) + fulltext, 4)
    return sorted(papers, key=lambda item: item.score, reverse=True)
