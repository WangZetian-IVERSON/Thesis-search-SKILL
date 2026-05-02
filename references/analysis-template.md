# Analysis Template

`analyze_paper.py` converts a reading manifest into a structured deep-reading draft.

## Sections

- Research problem: what the paper is trying to solve.
- Core claim: the author's main contribution or argument.
- Method and materials: data, model, framework, experiment, corpus, or theory.
- Key evidence: results, figures, tables, metrics, or textual proof.
- Limitations: author-stated and inferred weaknesses.
- Relevance: how the paper relates to the user's topic.

## Status Labels

- `heuristic`: extracted by deterministic rules and needs review.
- `needs-review`: no stable extractive candidate was found.
- `heuristic-draft`: whole-file status for first-pass analysis.

## Rule

Do not present heuristic drafts as final scholarly judgment. They are structured evidence maps for Agent/human review.
