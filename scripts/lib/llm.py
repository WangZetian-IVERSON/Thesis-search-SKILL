"""LLM-based section & paragraph summarisation.

Backends (tried in order of availability):
1. claude CLI       — `claude -p "<prompt>"`
2. Anthropic API    — `ANTHROPIC_API_KEY` env var
3. OpenAI API       — `OPENAI_API_KEY` env var

If no backend is available the heuristic values are kept and a warning is printed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Backend detection & calling
# ---------------------------------------------------------------------------

_AVAILABLE_BACKEND: str | None = None
_BACKEND_LABEL: str = ""


def _detect_backend() -> tuple[str | None, str]:
    """Return (backend_id, human_label)."""
    # 1) claude CLI
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return ("claude-cli", f"claude CLI ({result.stdout.strip().split(chr(10))[0]})")
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # 2) Anthropic API
    if os.getenv("ANTHROPIC_API_KEY"):
        return ("anthropic-api", "Anthropic API (ANTHROPIC_API_KEY)")

    # 3) OpenAI / compatible API
    if os.getenv("OPENAI_API_KEY"):
        base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return ("openai-api", f"OpenAI API ({base})")

    return (None, "")


def _call_llm(prompt: str, *, max_tokens: int = 300) -> str | None:
    """Call the first available backend.  Returns None when no backend works."""
    global _AVAILABLE_BACKEND, _BACKEND_LABEL
    if _AVAILABLE_BACKEND is None:
        _AVAILABLE_BACKEND, _BACKEND_LABEL = _detect_backend()

    backend = _AVAILABLE_BACKEND
    if backend == "claude-cli":
        return _call_claude_cli(prompt)
    if backend == "anthropic-api":
        return _call_anthropic(prompt, max_tokens)
    if backend == "openai-api":
        return _call_openai(prompt, max_tokens)

    # no backend at all — print once
    print(
        "  [LLM] No backend available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY, "
        "or install the Claude CLI. Heuristic summaries kept.",
        file=sys.stderr,
    )
    return None


def _call_claude_cli(prompt: str) -> str | None:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, encoding="utf-8", timeout=120,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _call_anthropic(prompt: str, max_tokens: int) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    body = json.dumps({
        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"].strip()
    except Exception as exc:
        print(f"  [LLM] Anthropic API error: {exc}", file=sys.stderr)
    return None


def _call_openai(prompt: str, max_tokens: int) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    body = json.dumps({
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"  [LLM] OpenAI API error: {exc}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Section-level enrichment (used by analyze_paper.py)
# ---------------------------------------------------------------------------

SECTION_LABEL_ZH = {
    "research_problem": "研究问题",
    "core_claim": "核心论点",
    "method": "方法与材料",
    "evidence": "关键证据",
    "limitations": "局限与风险",
}

SECTION_QUESTION_ZH = {
    "research_problem": "这篇论文研究的是什么问题？它想填补什么空白或解决什么矛盾？",
    "core_claim": "这篇论文的核心观点或主要贡献是什么？作者想让读者相信什么？",
    "method": "这篇论文用什么方法、数据或实验来开展研究？",
    "evidence": "这篇论文给出了哪些关键数据、结果或图表来支撑其论点？",
    "limitations": "这篇论文有哪些局限性、适用边界或作者自认不足的地方？",
}


def _build_evidence_block(section: dict[str, Any], max_quotes: int = 5) -> str:
    lines = []
    main = section.get("summary") or ""
    if main:
        lines.append(f"- (p.{section.get('page', '?')}) {main}")
    for item in section.get("evidence", [])[:max_quotes]:
        quote = item.get("quote", "")
        page = item.get("page", "?")
        if quote and quote != main:
            lines.append(f"- (p.{page}) {quote}")
    return "\n".join(lines) if lines else ""


def enrich_analysis_zh(analysis: dict[str, Any], title: str = "", topic: str = "") -> dict[str, Any]:
    """Replace heuristic deep_summary_zh with real Chinese summaries via available LLM.

    Modifies analysis in-place. Heuristic values are kept on any failure.
    """
    backend_label = _detect_backend()[1]
    if backend_label:
        print(f"  [LLM] Using {backend_label}", file=sys.stderr)

    title_hint = f"论文标题：{title}\n" if title else ""
    topic_hint = f"研究主题：{topic}\n" if topic else ""
    enriched: dict[str, str] = {}

    for key, label in SECTION_LABEL_ZH.items():
        section = analysis.get("sections", {}).get(key)
        if not section:
            continue
        evidence_block = _build_evidence_block(section)
        if not evidence_block:
            continue

        question = SECTION_QUESTION_ZH[key]
        prompt = (
            f"{title_hint}{topic_hint}"
            f"以下是从论文中自动抽取的「{label}」相关原文片段（英文）：\n\n"
            f"{evidence_block}\n\n"
            f"请回答：{question}\n"
            "要求：\n"
            "- 用2-3句中文直接陈述论文的具体内容\n"
            '- 不要有\u201c这部分\u201d、\u201c作者通常\u201d之类套话，直接说这篇论文做了什么\n'
            "- 控制在120字以内\n"
            "只输出中文总结，不要其他任何内容。"
        )

        summary = _call_llm(prompt)
        if summary:
            section["deep_summary_zh"] = summary
            section["llm_enriched"] = True
            enriched[key] = summary
            print(f"  [LLM] {label} enriched", file=sys.stderr)

    # relevance section
    if topic and enriched:
        rel_parts = [enriched[k] for k in ["research_problem", "core_claim", "method"] if k in enriched]
        if rel_parts:
            rel_prompt = (
                f"{title_hint}"
                f"研究主题：{topic}\n\n"
                "这篇论文的核心内容：\n"
                + "\n".join(f"- {p}" for p in rel_parts)
                + "\n\n"
                f"请用2-3句中文说明：这篇论文对「{topic}」这个研究主题有什么具体价值？"
                "直接说它能提供哪方面的参考（理论背景、方法借鉴、实证数据、反面案例等），不要泛泛而谈。"
                "只输出中文，控制在100字以内。"
            )
            rel_summary = _call_llm(rel_prompt)
            if rel_summary:
                analysis["relevance"]["summary_zh"] = rel_summary
                analysis["relevance"]["summary"] = rel_summary
                analysis["relevance"]["llm_enriched"] = True
                print("  [LLM] 与用户主题的关系 enriched", file=sys.stderr)

    if enriched:
        analysis["analysis_status"] = "llm-enriched"

    return analysis


# ---------------------------------------------------------------------------
# Paragraph-level enrichment (used by read_paper.py)
# ---------------------------------------------------------------------------

def summarize_paragraph_zh(text: str, title: str = "", page: int = 0) -> str | None:
    """Return a 1-2 sentence Chinese summary of *text*, or None."""
    title_hint = f"论文：{title}\n" if title else ""
    page_hint = f"（第{page}页）" if page else ""
    prompt = (
        f"{title_hint}"
        f"以下是论文{page_hint}中的一段英文原文：\n\n"
        f"{text[:2000]}\n\n"
        "请用1-2句中文概括这段话的核心内容。只输出中文，控制在80字以内。"
    )
    return _call_llm(prompt, max_tokens=120)
