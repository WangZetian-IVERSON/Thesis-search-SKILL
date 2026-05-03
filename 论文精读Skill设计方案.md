# 论文精读 Skill 设计方案（第一版）

## 1. 目标定位

这个 Skill 的目标不是代替研究者判断论文，而是把“找论文、验真、读论文、抽图表、梳理论证、生成精读报告、最终质检”做成一条可复用的 Agent 工作流。

用户只需要给出研究主题、关键词、问题意识或已有论文列表，Agent 按照标准流程检索公开数据库和用户提供的材料，输出可检查、可追溯、可复核的 PDF 或 HTML 精读报告。

核心原则：

- 不编造论文：所有论文必须有可验证来源，如 DOI、OpenAlex ID、Semantic Scholar ID、期刊官网页面、图书馆记录或用户上传原文。
- 不绕过付费墙或反爬限制：对知网、万方、Web of Science、Scopus、Google Scholar 等限制较强的平台，采用“用户导出/上传 + Agent 解析”的方式。
- 图表必须可追溯：每张截图都记录来源论文、页码、图/表编号、截图文件路径、提取方法和人工复核状态。
- 结论必须回到文本：总结中的重要判断必须绑定原文证据、页码或段落位置。
- 最终报告必须经过独立校验：用验证 Agent 检查真实性、图表对应、引用格式、逻辑连贯和输出文件完整性。

## 2. 典型使用方式

用户输入示例：

```text
请围绕“LLM agents in academic literature review”找 10 篇近五年的核心论文，做深度精读，重点分析方法、数据集、评价指标、局限和未来研究方向，最后输出 HTML 报告。
```

或：

```text
我上传了 6 篇 PDF，请逐篇精读，提取关键图表截图，整理每篇论文的论证结构，并生成一个横向对比报告。
```

Agent 输出：

- `outputs/report.html` 或 `outputs/report.pdf`
- `outputs/evidence/metadata.json`
- `outputs/screenshots/<paper_id>/figure_*.png`
- `outputs/screenshots/<paper_id>/table_*.png`
- `outputs/checks/final_audit.md`
- `outputs/checks/source_verification.csv`

## 3. 整体工作流

### 阶段 A：需求澄清

Agent 先把用户需求转化为结构化任务：

- 研究主题：用户关心的问题是什么。
- 学科范围：计算机、医学、人文社科、教育、管理等。
- 时间范围：默认近 5 年，可由用户指定。
- 文献数量：默认 8-12 篇核心论文。
- 文献类型：综述、实证研究、方法论文、理论论文、会议论文、学位论文等。
- 输出语言：中文、英文或双语。
- 输出格式：Markdown、HTML、PDF。
- 图表处理强度：不截图、只截核心图表、尽量提取全部图表。

若用户没有明确要求，默认采用“可复核精读报告”模式：检索 20-40 条候选文献，筛选 8-12 篇，逐篇精读并生成 HTML。

### 阶段 B：文献检索

优先使用公开、稳定、合法的数据源：

| 数据源 | 用途 | 自动化程度 | 备注 |
|---|---|---:|---|
| OpenAlex | 跨学科论文元数据、引用关系、开放获取链接 | 高 | 免费公开 API，适合首轮检索 |
| Semantic Scholar | 摘要、引用、影响力、相关论文 | 高 | 免费 API，有速率限制 |
| CrossRef | DOI、出版信息、期刊信息核验 | 高 | 适合 DOI 验真 |
| CORE | 开放获取全文和元数据 | 中高 | 适合找可下载 PDF |
| arXiv | 预印本全文 | 高 | 适合计算机、物理、数学等 |
| PubMed / Europe PMC | 生医论文 | 高 | 医学方向可启用 |
| DBLP | 计算机会议论文 | 高 | 适合 CS 论文核对 |
| Unpaywall | 查找合法开放获取 PDF | 高 | 需要 email 配置 |
| CNKI / 万方 / 维普 | 中文论文 | 低 | 不建议自动抓取，推荐用户导出题录或上传 PDF |
| Google Scholar | 补充发现 | 低 | 不建议自动抓取，推荐用户手动导出/复制 |

检索策略：

1. 将用户问题扩展为中英文关键词、同义词和学科术语。
2. 对每个数据源调用独立 source 模块。
3. 合并结果并去重：按 DOI、标题相似度、作者、年份合并。
4. 初步评分：主题相关度、年份、引用量、期刊/会议质量、开放全文可得性。
5. 生成候选清单，让 Agent 选择或请用户确认。

### 阶段 C：论文获取

论文全文来源优先级：

1. 用户上传的 PDF。
2. 开放获取 PDF，如 arXiv、PubMed Central、期刊 OA 页面、CORE、Unpaywall。
3. HTML 全文页面，如期刊官网开放页面。
4. 只有元数据和摘要的论文：可纳入“背景文献”，但不能作为“已精读全文论文”。

重要边界：

- 不自动登录用户账号。
- 不绕过验证码、付费墙、机构访问控制或数据库反爬限制。
- 对无法合法获取全文的论文，只能做“元数据级摘要”，并在报告中标注“未读取全文”。

### 阶段 D：PDF / HTML 解析

对 PDF：

- 使用 PyMuPDF 提取文本、页码、图片块、页面截图。
- 使用 pdfplumber 或 Camelot/Tabula 尝试提取表格结构。
- 使用 GROBID 或 Science Parse 提取标题、作者、摘要、章节、参考文献。
- 保留每段文字的页码映射。

对 HTML 全文：

- 使用浏览器工具或 Playwright 获取页面正文和截图。
- 解析 figure/table 节点、caption、图片链接。
- 对需要视觉确认的图表区域做元素截图。

推荐生成中间结构：

```json
{
  "paper_id": "smith-2024-agent-review",
  "title": "...",
  "doi": "...",
  "source_pdf": "papers/smith-2024.pdf",
  "pages": [
    {
      "page": 1,
      "text": "...",
      "blocks": []
    }
  ],
  "figures": [
    {
      "figure_id": "fig1",
      "label": "Figure 1",
      "caption": "...",
      "page": 3,
      "screenshot": "outputs/screenshots/smith-2024/fig1.png"
    }
  ],
  "tables": []
}
```

### 阶段 E：图表截图与对应关系

截图可行，但要区分两类：

1. PDF 页面截图：技术上最稳定。用 PyMuPDF 根据页面坐标裁剪，或整页截图后标出图表区域。
2. 网页元素截图：用 Playwright 对 figure/table 元素截图，适合 HTML 全文。

图表识别策略：

- 优先使用 PDF 内置图片对象和 caption 文本定位。
- 若无法精准裁剪，退化为整页截图，并在报告中标注页码和图表编号。
- 表格优先提取结构化数据；结构化失败时保存截图。
- 每张图表必须写入 manifest：论文 ID、页码、图表编号、caption、截图路径、提取置信度。

图表不得脱离语境使用：精读报告中引用图表时，必须说明该图表支持什么论点、在哪一节出现、与作者论证链条的关系是什么。

### 阶段 F：逐篇精读

每篇论文采用固定精读模板，避免“泛泛总结”：

1. 元信息
   - 标题、作者、年份、发表 venue、DOI/URL、数据源。
   - 是否读取全文、全文来源、开放获取状态。
2. 研究问题
   - 作者试图解决什么问题。
   - 这个问题为什么重要。
3. 核心论点
   - 主张是什么。
   - 与已有研究相比新在哪里。
4. 方法与材料
   - 数据、样本、实验设置、理论框架或文本材料。
   - 方法是否能支撑结论。
5. 论证结构
   - 问题提出 → 方法设计 → 证据展开 → 结果解释 → 结论外推。
6. 关键图表
   - 图表编号、页码、截图、caption、解释、在论证中的作用。
7. 关键发现
   - 分条列出，并绑定证据位置。
8. 局限与风险
   - 作者自述局限。
   - Agent 识别的隐含局限。
9. 可引用观点
   - 必须附页码或章节位置。
10. 与用户研究问题的关系
   - 理论基础、方法借鉴、对话对象、反例或背景文献。

### 阶段 G：横向综合

当论文数量超过 3 篇时，生成横向综合：

- 主题聚类：哪些论文处理同一问题。
- 方法比较：数据、模型、实验、理论框架的差异。
- 结论共识：多篇论文共同支持什么。
- 争议分歧：哪些结论互相冲突。
- 研究空白：哪些问题没有被充分解决。
- 证据强度：哪些结论来自强证据，哪些只是推测。
- 推荐阅读顺序：入门、核心、进阶、反方。

### 阶段 H：报告生成

推荐优先生成 HTML，再按需转换为 PDF。

HTML 报告结构：

1. 封面：主题、检索时间、数据库、论文数量、输出版本。
2. 执行摘要：最重要发现和阅读建议。
3. 检索方法：关键词、数据库、筛选标准。
4. 文献总览表：标题、作者、年份、venue、DOI、全文状态、评分。
5. 逐篇精读：按论文展开。
6. 图表证据库：所有截图及对应说明。
7. 横向综合：主题、方法、结论、局限、空白。
8. 参考文献：BibTeX / APA / GB/T 7714 可选。
9. 审计附录：真实性验证、图表对应检查、未解决问题。

PDF 生成建议：

- HTML 使用 Playwright 或 WeasyPrint 转 PDF。
- 图片路径使用相对路径或嵌入 base64，避免 PDF 丢图。
- 每次生成后执行自动打开/截图检查，确认页面非空、图片存在、目录可读。

## 4. 最终检验 Agent

建议设计一个独立的 `paper-reading-auditor` 子流程。它不负责写报告，只负责挑错。

校验维度：

### 4.1 论文真实性

- DOI 是否能在 CrossRef / OpenAlex / Semantic Scholar 至少一个来源查到。
- 标题、作者、年份是否与外部元数据一致。
- PDF 首页标题是否与元数据标题相符。
- 引用信息是否存在未来年份、缺失期刊、作者错配等异常。
- 对仅由模型生成、无数据源记录的论文标红。

### 4.2 全文读取真实性

- 报告声称“精读全文”的论文，必须有本地 PDF/HTML 记录。
- 精读中的页码引用必须能在解析文本中找到对应页。
- 关键观点必须能回溯到原文片段或图表。

### 4.3 图表对应关系

- 每张截图文件必须存在且可打开。
- manifest 中的页码、图表编号、caption 与报告中引用一致。
- 截图不能来自另一篇论文。
- 若图表裁剪置信度低，报告必须标注“整页截图/需人工复核”。

### 4.4 逻辑畅通

- 每篇论文总结是否包含研究问题、方法、结论、局限。
- 横向综合是否区分“作者结论”和“Agent 推断”。
- 是否存在没有证据支撑的强断言，如“彻底证明”“必然导致”。
- 是否把摘要级信息误写成全文精读结论。

### 4.5 输出文件质量

- HTML/PDF 是否生成成功。
- 图片是否显示。
- 内部链接是否可跳转。
- 参考文献是否缺字段。
- 审计附录是否列出数据源、失败项和人工复核建议。

最终校验输出示例：

```markdown
# Final Audit

结论：有条件通过

## 必须修复
- Paper 03 报告中引用 Figure 2，但 manifest 只有 Figure 1 和 Table 1。
- Paper 07 DOI 与 CrossRef 返回标题不一致，需人工核验。

## 建议修复
- Paper 02 的表格截图为整页截图，建议手动裁剪。
- 横向综合第 3 节有 2 个强断言缺少对应证据。

## 已通过
- 10 篇论文中 9 篇 DOI 核验成功。
- 23 张图表截图文件均存在且可打开。
```

## 5. 推荐项目结构

参考 `humanities-thesis-skill` 的结构，可以设计为：

```text
thesis-reading-skill/
├── SKILL.md
├── README.md
├── requirements.txt
├── .env.example
├── references/
│   ├── workflow.md                    # 总流程说明
│   ├── search-strategy.md             # 检索策略和数据库说明
│   ├── paper-reading-template.md      # 逐篇精读模板
│   ├── figure-table-policy.md         # 图表截图和证据规则
│   ├── report-template.md             # HTML/PDF 报告结构
│   ├── audit-rules.md                 # 最终校验规则
│   └── citation-style.md              # APA / GB/T 7714 / BibTeX 说明
├── scripts/
│   ├── search.py                      # 多数据库检索入口
│   ├── fetch_fulltext.py              # 合法全文获取入口
│   ├── parse_pdf.py                   # PDF 文本、页码、图表解析
│   ├── capture_figures.py             # 图表截图/裁剪
│   ├── build_report.py                # HTML 报告生成
│   ├── export_pdf.py                  # HTML 转 PDF
│   ├── audit_report.py                # 最终质检入口
│   ├── lib/
│   │   ├── schema.py                  # Paper、Figure、AuditFinding 等数据模型
│   │   ├── http_client.py             # 请求封装、限速、重试
│   │   ├── query.py                   # 查询扩展
│   │   ├── dedupe.py                  # 去重
│   │   ├── score.py                   # 候选论文评分
│   │   ├── metadata_verify.py         # DOI/标题/作者核验
│   │   ├── pdf_extract.py             # PDF 解析公共函数
│   │   ├── figure_detect.py           # 图表定位
│   │   ├── render.py                  # HTML 渲染
│   │   └── audit_rules.py             # 确定性校验规则
│   └── sources/
│       ├── source_openalex.py
│       ├── source_semantic_scholar.py
│       ├── source_crossref.py
│       ├── source_core.py
│       ├── source_arxiv.py
│       ├── source_pubmed.py
│       ├── source_dblp.py
│       └── source_unpaywall.py
├── templates/
│   ├── report.html.j2
│   ├── paper_section.html.j2
│   └── audit.md.j2
├── papers/                            # 用户上传或合法下载的 PDF，不提交 git
├── outputs/
│   ├── report.html
│   ├── report.pdf
│   ├── evidence/
│   ├── screenshots/
│   └── checks/
└── tests/
    ├── fixtures/
    ├── test_dedupe.py
    ├── test_metadata_verify.py
    ├── test_manifest.py
    └── test_audit_rules.py
```

## 6. SKILL.md 初步设计

`SKILL.md` 应保持精简，只写 Agent 必须遵守的工作流程和安全边界，把长模板放到 `references/`。

建议 frontmatter：

```yaml
---
name: thesis-reading-skill
description: "Use when: searching academic papers, verifying real papers, reading PDFs deeply, extracting figures and tables, building literature review reports, auditing academic report accuracy. Supports thesis reading, paper deep reading, literature review, DOI verification, figure/table screenshots, HTML/PDF report generation."
argument-hint: "research topic, paper list, uploaded PDFs, output format, reading depth"
---
```

建议主体结构：

```markdown
# Thesis Reading Skill

## When to Use
Use this skill when the user asks to search papers, deeply read papers, summarize academic literature, extract figures/tables, build a thesis reading report, or verify whether papers and citations are real.

## Non-Negotiable Rules
1. Never invent papers, DOI, authors, pages, figures, tables, or quotations.
2. Do not bypass paywalls, CAPTCHA, login systems, or database access controls.
3. Distinguish full-text reading from metadata-only analysis.
4. Every figure/table screenshot must have provenance metadata.
5. Run final audit before presenting HTML/PDF outputs.

## Procedure
1. Clarify task scope.
2. Search public metadata sources.
3. Verify and deduplicate papers.
4. Acquire legal full text or request user upload.
5. Parse PDF/HTML.
6. Extract figures/tables and create manifest.
7. Deep read each paper using the template.
8. Generate cross-paper synthesis.
9. Build HTML/PDF report.
10. Run final audit and fix blocking issues.
```

## 7. 工具可行性判断

### 可以实现

- 多公开数据库检索和元数据合并。
- DOI、标题、作者、年份交叉核验。
- 合法开放 PDF 下载。
- 用户上传 PDF 后自动解析文本和页码。
- PDF 页面截图、图片提取、表格截图。
- HTML 报告生成和 PDF 导出。
- 最终审计报告。

### 部分可实现，需要降级策略

- 精准识别所有图表边界：不同 PDF 版式差异很大，需要“精准裁剪失败则整页截图”。
- 表格结构化提取：扫描版 PDF 或复杂跨页表格可能失败，需要截图替代。
- 中文商业数据库自动抓取：不稳定且可能违反条款，建议用户导出题录或上传 PDF。
- 论文质量排序：可结合引用量、venue、相关度，但不能完全等同于学术质量。

### 不建议实现

- 自动绕过知网/万方/Google Scholar 反爬。
- 自动登录用户学校图书馆账号。
- 声称“已读全文”但只有摘要或元数据。
- 没有来源截图/页码的“关键图表分析”。

## 8. MVP 实现路线

### MVP 1：元数据检索与验真

- 支持 OpenAlex、Semantic Scholar、CrossRef、arXiv。
- 输出候选论文 CSV/JSON。
- 做 DOI 和标题核验。
- 生成文献筛选表。

### MVP 2：用户上传 PDF 精读

- 解析本地 PDF。
- 提取每页文本和基础元数据。
- 生成逐篇精读 Markdown/HTML。
- 区分原文证据和 Agent 分析。

### MVP 3：图表截图与 manifest

- 支持整页截图。
- 尝试基于 caption 定位图表。
- 生成 `figures_manifest.json`。
- 在 HTML 报告中嵌入截图。

### MVP 4：最终审计

- 检查论文真实性。
- 检查截图文件和 manifest 对应。
- 检查报告引用的 DOI、页码、图表编号。
- 输出 `final_audit.md`。

### MVP 5：完整报告导出

- HTML 模板美化。
- PDF 导出。
- 自动检查 PDF 非空、图片存在。
- 增加测试和示例数据。

## 9. 后续需要你确认的问题

1. 你主要面向哪个学科？不同学科的数据源和精读模板会不一样。
2. 你希望这个 Skill 运行在 VS Code Copilot、Claude Code、OpenClaw，还是多个平台都兼容？
3. 第一版是否优先支持英文论文，中文论文采用用户上传/导出的方式？
4. 报告输出你更想要 HTML、PDF，还是两者都要？
5. 你希望 Agent 自动筛选论文，还是先给你候选清单确认后再精读？

## 10. Paperwise 的参考价值

`sjqsgg/Paperwise` 对本项目有较强参考意义，但它更像“论文阅读与 HTML 注释 Skill”，不是完整的“多数据库检索 + 图表证据 + 最终审计”系统。建议吸收它的产品形态和交互设计，而不是直接照搬能力边界。

### 值得吸收的部分

1. 命令式工作流
   - Paperwise 把能力拆成 `/paper find`、`/paper read`、`/paper digest`、`/paper cite`。
   - 本项目可以借鉴为 `find`、`read`、`synthesize`、`audit`、`export` 等子流程。

2. 双栏 HTML 精读界面
   - 左栏保留论文原文，右栏放 Agent 注释卡片。
   - 这非常适合“精读”，比单纯 Markdown 摘要更可复核。
   - 本项目可以扩展为：左栏原文片段/图表截图，右栏研究问题、论证角色、证据强度、局限分析。

3. 颜色标注系统
   - Paperwise 用 5 种颜色区分 thesis、concept、evidence、concession、methodology。
   - 本项目可以保留这个思想，但改成更学术审计化的标签：核心论点、概念定义、方法证据、数据结果、限制/反驳、可引用句。

4. 问题驱动阅读模式
   - Paperwise 的 `--questions` 模式很适合用户带着具体问题读论文。
   - 本项目应把它作为核心入口：用户可以指定“方法是什么、数据集是什么、局限是什么、和我的研究有什么关系”。

5. Paper Quality Bar
   - Paperwise 在页面顶部展示来源、venue、年份、引用层级、preprint 标签。
   - 本项目可以升级为 Evidence Quality Bar：来源数据库、 DOI 核验状态、全文状态、图表提取状态、审计状态。

6. 本地 PDF 模式
   - `--local` 对本项目非常重要。
   - 对中文数据库、付费论文、用户已有文献，最稳妥的第一版就是“用户上传/指定本地 PDF，Agent 解析和精读”。

7. 自包含 HTML 输出
   - Paperwise 把 CSS 嵌入 HTML，便于分享和归档。
   - 本项目也应优先生成自包含 HTML，再导出 PDF，减少图片和样式丢失。

### 不能直接照搬的部分

1. 数据源覆盖较窄
   - Paperwise 主要是 OpenAlex、arXiv 和可选 Semantic Scholar。
   - 本项目还需要 CrossRef、CORE、Unpaywall、PubMed、DBLP，以及中文题录导入能力。

2. 缺少强审计流程
   - Paperwise 强在阅读呈现，但没有把“论文是否真实、图表是否对应、报告是否有错误”作为独立最终关卡。
   - 本项目应保留独立 `audit_report.py` 和审计附录。

3. 图表证据链不足
   - Paperwise 主要关注段落级逻辑注释，没有专门处理图表截图、页码、caption、manifest 对应关系。
   - 本项目的特色应放在“图表可追溯证据库”。

4. 不适合直接作为多论文综述引擎
   - Paperwise 的单篇阅读体验很好，但横向综合、争议对比、研究空白识别需要额外设计。
   - 本项目需要把单篇精读结果结构化后再做跨论文 synthesis。

### 建议吸收后的设计调整

本项目可以采用“Paperwise 式前端体验 + 更强的证据审计后端”：

```text
find        检索和候选论文卡片
read        单篇 PDF/HTML 精读，生成双栏注释页
figures     提取图表截图和 manifest
synthesize  多篇论文横向综合
cite        生成 APA / BibTeX / GB/T 7714
audit       最终真实性、图表对应、逻辑和输出质量检查
export      输出自包含 HTML 和 PDF
```

第一版可以优先复刻 Paperwise 最成熟的部分：`read` 生成双栏 HTML 精读页；再叠加本项目自己的 `figures` 和 `audit`，这样实现路径最稳。

## 11. 第一版建议结论

建议先做一个保守但真实可靠的版本：

- 自动检索公开英文数据库。
- 中文数据库不自动爬取，改为用户导出/上传。
- 全文精读只基于合法获取的 PDF/HTML。
- 图表先做“整页截图 + caption 对应”，再逐步升级为精准裁剪。
- 把最终审计作为强制步骤，任何未核验论文、缺失截图、错误图表对应都必须在报告中显式标出。

这样第一版能跑通完整闭环，而且不会因为数据库访问、版权、反爬和图表识别问题卡死。后续再逐步增强图表定位、表格结构化、中文题录解析和更漂亮的报告模板。
