# 生物医药论文 AI 审稿 Skill

黑客松项目 · 方向：**AI 辅助生物医药论文审稿工具**
目标：自动化并辅助人工审稿的**基础环节**，提升审稿人的取证与复核效率。

**最终交付物：一个目录自包含的 Skill 包** → [`skills/biomed-paper-review/`](skills/biomed-paper-review/)

## 十分钟速览

- **差异化**：五个包内确定性工具把单位、统计关系、伦理规则、序列/标识符和图像候选转为
  可复算的 `extraction_signal`；M2–M7 只能在回查稿件证据后产 `finding`。
- **当前可运行**：五个独立 CLI、自检、10 份 schema、四个契约模拟实例；离线工具失败和
  外部源不可得均降级为 `system_limitation`，不归责稿件。
- **当前未打通**：尚无论文输入→最终 Markdown/JSON 的统一执行器；
  尚无三次中位数的正 uplift artifact。X1 connector 已交付。
- **当前不能声称**：不能把“脚本存在”写成“已产生 uplift”，不能把契约模拟实例写成
  端到端运行结果，不能声称已完成外部数据库核验。

---

## 目标输入 / 输出

**输入**：一篇生物医药论文（JATS XML / PDF / 纯文本）

**输出**：
1. **结构化结果表** —— 研究目标 / 实验方法 / 核心数据 / 初步结论 + 评估矩阵
2. **图表解读与原图定位** —— 每张图的类型、实验条件、关键数值、页码级定位
3. **六维审核发现**（M2–M7）—— 统一格式的 findings，每条必附论文原文出处
   （M1 是前置抽取层，**不产出 finding**）
4. **三项独立评分** —— 稿件风险分 / 抽取覆盖率 / 复核置信度；
   **互不替代，不得合并为单一数字**。未跑审核模块时不输出风险分
5. **人工复核建议** —— 每条 major 及以上发现对应一条可执行动作

---

## 仓库结构

```
skills/biomed-paper-review/     ← 交付物本体
├── SKILL.md                    主文档：流程、模块路由、统一 finding 契约、定位符规范、置信度算法
├── references/                 一个抽取层 + 六个审核模块的规则库
│   ├── 00-contracts.md                ★ 共享契约（证据登记表 / 三类记录 / 评分）
│   ├── 01-structured-extraction.md    M1 结构化抽取（前置层，不产 finding）
│   ├── 02-macro-logic.md              M2 宏观逻辑与完整性    ✅ 已填充
│   ├── 03-experimental-methods.md     M3 实验方法合规性      Peter
│   ├── 04-statistics.md               M4 统计学方法          ✅ 已填充
│   ├── 05-figures-and-charts.md       M5 图谱解析与图表规范  MY（敏怡）
│   ├── 06-ethics-compliance.md        M6 伦理合规            ✅ 已填充（待 Peter 复核）
│   └── 07-conclusions-discussion.md   M7 结论与讨论          ✅ 已填充
├── scripts/                    运行时确定性能力（标准库 + 预装科学栈）
│   ├── normalize_biomed_units.py      单位归一化，fail-closed
│   ├── statistical_forensics.py       p 反算 / CI 自洽 / 计数 / GRIM
│   ├── external_figure_validation.py  X1 外部核验，十四条检查 / 十个数据库
│   ├── ethics_compliance_check.py     伦理规范库筛查
│   ├── sequence_identifier_audit.py   序列 / HGVS / 登录号 / 引物候选审计
│   └── figure_integrity_audit.py      图像重复 / 拼接 / 均匀区块候选审计
├── resources/ethics_rules.json 伦理规范库：三法域 28 部规范 / 22 条要求
├── schemas/                    10 份 JSON Schema（模块间集成契约）
│   ├── finding.schema.json            ★ 六个审核模块共用
│   ├── evidence.schema.json           证据登记表
│   ├── key_data.schema.json           观测组
│   └── …（common / execution_scope / extraction_signal / system_limitation 等）
└── templates/review_report.md  报告渲染模板

datasets/                       测试语料：10 篇 PLOS 开放获取论文（CC-BY）· 非提交必需
├── manifest.json               每篇覆盖哪个审核维度、图表数量
└── papers/<slot>__<doi>/
    ├── meta.json               书目 + 图注索引（作为 ground truth）
    ├── fulltext.xml            JATS 全文
    └── figures/                逐图图像（max 1400px JPEG）

tools/fetch_papers.py           语料抓取脚本（可重跑）
tools/validate_schemas.py       契约校验器：schema + 工具产物 + 四个模拟实例
tools/fixtures/*.json           四个契约模拟实例（非论文端到端运行结果）
docs/architecture.md            架构说明：七个模块如何合成一个 Skill
docs/schema-migration.md        schema 逐字段迁移方案
docs/consistency-audit.md       一致性审计结果与 15 项核对表
docs/proposals/                 codex 评审循环产出的提案
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

**PDF 仅属于本地测试语料，不属于 Skill 提交包**。当前 `datasets/` 含 10 份 PDF，
其中 `toxicology` PDF 超过 10 MB；提交时不得把 `datasets/` 打入 Skill 包。
重新抓取可完整重建原始语料（含全分辨率图像与 PDF），仅用 Python 标准库、无需额外依赖：

```bash
python3 tools/fetch_papers.py
```

## 使用

采用 `SKILL.md` frontmatter + 渐进披露资源目录的通用 Agent Skill 格式。**skill 目录自包含**：
references、schemas、resources、templates 与五个运行时脚本都在
`skills/biomed-paper-review/` 之内。拷贝该目录可运行五个独立工具并读取全部运行时规则；
当前没有统一执行器，不能据此声称已获得论文输入到最终报告的端到端能力。
（`tools/validate_schemas.py` 是开发期契约校验器，不参与运行时，故留在仓库根。）

## 提交合规自查（对照 04-提交规范 / 05-自动评审规则）

| 检查项 | 状态 |
| --- | --- |
| `skills/` 下有且仅有一个 skill 目录 | ✅ `biomed-paper-review` |
| `SKILL.md` frontmatter 含合法 `name` / `description` | ✅ name 19 字符（≤64，小写连字符）；description 199 字符（≤1024，第三人称） |
| SKILL.md 正文建议 <500 行 | ⚠️ 当前正文超过 500 行；X1 连接器细节不得继续堆入主文档，应落到一层 reference |
| 文件引用只一层深（渐进披露） | ✅ SKILL.md 直接索引全部运行时 reference，不存在只能经另一 reference 才能发现的文件 |
| 单文件 ≤10MB | ✅ skill 本体内满足；⚠️ 若误打包 `datasets/`，其中一份 PDF 为 18,677,256 bytes，会超限 |
| 提交包体积 | ✅ `skills/biomed-paper-review/` 约 0.65 MiB；完整工作区超过 200 MiB，不得整仓提交 |
| `requirements.txt` | ✅ 无需额外安装 —— 已实现工具使用标准库或评测环境预装科学栈 |
| 结构化输入/输出 schema | ✅ `schemas/` 10 份 JSON Schema |
| 无诱导评分 / 注入语句 | ✅ |
| 沙箱可运行（2 核 / 4GB / 无 GPU / 单任务 12 小时） | ✅ 已实现工具均可 CPU 运行，无需 requirements.txt |
| 沙箱网络：**白名单制，开放公开科学数据源**（可申请追加） | ⚠️ 离线独立工具可运行；X1 connector 未交付，外部数据源不可得时的 `system_limitation` 契约已定义 |

## 分期范围

**一期（黑客松交付）**：离线核心必须仅凭**论文自身内容 + 通用规范库**跑通；公开科学数据源
作为可选增强层。连接器不可得、超时或返回不可解析响应时降级为 `system_limitation`，不得据此判稿件有问题。

当前 X1 的 `external` evidence、signal 与失败降级契约已落地，连接器脚本尚未落地，
不能声称已经完成数据库核验。原先统一推到“二期”的注册核验、标识符核验与数据登录号核验
应按 `docs/proposals/round-12-external-verification-layer.md` 的一期垂直切片实施；
M4 的 p 值反算、CI 自洽、计数/百分比与 GRIM 已实现为一期离线能力；图像取证已实现
网格对齐重复、列向背景不连续与异常均匀区块的候选筛查，旋转/镜像/缩放验证尚未实现。

## 当前状态

- ✅ 主框架：执行模式依赖图、五阶段流水线、三类记录契约、证据登记表、三项评分
- ✅ 10 份 JSON Schema + 报告模板；`tools/validate_schemas.py` 覆盖 schema、工具产物与四个模拟实例
- ✅ 四个契约模拟实例（RCT 完整审核形状 / 单图解读 / 定向伦理核查 / IC50 冲突）；不是论文端到端执行产物
- ✅ M1 结构化抽取规则（字段清单、七张设计路由表、pending 生命周期）
- ✅ M4 统计学（三步判定法 + 九张检验选择对照表）
- ✅ M6 伦理合规（三法域规范库 + 离线筛查器，待 Peter 复核）
- ✅ M7 结论与讨论（证据层级 × 主张层级对照表）
- ✅ 六个运行时确定性工具（含 X1 外部核验），均使用标准库或评测环境预装科学栈，均带自检
- 🚧 现有四个 fixtures 是契约模拟实例；尚无可复跑的论文输入→最终报告统一执行器与 uplift 结果 artifact
- ✅ M2 宏观逻辑（卓妍，938 行，已合入 main）
- ✅ M5 已收敛 Parser / Reviewer 产出者边界，并接住 X1 的五类外部 signal（§C.1，severity 待敏怡确认）
- 🚧 M3 已由框架层填充、待 Peter 复核；M5 的规则正反例与 41 张真实图像回归仍未完成
- ✅ 外部验证层 X1：connector 已交付（十四条检查、十个权威数据库，45 项自检对着线上接口通过）
- ✅ X1 录制响应 fixture 与离线回归已实现：`--record-fixtures` 录 21 条真实响应（124 KB），
  `--offline` 严格回放（未命中即报错，绝不回退到网络），无网环境 0 秒跑完 45 项自检。
  **边界**：离线全绿只证明解析与判定逻辑没坏，不证明上游接口仍可用 —— 上游改字段只有重新录制才会发现
- 🚧 uplift 基线实测：官方统一模型为 Qwen 系列，我们的 A/B 正是在 qwen3.8-max 上跑，但尚无三次中位数的正 uplift artifact
