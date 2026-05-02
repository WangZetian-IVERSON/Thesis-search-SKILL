# Audit Rules

## Paper Reality

- DOI should resolve in CrossRef, OpenAlex, Semantic Scholar, or publisher pages when possible.
- Title, authors, year, and venue should match at least one external metadata source.
- Papers without DOI or URL must be marked for manual verification.

## Full-Text Claims

- A paper can be labeled full-text read only if a local PDF or HTML full text was parsed.
- Page-level claims must reference parsed pages or screenshots.
- Metadata-only papers may appear in background sections but not in full-text reading sections.

## Figure/Table Consistency

- Every referenced screenshot must exist on disk.
- Manifest page numbers and captions must match the report.
- Low-confidence or full-page screenshots must be labeled.

## Logic

- Separate author claims from Agent analysis.
- Avoid strong claims without evidence.
- Flag contradictions between per-paper summaries and synthesis.

## Output Quality

- HTML/PDF must exist and be non-empty.
- Images should render.
- Links and citation fields should be present when available.
