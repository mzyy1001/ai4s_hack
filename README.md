# 生物医药论文 AI 审稿 Skill

黑客松项目 · 方向：**AI 辅助生物医药论文审稿工具**
目标：替代人工审稿的**基础环节**，大幅提升审稿人的工作效率。

**最终交付物：一个完整、可复用的 Skill 文档** → [`skills/biomed-paper-review/SKILL.md`](skills/biomed-paper-review/SKILL.md)

---

## 输入 / 输出

**输入**：一篇生物医药论文（JATS XML / PDF / 纯文本）

**输出**：
1. **结构化结果表** —— 研究目标 / 实验方法 / 核心数据 / 初步结论 + 评估矩阵
2. **图表解读与原图定位** —— 每张图的类型、实验条件、关键数值、页码级定位
3. **七维审核发现** —— 统一格式的 findings，每条必附论文原文出处
4. **整体置信度评分** —— 0–100，仅作排序信号
5. **人工复核建议** —— 每条 major 及以上发现对应一条可执行动作

---

## 仓库结构

```
skills/biomed-paper-review/     ← 交付物本体
├── SKILL.md                    主文档：流程、模块路由、统一 finding 契约、定位符规范、置信度算法
├── references/                 七个审核模块的规则库（各自由负责人填充）
│   ├── 01-structured-extraction.md    M1 结构化抽取         MZYY（陈泓睿）
│   ├── 02-macro-logic.md              M2 宏观逻辑与完整性    ZY（卓妍）
│   ├── 03-experimental-methods.md     M3 实验方法合规性      Peter
│   ├── 04-statistics.md               M4 统计学方法          JY（蒋运）
│   ├── 05-figures-and-charts.md       M5 图谱解析与图表规范  MY（敏怡）
│   ├── 06-ethics-compliance.md        M6 伦理合规            Peter
│   └── 07-conclusions-discussion.md   M7 结论与讨论          MY（敏怡）
├── schemas/                    机器可校验的输出模式（模块间的集成契约）
│   ├── finding.schema.json            ★ 七模块共用，最重要
│   ├── structured_result.schema.json
│   ├── figure_record.schema.json
│   └── review_report.schema.json
└── templates/review_report.md  报告渲染模板

datasets/                       测试语料：10 篇 PLOS 开放获取论文（CC-BY）· 非提交必需
├── manifest.json               每篇覆盖哪个审核维度、图表数量
└── papers/<slot>__<doi>/
    ├── meta.json               书目 + 图注索引（作为 ground truth）
    ├── fulltext.xml            JATS 全文
    └── figures/                逐图图像（max 1400px JPEG）

tools/fetch_papers.py           语料抓取脚本（可重跑）
docs/architecture.md            架构说明：七个模块如何合成一个 Skill
```

## 语料

`datasets/` 中每篇论文对应一个审核维度，避免十篇同质化：

| slot | 覆盖维度 |
| --- | --- |
| `dose_response` | 剂量响应曲线 / IC50 拟合 |
| `animal_invivo` | 动物实验必要性 + 伦理 |
| `rct_clinical` | CONSORT 流程图 + 样本量 |
| `microscopy_ihc` | 显微图 / 免疫组化定量 |
| `flow_cytometry` | 流式散点与门控图 |
| `small_sample_pilot` | 小样本负面样例 |
| `meta_analysis` | PRISMA 流程图 + 森林图 |
| `omics_heatmap` | 火山图/热图 + 多重比较 |
| `toxicology` | 毒理剂量爬坡 |
| `survival_km` | Kaplan-Meier 生存曲线 |

**PDF 不入库**：仅用于本地测试页码级定位，为控制仓库体积未纳入。
重新抓取可完整重建原始语料（含全分辨率图像与全部 PDF），仅用 Python 标准库、无需额外依赖：

```bash
python3 tools/fetch_papers.py
```

## 使用

遵循 opencode / Anthropic Agent Skill 标准格式。当前 references、schemas、resources 与模板位于
`skills/biomed-paper-review/`，但四个确定性工具仍在仓库根 `tools/`；因此当前必须以完整仓库运行，
尚不能声称仅拷贝 skill 目录即可获得工具能力。迁入 `skills/biomed-paper-review/scripts/` 后才自包含。

在 Claude Code 中，本仓库已通过 `.claude/skills/` 软链接自动加载。

## 提交合规自查（对照 04-提交规范 / 05-自动评审规则）

| 检查项 | 状态 |
| --- | --- |
| `skills/` 下有且仅有一个 skill 目录 | ✅ `biomed-paper-review` |
| `SKILL.md` frontmatter 含合法 `name` / `description` | ✅ name 19 字符（≤64，小写连字符）；description 200 字符（≤1024，第三人称） |
| SKILL.md 正文建议 <500 行 | ✅ 正文 496 行（文件含 frontmatter 共 501 行）；契约细节已拆入 `references/00-contracts.md` |
| 文件引用只一层深（渐进披露） | ✅ SKILL.md → `references/*.md`，无二层跳转 |
| 单文件 ≤10MB | ✅ skill 本体内满足；⚠️ 若误打包 `datasets/`，其中一份 PDF 为 18,677,256 bytes，会超限 |
| 提交包体积 | ✅ `skills/biomed-paper-review/` 约 396 KiB；完整工作区约 200 MiB，不得整仓提交 |
| `requirements.txt` | ✅ 无需额外安装 —— 已实现工具使用标准库或评测环境预装科学栈 |
| 结构化输入/输出 schema | ✅ `schemas/` 10 份 JSON Schema |
| 无诱导评分 / 注入语句 | ✅ |
| 沙箱可运行（2 核 / 4GB / 无 GPU / 单任务 12 小时） | ✅ 已实现工具均可 CPU 运行，无需 requirements.txt |
| 沙箱网络：**白名单制，开放公开科学数据源**（可申请追加） | ✅ 一期离线即可跑通；外部数据源作为**可选增强层**，不可得时降级为 `system_limitation` |

## 分期范围

**一期（黑客松交付）**：离线核心必须仅凭**论文自身内容 + 通用规范库**跑通；公开科学数据源
作为可选增强层。连接器不可得、超时或返回不可解析响应时降级为 `system_limitation`，不得据此判稿件有问题。

当前外部证据契约与连接器尚未落地，不能声称已经完成数据库核验。原先统一推到“二期”的注册核验、
标识符核验与数据登录号核验应按 `docs/proposals/round-4-external-data-components.md` 重新排期；
M4 的 p 值反算、CI 自洽、计数/百分比与 GRIM 已实现为一期离线能力，图像取证仍未实现。

## 当前状态

- ✅ 主框架、模块路由、统一 finding 契约、定位符规范、置信度算法
- ✅ 10 份 JSON Schema + 报告模板（`external` 证据型尚未写入 schema）
- ✅ 10 篇测试语料（全文 + PDF + 逐图图像）
- ✅ M1 结构化抽取规则（字段定义、抽取顺序、缺口登记）
- ✅ 七个模块的二期扩展规则草案
- 🚧 M2–M7 一期规则库待各负责人填充（每份文件末尾有 TODO 清单）
- 🚧 统计学数据库 MCP 接入
