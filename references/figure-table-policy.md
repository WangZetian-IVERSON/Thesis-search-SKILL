# Figure and Table Policy

## Provenance Requirements

Every screenshot record must include:

- paper_id
- figure_id or table_id
- kind: figure or table
- page number
- caption if detected
- screenshot path
- extraction method
- confidence

## Extraction Levels

1. Precise crop: best, when coordinates are reliable.
2. Caption-detected full-page screenshot: acceptable for MVP.
3. Manual-review full-page screenshot: acceptable only if clearly labeled.

## Report Rules

- Do not show screenshots without provenance.
- Do not reuse a screenshot for another paper.
- If the crop is imprecise, say it is a full-page screenshot.
- Explain what the figure/table proves or illustrates in the paper's argument.

## Known Limitations

Scanned PDFs, multi-column layouts, multi-page tables, and image-only captions may require manual review.
