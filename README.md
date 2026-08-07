# 生物医药论文 AI 审稿 Skill

**交付物**：一个自包含的 Agent Skill 包 → [`skills/biomed-paper-review/`](skills/biomed-paper-review/)

输入一篇生物医药论文（JATS XML / PDF / 纯文本），做两件事：

1. **抽成可复用的结构化事实表** —— 研究设计、受试对象、干预分组、测量与终点、
   关键数值、主张清单与各类声明，每个字段都带适用性、必要性、状态与原文证据引用。
2. **审稿**：以资深同行评审身份通读全文，再由六本领域规则库分头复核，
   并以**确定性计算**与**12 个外部权威数据库**交叉核验；
   图谱模块在有视觉通道时**从原图**抽数值并定位回图号/面板/页码。

输出结构化结果表、可回溯到原文位置的分级发现、抽取覆盖率与复核置信度，
以及分优先级的人工复核建议。抽取与审稿可分开用（`structured_extraction` 模式）。

> 本分支（`main`）只放交付物本体。开发工作区 —— 测试语料、评测工具、实验记录、
> 设计文档与全部实跑产物 —— 在 [`dev`](../../tree/dev) 分支。

---

## 一、它解决什么问题，以及为什么这样解决

裸模型本身就是**很强的审稿人**。所以真正的问题不是「怎么让模型会审稿」，
而是「**挂上 Skill 之后，怎么保证比不挂更好**」。

这件事我们做砸过一次，值得写在最前面。

### 失败的那一版：把论文压成候选清单

第一版架构是：发现层通读全文 → 压成候选问题清单 → 每个专家只拿按清单切出来的证据包。
听起来很合理，实测却**比裸模型更差**：

| 同一篇真实论文、同一模型、同一份全文 | 发现数 | critical |
| --- | --- | --- |
| 裸模型（全文 + 开放提问） | 63 | 2 |
| **旧架构**（发现层压候选 → 专家拿证据包） | 43 | **0** |
| **现架构**（每层都拿全文） | **96** | **6** |

失效机理是**两次压缩、且第二次由第一次决定**：发现层把论文压成清单，
证据包又按清单去正文取片段 —— 于是**没人标注过的段落根本没有任何一层读得到**。
裸模型抓到的最深两条（敲入等位基因同时是全长 RAGE-null，使所谓「独立遗传学验证」
自带混杂；单一 7 dpi 时间点撑不起「加速再生」），旧架构一条都没有。

而且「隔离」本就是假的：切出来的统计包已占全文 71%，主张包 52% ——
**付了召回的代价，却没真的隔离。**

### 现在的架构公理

> **分层隔离的是「审阅目标与推理上下文」，不是「论文正文」。**

```
L0   全局审阅    全文 + 极简提问，无规则库 / 无 schema / 无清单
                 └ 这就是裸模型条件本身 → Skill 的下限被钉死在裸模型上
L0b  测绘与路由  全文，只产地图与标识符，不找问题
L1   M2–M7      **各拿全文** + 自己那一本规则；对 L0 的每一条必须表态
L2   确定性工具 + X1 外部核验
L3   同 task_id 续接，让专家看到确定性证据后复议
L4   校正子会话  **也拿全文**；审计有没有 L0 条目不明不白消失
L5   契约归一与报告渲染
```

**加法保证**：最终结果 ⊇ L0 的结论，减去且仅减去被显式驳回并给出理由的条目。
实测成立 —— L0 产出 70 条，60 条升为 finding、17 条合并、2 条因系统限制阻塞
（均写明理由）、**0 条被驳回、0 条蒸发**。

### 增益只可能来自两处

纯文本的内部一致性检查，裸模型本来就会做 —— 那部分的 uplift 结构上只能是零或负。
真正的增益只能来自模型**结构上做不到**的事：

**1. 确定性计算。** 例：某临床 RCT 的 Table 5 标注 `*ITT`，但均值 43.68±3.5 在
整数量表、n=39 下**数学上不可能**，只与 n=34/37/38 相容 —— 而 n=34 恰是完成者数。
GRIM 类算术**证伪了一个方法学标签**，这是纯阅读做不到的。

**2. 外部权威数据。** 例：某论文 Introduction 引用 `10.1002/jcp.26311` 支撑主张，
而该文献已于 **2024-08-26 撤稿**。撤稿晚于被审论文四年，稿件里没有、元数据里没有、
模型训练语料里也不可能有 —— **只能靠查库**。
（已用 Crossref `updated-by` 与 Europe PMC `Retraction in` 双向复核。）

`scripts/external_figure_validation.py`（X1）按需查询 **12 个数据库、14 项检查**：
Cellosaurus、ClinicalTrials.gov、Europe PMC、Crossref、UniProt、ChEMBL、PubChem、
RCSB PDB、HGNC、SciCrunch/RRID、NCBI E-utilities、PRIDE。
**不预置任何数据集**：稿件里真的出现某个标识符，才发起那一次查询。

外部源不可达时一律产 `system_limitation`，**绝不**变成 finding ——
「查不到」不等于「论文错」。

### 图表读取：有视觉通道就读原图，没有就诚实降级

M5 的图谱解析（Stage 3 Figure Parser）**从图像本身**抽实验条件与关键数值，并定位回原图：

- **图像来源优先级**：`original_figure_file > extracted_pdf_figure >
  rendered_pdf_page > text_only_caption`；
- **数值证据分级**：`explicit_main_text > explicit_table > explicit_figure_caption >
  axis_readable > pixel_estimated`，且 `provenance.source_type` 如实标注；
- **像素估读的硬性约束**：一律 `extraction_confidence: low`、**必须写成区间**
  （禁止点值）、置 `manual_review_needed`；对数轴须先确认轴类型再读数；
  误差棒不得直接当 SD/SEM；星号阈值必须回查图注定义；
- **原图定位**：每条 `figure_record` 给出图号、面板、PDF 页码与首次引用位置。

**图像确实取不到时不假装看过图**（未随稿提供、格式不可读等）：
登记 `system_limitation(figure_unreadable)`，退化为图注 / 正文 / 源 XML 交叉核验 +
`figure_integrity_audit.py` 的确定性像素审计（重复 / 拼接 / 异常均匀区块），
并在报告中写明本次未覆盖像素级判据。该降级路径带专门自检。

### 结构化抽取：不只是审稿的前置，本身就是可复用产物

`structured_result` 是一份**机器可消费的论文事实表**，按 `structured_result.schema.json`
组织，实测一篇真实论文抽出约 16 KB：

| 字段族 | 内容 |
| --- | --- |
| `article_design` | 研究设计族/类型（如 `experimental` / `in_vivo_animal`）与判定依据 |
| `population` | 受试对象、纳排、样本量口径 |
| `design` | 分组、干预、对照、随机化与盲法 |
| `measurement` | 测定方法、终点、时间点 |
| `key_data` | 关键数值，带分组键（实验 / 组别 / 比较 / 时间点 / 终点）与规范观测 |
| `conclusion.claims[]` | 逐条主张（`CLM-01`…），供 M7 做证据层级比对 |
| `declarations` | 伦理、注册、知情同意、利益冲突、数据可得性 |

**每个字段都带四件套**：`applicability`（是否适用）、`requiredness`（是否必填）、
`status`（reported / not_reported / parse_failed）、`evidence_refs`（原文出处）。
所以「没写」与「我们没抽到」在数据结构层面就是两回事，不会混为一谈。

实测字段解析率 **22/23 = 95.7%**。`extraction_coverage` 总分会低于此值，
因为它同时计入图像可读性与补充材料可得性 —— 那两项受运行环境限制，
**不是抽取失败**，且各自单独列出，不与字段解析率混算。

---

## 二、最小复现步骤

### 1. 离线自检（无需网络、无需模型、无需安装）

```bash
cd skills/biomed-paper-review
for f in scripts/*.py; do python3 "$f" --selftest; done
```

预期：七个脚本全部通过。**这一步不需要任何第三方依赖。**

### 2. X1 外部核验的离线回放

```bash
python3 scripts/external_figure_validation.py --offline --selftest
```

严格回放已录制的真实响应；未命中即报错，**绝不回退到网络**。
边界：离线全绿只证明解析与判定逻辑没坏，**不证明上游接口仍可用**。

### 3. 联网核验单个标识符（可选，需白名单网络）

```bash
# 细胞系误认（Cellosaurus）
printf '%s' '[{"check":"cell_line","cell_line":"MDA-MB-435","evidence_refs":["EV-001"]}]' \
  | python3 scripts/external_figure_validation.py --input -

# 被引文献是否已撤稿（Crossref / Europe PMC）
printf '%s' '[{"check":"cited_retracted","doi":"10.1002/jcp.26311","evidence_refs":["EV-001"]}]' \
  | python3 scripts/external_figure_validation.py --input -
```

### 4. 只跑结构化抽取（不产 finding，分钟级）

```bash
opencode run --dir . --model <统一模型> \
  "请使用 biomed-paper-review skill，模式 structured_extraction：
   只抽结构化结果，不做审核判定、不产 finding、不输出风险分。"
```

产出 `structured_result`（含字段解析率）与 `output_confidence`。
**该模式不输出 `manuscript_risk_score`** —— 没跑审核模块就给风险分是无源之水。

### 5. 跑一次完整审核（需 opencode + 模型凭据）

```bash
mkdir -p run && cd run
curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11856280/fullTextXML" -o paper.xml
mkdir -p .claude/skills && cp -R ../skills/biomed-paper-review .claude/skills/
opencode run --dir . --model <统一模型> \
  "请使用 biomed-paper-review skill 对当前目录的论文做完整审核（full_review）。"
```

产出 `review_report.json`（机器可校验）与 `review_report.md`（人读）。

**运行特征（实测，qwen3.8-max）**：完整审核一篇真实论文约 80–110 分钟，
其中六个专家子会话**并行**约 7 分钟（串行约需 60 分钟）——
关键路径是 `max(各波次)` 而非求和，并行化把总耗时从 2h20m 压到 1h48m。
定向核查与图表解析模式为分钟级。

---

## 三、包内结构

```
skills/biomed-paper-review/
├── SKILL.md                    唯一入口：编排流程、模块路由、共享契约（499 行）
├── references/                 11 份规则库（00 契约 / 路由 / 运行时；01 抽取；02–07 六个审核模块）
├── scripts/                    7 个确定性工具，全部带 --selftest
│   ├── statistical_forensics.py      5 项统计取证（table_total / GRIM / p 反算 / CI / 计数）
│   ├── external_figure_validation.py X1 外部核验：12 库 / 14 检查
│   ├── ethics_compliance_check.py    伦理规范库筛查（三法域）
│   ├── animal_model_compliance.py    动物福利红线与 3R 审计
│   ├── sequence_identifier_audit.py  序列 / HGVS / 登录号 / 引物
│   ├── figure_integrity_audit.py     图像重复 / 拼接 / 异常均匀区块
│   └── normalize_biomed_units.py     单位归一化，fail-closed
├── schemas/                    12 份 JSON Schema（模块间集成契约）
├── resources/                  伦理规范库 + X1 离线回放 fixture
└── templates/review_report.md  报告渲染模板
```

**自包含**：包内不引用任何包外路径，全部内部引用可解析。

**依赖：不提供 `requirements.txt`，且这是有意的。**
六个脚本纯标准库；`figure_integrity_audit.py` 可选用 `numpy` + `Pillow`
（仅像素级审计需要），缺失时登记 `system_limitation(figure_unreadable)` 后
**正常退出（exit 0）**，其余审核不受影响 —— 该降级路径带专门自检。
给了 `requirements.txt` 反而等于请求沙箱执行一次 pip 安装：
白名单网络下安装失败会把「一个可选检查降级」升级成「整次运行的风险」。

---

## 四、提交合规自查

对照 `04-提交规范` 与 `05-自动评审规则说明`：

### L0 合规硬筛

| 检查项 | 状态 |
| --- | --- |
| `skills/` 下有且仅有一个 skill 目录 | ✅ `biomed-paper-review` |
| `SKILL.md` frontmatter `name` 合法 | ✅ `biomed-paper-review`，19 字符，小写连字符（≤64） |
| `SKILL.md` frontmatter `description` 合法 | ✅ 473 字符（≤1024），第三人称，写清「做什么 + 何时使用」，含触发关键词 |
| 提交包大小 | ✅ **936 KB**，最大单文件 136 KB |
| 依赖可装 | ✅ 无 `requirements.txt` → 使用预装科学栈（见 §三） |
| 安全红线：无诱导评分 / 无注入语句 | ✅ |
| 原创性 / 课题相关性 | ✅ 自建架构与规则库，非改写公开 skill |
| 课题匹配 | ✅ 已在提交表单选定官方课题 |
| 仓库为私有 + 邀请 `synmatai-hackathon` | ✅ 已完成 |

### L1 静态质量

| 检查项 | 状态 |
| --- | --- |
| 正文 <500 行 | ✅ **499 行** |
| 引用只一层深（渐进披露） | ✅ SKILL.md 直接索引全部 reference，无二级跳转 |
| 输入/输出 Schema 明确 | ✅ 12 份 JSON Schema；`structured_result` 为可被他项目直接消费的事实表（字段解析率 22/23） |
| 工程健壮性：无硬编码路径 | ✅ 已在隔离目录验证（无仓库上下文亦可跑通自检） |
| 正文语言建议中文 | ✅ SKILL.md 与多数规则库为中文（M3 与 06b 为英文） |
| 具体使用示例 | ✅ 见 §二最小复现步骤 |

### L2 沙箱实战（uplift 消融）

评分看的是**相对无 skill 基线的提升**。本架构对此做了一条结构性设计：
**L0 全局审阅就是裸模型条件本身**（全文 + 极简提问、无任何规则与清单），
再由加法保证约束「只能加、不能凭空减」。
换言之，**Skill 的下限被钉死在基线上**，增益来自 L1–L4 之上叠加的部分。

**已知局限（如实声明）**：

- 实测均在 `qwen3.8-max` 上完成；跨模型行为未逐一验证。
- 完整审核耗时约 80–110 分钟（并行后）；时间受限时可用
  `targeted_check` / `figure_analysis` 等分级模式，分钟级返回。

---

## 五、边界声明（必须原样写入每份报告）

- 本工具**不替代同行评审**，不产出录用/退稿决定；
- 每条发现必须可回溯到论文原文位置，**不得**凭生成内容立论；
- 「未报告」不等于「未实施」；「我们没拿到」不等于「稿件没写」；
- 工具失败、外部源不可达、图像无法读取，一律登记 `system_limitation`，**不归责稿件**；
- 三项评分（稿件风险分 / 抽取覆盖率 / 复核置信度）**互不替代**，不得合并为单一数字；
  partial 分数不得与完整审核分数并列比较。
