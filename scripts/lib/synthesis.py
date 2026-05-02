from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lib.utils import read_json

SECTION_KEYWORDS = {
    "research_problem": ["problem", "challenge", "gap", "need", "question", "motivation", "workflow", "task"],
    "core_claim": ["propose", "argue", "show", "demonstrate", "contribution", "claim", "hypothesis"],
    "method": ["method", "approach", "framework", "model", "dataset", "experiment", "procedure", "evaluate"],
    "evidence": ["result", "performance", "accuracy", "finding", "figure", "table", "metric", "evaluation"],
    "limitations": ["however", "limitation", "limited", "future work", "bias", "cannot", "threat", "small"],
}

ROLE_TO_SECTION = {
    "thesis": "core_claim",
    "methodology": "method",
    "evidence": "evidence",
    "concession": "limitations",
    "context": "research_problem",
    "concept": "research_problem",
}

LABELS_ZH = {
    "research_problem": "研究问题",
    "core_claim": "核心论点",
    "method": "方法与材料",
    "evidence": "关键证据",
    "limitations": "局限与风险",
    "relevance": "与用户主题的关系",
}

LABELS_EN = {
    "research_problem": "Research Problem",
    "core_claim": "Core Claim",
    "method": "Method and Materials",
    "evidence": "Key Evidence",
    "limitations": "Limitations and Risks",
    "relevance": "Relation to the User Topic",
}

SECTION_SUMMARY_ZH_PREFIX = {
    "research_problem": "这部分表明论文关注的问题、动机或研究缺口是：",
    "core_claim": "这部分可作为论文核心主张或主要贡献的线索：",
    "method": "这部分说明作者采用的方法、材料、数据或分析路径：",
    "evidence": "这部分提供了支撑论点的结果、图表或经验证据：",
    "limitations": "这部分提示论文的适用边界、潜在风险或作者自述局限：",
}

SECTION_SUMMARY_EN_PREFIX = {
    "research_problem": "The paper's research problem, motivation, or gap is captured by this passage: ",
    "core_claim": "This passage is the strongest available signal for the paper's core claim or contribution: ",
    "method": "This passage describes the method, materials, data, or analytical procedure: ",
    "evidence": "This passage provides results, figures, tables, or empirical support for the argument: ",
    "limitations": "This passage indicates the paper's scope limits, risks, or stated limitations: ",
}

SECTION_DETAIL_ZH = {
    "research_problem": {
        "role": "这一部分用于说明论文为什么要研究这个问题：作者通常会在这里交代现象背景、已有研究不足、学术或实践上的矛盾，以及本文试图解释的对象。",
        "use": "写综述时可以把它放在“研究背景/问题提出”位置，用来说明这篇论文为什么值得进入文献脉络。",
        "check": "需要复核作者是否清楚界定了研究对象，以及问题提出是否真的由后续方法和证据承接。",
    },
    "core_claim": {
        "role": "这一部分对应论文最想让读者接受的判断：它可能是一个理论解释、经验发现、方法贡献，或对已有观点的修正。",
        "use": "写精读报告时应把它作为全文论证主线，再回看方法、证据和局限是否都围绕这一主线展开。",
        "check": "需要复核核心主张是否只是作者的表达性判断，还是已经由数据、图表、实验或文本分析支撑。",
    },
    "method": {
        "role": "这一部分说明作者如何把研究问题转化为可操作的分析：包括研究对象、样本范围、数据来源、处理步骤、分类标准或评价方式。",
        "use": "写方法复盘时可以用它说明论文的证据是如何产生的，并判断这个方法是否可复用到用户自己的研究主题。",
        "check": "需要复核样本是否完整、分类或抽取规则是否清楚，以及方法是否会遗漏重要材料。",
    },
    "evidence": {
        "role": "这一部分展示作者用来支撑判断的材料：可能是统计结果、图表趋势、类别分布、案例对比、实验指标或文本证据。",
        "use": "写结论支撑时应优先引用这里的页码和图表，把作者的结论和具体证据绑定起来。",
        "check": "需要复核图表数字、趋势解释和作者推论之间是否匹配，避免把相关性当作因果性。",
    },
    "limitations": {
        "role": "这一部分界定论文结论能成立到什么程度：包括数据来源限制、样本范围限制、方法假设、未覆盖对象和未来工作。",
        "use": "写批判性评价时可以把它作为风险清单，说明这篇论文适合支持什么、不适合支持什么。",
        "check": "需要区分作者明确承认的局限和读者根据方法推断出的潜在局限。",
    },
}


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+", " ".join(text.split()))
    return [part.strip() for part in parts if len(part.strip()) >= 25]


def sentence_score(sentence: str, keywords: list[str], topic_terms: list[str], topic_weight: int = 1) -> int:
    lower = sentence.lower()
    score = sum(3 for keyword in keywords if keyword in lower)
    score += sum(topic_weight for term in topic_terms if term and term in lower)
    return score


def choose_sentence(annotations: list[dict[str, Any]], section: str, topic_terms: list[str]) -> dict[str, Any] | None:
    candidates = []
    keywords = SECTION_KEYWORDS[section]
    topic_weight = 1 if section in {"research_problem", "core_claim"} else 0
    for annotation in annotations:
        role = annotation.get("role")
        role_bonus = 4 if ROLE_TO_SECTION.get(role) == section else 0
        for sentence in split_sentences(annotation.get("text") or ""):
            score = sentence_score(sentence, keywords, topic_terms, topic_weight) + role_bonus
            if score > 0:
                candidates.append((score, annotation.get("page"), sentence, role))
    if not candidates:
        return None
    score, page, sentence, role = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return {"summary": sentence, "page": page, "role": role, "score": score}


def collect_evidence(annotations: list[dict[str, Any]], section: str, topic_terms: list[str], limit: int = 3) -> list[dict[str, Any]]:
    keywords = SECTION_KEYWORDS.get(section, [])
    rows = []
    topic_weight = 1 if section in {"research_problem", "core_claim"} else 0
    for annotation in annotations:
        role = annotation.get("role")
        role_bonus = 4 if ROLE_TO_SECTION.get(role) == section else 0
        for sentence in split_sentences(annotation.get("text") or ""):
            score = sentence_score(sentence, keywords, topic_terms, topic_weight) + role_bonus
            if score > 0:
                rows.append({"page": annotation.get("page"), "role": role, "quote": sentence, "score": score})
    return sorted(rows, key=lambda item: item["score"], reverse=True)[:limit]


def make_section_summary(section: str, sentence: str | None) -> tuple[str, str]:
    if not sentence:
        return (
            "当前解析文本中没有稳定线索，需要 Agent 或人工结合原文补写。",
            "No stable signal was extracted from the parsed text; an agent or human reader should complete this section from the source paper.",
        )
    zh_templates = {
        "research_problem": "论文的问题意识主要围绕研究动机、传播背景或待解释现象展开。具体原文证据见下方折叠摘录，最终提交前需要结合页码逐句复核。",
        "core_claim": "论文的核心判断集中在作者试图证明或解释的主要现象、机制或贡献上。具体主张需以原文证据为准。",
        "method": "论文的方法线索包括确定研究对象、收集或构造材料、组织分析步骤，并据此回答研究问题。具体数据口径和操作流程需查看原文证据。",
        "evidence": "论文的关键证据来自图表、实验结果、类别分布、时间趋势或统计描述，用来支撑作者的主要判断。具体数值和图表说明见原文证据。",
        "limitations": "论文的局限主要涉及数据来源、样本范围、外推边界或作者自述的未覆盖内容。具体限制需依据原文页码复核。",
    }
    return (zh_templates[section], f"{SECTION_SUMMARY_EN_PREFIX[section]}{sentence}")


def extract_key_signals(evidence: list[dict[str, Any]], limit: int = 6) -> list[str]:
    text = " ".join(str(item.get("quote") or "") for item in evidence)
    signals = []
    for value in re.findall(r"\b\d+(?:\.\d+)?%?|\b\d{4}\b", text):
        if value not in signals:
            signals.append(value)
    return signals[:limit]


def evidence_pages(selected: dict[str, Any] | None, evidence: list[dict[str, Any]]) -> list[int]:
    pages = []
    if selected and selected.get("page"):
        pages.append(int(selected["page"]))
    for item in evidence:
        page = item.get("page")
        if page and int(page) not in pages:
            pages.append(int(page))
    return pages[:4]


def make_deep_summary_zh(section: str, selected: dict[str, Any] | None, evidence: list[dict[str, Any]], topic: str) -> str:
    details = SECTION_DETAIL_ZH[section]
    pages = evidence_pages(selected, evidence)
    page_text = "、".join(f"第{page}页" for page in pages) if pages else "当前解析文本"
    topic_text = f"围绕“{topic}”，" if topic else "围绕用户的研究问题，"
    signals = extract_key_signals(evidence)
    signal_text = f"可见数字线索包括：{'、'.join(signals)}。" if signals else "当前自动抽取尚未形成稳定的数字线索。"
    return (
        f"{page_text}提供了本栏目的主要证据。{details['role']}"
        f"{topic_text}这里的价值在于帮助判断论文在整个文献链条中承担的是背景铺垫、方法依据、证据支撑还是批判性限制。"
        f"{signal_text}这些线索不能单独当作最终结论，仍需要打开原文证据逐句核对。"
    )


def make_deep_points_zh(section: str, selected: dict[str, Any] | None, evidence: list[dict[str, Any]], topic: str) -> list[str]:
    details = SECTION_DETAIL_ZH[section]
    pages = evidence_pages(selected, evidence)
    page_text = "、".join(f"第{page}页" for page in pages) if pages else "暂无稳定页码"
    points = [
        f"原文定位：主要证据来自{page_text}，建议先展开下方“查看原文证据”核对上下文。",
        f"论证作用：{details['role']}",
        f"写作使用：{details['use']}",
        f"复核重点：{details['check']}",
    ]
    if topic:
        points.insert(2, f"主题关联：它需要被放回“{topic}”这个问题中判断，不能只按论文自身摘要来决定价值。")
    return points


def load_figures(manifest_paths: list[Path]) -> list[dict[str, Any]]:
    figures = []
    for path in manifest_paths:
        data = read_json(path, {})
        source_pdf = data.get("source_pdf") if isinstance(data, dict) else None
        for record in data.get("records", []) if isinstance(data, dict) else []:
            if source_pdf:
                record["source_pdf"] = source_pdf
            figures.append(record)
    return figures


def build_paper_analysis(reading_manifest: dict[str, Any], *, topic: str = "", figure_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    annotations = reading_manifest.get("annotations", [])
    topic_terms = [term for term in re.split(r"\W+", topic.lower()) if len(term) >= 4]
    sections = {}
    for section in ["research_problem", "core_claim", "method", "evidence", "limitations"]:
        selected = choose_sentence(annotations, section, topic_terms)
        evidence = collect_evidence(annotations, section, topic_terms)
        if selected:
            summary_zh, summary_en = make_section_summary(section, selected["summary"])
            sections[section] = {
                "label": LABELS_ZH[section],
                "label_zh": LABELS_ZH[section],
                "label_en": LABELS_EN[section],
                "summary": selected["summary"],
                "summary_zh": summary_zh,
                "summary_en": summary_en,
                "deep_summary_zh": make_deep_summary_zh(section, selected, evidence, topic),
                "deep_points_zh": make_deep_points_zh(section, selected, evidence, topic),
                "page": selected["page"],
                "evidence": evidence,
                "status": "heuristic",
            }
        else:
            summary_zh, summary_en = make_section_summary(section, None)
            sections[section] = {
                "label": LABELS_ZH[section],
                "label_zh": LABELS_ZH[section],
                "label_en": LABELS_EN[section],
                "summary": summary_zh,
                "summary_zh": summary_zh,
                "summary_en": summary_en,
                "deep_summary_zh": "当前解析文本中没有稳定证据可生成详细总结。建议回到分块译读页，人工选择对应段落后再补写这一栏。",
                "deep_points_zh": [
                    "原文定位：暂无稳定页码。",
                    "论证作用：需要人工判断该部分在论文中的位置。",
                    "写作使用：暂不建议直接纳入最终报告。",
                    "复核重点：先确认 PDF 解析是否漏掉标题、表格或章节文本。",
                ],
                "page": None,
                "evidence": [],
                "status": "needs-review",
            }

    figures = figure_records or []
    reading_source = str(reading_manifest.get("source") or "")
    paper_id = reading_manifest.get("paper_id")
    matched_figures = []
    for item in figures:
        same_id = item.get("paper_id") == paper_id
        same_source = item.get("source_pdf") and reading_source and str(item.get("source_pdf")) == reading_source
        if same_id or same_source:
            matched_figures.append(item)
    figure_notes = [
        {
            "figure_id": item.get("figure_id"),
            "kind": item.get("kind"),
            "page": item.get("page"),
            "caption": item.get("caption"),
            "role": "图表证据，需在精读中说明它支持的具体论点。",
            "role_zh": "图表证据，需在精读中说明它支持的具体论点。",
            "role_en": "Figure/table evidence; the final reading should explain which exact claim it supports.",
            "screenshot": item.get("screenshot"),
        }
        for item in matched_figures
    ]

    relation_summary = ""
    relation_summary_en = ""
    if topic:
        method = sections["method"]["summary"]
        evidence = sections["evidence"]["summary"]
        relation_summary = f"这篇论文与“{topic}”的关系主要体现在：它提供了可用于理解用户主题的研究对象、方法线索或证据材料。更具体地说，报告应先判断它是否能帮助界定问题背景，再判断其方法是否可迁移，最后检查图表或结果能否支撑用户自己的论证。最终写作时不要只把它当作普通相关文献，而要标明它在文献链条中的角色：理论基础、方法借鉴、背景文献、案例材料或反面材料。"
        relation_summary_en = f"This paper relates to \"{topic}\" mainly through its method signal, \"{method}\", and evidence signal, \"{evidence}\". The final report should still judge whether it functions as theoretical background, methodological reference, contextual literature, or a counterexample for the user's research question."
    else:
        relation_summary = "用户未提供主题；需要在最终报告中补充本论文与具体研究问题的关系。"
        relation_summary_en = "No user topic was provided; the final report should add how this paper relates to the specific research question."

    return {
        "paper_id": reading_manifest.get("paper_id"),
        "title": reading_manifest.get("title"),
        "source": reading_manifest.get("source"),
        "topic": topic,
        "analysis_status": "heuristic-draft",
        "sections": sections,
        "figure_table_notes": figure_notes,
        "relevance": {
            "label": LABELS_ZH["relevance"],
            "label_zh": LABELS_ZH["relevance"],
            "label_en": LABELS_EN["relevance"],
            "summary": relation_summary,
            "summary_zh": relation_summary,
            "summary_en": relation_summary_en,
            "deep_points_zh": [
                "先用题名、摘要和精读证据判断它为什么进入候选文献。",
                "再根据方法与证据判断它能支持用户主题中的哪一个子问题。",
                "最后结合局限部分决定引用时应保留哪些边界条件。",
            ],
            "status": "heuristic",
        },
        "audit_notes": [
            "本分析由确定性启发式规则生成，适合作为 Agent 深度精读的底稿。",
            "所有 summary 都应在最终提交前由 Agent 或人工按原文页码复核。",
            "不能把 needs-review 字段直接当作已确认结论。",
        ],
        "audit_notes_en": [
            "This analysis is generated by deterministic heuristics and should be treated as a draft for agent-assisted deep reading.",
            "Every summary should be checked against the source pages before final delivery.",
            "Fields marked needs-review must not be treated as confirmed conclusions.",
        ],
    }
