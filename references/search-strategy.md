# Search Strategy

## Preferred Sources

| Source | Role | Notes |
|---|---|---|
| OpenAlex | Primary metadata search | Free and broad coverage |
| CrossRef | DOI and publication metadata | Good for verification |
| Semantic Scholar | Abstracts and citation signal | Optional API key improves limits |
| arXiv | Preprints and direct PDFs | Good for CS, physics, math |

## Restricted Sources

Do not automate paywalled or anti-bot platforms such as CNKI, Wanfang, Google Scholar, Web of Science, Scopus, or institutional library portals. Ask the user to export citations or upload PDFs.

## Ranking Signals

- Query relevance
- Citation count where available
- Recency
- Venue or source quality
- Availability of legal full text
- Match with user-provided reading questions

## Required Metadata

Every selected paper should keep title, authors, year, venue, DOI or URL, source database, full-text status, and score.
