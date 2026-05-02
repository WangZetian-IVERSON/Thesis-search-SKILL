# Thesis Reading Skill

> 面向学术论文的 Agent Skill —— 检索、初筛、精读、图表取证、报告生成、最终审计，全流程可信闭环。

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PyPI Package](https://img.shields.io/badge/install-pip-orange)](#安装)

---

## 目录

- [功能概览](#功能概览)
- [多平台适配](#多平台适配)
- [安装](#安装)
- [快速开始](#快速开始)
- [完整工作流](#完整工作流)
- [数据源](#数据源)
- [项目结构](#项目结构)
- [边界与局限](#边界与局限)

---

## 功能概览

| 能力 | 说明 |
|------|------|
| 🔍 **文献检索** | 从 OpenAlex、CrossRef、Semantic Scholar、arXiv 查询元数据 |
| 📋 **初筛候选** | 不下载 PDF，基于摘要+元数据生成带中文导读的候选清单 |
| 📚 **统一工作台** | 累积所有检索批次，支持日期/关键词/精读状态筛选 |
| 📖 **深度精读** | 合法开放 PDF 或用户上传 PDF → 分块译读 + 结构化笔记 |
| 🖼️ **图表取证** | 图表截图 + 来源 manifest，每条证据记录页码、标题、置信度 |
| 📊 **报告生成** | 中文为主视图的 HTML 报告，原文证据折叠保留 |
| ✅ **最终审计** | 上报生成前自动校验引用完整性、DOI 可验证性、图表来源 |

**设计原则**：
- 初筛阶段只读元数据 + 摘要，不声称已读全文
- 下载 PDF 仅限合法开放来源（Unpaywall、arXiv、PubMed Central 等），或用户自行上传
- 报告由可溯源的证据驱动，不凭空生成引用或数据

---

## 多平台适配

本项目把核心逻辑封装为 Python CLI，与 Agent 平台解耦。各平台通过自己的约定入口读取同一套工作流，不需要维护多套逻辑。

| 平台 | 入口文件 |
|------|----------|
| **Claude Code** | `CLAUDE.md` + `.claude/skills/thesis-reading-skill/SKILL.md` |
| **GitHub Copilot / VS Code** | `.github/skills/thesis-reading-skill/SKILL.md` |
| **Codex / OpenAI 风格 coding agents** | `AGENTS.md` + `.agents/skills/thesis-reading-skill/SKILL.md` |
| **OpenClaw / 其他开源 Agent** | `OPENCLAW.md` |
| **通用** | 根目录 `SKILL.md` |

所有入口均指向根目录的 `SKILL.md`，保证行为一致。

### 安装为 Claude Code Skill

```bash
# 方法一：复制 skill 目录到 Claude 全局 skills 目录
cp -r .claude/skills/thesis-reading-skill ~/.claude/skills/

# 方法二：pip 安装包（需要同时保留 skill 目录）
pip install thesis-reading-skill
```

### 安装为 OpenClaw / OpenAI Agents Skill

```bash
# 复制 skill 目录到 agents 全局 skills 目录
cp -r .agents/skills/thesis-reading-skill ~/.agents/skills/
pip install thesis-reading-skill
```

---

## 安装

**前提条件**：Python 3.10+

```bash
# 克隆仓库
git clone https://github.com/WangZetian-IVERSON/Thesis-search-SKILL.git
cd Thesis-search-SKILL

# 方式 1：可编辑模式安装（开发推荐）
pip install -e .

# 方式 2：从 requirements.txt 安装依赖（直接用 python scripts/ 调用）
pip install -r requirements.txt
```

**可选配置**：复制 `.env.example` 为 `.env`，填入 API key 以提升检索质量：

```bash
cp .env.example .env
# 编辑 .env，填入 OPENALEX_EMAIL 或 SEMANTIC_SCHOLAR_API_KEY
```

---

## 快速开始

```bash
# 1. 检索论文（生成 outputs/evidence/find-xxx.json）
thesis-search "LLM agents literature review" --top 20

# 2. 初筛候选，同步更新统一工作台
thesis-screen outputs/evidence/find-xxx.json --top 20

# 3. 打开工作台查看候选清单
# 浏览器打开 outputs/library/index.html

# 4. 精读某篇论文
thesis-deep-request "给我今天抓取的第一个论文的精读" --topic "LLM agents"

# 5. 手动刷新工作台
thesis-library
```

所有命令也支持 `python scripts/xxx.py` 等价调用，以及统一入口 `thesis-reading <子命令>`。

---

## 完整工作流

### 检索与初筛

```bash
# 检索元数据
thesis-search "your topic" --top 20

# 基于摘要生成初筛候选清单（不下载 PDF）
thesis-screen outputs/evidence/find-YYYYMMDD-HHMMSS-query.json --top 20

# 按初筛排名精读第 N 篇
thesis-deep-read outputs/screening/screen-topic.json "帮我精读第3篇" --topic "your topic"

# 按日期+序号触发精读
thesis-deep-request "给我4.29号抓取的第一个论文的精读" --topic "your topic"
```

### 全文处理

```bash
# 尝试下载合法开放 PDF
thesis-fetch outputs/evidence/find-xxx.json

# 解析本地 PDF（输出 parsed.json）
thesis-parse papers/example.pdf

# 生成中文主视图分块译读页
thesis-read papers/example.pdf --questions "方法是什么; 数据集是什么; 局限是什么"
```

### 证据采集与报告

```bash
# 生成结构化精读分析草稿
thesis-analyze outputs/readings/example.reading_manifest.json \
  --manifest outputs/evidence/example.figures_manifest.json \
  --topic "your topic"

# 捕获图表截图，生成 figures_manifest.json
thesis-capture papers/example.pdf

# 生成 HTML 报告
thesis-report \
  --metadata outputs/evidence/find-xxx.json \
  --parsed outputs/evidence/example.parsed.json \
  --reading outputs/readings/example.reading_manifest.json \
  --analysis outputs/analyses/example.analysis.json \
  --manifest outputs/evidence/example.figures_manifest.json

# 导出 PDF
thesis-export-pdf outputs/report.html --output outputs/report.pdf

# 最终审计（提交报告前必须运行）
thesis-audit \
  --metadata outputs/evidence/find-xxx.json \
  --reading outputs/readings/example.reading_manifest.json \
  --analysis outputs/analyses/example.analysis.json \
  --manifest outputs/evidence/example.figures_manifest.json \
  --report outputs/report.html
```

### 所有 CLI 命令

| 命令 | 说明 |
|------|------|
| `thesis-reading` | 统一入口（子命令模式） |
| `thesis-search` | 检索论文元数据 |
| `thesis-screen` | 初筛候选清单 |
| `thesis-library` | 刷新统一工作台 |
| `thesis-fetch` | 下载合法开放 PDF |
| `thesis-parse` | 解析本地 PDF |
| `thesis-read` | 生成分块译读页 |
| `thesis-analyze` | 生成精读分析草稿 |
| `thesis-capture` | 捕获图表截图 |
| `thesis-report` | 生成 HTML 报告 |
| `thesis-export-pdf` | 导出 PDF |
| `thesis-audit` | 最终审计 |
| `thesis-deep-read` | 按初筛排名精读 |
| `thesis-deep-request` | 按日期+序号触发精读 |
| `thesis-cite` | 生成引用条目 |

---

## 数据源

| 来源 | 说明 |
|------|------|
| **OpenAlex** | 开放学术图谱，覆盖面广 |
| **CrossRef** | DOI 注册机构，元数据权威 |
| **Semantic Scholar** | AI 增强的学术搜索，摘要质量好 |
| **arXiv** | 预印本，开放全文 |

中文商业数据库（CNKI、万方、维普）、Google Scholar、Web of Science、Scopus 等**不建议自动抓取**。
推荐用户手动导出题录或上传 PDF，由 Agent 负责解析和精读。

---

## 项目结构

```
.
├── SKILL.md                    # 主 skill 定义（所有平台通用）
├── CLAUDE.md                   # Claude Code 专属指令
├── AGENTS.md                   # Codex / OpenAI agents 适配
├── OPENCLAW.md                 # OpenClaw / 其他 Agent 适配
├── pyproject.toml              # Python 包配置
├── requirements.txt            # 直接依赖清单
├── .env.example                # 环境变量示例
│
├── scripts/                    # 可执行 CLI 模块
│   ├── cli.py                  # 统一入口 thesis-reading
│   ├── search.py               # 文献检索
│   ├── screen_papers.py        # 初筛候选
│   ├── deep_read_selected.py   # 按排名精读
│   ├── deep_read_request.py    # 按日期序号精读
│   ├── build_library.py        # 刷新统一工作台
│   ├── fetch_fulltext.py       # 下载开放 PDF
│   ├── parse_pdf.py            # PDF 解析
│   ├── read_paper.py           # 分块译读
│   ├── analyze_paper.py        # 精读分析草稿
│   ├── capture_figures.py      # 图表截图
│   ├── build_report.py         # HTML 报告生成
│   ├── export_pdf.py           # PDF 导出
│   ├── audit_report.py         # 最终审计
│   ├── cite.py                 # 引用条目
│   ├── lib/                    # 共享库
│   └── sources/                # 各数据源适配器
│
├── templates/                  # Jinja2 HTML 模板
│   ├── library.html.j2         # 统一工作台
│   ├── reading.html.j2         # 分块译读页
│   └── report.html.j2          # 精读报告
│
├── references/                 # 工作流参考文档（随包分发）
│   ├── workflow.md
│   ├── search-strategy.md
│   ├── paper-reading-template.md
│   ├── analysis-template.md
│   ├── figure-table-policy.md
│   ├── audit-rules.md
│   └── citation-style.md
│
├── .claude/skills/             # Claude Code skill 目录
├── .agents/skills/             # OpenAI agents skill 目录
├── .github/skills/             # GitHub Copilot skill 目录
│
├── papers/                     # PDF 存放目录（不随仓库上传）
└── outputs/                    # 运行产物目录（不随仓库上传）
```

---

## 边界与局限

- 初筛阶段只使用元数据 + 摘要，不声称已读全文
- 精读阶段仅支持合法开放 PDF 或用户手动上传的 PDF
- 图表提取当前采用整页截图，尚未实现精准裁剪
- 表格结构化抽取未完整实现，复杂表格以截图证据保存
- `build_report.py` 生成报告骨架，深度段落需 Agent 读取解析 JSON 后补写
- `analyze_paper.py` 生成结构化草稿，不应未经复核直接当作最终学术判断
- `audit_report.py` 已支持 CrossRef DOI 可选核验，截图视觉检查后续增强

---
built by WangZetian with claude code

## License

[MIT](LICENSE)

