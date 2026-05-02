from __future__ import annotations

import html
import re
from dataclasses import dataclass, asdict
from typing import Any

ROLE_KEYWORDS = {
    "methodology": ["method", "approach", "framework", "model", "dataset", "experiment", "procedure", "we propose", "we train"],
    "evidence": ["result", "finding", "accuracy", "performance", "significant", "table", "figure", "evaluation", "measure"],
    "concession": ["however", "although", "limitation", "future work", "threat", "bias", "cannot", "fails"],
    "concept": ["define", "definition", "concept", "refers to", "known as", "called", "terminology"],
    "thesis": ["argue", "claim", "show that", "demonstrate", "contribute", "contribution", "hypothesis"],
}

ROLE_LABEL_ZH = {
    "thesis": "核心论点",
    "concept": "概念定义",
    "evidence": "证据/结果",
    "concession": "限制/反驳",
    "methodology": "方法设计",
    "context": "背景铺垫",
}

ROLE_LABEL_EN = {
    "thesis": "Core claim",
    "concept": "Concept",
    "evidence": "Evidence/result",
    "concession": "Limitation/concession",
    "methodology": "Methodology",
    "context": "Context",
}


@dataclass
class ParagraphAnnotation:
    page: int
    paragraph_index: int
    text: str
    role: str
    role_label: str
    role_label_zh: str
    role_label_en: str
    highlighted_html: str
    translation_zh: str
    paragraph_function: str
    paragraph_function_zh: str
    paragraph_function_en: str
    logical_role: str
    logical_role_zh: str
    logical_role_en: str
    risk_note: str
    risk_note_zh: str
    risk_note_en: str
    matched_questions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def split_paragraphs(text: str, min_chars: int = 120) -> list[str]:
    raw_parts = re.split(r"\n\s*\n|(?<=\.)\s{2,}", text)
    paragraphs: list[str] = []
    buffer = ""
    for part in raw_parts:
        cleaned = " ".join(part.split())
        if not cleaned:
            continue
        if len(buffer) < min_chars:
            buffer = f"{buffer} {cleaned}".strip()
            continue
        paragraphs.append(buffer)
        buffer = cleaned
    if buffer:
        paragraphs.append(buffer)
    return [item for item in paragraphs if len(item) >= 40]


def classify_role(paragraph: str) -> str:
    lower = paragraph.lower()
    scores = {role: sum(1 for keyword in keywords if keyword in lower) for role, keywords in ROLE_KEYWORDS.items()}
    role, score = max(scores.items(), key=lambda item: item[1])
    return role if score > 0 else "context"


def highlight(paragraph: str, role: str) -> str:
    escaped = html.escape(paragraph)
    keywords = ROLE_KEYWORDS.get(role, [])[:8]
    if not keywords:
        return escaped
    pattern = re.compile("|".join(re.escape(keyword) for keyword in sorted(keywords, key=len, reverse=True)), re.IGNORECASE)
    return pattern.sub(lambda match: f'<mark class="{role}">{match.group(0)}</mark>', escaped)


def match_questions(paragraph: str, questions: list[str]) -> list[str]:
    if not questions:
        return []
    lower = paragraph.lower()
    matched = []
    for question in questions:
        terms = [term for term in re.split(r"\W+", question.lower()) if len(term) >= 4]
        if terms and any(term in lower for term in terms):
            matched.append(question)
    return matched


def make_notes(role: str, lang: str) -> tuple[str, str, str]:
    zh = lang.lower().startswith("zh")
    if role == "methodology":
        return (
            "说明作者如何设计研究或方法。" if zh else "Explains how the study or method is designed.",
            "把研究问题转化为可操作的分析路径。" if zh else "Turns the research problem into an operational path.",
            "需要检查方法是否足以支撑后续结论。" if zh else "Check whether the method can support later conclusions.",
        )
    if role == "evidence":
        return (
            "呈现数据、结果、图表或评价指标。" if zh else "Presents data, results, figures, or metrics.",
            "为作者主张提供经验证据。" if zh else "Provides empirical support for the author's claim.",
            "需要确认指标解释和结论外推是否过度。" if zh else "Check whether metric interpretation or extrapolation is overstated.",
        )
    if role == "concession":
        return (
            "处理限制、反例、失败情形或未来工作。" if zh else "Handles limitations, counterexamples, failures, or future work.",
            "限定论证边界，避免结论过度扩张。" if zh else "Constrains the argument and prevents overreach.",
            "需要区分作者自述限制和读者可推断限制。" if zh else "Separate stated limitations from inferred limitations.",
        )
    if role == "concept":
        return (
            "界定关键概念或术语。" if zh else "Defines key concepts or terms.",
            "为后续论证提供概念前提。" if zh else "Provides conceptual premises for later argument.",
            "需要检查同一概念是否前后一致。" if zh else "Check whether the concept remains consistent.",
        )
    if role == "thesis":
        return (
            "表达作者的核心主张或贡献。" if zh else "States the author's core claim or contribution.",
            "建立全文论证方向。" if zh else "Sets the direction of the paper's argument.",
            "需要追踪后文是否提供足够证据。" if zh else "Track whether later sections provide enough evidence.",
        )
    return (
        "提供背景、问题动机或过渡信息。" if zh else "Provides background, motivation, or transition.",
        "帮助读者理解研究位置。" if zh else "Helps situate the study.",
        "需要确认背景陈述是否有来源支撑。" if zh else "Check whether background claims are sourced.",
    )


def make_notes_bilingual(role: str) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
    return make_notes(role, "zh"), make_notes(role, "en")


def make_translation_draft(paragraph: str, role: str) -> str:
    role_name = ROLE_LABEL_ZH.get(role, "论文内容")
    if role == "methodology":
        focus = "作者在这里交代研究对象、数据来源、分析步骤或方法设计。阅读时应重点确认样本范围、变量定义和方法是否足以支撑后文结论。"
    elif role == "evidence":
        focus = "作者在这里呈现图表、统计结果或经验发现。阅读时应重点确认数字、趋势和图表说明是否真的支持作者的核心主张。"
    elif role == "concession":
        focus = "作者在这里限定结论边界，说明研究局限、反例、失败情形或未来工作。阅读时应区分作者明确承认的局限和读者推断出的潜在风险。"
    elif role == "concept":
        focus = "作者在这里界定关键概念、术语或理论背景。阅读时应检查概念定义是否清楚，以及后文是否保持同一用法。"
    elif role == "thesis":
        focus = "作者在这里表达核心主张、贡献或主要判断。阅读时应追踪后文是否提供足够证据支持这一主张。"
    else:
        focus = "作者在这里提供背景、问题动机或过渡信息。阅读时应确认这些背景陈述是否有来源支撑，并判断它们如何引出研究问题。"
    return (
        f"本段属于“{role_name}”内容。中文译读：{focus}"
        "原文证据已折叠在下方，正式提交前应由 Agent 按原文逐句精译并复核专业术语。"
    )


def annotate_paragraphs(page_texts: list[tuple[int, str]], *, questions: list[str] | None = None, lang: str = "zh", max_paragraphs: int = 80) -> list[ParagraphAnnotation]:
    questions = questions or []
    labels = ROLE_LABEL_ZH if lang.lower().startswith("zh") else ROLE_LABEL_EN
    annotations: list[ParagraphAnnotation] = []
    paragraph_index = 1
    for page_number, text in page_texts:
        for paragraph in split_paragraphs(text):
            role = classify_role(paragraph)
            paragraph_function, logical_role, risk_note = make_notes(role, lang)
            zh_notes, en_notes = make_notes_bilingual(role)
            annotations.append(
                ParagraphAnnotation(
                    page=page_number,
                    paragraph_index=paragraph_index,
                    text=paragraph,
                    role=role,
                    role_label=labels[role],
                    role_label_zh=ROLE_LABEL_ZH[role],
                    role_label_en=ROLE_LABEL_EN[role],
                    highlighted_html=highlight(paragraph, role),
                    translation_zh=make_translation_draft(paragraph, role),
                    paragraph_function=paragraph_function,
                    paragraph_function_zh=zh_notes[0],
                    paragraph_function_en=en_notes[0],
                    logical_role=logical_role,
                    logical_role_zh=zh_notes[1],
                    logical_role_en=en_notes[1],
                    risk_note=risk_note,
                    risk_note_zh=zh_notes[2],
                    risk_note_en=en_notes[2],
                    matched_questions=match_questions(paragraph, questions),
                )
            )
            paragraph_index += 1
            if len(annotations) >= max_paragraphs:
                return annotations
    return annotations


def parse_questions(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"\n|;|,|Q\d+[:：]", raw)
    return [part.strip() for part in parts if part.strip()][:6]
