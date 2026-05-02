from __future__ import annotations

import re
from html import escape
from typing import Any


def tokenize(value: str) -> set[str]:
    return {term for term in re.split(r"\W+", value.lower()) if len(term) >= 4}


def trim_text(value: str | None, max_chars: int = 420) -> str:
    if not value:
        return "No abstract available from the selected metadata source."
    compact = " ".join(value.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def infer_paper_type(paper: dict[str, Any]) -> str:
    title = (paper.get("title") or "").lower()
    abstract = (paper.get("abstract") or "").lower()
    text = f"{title} {abstract}"
    if any(term in text for term in ["survey", "review", "overview", "systematic literature"]):
        return "review/survey"
    if any(term in text for term in ["dataset", "benchmark", "evaluation", "experiment", "empirical"]):
        return "empirical/method"
    if any(term in text for term in ["framework", "model", "architecture", "algorithm", "approach"]):
        return "method/theory"
    if paper.get("venue") == "arXiv":
        return "preprint"
    return "research paper"


def paper_type_zh(paper_type: str) -> str:
    mapping = {
        "review/survey": "综述或调研论文",
        "empirical/method": "实证或方法论文",
        "method/theory": "方法或理论论文",
        "preprint": "预印本论文",
        "research paper": "研究论文",
    }
    return mapping.get(paper_type, paper_type)


def abstract_sentences(abstract: str | None) -> list[str]:
    if not abstract:
        return []
    parts = re.split(r"(?<=[.!?。！？])\s+", " ".join(abstract.split()))
    return [part.strip() for part in parts if len(part.strip()) >= 25]


def find_sentence(sentences: list[str], keywords: list[str]) -> str:
    for sentence in sentences:
        lower = sentence.lower()
        if any(keyword in lower for keyword in keywords):
            return sentence
    return ""


def extract_numbers(text: str, limit: int = 4) -> list[str]:
    numbers = []
    pattern = re.compile(
        r"(?<![A-Za-z0-9-])\d+(?:\.\d+)?%\s*-\s*\d+(?:\.\d+)?%(?![A-Za-z0-9-])"
        r"|(?<![A-Za-z0-9-])\d{1,3}(?:,\d{3})+(?![A-Za-z0-9-])"
        r"|(?<![A-Za-z0-9-])\d+(?:\.\d+)?%?(?![A-Za-z0-9-])"
    )
    for value in pattern.findall(text):
        value = re.sub(r"\s*-\s*", "-", value)
        if value not in numbers:
            numbers.append(value)
    return numbers[:limit]


def topic_relation_zh(title: str, abstract: str, topic: str) -> str:
    if not topic:
        return ""
    topic_terms = tokenize(topic)
    paper_terms = tokenize(f"{title} {abstract}")
    matched = sorted(topic_terms & paper_terms)
    if len(matched) >= 2:
        return f"它和“{topic}”的关系在于：摘要明确涉及{ '、'.join(matched[:4]) }等主题线索，可进入后续精读候选。"
    if matched:
        return f"它和“{topic}”只有弱相关，主要匹配到{matched[0]}这一条线索；若排序靠后，应谨慎选择是否精读。"
    return f"它和“{topic}”的摘要相关性较弱，除非用户另有理由，否则不应优先精读。"


def infer_abstract_topic_zh(title: str, abstract: str) -> str:
    text = f"{title} {abstract}".lower()
    if "cost-aware" in text and "tool planning" in text:
        return "LLM 工具规划中的执行成本、计划质量和性能-成本权衡问题"
    if "user-mediated" in text and "attack" in text:
        return "规划型或网页使用型 Agent 在用户转发不可信内容时面临的安全风险"
    if "plan reuse" in text or "agentreuse" in text:
        return "LLM 驱动 Agent 中复用历史计划以降低响应延迟的问题"
    if "multi-llm" in text and "tool" in text:
        return "小型 LLM 在工具调用、任务规划和结果汇总中的能力拆分问题"
    if "climate" in text:
        return "低成本生成区域气候变化情景和风险度量的工具问题"
    if "benchmark" in text or "dataset" in text:
        return "面向特定任务的数据集、基准或评估方法问题"
    if "survey" in text or "review" in text:
        return "相关研究脉络、方法类别和开放问题的综述整理"
    return "论文摘要中提出的核心研究问题"


def infer_method_zh(title: str, abstract: str) -> str:
    text = f"{title} {abstract}".lower()
    names = []
    for name in ["CATP-LLM", "OpenCATP", "AgentReuse", "CAORL", "TPL", "QoP"]:
        if name.lower() in text and name not in names:
            names.append(name)
    if "cost-aware" in text and "offline reinforcement learning" in text:
        return "作者提出成本感知工具规划框架，结合工具规划语言、成本感知上下文和离线强化学习来优化工具计划。"
    if "tool planning language" in text:
        return "作者设计工具规划语言，把工具和依赖关系编码为可学习 token，以支持多分支、非顺序的工具计划。"
    if "plan reuse" in text or "agentreuse" in text:
        return "作者通过请求语义相似度和意图分类来判断历史计划是否可复用，从而减少重复规划开销。"
    if "planner" in text and "caller" in text and "summarizer" in text:
        return "作者把工具使用能力拆成 planner、caller 和 summarizer 等子模块，让多个 LLM 分工协作完成任务。"
    if "systematic evaluation" in text:
        return "作者采用系统评测方式，在受控环境中比较不同 Agent 在多种场景下的行为表现。"
    if names:
        return f"摘要显示作者提出或使用了 {', '.join(names)} 等核心组件来完成方法设计。"
    return "摘要显示作者提出了一个方法、框架、工具或评估流程来处理上述问题。"


def infer_result_zh(abstract: str) -> str:
    lower = abstract.lower()
    numbers = extract_numbers(abstract)
    number_text = f"摘要中的关键数字包括 {'、'.join(numbers)}。" if numbers else "摘要未提供明显的核心数字指标。"
    if "bypass" in lower or "security" in lower or "attack" in lower:
        return f"评测结果主要用于揭示安全风险、约束绕过或执行边界问题，{number_text}"
    if "outperform" in lower or "improvement" in lower or "surpass" in lower:
        return f"实验结果声称该方法优于若干基线或已有方法，{number_text}"
    if "achieves" in lower or "achieve" in lower or "results show" in lower:
        return f"实验或评测结果显示方法在目标指标上取得改进，{number_text}"
    if "show" in lower or "demonstrate" in lower:
        return f"摘要报告了实验证据或案例结果来支持作者主张，{number_text}"
    return number_text


def abstract_summary_zh(paper: dict[str, Any], topic: str) -> str:
    title = paper.get("title") or "该论文"
    abstract = paper.get("abstract") or ""
    if not abstract:
        return "当前数据源没有提供摘要，因此无法生成真正的摘要总结；这里只能保留题名、作者、年份和来源信息供初筛。"
    sentences = abstract_sentences(abstract)
    topic_zh = infer_abstract_topic_zh(title, abstract)
    method_zh = infer_method_zh(title, abstract)
    result_zh = infer_result_zh(abstract)
    gap_sentence = find_sentence(sentences, ["however", "unfortunately", "overlook", "lack", "challenge", "cost", "risk"])
    gap_zh = "摘要强调现有研究或应用仍存在明显缺口。" if gap_sentence else "摘要主要围绕作者提出的问题和解决思路展开。"
    topic_note = topic_relation_zh(title, abstract, topic)
    return f"摘要总结：这篇论文研究{topic_zh}。{gap_zh}{method_zh}{result_zh}{topic_note}"


def relevance_reason(paper: dict[str, Any], topic_terms: set[str]) -> str:
    title_terms = tokenize(paper.get("title") or "")
    abstract_terms = tokenize(paper.get("abstract") or "")
    matched_title = sorted(title_terms & topic_terms)
    matched_abstract = sorted((abstract_terms & topic_terms) - set(matched_title))
    parts = []
    if matched_title:
        parts.append("title matches: " + ", ".join(matched_title[:5]))
    if matched_abstract:
        parts.append("abstract matches: " + ", ".join(matched_abstract[:5]))
    if paper.get("cited_by_count"):
        parts.append(f"citation signal: {paper.get('cited_by_count')}")
    if paper.get("fulltext_status") and paper.get("fulltext_status") != "metadata-only":
        parts.append(f"full text: {paper.get('fulltext_status')}")
    return "; ".join(parts) if parts else "kept by source ranking; requires manual relevance check"


def relevance_reason_zh(paper: dict[str, Any], topic_terms: set[str]) -> str:
    reason = relevance_reason(paper, topic_terms)
    if reason == "kept by source ranking; requires manual relevance check":
        return "该论文由数据库排序保留，但题名或摘要中的主题匹配信号不强，需要人工进一步判断相关性。"
    return f"该论文入选初筛的主要依据是：{reason}。"


def next_action(paper: dict[str, Any]) -> str:
    if paper.get("pdf_path"):
        return "ready for deep reading from local PDF"
    url = (paper.get("url") or "").lower()
    if url.endswith(".pdf") or "arxiv.org/pdf" in url:
        return "can deep read after downloading open PDF"
    if paper.get("fulltext_status") == "open-access":
        return "try legal full-text fetch, otherwise ask user to upload PDF"
    return "screening only; request PDF before deep reading"


def next_action_zh(paper: dict[str, Any]) -> str:
    action = next_action(paper)
    mapping = {
        "ready for deep reading from local PDF": "已有本地 PDF，可以直接进入全文精读。",
        "can deep read after downloading open PDF": "发现开放 PDF 链接，选择后可先合法下载再精读。",
        "try legal full-text fetch, otherwise ask user to upload PDF": "可尝试合法获取开放全文；如果失败，需要用户上传 PDF。",
        "screening only; request PDF before deep reading": "目前只能初筛，若要精读需要用户提供 PDF 或开放全文链接。",
    }
    return mapping.get(action, action)


def concise_zh_takeaway(paper: dict[str, Any], topic: str) -> str:
    return abstract_summary_zh(paper, topic)


def concise_en_takeaway(paper: dict[str, Any], topic: str) -> str:
    paper_type = infer_paper_type(paper)
    abstract_line = trim_text(paper.get("abstract"), 260)
    if abstract_line == "No abstract available from the selected metadata source.":
        abstract_line = "The selected metadata source does not provide an abstract, so this screening relies on title, year, venue, and source ranking signals."
    return (
        f"This paper is preliminarily classified as {paper_type}. For the topic \"{topic}\", its relevance mainly comes from title, abstract, or source-ranking signals. "
        f"Abstract signal: {abstract_line}"
    )


def english_digest(paper: dict[str, Any]) -> str:
    return trim_text(paper.get("abstract"), 520)


def natural_language_prompt(rank: int) -> str:
    return f"帮我精读第{rank}篇"


def screen_papers(metadata: dict[str, Any], topic: str = "", limit: int | None = None) -> dict[str, Any]:
    papers = metadata.get("papers", []) if isinstance(metadata, dict) else []
    topic = topic or metadata.get("query") or ""
    topic_terms = tokenize(topic)
    if limit:
        papers = papers[:limit]

    cards = []
    for index, paper in enumerate(papers, start=1):
        card = dict(paper)
        card["rank"] = index
        card["paper_type"] = infer_paper_type(paper)
        card["screening_summary"] = trim_text(paper.get("abstract"), 520)
        card["zh_takeaway"] = concise_zh_takeaway(paper, topic)
        card["en_takeaway"] = concise_en_takeaway(paper, topic)
        card["english_digest"] = english_digest(paper)
        card["screening_reason"] = relevance_reason(paper, topic_terms)
        card["screening_reason_zh"] = relevance_reason_zh(paper, topic_terms)
        card["screening_reason_en"] = relevance_reason(paper, topic_terms)
        card["next_action"] = next_action(paper)
        card["next_action_zh"] = next_action_zh(paper)
        card["next_action_en"] = next_action(paper)
        card["natural_language_prompt"] = natural_language_prompt(index)
        card["deep_read_hint"] = f"python scripts/deep_read_selected.py <screening.json> {index} --topic \"{topic}\""
        cards.append(card)

    return {
        "topic": topic,
        "source_metadata": metadata.get("query"),
        "screening_mode": "metadata-and-abstract-only",
        "count": len(cards),
        "papers": cards,
        "limits": [
            "This screening does not claim full-text reading.",
            "Use deep_read_selected.py only after a paper is selected for full-text analysis.",
        ],
    }


def render_markdown(screening: dict[str, Any]) -> str:
    lines = [f"# 初筛候选论文：{screening.get('topic')}", "", f"Mode: {screening.get('screening_mode')}", ""]
    for paper in screening.get("papers", []):
        lines.append(f"## {paper['rank']}. {paper.get('title')}")
        authors = ", ".join(paper.get("authors") or []) or "Unknown authors"
        lines.append(f"{authors} · {paper.get('year') or 'n.d.'} · {paper.get('venue') or 'Unknown venue'}")
        lines.append(f"Type: {paper.get('paper_type')} · Score: {paper.get('score')}")
        if paper.get("doi"):
            lines.append(f"DOI: {paper.get('doi')}")
        if paper.get("url"):
            lines.append(f"URL: {paper.get('url')}")
        lines.append("")
        lines.append(f"中文精简导读：{paper.get('zh_takeaway')}")
        lines.append(f"English concise guide: {paper.get('en_takeaway')}")
        lines.append(f"English abstract digest: {paper.get('english_digest')}")
        lines.append(f"入选理由：{paper.get('screening_reason_zh')}")
        lines.append(f"Screening reason: {paper.get('screening_reason_en')}")
        lines.append(f"下一步：{paper.get('next_action_zh')}")
        lines.append(f"Next action: {paper.get('next_action_en')}")
        lines.append(f"自然语言口令：{paper.get('natural_language_prompt')}")
        lines.append(f"深读命令：`{paper.get('deep_read_hint')}`")
        lines.append("")
    lines.append("## 注意")
    for item in screening.get("limits", []):
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_html(screening: dict[str, Any]) -> str:
    cards = []
    for paper in screening.get("papers", []):
        authors = escape(", ".join(paper.get("authors") or []) or "Unknown authors")
        title = escape(paper.get("title") or "Untitled")
        venue = escape(paper.get("venue") or "Unknown venue")
        link = paper.get("url") or (f"https://doi.org/{paper.get('doi')}" if paper.get("doi") else "")
        link_html = f'<a href="{escape(link)}">source</a>' if link else "no source link"
        prompt = escape(paper.get("natural_language_prompt") or "")
        cards.append(
            f"""
            <article class="card">
              <div class="rank">{paper.get('rank')}</div>
              <div class="body">
                <div class="card-head">
                  <h2>{title}</h2>
                  <span class="badge">#{paper.get('rank')}</span>
                </div>
                <p class="meta">{authors} · {paper.get('year') or 'n.d.'} · {venue}</p>
                <div class="quality-row">
                  <span>{escape(paper.get('paper_type') or '')}</span>
                  <span>Score {paper.get('score')}</span>
                  <span>{escape(paper.get('source') or '')}</span>
                  <span>{link_html}</span>
                </div>
                <div class="summary-grid">
                  <section>
                    <h3>中文精简导读</h3>
                    <p>{escape(paper.get('zh_takeaway') or '')}</p>
                  </section>
                  <section>
                                        <h3>English Concise Guide</h3>
                                        <p>{escape(paper.get('en_takeaway') or paper.get('english_digest') or '')}</p>
                  </section>
                </div>
                                <div class="mini-grid">
                                    <section>
                                        <h3>入选理由</h3>
                                        <p>{escape(paper.get('screening_reason_zh') or paper.get('screening_reason') or '')}</p>
                                    </section>
                                    <section>
                                        <h3>Screening Reason</h3>
                                        <p>{escape(paper.get('screening_reason_en') or paper.get('screening_reason') or '')}</p>
                                    </section>
                                    <section>
                                        <h3>推荐动作</h3>
                                        <p>{escape(paper.get('next_action_zh') or paper.get('next_action') or '')}</p>
                                    </section>
                                    <section>
                                        <h3>Next Action</h3>
                                        <p>{escape(paper.get('next_action_en') or paper.get('next_action') or '')}</p>
                                    </section>
                                </div>
                <div class="prompt-line"><span>自然语言：</span><code>{prompt}</code></div>
                <div class="prompt-line"><span>CLI：</span><code>{escape(paper.get('deep_read_hint') or '')}</code></div>
              </div>
            </article>
            """
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>初筛候选论文 - {escape(screening.get('topic') or '')}</title>
  <style>
    body {{ margin: 0; background: #f7f7f4; color: #1f2933; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }}
    header {{ background: #243b53; color: white; padding: 28px 36px; }}
    header h1 {{ margin: 0 0 8px; font-size: 30px; }}
    header p {{ margin: 0; color: #d9e2ec; }}
    main {{ max-width: 1220px; margin: 0 auto; padding: 24px; }}
    .note {{ background: #e0f2fe; border: 1px solid #bae6fd; border-radius: 6px; padding: 14px 16px; margin-bottom: 18px; }}
    .card {{ display: grid; grid-template-columns: 58px 1fr; gap: 16px; background: white; border: 1px solid #d9e2ec; border-radius: 6px; padding: 18px; margin-bottom: 16px; }}
    .rank {{ width: 44px; height: 44px; border-radius: 50%; background: #0b69a3; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; }}
    .card-head {{ display: flex; align-items: start; justify-content: space-between; gap: 12px; }}
    .badge {{ background: #edf2f7; color: #243b53; border-radius: 999px; padding: 3px 10px; font-weight: 700; }}
    h2 {{ margin: 0 0 6px; font-size: 20px; line-height: 1.35; }}
    h3 {{ margin: 0 0 6px; font-size: 14px; color: #243b53; }}
    .meta {{ color: #52606d; }}
    .quality-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
    .quality-row span {{ background: #f0f4f8; border: 1px solid #d9e2ec; border-radius: 4px; padding: 3px 8px; font-size: 13px; }}
    .summary-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; margin: 12px 0; }}
    .summary-grid section {{ background: #fbfdff; border: 1px solid #d9e2ec; border-radius: 6px; padding: 12px; }}
    .mini-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 12px 0; }}
    .mini-grid section {{ background: #f8fafc; border: 1px solid #d9e2ec; border-radius: 6px; padding: 10px 12px; }}
    .mini-grid p {{ margin: 0; }}
    .prompt-line {{ display: grid; grid-template-columns: 86px 1fr; gap: 10px; align-items: start; margin-top: 8px; }}
    .prompt-line span {{ color: #52606d; font-weight: 700; }}
    code {{ display: block; background: #f0f4f8; border: 1px solid #d9e2ec; padding: 8px; border-radius: 4px; white-space: pre-wrap; }}
    a {{ color: #0b69a3; }}
    @media (max-width: 820px) {{ .card {{ grid-template-columns: 1fr; }} .summary-grid, .mini-grid {{ grid-template-columns: 1fr; }} .prompt-line {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<header><h1>初筛候选论文</h1><p>{escape(screening.get('topic') or '')} · metadata + abstract only · {screening.get('count')} papers</p></header>
<main><div class="note">这是初筛页：仅基于数据库 metadata 和 abstract 生成，不声称已读全文。用户可以直接说“帮我精读第 3 篇”，Agent 再进入 PDF/HTML 全文精读和审计流程。</div>{''.join(cards)}</main>
</body>
</html>"""
