from __future__ import annotations

from lib.schema import PaperMetadata


def format_apa(paper: PaperMetadata) -> str:
    authors = ", ".join(paper.authors[:6]) if paper.authors else "Unknown author"
    if len(paper.authors) > 6:
        authors += ", et al."
    year = paper.year or "n.d."
    venue = f" *{paper.venue}*." if paper.venue else ""
    doi = f" https://doi.org/{paper.doi}" if paper.doi else (f" {paper.url}" if paper.url else "")
    return f"{authors} ({year}). {paper.title}.{venue}{doi}".strip()


def format_bibtex(paper: PaperMetadata) -> str:
    key_author = paper.authors[0].split()[-1].lower() if paper.authors else "unknown"
    key_year = paper.year or "nd"
    key = f"{key_author}{key_year}"
    fields = {
        "title": paper.title,
        "author": " and ".join(paper.authors) if paper.authors else "Unknown",
        "year": str(paper.year or ""),
    }
    if paper.venue:
        fields["journal"] = paper.venue
    if paper.doi:
        fields["doi"] = paper.doi
    elif paper.url:
        fields["url"] = paper.url
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields.items() if value)
    return f"@article{{{key},\n{body}\n}}"
