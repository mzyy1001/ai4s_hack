---
name: biomed-paper-review
description: 生物医药论文结构化抽取与审稿辅助。输入一篇论文（PDF / JATS XML / 纯文本），输出结构化证据表、图表解读与原图定位、多维审核发现、抽取覆盖率与复核置信度，以及分优先级的人工复核建议。支持四种执行模式（完整审核 / 仅结构化抽取 / 图表解析 / 定向核查）。当用户需要预审、复核生物医药论文或稿件，或需要抽取论文中的实验条件、剂量响应曲线、统计图、实验流程图、显微图的关键数值时使用。
---

# 生物医药论文审稿辅助 Skill

## 0. 你是编排者，不是审稿人

**你自己不做逐条审阅。** 你的职责是把审阅**拆成多次独立的子会话**，
每个子会话只拿它那一份材料和那一本规则，最后由你汇总成契约化报告。

为什么必须这样：裸模型本身就是很强的审稿人，而把五千行规则压在一次上下文里
只会挤占注意力 —— 实测出现过挂 Skill 反而比裸模型少提问题且是真子集，
也出现过八本规则库只读了一本。**分开跑，每个通道都清爽，才可能超过裸模型。**

### 0.1 用 `task` 工具创建子会话（这是本 Skill 的核心机制）

每个阶段都必须通过 `task` 工具真正创建一个**独立子会话**：

```
task(
  subagent_type = "general",        ← 用内置 general，不需要任何自定义 agent 文件
  description   = "<阶段名>",
  prompt        = "<该阶段的完整独立指令 + 它需要的全部材料>"
)
```

**已实测确认的运行时能力**（勿再怀疑）：

| 能力 | 状态 |
| --- | --- |
| `subagent_type: general` 创建独立子会话 | 可用，返回独立 `sessionId` |
| 一次调用里顺序创建多个子会话 | 可用 |
| **用同一个 task_id 续接同一子会话** | 可用，子会话记得上一轮 |
| 子会话继承主会话模型（不指定 model 时） | 可用 |
| 子会话看不到主会话未显式传入的内容 | 已验证隔离 |
| 子会话内可跑 bash / 读文件 | 可用 |

**三条硬规则**：

1. **不要指定 model 覆盖。** 子会话必须继承主会话模型，否则评测对比失效。
2. **子会话的 prompt 必须自足。** 它看不见你的上下文，你不写进 prompt 的东西它就没有。
3. **不要把全文塞给每个子会话。** 那样等于没分层，只是多花了钱。

### 0.2 执行图

```
主会话（你）
├── task(general) → 发现子会话        全文 + 发现指令，**不给规则库**
├── task(general) → M4 统计子会话     统计包 + 04-statistics.md
│      └── 同一 task_id 续接          喂入确定性工具结果，让它复议
├── task(general) → M6 伦理子会话     伦理包 + 06-ethics-compliance.md
├── task(general) → M7 结论子会话     主张包 + 07-conclusions-discussion.md
└── task(general) → 校正子会话        各子会话产物 + 论文地图，**不给全文**
        ↓
   主会话做契约归一与报告渲染
```

**M2–M6 之间无依赖，可连续发起；M7 必须在它们之后**（它要消费其他模块结论）。

---

## 1. Layer 1 · 发现子会话

```
task(subagent_type="general", description="Discovery",
     prompt = 发现指令 + 论文全文)
```

发现子会话的 prompt 里**只放**：论文全文、图表清单、下面这段指令。
**不要**放契约、schema、M2–M7 规则库 —— 那会让结构化取代发现。

指令要点（写进 prompt）：

> 你是资深同行评审。通读全文，把你会在审稿意见里提的问题**全部列出来**。
> **优先召回**：拿不准的也列，标 `confidence: low`。**不要**为了给证据而放弃提出问题，
> 定位不到就把 `locations` 留空。不需要给严重度，不需要套 schema。
>
> 至少扫：表格分母与计数是否自洽、同一结局在不同位置数值/P 值是否一致、
> 结论是否超出数据、纳入标准与基线表是否矛盾、盲法是否可能被识破、
> 安全性结论与随访时长是否匹配、样本量有无依据、多重比较有无校正、
> 伦理与注册信息是否齐全。
>
> 只有同时看两个 section 才能发现的矛盾（如 Methods 写纳入 ASA I–III、
> 基线表却只有 II/III），`suggested_route` 记 `["reconcile"]`。
>
> 输出 JSON：`paper_map`、`study_design`、`followup_duration`、`n_total`、
> `experiment_map`、`claim_map`、`candidate_issues[]`。
> 候选形如 `{"id":"CAND-01","description":"…","locations":[],
> "confidence":"medium","suggested_route":["statistics"]}`。

## 2. 路由：决定开哪几个子会话

**不默认跑满六个模块。** 按下表取并集，跑与不跑都要在报告里写明理由。

| 触发来源 | 规则 |
| --- | --- |
| 研究设计 | RCT / 队列 → M4、M6、M7；动物 → M3、M6；体外细胞 → M3；meta 分析 → M2、M4、M7 |
| 候选路由 | `suggested_route` 指向哪个模块就开哪个 |
| 工具信号 | 表格/p 值/CI 不符 → M4、M2；伦理项缺失 → M6；标识符异常 → M3 |

| 模块 | 规则库 | 证据包 |
| --- | --- | --- |
| M2 宏观逻辑 | `references/02-macro-logic.md` | 跨节包、参考文献包 |
| M3 实验方法 | `references/03-experimental-methods.md` | 方法包、标识符包 |
| M4 统计 | `references/04-statistics.md` | 统计包 |
| M5 图表 | `references/05-figures-and-charts.md` | 图包 |
| M6 伦理 | `references/06-ethics-compliance.md` | 伦理包 |
| M7 结论 | `references/07-conclusions-discussion.md` | 主张包 |

完整路由表见 `references/00-routing.md`。

**指标不是「读满八本」**，而是路由召回率：本次要跑的模块对应的规则库一个不漏。
一篇纯生信论文不读伦理规则库是对的，不是缺陷。

## 3. Layer 2 · 专家子会话

每个模块一次 `task(general)`。prompt 必须自足，包含四样东西：

```
① 角色与边界指令（见下）
② 该模块的证据包（只放相关段落，不放全文）
③ 轻量全局上下文
④ 路由给它的候选 + 已有工具信号
```

**轻量全局上下文**不能省，否则专家会做出局部正确、整体荒谬的判断：

```json
{"study_design":"randomised controlled trial","n_total":89,
 "followup_duration":"48 hours","experiment_id":"EXP-02",
 "supports_claims":["CL-05"],"related_tables":["Table 3"]}
```

角色指令（写进每个专家 prompt）：

> 你是 **<模块>** 领域的审稿专家。
> **先读规则库**：`<skill 目录>/references/<对应文件>`（用 read 工具读，路径见上表）。
> 你**看不到全文**，这是有意的。判断所需材料不在包里时，产出 `unresolved`
> 并写清缺什么 —— **不要臆测，也不要当作稿件没写**。
> 「我们没拿到」和「稿件没写」是两回事。
> 工具信号是确定性事实但**没有严重度**：是否构成问题、多严重，由你结合影响判定。
> 你**不做**去重、聚簇、最终定级、报告渲染。
> 输出 JSON：`provisional_findings[]`（含 category / severity / statement /
> evidence_locations / candidate_ids）、`candidate_verdicts[]`、`requested_tool_checks[]`。

### 3.1 证据包怎么切

| 包 | 放什么 |
| --- | --- |
| 统计包 | 统计方法段落、相关 Results、表格、图注统计量、样本量、检验、p 值、CI |
| 方法包 | Methods 全节、试剂设备、样本来源 |
| 标识符包 | 细胞系、抗体/RRID、基因符号、物种品系、登录号、变异写法 |
| 图包 | 图注、正文首次引用处、相关 Results |
| 伦理包 | 研究设计摘要、受试者描述、伦理声明、知情同意、注册信息、各类声明 |
| 主张包 | 主张原文、支撑它的 Results、关联表图、随访时长、研究人群、局限性 |
| 跨节包 | `paper_map` + `claim_map` + 涉及的两个及以上 section 的相关段落 |
| 参考文献包 | 参考文献列表、DOI、正文引用位置 |

## 4. Layer 3 · 确定性核验（你自己跑，不交给子会话）

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

### 4.1 拿到工具结果后，**续接同一个专家子会话**

这是本架构最有价值的一环：让专家在看到确定性证据后**复议自己的判断**。

```
task(task_id = <该专家子会话的 id>,
     prompt  = "确定性核验结果如下：<工具输出>。
                请据此复议你上一轮的判定：哪些确认、哪些撤回、严重度是否调整。")
```

续接用**同一个 task_id**，子会话记得上一轮，不必重发证据包。

## 5. Layer 4 · 校正子会话

```
task(subagent_type="general", description="Reconciliation", prompt = …)
```

prompt 里放：`paper_map`、`experiment_map`、`claim_map`、候选清单、
各专家 `provisional_findings`、工具信号、`system_limitations`。
**不要放全文，不要放规则库全文。**

指令要点：

> 各专家只看到了论文的一部分，因此有一类问题他们结构上不可能发现：跨节矛盾。
> 那是你唯一的任务。逐条核对：
> Abstract↔Results、Methods↔Results、Methods↔基线表、Results↔Tables、
> Results↔Figures、Tables↔Discussion、Discussion↔Conclusion、
> 随访时长↔安全性主张、研究人群↔外推主张、注册记录↔稿件、参考文献↔引文核验结果。
>
> 典型（都真实出现过、分块审阅必然漏掉）：Methods 写纳入 ASA I–III 而基线表只有 II/III；
> 表里一个 p 值、Discussion 里另一个；随访 48 小时却称「未见严重并发症」。
>
> 另外两件事：合并不同专家对同一处问题的重复条目；**结清每一个候选**。
> 输出 `reconciled_findings[]`、`cross_section_findings[]`、`candidate_resolution_log[]`。

## 6. 候选生命周期（硬性要求）

每个发现候选**必须**有归宿：

```
promoted_to_finding | merged | rejected | unresolved | blocked_by_system_limitation
```

- `rejected` **必须**给 `rejection_reason`
- `promoted_to_finding` 必须指向 `final_finding_id`；`merged` 必须指向 `merged_into`
- **定位不到证据记 `unresolved`，不得记 `rejected`** —— 那是我们没定位到，不是问题不存在

此前的实现会在发现与渲染之间静默丢掉有效问题，这张台账就是为了让丢失可见。

## 7. Layer 5 · 契约归一（你自己做，不交给子会话）

**到这一步才套完整契约**，此前不得用 schema 约束发现：

```
证据登记表归一 → finding schema 归一 → 去重 → 聚簇
→ severity 协调 → 置信度 → 覆盖率 → 报告渲染
```

完整契约见 `references/00-contracts.md`，机器校验以 `schemas/*.json` 为准；
子会话只需 `references/00-runtime-contract.md` 的最小集合。

**每条 finding 标注来源**：`discovery` / `specialist_rule` / `deterministic_tool` /
`external_validation` / `cross_section_reconciliation` / `multiple`。
若绝大多数来自工具与外部核验，说明规则库贡献有限，应据此**裁剪**而非继续加规则。

### 7.1 必须输出运行时遥测

```json
{"runtime_utilization":{
  "child_sessions": 5, "task_calls": 6, "continuations": 1,
  "modules_run": ["M4","M6","M7"], "modules_skipped": {"M3":"无体外/动物成分"},
  "references_required": ["04-statistics","06-ethics-compliance","07-conclusions-discussion"],
  "references_read": ["04-statistics","06-ethics-compliance","07-conclusions-discussion"],
  "routing_recall": 1.0, "tool_execution_recall": 1.0,
  "candidate_count_discovery": 17, "candidate_count_promoted": 9,
  "finding_origin_breakdown": {"deterministic_tool":3,"specialist_rule":2}}}
```

**若 `child_sessions` 为 0，说明分层没有真的发生** —— 那是执行失败，
不是「架构无效」，必须在报告里如实写明。

---

## 8. 执行模式

默认 `full_review`。用户只要一张图或一个数值时**不得**自动跑完整审核。

| 模式 | 开哪些子会话 | risk_score | 置信度字段 |
| --- | --- | --- | --- |
| `full_review` | 发现 + 路由到的模块 + 校正 | 完整 | `review_confidence` |
| `structured_extraction` | 仅发现 + 抽取 | **不输出** | `output_confidence` |
| `figure_analysis / interpretation_only` | 仅图解析 | **不输出** | `output_confidence` |
| `figure_analysis / figure_review` | 发现 + M5 | partial | `review_confidence` |
| `targeted_check` | 发现 + 选定模块 | partial | `review_confidence` |

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
