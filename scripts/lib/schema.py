from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PaperMetadata:
    paper_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    url: str | None = None
    source: str | None = None
    cited_by_count: int | None = None
    abstract: str | None = None
    pdf_path: str | None = None
    fulltext_status: str = "metadata-only"
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedPage:
    page: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FigureRecord:
    paper_id: str
    figure_id: str
    kind: str
    page: int
    caption: str | None
    screenshot: str
    extraction_method: str
    confidence: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditFinding:
    severity: str
    code: str
    message: str
    target: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
