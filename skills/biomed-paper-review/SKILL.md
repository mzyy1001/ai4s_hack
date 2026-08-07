---
name: biomed-paper-review
description: 生物医药论文预审与审稿辅助。输入一篇论文（PDF / JATS XML / 纯文本），先以资深同行评审身份通读全文提出问题，再由六本领域规则库分头复核，并用确定性计算与外部权威数据库交叉核验：重算表格分母与计数、GRIM、p 值与置信区间自洽性、剂量单位量纲；对照 Cellosaurus、Crossref、Europe PMC、ClinicalTrials.gov、HGNC、UniProt、PubChem、RCSB PDB 等 12 个数据库，核查被引文献是否已撤稿、细胞系是否被误认或污染、试验注册与主要结局是否被切换、基因符号与数据登录号是否真实存在。输出结构化证据表、可回溯到原文位置的分级审核发现、图表与表格解读、抽取覆盖率与复核置信度，以及分优先级的人工复核建议；外部源不可达或图像不可读时登记为系统限制，不归责稿件。支持完整审核 / 仅结构化抽取 / 图表解析 / 定向核查四种模式。当用户需要预审或复核生物医药论文与稿件、核验参考文献与标识符、检查统计方法与样本量报告、审查动物或人体伦理合规、或判断结论是否超出证据支撑时使用。
---

# 生物医药论文审稿辅助 Skill

## 0. 你是编排者，不是审稿人

**你自己不做逐条审阅。** 你的职责是把审阅**拆成多次独立的子会话**，
每个子会话带着**自己的审阅目标和自己那一本规则**去读同一篇论文，
最后由你汇总成契约化报告。

### 0.0 唯一的架构公理

> **分层隔离的是「审阅目标与推理上下文」，不是「论文正文」。**

裸模型本身就是很强的审稿人。把五千行规则压在一次上下文里会挤占注意力
（实测出现过八本规则库只读了一本），所以**目标必须分开**：一个子会话一个角色、
一本规则、一个干净的推理上下文。

但**正文不能跟着一起切**。同一篇真实论文、同模型、同全文的三条件实测：
裸模型（全文 + 开放提问）**63 条含 2 条 critical**；旧架构（发现层压成候选 →
专家只拿证据包）43 条、**0 条 critical**，且裸模型最强的两条一条未得；
本架构（各层拿全文）**96 条含 6 条 critical**，那七条深层问题 recover 6 条。

失效机理是**两次压缩、且第二次由第一次决定**：发现层把论文压成候选清单，
证据包又按该清单去正文取片段 —— 没人标注过的段落（构件示意图、克隆描述、品系来源）
没有任何一层读得到，漏了即结构性不可恢复。而且「隔离」本就是假的：
统计包已占全文 71%，主张包 52% —— 付了召回的代价，却没真的隔离。

**因此：全文对需要它的每一层开放；被隔离的只有目标、规则与推理上下文。**

### 0.1 用 `task` 工具创建子会话（这是本 Skill 的核心机制）

每个阶段都必须通过 `task` 工具真正创建一个**独立子会话**：

```
task(
  subagent_type = "general",        ← 用内置 general，不需要任何自定义 agent 文件
  description   = "<阶段名>",
  prompt        = "<该阶段的完整独立指令 + 它需要的全部材料>"
)
```

**已实测确认，勿再怀疑**：`subagent_type: general` 能创建返回独立 `sessionId`
的子会话；一条回复里可发多个 task 并发执行；同一 `task_id` 可续接且子会话记得上一轮；
不指定 model 时继承主会话模型；子会话看不到未显式传入的内容；子会话内可跑 bash 与读文件。

**三条硬规则**：

1. **不要指定 model 覆盖。** 子会话必须继承主会话模型，否则评测对比失效。
2. **子会话的 prompt 必须自足。** 它看不见你的上下文，你不写进 prompt 的东西它就没有。
3. **全文给到需要它的每一层。** 正文不是稀缺资源，注意力才是 ——
   隔离靠「一个子会话只有一个目标、一本规则」，不靠克扣正文。

### 0.2 执行图

```
主会话（你）
│
├── L0  task(general) → 全局审阅       **全文 + 极简提问，无规则库、无 schema、无清单**
│                                      ← 必须第一个跑，跑完才允许任何东西碰论文
│                                      产出 G-01…G-nn，直接进台账
│
├── L0b task(general) → 测绘与路由     全文 + 测绘指令（**不找问题**）
│                                      产出 paper_map / claim_map / experiment_map
│                                      + 图表清单 + 标识符收割 + 开哪几个模块
│
├── L1  task(general) → M2 宏观逻辑    **全文** + 02-macro-logic.md      + 路由给它的 G 条目
│      task(general) → M3 实验方法     **全文** + 03-experimental-methods.md + …
│      task(general) → M4 统计         **全文** + 04-statistics.md      + …
│      task(general) → M5 图表         **全文** + 05-figures-and-charts.md + …
│      task(general) → M6 伦理         **全文** + 06-ethics-compliance.md + …
│      task(general) → M7 结论         **全文** + 07-conclusions-discussion.md + …
│
├── L2  确定性工具 + X1 外部核验       主会话自己跑，不下放
│
├── L3  同一 task_id 续接各专家        喂确定性证据，让它们复议
│
├── L4  task(general) → 校正子会话     **全文** + 各专家产物 + G 条目 + 工具信号
│                                      多一项职责：审计有没有 G 条目不明不白消失
│
└── L5  主会话做契约归一与报告渲染
```

L0 的 prompt 里不得出现规则库、契约、schema、任何清单 —— 它就是裸模型条件本身。
**这条保证了本 Skill 的下限就是裸模型**：后面各层只能在它之上做加法，
或者带理由地驳回某一条，不能凭空让它变少。

### 0.3 并行执行（子会话彼此隔离，能并的必须并）

子会话之间**互不可见**，所以「L0 要干净」靠的是**它自己的 prompt 干净**，
不靠让别人等它。真正的依赖只有三条：

```
L0 ∥ L0b                       并行：互相看不见，不会污染
   ↓（都返回后）
M2 ∥ M3 ∥ M4 ∥ M5 ∥ M6         并行：五个模块之间无依赖
   ↓
M7                              串行：它要消费其他模块的结论
   ↓
L2 工具（主会话，多条命令并发）
   ↓
M2…M6 的续接复议                并行：同 task_id，互不依赖
   ↓
L4 校正 → L5 渲染               串行
```

**怎么真的并行**：在**同一条回复里一次性发出多个 `task` 调用**，运行时会并发执行；
一次发一个、等它回来再发下一个，就退化成串行了。实测：五个专家串行发起耗时约
是并行的数倍，而它们之间没有任何依赖。

关键路径 ≈ `max(L0, L0b)` + `max(M2…M6)` + `M7` + 工具 + `max(续接)` + `L4` + `L5`。

---

## 1. L0 · 全局审阅（整篇论文，极简约束）

```
task(subagent_type="general", description="L0 Global Review",
     prompt = 极简提问 + 论文全文)
```

**这一层必须最干净**：干净靠的是它自己的 prompt 里没有任何规则与清单，
不是靠让别的层等它。**可以与 L0b 并行发起**（子会话互不可见，不会污染）。

prompt 里**只放**：论文全文、图表清单、下面这段话。
**严禁**放入：规则库、契约、schema、候选类型枚举、任何形式的检查清单 ——
**任何清单都会变成天花板**。实测：发现层挂清单时，39 条候选几乎一一对应清单条目，
而裸模型在同一篇论文上最强的两条一条都没进池。清单本意是下限，实际成了上限。

指令全文（不要加料）：

> 你是该领域资深同行评审。通读这篇论文，把你会在审稿意见里提的问题**全部列出来**。
>
> 科学逻辑、实验设计、统计方法、图表与数据呈现、伦理合规、结论与证据匹配度、
> 报告完整性 —— 任何方面。**穷尽你能发现的所有问题。**
>
> 每条必须落到具体位置与具体内容（章节 / 图表 / 原文措辞），不要泛泛而谈。
> 每条给一个严重度：`critical` / `major` / `minor` / `info`。
> 拿不准的也提，标 `confidence: low`。
>
> 输出 JSON 数组，每条形如：
> `{"id":"G-01","statement":"…","locations":["Methods sec006","Fig 3A"],
>   "severity":"major","confidence":"high"}`

**这就是裸模型条件本身**，所以本 Skill 的下限被钉死在裸模型上。
G 条目**立刻**进 `candidate_resolution_log`，此后只能被显式处置，不能蒸发（见 §6）。

### 1.1 为什么不再有「发现层」

旧发现层同时做**实质审阅**与**测绘路由**，而测绘所需的结构化会挤掉审阅的开放性。
现已拆开：实质审阅上移为 L0（无约束，因此更强），测绘路由下沉为 L0b（纯机械，因此更省）。

**合规清单也不需要单独通道** —— M2/M4/M6 的规则库本身就是那些清单。
实测：双通道里的清单通道反而把「全文无精确 P 值 / 检验统计量 / CI / 效应量」
打包丢失，而 M4 规则库天然覆盖它。**清单归规则库，不归发现层。**

## 1b. L0b · 测绘与路由（不找问题）

```
task(subagent_type="general", description="L0b Map & Route",
     prompt = 测绘指令 + 论文全文)
```

> 你**不是审稿人**，这一轮不要提任何审稿意见，也不要评价论文好坏。
> 你只做三件事：
>
> 1. **测绘**：`paper_map`（分节与角色）、`experiment_map`（每个实验：模型/分组/
>    干预/终点/时间点/n）、`claim_map`（每条主张原文、位置、支撑它的 Results/图表）、
>    图表与表格清单。
> 2. **标识符收割**（给确定性工具用）：参考文献 DOI/PMID、注册号、细胞系名、
>    抗体货号与 RRID、基因/蛋白符号、登录号、物种品系、剂量与单位对。
> 3. **路由建议**：按 §2 的触发表，说明该开哪几个模块、每个模块的理由，
>    以及不开哪几个、为什么。
>
> 输出 JSON：`paper_map`、`experiment_map`、`claim_map`、`figure_inventory`、
> `identifier_harvest`、`routing_plan[]`。

L0b 的产物是**给工具和路由用的地图**，不是候选清单。它不产 finding，也不产 severity。

## 2. 路由：决定开哪几个子会话

**不默认跑满六个模块。** 按下表取并集，跑与不跑都要在报告里写明理由。

| 触发来源 | 规则 |
| --- | --- |
| 研究设计 | RCT / 队列 → M4、M6、M7；动物 → M3、M6；体外细胞 → M3；meta 分析 → M2、M4、M7 |
| 候选路由 | `suggested_route` 指向哪个模块就开哪个 |
| 工具信号 | 表格/p 值/CI 不符 → M4、M2；伦理项缺失 → M6；标识符异常 → M3 |

| 模块 | 规则库 | 拿到的材料 |
| --- | --- | --- |
| M2 宏观逻辑 | `references/02-macro-logic.md` | **全文** + 地图 + 索引 |
| M3 实验方法 | `references/03-experimental-methods.md` | **全文** + 地图 + 索引 |
| M4 统计 | `references/04-statistics.md` | **全文** + 地图 + 索引 |
| M5 图表 | `references/05-figures-and-charts.md` | **全文** + 图表清单 + 图像文件（若可读） |
| M6 伦理 | `references/06-ethics-compliance.md` + `06b-animal-model-ethics-enhancement.md` | **全文** + 地图 + 索引 |
| M7 结论 | `references/07-conclusions-discussion.md` | **全文** + 地图 + 各模块结论 |

第三列的「索引」只是起点提示，**不构成边界**（见 §3.1）。

完整路由表见 `references/00-routing.md`。

**指标不是「读满八本」**，而是路由召回率：本次要跑的模块对应的规则库一个不漏。
一篇纯生信论文不读伦理规则库是对的，不是缺陷。

## 3. L1 · 专家子会话（全文 + 自己那一本规则）

每个模块一次 `task(general)`。prompt 必须自足，包含五样东西：

```
① 角色与边界指令（见下）
② **论文全文** —— 不再是证据包
③ 索引：该模块的相关位置清单（起点，不是边界）
④ L0b 的地图（paper_map / experiment_map / claim_map）
⑤ 路由给它的 G 条目 + 已有工具信号
```

**③ 从「替代品」降级为「索引」**：过去的证据包是全文的替代物，
现在只是一句「这些位置已知相关，从这里开始看」。**专家有义务读全文**，
不得因为某处不在索引里就当它不存在。

角色指令（写进每个专家 prompt）：

> 你是 **<模块>** 领域的审稿专家。
> **先读规则库**：`<skill 目录>/references/<对应文件>`（用 read 工具读，路径见上表）。
>
> **规则库是你的镜片，全文是你的对象。** 你拿到了整篇论文：
> 需要跨节比对、需要回看 Methods 里的构件描述、需要核对图注与正文，就直接去读。
> **不要**把注意力全给规则库而不读论文，也**不要**读了论文却不用规则库 ——
> 你的价值恰恰在于「用这本规则去看整篇论文」，这是全局审阅那一层做不到的。
>
> 同时给你的还有**全局审阅（L0）已经提出的、属于你领域的条目**。对每一条，
> 你必须给出明确判定：`confirm`（并补齐证据与定级）/ `refine`（修正表述或定级，
> 说明理由）/ `refute`（驳回，**必须**给出反驳依据）/ `out_of_scope`（不属于你的领域）。
> **不得沉默略过任何一条。** 你可以驳回，但不能让它消失。
>
> 除此之外，**主动补充**你领域内 L0 没提到的问题 —— 这是你存在的意义。
>
> 工具信号是确定性事实但**没有严重度**：是否构成问题、多严重，由你结合影响判定。
> 你**不做**去重、聚簇、最终定级、报告渲染。
> 输出 JSON：`provisional_findings[]`（含 category / severity / statement /
> evidence_locations / source: `specialist_rule` | `confirms_global`）、
> `global_verdicts[]`（对每条 G 条目的判定与理由）、`requested_tool_checks[]`。

### 3.1 索引怎么切（起点，不是边界）

| 模块 | 索引指向 |
| --- | --- |
| M4 统计 | 统计方法段落、相关 Results、表格、图注统计量、样本量、检验、p 值、CI |
| M3 实验方法 | Methods 全节、试剂设备、样本来源、构件与克隆描述、品系来源 |
| M5 图表 | 图注、正文首次引用处、相关 Results |
| M6 伦理 | 研究设计摘要、受试者/动物描述、伦理声明、知情同意、注册信息 |
| M7 结论 | 主张原文、支撑它的 Results、关联表图、随访时长、研究人群、局限性 |
| M2 宏观逻辑 | `paper_map` + `claim_map` + 参考文献列表与正文引用位置 |

### 3.2 「拿不到」与「稿件没写」仍然是两回事

专家现在有全文，所以**「材料不在包里」这个借口没有了**。
但另一类限制仍然存在且必须如实登记：图像无视觉通道、补充材料未提供、
外部接口不可达。这些一律产 `system_limitation`，
**不得**当作「稿件没写」，也不得当作「稿件没问题」。

## 4. L2 · 确定性核验与 X1 外部核验（你自己跑，不交给子会话）

**主动扫描不可省。** 真正的增益往往来自裸模型根本不会想到去做的检查 ——
只要解析出结构化对象就跑，**不等任何候选**：

| 解析到 | 跑什么 |
| --- | --- |
| 互斥穷尽分类计数的表格 | `statistical_forensics` 的 `table_total` |
| 「计数 + 百分比」 | `count_percentage` |
| 「均值 + 整数量表 + n」 | `grim` |
| 检验统计量 + df + p | `test_statistic_p` |
| 点估计 + CI | `ci_estimate` |
| 细胞系名 / NCT 注册号 / 参考文献 DOI / 人类基因符号 | `external_figure_validation` |
| 图像文件 | `figure_integrity_audit` |
| 剂量单位对 | `normalize_biomed_units` |
| 动物实验（物种/麻醉/安乐死/3R） | `animal_model_compliance`（规则见 `references/06b-animal-model-ethics-enhancement.md`，产物交 M6） |

每次调用都要落到唯一终态：`executed` / `not_applicable` / `failed` / `skipped`，
后两者必须给理由。**不得让该跑的工具悄无声息地消失。**
退出码非 0 视为未完成，登记 `system_limitation`，
**禁止把空 stdout 解释为「未发现问题」**。

**中间文件写当前工作目录，禁止写 `/tmp`** —— 实测被运行时以
`permission requested: external_directory (/tmp/*); auto-rejecting` 拒绝，
整条取证链断掉。能走 stdin 就走 stdin。

```bash
if [ -z "${BIOMED_REVIEW_SKILL_DIR:-}" ]; then
  BIOMED_REVIEW_SKILL_DIR="$(git rev-parse --show-toplevel)/skills/biomed-paper-review"
fi
export BIOMED_REVIEW_SKILL_DIR

printf '%s' '[{"check":"table_total","counts":[12,18],"declared_total":28,"categories_exhaustive":true,"target":"Table 1"}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/statistical_forensics.py" --input -

printf '%s' '[{"check":"cell_line","cell_line":"MDA-MB-435","evidence_refs":["EV-001"]}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/external_figure_validation.py" --input -

python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/ethics_compliance_check.py" --input structured_result_v2.json
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/animal_model_compliance.py" --input structured_result_v2.json  # 仅动物实验论文
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/figure_integrity_audit.py" --input figures
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/normalize_biomed_units.py" --compare 'mg/mL' 'g/L'
printf '%s' '[{"check":"accession","accession":"NCT123","database":"clinicaltrials"}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/sequence_identifier_audit.py" --input -
```

### 4.1 L3 · 拿到工具结果后，**续接同一个专家子会话**

这是本架构最有价值的一环：让专家在看到确定性证据后**复议自己的判断**。

```
task(task_id = <该专家子会话的 id>,
     prompt  = "确定性核验结果如下：<工具输出>。
                请据此复议你上一轮的判定：哪些确认、哪些撤回、严重度是否调整。")
```

续接用**同一个 task_id**，子会话记得上一轮，**不必重发全文**（这也是续接
比新开会话便宜得多的原因）。

## 5. L4 · 校正子会话（全文 + 全部产物）

```
task(subagent_type="general", description="Reconciliation", prompt = …)
```

prompt 里放：**论文全文**、`paper_map`、`experiment_map`、`claim_map`、
L0 的全部 G 条目、各专家 `provisional_findings` 与 `global_verdicts`、
工具信号、`system_limitations`。**规则库全文不要放**（那会挤掉正文）。

### 5.0 大产出层必须落盘，只回传指针（实测教训）

L4 同时握有全文、几十条 G 条目与六个专家产物，**返回体积会超限**：
实测出现过 `truncated: true`（返回 42,049 字符后被截断）。那一次编排者自行
从落盘文件恢复没丢数据，但不能指望每次都恰好如此。

**因此凡产出可能超过约 3 万字符的子会话（L4 必然，L0 与各专家经常），
一律要求它：**

```
把完整 JSON 写入 <工作目录>/<阶段名>.json，
回复里**只**给：文件路径 + 计数摘要（各类条目数）+ 最重要的 3–5 条摘要。
不要把完整 JSON 内联回传。
```

主会话随后用 read 工具读该文件。**回传被截断 = 该层失败**，
必须重跑或从落盘文件恢复，**不得**把截断后的残缺产物当成完整结果继续往下走。

指令要点：

> 你有整篇论文，也有各专家的产物。你的任务有三件：
>
> **一、跨节矛盾。** 逐条核对：
> Abstract↔Results、Methods↔Results、Methods↔基线表、Results↔Tables、
> Results↔Figures、Tables↔Discussion、Discussion↔Conclusion、
> **构件设计↔归因主张**、随访时长↔安全性主张、研究人群↔外推主张、
> 注册记录↔稿件、参考文献↔引文核验结果。
>
> 典型（都真实出现过）：Methods 写纳入 ASA I–III 而基线表只有 II/III；
> 表里一个 p 值、Discussion 里另一个；随访 48 小时却称「未见严重并发症」；
> Discussion 称两套遗传系统结论一致，按年龄对齐后在成年鼠上恰恰相反。
>
> **二、合并去重。** 合并不同专家对同一处问题的重复条目，保留更具体的表述与定位。
>
> **三、G 条目审计（不可省）。** 逐条检查 L0 的每一个 G 条目：
> 它是否在最终结果里有明确归宿？若某条被所有专家忽略（没有任何 `global_verdicts`
> 覆盖它），**你必须自己给出判定**并写清理由；若被 `refute`，检查反驳依据是否成立。
> **任何 G 条目都不得不明不白地消失** —— 这是本层的硬性交付物。
>
> 输出 `reconciled_findings[]`、`cross_section_findings[]`、
> `candidate_resolution_log[]`、`global_audit[]`（每条 G 的最终归宿与理由）。

## 6. 候选生命周期与**加法保证**（硬性要求）

### 6.1 每个条目必须有归宿

L0 的 G 条目、专家新提的条目、工具与外部核验信号，**一律进同一张台账**：

```
promoted_to_finding | merged | rejected | unresolved | blocked_by_system_limitation
```

- `rejected` **必须**给 `rejection_reason`
- `promoted_to_finding` 必须指向 `final_finding_id`；`merged` 必须指向 `merged_into`
- **定位不到证据记 `unresolved`，不得记 `rejected`** —— 那是我们没定位到，不是问题不存在

此前的实现会在发现与渲染之间静默丢掉有效问题，这张台账就是为了让丢失可见。

### 6.2 加法保证（本架构的核心承诺）

> **最终结果 ⊇ L0 全局审阅的结论，减去且仅减去被显式驳回并给出理由的那些。**

Skill 相对裸模型只能做加法，或者**带论证地**做减法，不得凭空缩水。
落实到检查项，报告渲染前必须自检：

1. 每一条 G 都在 `global_audit[]` 里有终态；
2. `rejected` 的每一条都有 `rejection_reason`，且理由是**反驳依据**，
   不是「专家没提到」「不在我的模块范围」；
3. `severity` 被下调的 G 条目，必须记录下调理由；
4. 若最终 finding 数**少于** G 条目数，报告里必须显式解释差额去哪了。

**做不到上述任何一条，就不要渲染报告** —— 直接把缺口写进 `system_limitations`。

## 7. L5 · 契约归一与报告渲染（你自己做，不交给子会话）

**到这一步才套完整契约**，此前不得用 schema 约束发现：

```
证据登记表归一 → finding schema 归一 → 去重 → 聚簇
→ severity 协调 → 置信度 → 覆盖率 → 报告渲染
```

完整契约见 `references/00-contracts.md`，机器校验以 `schemas/*.json` 为准；
子会话只需 `references/00-runtime-contract.md` 的最小集合。

**每条 finding 标注来源**：`global_review` / `specialist_rule` / `deterministic_tool` /
`external_validation` / `cross_section_reconciliation` / `multiple`。

这张分布是**评估本架构是否值得**的唯一依据：只来自 `global_review` 的
= 裸模型本来就有的，**不算增益**；其余四类独有的才是**真增益**。
若增益很小，结论是**裁剪规则库**，不是继续加规则。

**`evidence_refs[]` 必须逐条特异**（契约 §1.4.1）：实测有过 60 条 finding
里 57 条挂同一组 24 条引用 —— 形式合规而可审计性归零。渲染前自检：
**过半 finding 共享相同引用列表 = 霰弹式，必须收窄。**

### 7.1 必须输出运行时遥测

**字段名逐字照抄下表，不得自造同义词。** 实测教训：曾输出
`candidate_count_discovery` 这类旧名而漏掉 `additive_guarantee_held` ——
结果是**加法保证实际成立，却没有被机器可读地断言**，等于没证。
渲染前先自检：下列每个键都在吗？缺一个就补，不要改名。

必填键：`child_sessions` `task_calls` `continuations` `modules_run`
`modules_skipped` `references_required` `references_read` `routing_recall`
`tool_execution_recall` `global_findings_count` `global_findings_confirmed`
`global_findings_refuted` `global_findings_unresolved`
`additive_guarantee_held` `findings_added_beyond_global`
`finding_origin_breakdown`

```json
{"runtime_utilization":{
  "child_sessions": 5, "task_calls": 6, "continuations": 1,
  "modules_run": ["M4","M6","M7"], "modules_skipped": {"M3":"无体外/动物成分"},
  "references_required": ["04-statistics","06-ethics-compliance","07-conclusions-discussion"],
  "references_read": ["04-statistics","06-ethics-compliance","07-conclusions-discussion"],
  "routing_recall": 1.0, "tool_execution_recall": 1.0,
  "global_findings_count": 63, "global_findings_confirmed": 58,
  "global_findings_refuted": 3, "global_findings_unresolved": 2,
  "additive_guarantee_held": true,
  "findings_added_beyond_global": 21,
  "finding_origin_breakdown": {"global_review":58,"specialist_rule":9,
    "deterministic_tool":3,"external_validation":6,"cross_section_reconciliation":3}}}
```

**若 `child_sessions` 为 0，说明分层没有真的发生** —— 那是执行失败，
不是「架构无效」，必须在报告里如实写明。

**若 `additive_guarantee_held` 为 false**，说明有 G 条目在管线里蒸发了 ——
同样是执行失败，必须写明是哪几条、卡在哪一层。

---

## 8. 执行模式

默认 `full_review`。用户只要一张图或一个数值时**不得**自动跑完整审核。

| 模式 | 开哪些子会话 | risk_score | 置信度字段 |
| --- | --- | --- | --- |
| `full_review` | L0 + L0b + 路由到的模块 + 校正 | 完整 | `review_confidence` |
| `structured_extraction` | 仅 L0b 测绘 + 抽取（**不跑 L0**） | **不输出** | `output_confidence` |
| `figure_analysis / interpretation_only` | 仅图解析 | **不输出** | `output_confidence` |
| `figure_analysis / figure_review` | L0b + M5 | partial | `review_confidence` |
| `targeted_check` | L0b + 选定模块 | partial | `review_confidence` |

**只有 `full_review` 跑 L0**。抽取与定向核查不需要全局审阅，跑它是浪费；
但也因此，这些模式**不享有 §6.2 的加法保证**，报告里必须写明这一点。

`review_confidence` 与 `output_confidence` **互斥**。partial 分数禁止与
`full_review` 分数并列比较。任何模式都要输出 `execution_scope`、
`coverage_breakdown`、`all_system_limitations[]`、`runtime_utilization`。

## 9. 边界声明（必须原样写入报告）

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查
> 与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。**
> 本 Skill 的任何评分均为筛查信号，不构成录用、退稿或发表决定。

**证据可审计**：最终 finding 必须有 `present`（含 locator）/ `absence`
（检索范围 + 检索词 + 结果）/ `external`（端点、查询、时间、响应 hash）三型之一的证据。
**绝不为不存在的内容伪造引文。** 但方向不能搞反 —— 证据要求用来**验证**发现，
不是用来**减少**发现。

M1 前置抽取层用 `references/01-structured-extraction.md`，它**不产 finding**，
职责是抽出字段与可核验标识符，供专家与外部核验使用。
