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

datasets/                       测试语料：10 篇 PLOS 开放获取论文（CC-BY）
├── manifest.json               每篇覆盖哪个审核维度、图表数量
└── papers/<slot>__<doi>/
    ├── meta.json               书目 + 图注索引（作为 ground truth）
    ├── fulltext.xml            JATS 全文
    ├── paper.pdf               原始 PDF（用于页码级原图定位）
    └── figures/                逐图高清图像

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

重新抓取：

```bash
python3 tools/fetch_papers.py
```

## 使用

在 Claude Code 中，本仓库已通过 `.claude/skills/` 软链接自动加载该 Skill。
在其他环境复用时，把 `skills/biomed-paper-review/` 整个目录拷贝到对应的 skills 目录即可 —— 
目录自包含，无外部依赖。

## 分期范围

**一期（黑客松交付）**：仅基于**论文自身内容 + 通用规范库**完成校验，不调用外部数据库。

**二期**：结论科学真伪、领域创新性、常识校验、统计复算、图像取证、注册与批件核验。
这些**不是做不到，是本期先不做** —— 都需要外部数据接入或更长的规则打磨周期。
每一项都已指派给对应模块，规则写在该模块 reference 文件的「二期扩展」一节，
二期直接启用，无需改动主框架。见 [`SKILL.md §0`](skills/biomed-paper-review/SKILL.md)。

二期建议的起点是**不依赖外部数据库的两组**：M4 的统计一致性检验（GRIM / p 值反算 / CI 自洽）
和 M5 的论文内图像取证。判定确定、无召回率风险、且现有大模型普遍查不出来。

## 当前状态

- ✅ 主框架、模块路由、统一 finding 契约、定位符规范、置信度算法
- ✅ 四份 JSON Schema + 报告模板（`external_source` 字段已为二期预留）
- ✅ 10 篇测试语料（全文 + PDF + 逐图图像）
- ✅ M1 结构化抽取规则（字段定义、抽取顺序、缺口登记）
- ✅ 七个模块的二期扩展规则草案
- 🚧 M2–M7 一期规则库待各负责人填充（每份文件末尾有 TODO 清单）
- 🚧 统计学数据库 MCP 接入
