# OpenClaw Adapter Notes

This project can be used by OpenClaw or other open coding agents as a terminal-first paper reading toolchain.

## Entry Point

Start with [SKILL.md](SKILL.md). It defines the full workflow, safety policy, commands, expected outputs, and audit requirements.

## Expected Capabilities

The agent should be able to:

- read repository files;
- run Python commands in the workspace;
- access public web APIs when the user requests search;
- write generated outputs under `outputs/` and `papers/`;
- avoid restricted sources that require login, CAPTCHA, institutional access, or paywall bypass.

## Minimal Workflow

```bash
python scripts/search.py "<topic>" --top 20
python scripts/screen_papers.py outputs/evidence/find-xxx.json --topic "<topic>" --top 20
python scripts/deep_read_request.py "给我5.2号抓取的第一个论文的精读" --topic "<topic>"
python scripts/build_library.py
```

For full-text reading, use only legal open PDFs or user-uploaded PDFs, then run parsing, reading, figure capture, report generation, and audit commands from [SKILL.md](SKILL.md).

## Output Convention

The primary interface is `outputs/library/index.html`. Reports should be Chinese-first, with source evidence kept as traceable folded details when appropriate.
