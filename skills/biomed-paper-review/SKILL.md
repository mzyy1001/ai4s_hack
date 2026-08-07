---
name: biomed-paper-review
description: 生物医药论文结构化抽取与审稿辅助。输入一篇论文（PDF / JATS XML / 纯文本），输出结构化证据表、图表解读与原图定位、多维审核发现、抽取覆盖率与复核置信度，以及分优先级的人工复核建议。支持四种执行模式（完整审核 / 仅结构化抽取 / 图表解析 / 定向核查）。当用户需要预审、复核生物医药论文或稿件，或需要抽取论文中的实验条件、剂量响应曲线、统计图、实验流程图、显微图的关键数值时使用。
---

# 生物医药论文审稿辅助 Skill

## 0. 这个 Skill 怎么工作（先读这一节）

**它不是「读完全部规则再审一遍论文」。** 那样做实测更差 ——
裸模型本身就是很强的审稿人，而把五千行规则压在它前面只会挤占注意力：
一次全流程追踪里，八个规则库只有一个被真正读过。

**它是一个分层的审阅计算：**

```
Layer 1  全局发现     以专家身份通读，产出论文地图与候选问题（高召回，不取证）
   ↓
Layer 2  路由专家     每个专家只拿自己那一包证据 + 自己那一本规则
   ↓
Layer 3  确定性核验   工具按对象定向执行，并主动扫描
   ↓
Layer 4  全局校正     跨节比对，合并去重，解决每一个候选
   ↓
Layer 5  契约归一     到这一步才套完整 schema，渲染报告
```

**一条贯穿始终的原则**：

> 契约与 schema 用来**组织和校验已发现的问题**，不得在发现之前占满注意力。
> 先高召回地发现，再形式化。

因此发现阶段用轻量结构（`candidate_issue`），
**不要求** `evidence_refs`；只有 Layer 5 的最终 finding 才必须完整合规。

**读什么、什么时候读**：

| 阶段 | 允许读 | 禁止读 |
| --- | --- | --- |
| Layer 1 | 本文件 + `references/00-runtime-contract.md` | M2–M7 规则库、完整契约 |
| Layer 2 | 本次路由指定的那一本规则库 + 自己那一包证据 | 其他模块的规则库、全文 |
| Layer 4 | `paper_map` / `claim_map` / 各专家产物 | 全文 |
| Layer 5 | `references/00-contracts.md`（完整契约） | — |

路由表见 `references/00-routing.md`。

## 0.1 定位与边界

**做什么**：自动化并辅助审稿的**基础性工作** —— 结构化证据抽取、图表解读、
报告规范核查，以及为专家复核排定优先级。

**明确声明（必须原样写入每份输出报告）**：

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查
> 与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。**
> 本 Skill 的任何评分均为筛查信号（screening / triage signal），
> 不构成录用、退稿或发表决定。

### 0.2 核心原则：证据可审计

**每一条最终 finding 都必须有可审计的证据支撑。** 已存在内容给 `present` 证据
（含结构化 locator）；缺失内容给 `absence` 证据（显式检索范围 + 检索词 + 结果）；
公开数据源事实给 `external` 证据（端点、查询、版本、时间、响应 hash）。
**绝不为不存在的内容伪造引文。** 证据的规范存储是 `evidence_registry`，
一切引用位置只写 `evidence_refs[]`。

**但方向不能搞反**：证据要求用来**验证**发现，不是用来**减少**发现。
Layer 1 先列全问题，Layer 2–3 再逐条取证；
**不得**因为取证麻烦，或因为「套不进 schema」，就在发现阶段丢掉它。

### 0.3 X1 外部核验：主要增益来源

`scripts/external_figure_validation.py` 已交付，十四条检查、十个数据库。
**离线检查只能查论文内部是否自洽，而内部自洽裸模型本来就会做** ——
把它写成规则再让模型执行一遍，相对裸模型的增益结构上只能是零或负（已实测）。

只有两类事情模型做不到：**确定性计算**，和**查外部权威库**。

| 能力 | 归属 | 状态 |
| --- | --- | --- |
| 细胞系是否被认定污染 / 错误鉴定 | M3 | 已接入（Cellosaurus） |
| 试验是否回顾性注册、是否结局切换 | M4 / M6 | 已接入（ClinicalTrials.gov） |
| 引用文献是否已撤稿、DOI 是否真实 | M2 | 已接入（Europe PMC / Crossref） |
| 判断结论在科学上是否为真 | M7 | 未接入，只做 claim↔evidence 对齐 |
| 判断领域创新性 / 重要性 | M7 | 未接入，不判断 |

X1 只产 `external` evidence、`external_validation_candidate` 与 `system_limitation`，
**禁止产 finding**。外部源不可达时按契约降级，离线流程仍须跑完。

---

## 1. 执行模式

先判定模式再进入流水线。默认 `full_review`；用户只要一张图或一个数值时，
**不得**自动跑完整审核。每个模式必须在输出中声明 `execution_scope`，
其中 `executed_stages[]` 是消费权限的白名单。

| 模式 / submode | 跑哪些层 | risk_score | 置信度字段 | 主结构化产物 |
| --- | --- | --- | --- | --- |
| `full_review` | L1→L2(M2–M6 并行→M7)→L3→L4→L5 | 完整 | `review_confidence` | `structured_result_v2` |
| `structured_extraction` | L1 + 抽取，不跑专家 | **不输出** | `output_confidence` | v1 或 v2 |
| `figure_analysis / interpretation_only` | L1 + 图解析 | **不输出** | `output_confidence` | 仅 records |
| `figure_analysis / figure_review` | L1 + 仅 M5 + L4 部分 | partial | `review_confidence` | `structured_result_v2` |
| `targeted_check` | L1 + 选定专家 + L4 部分 | partial | `review_confidence` | `structured_result_v2` |

`review_confidence` 与 `output_confidence` **互斥，不得同时输出**。
partial 分数**禁止**与 `full_review` 分数并列比较或排序。
任何模式都必须输出 `execution_scope`、`coverage_breakdown`、
`extraction_coverage`、`all_system_limitations[]`、`runtime_utilization`。

### 1.1 `structured_extraction` 细则

无视觉需求 → 输出 `structured_result_v1` + `stage_3b_executed: false`；
跑了 scoped 图解析与合并 → 输出 `v2` + `stage_3b_executed: true`。
**不得把 v1 冒充 v2。** v1 允许保留 `status: "unresolved"`，
但必须计入 `coverage_breakdown.unresolved_required_fields[]`。

### 1.2 `figure_analysis` 两个 submode 必须显式声明

`interpretation_only` 只解读不评判，**不产任何 M5 finding**。
`figure_review` 才跑 M5，需先跑最小抽取以提供 `structured_result_v1`。

---

## 2. Layer 1 · 全局发现

**这是一次独立的推理任务，不是长提示里的一段指令。**
执行它时**只带**本文件与 `00-runtime-contract.md`，
**不得**读 M2–M7 规则库或完整契约 —— 那会让结构化取代发现。

输入：归一化后的稿件、文档地图、图表清单。

以资深审稿人身份通读，产出：

| 产物 | 说明 |
| --- | --- |
| `paper_map` | 章节、表、图、supplement、声明、参考文献、注册信息 |
| `experiment_map` | 每个实验/研究成分一条。**不得把每篇论文强压成一个实验** |
| `claim_map` | 每条重要主张：陈述、覆盖范围、出处、期望证据、关联结果 |
| `candidate_issues[]` | 候选问题，**优先召回** |
| `review_routing_plan` | 每个候选交给谁、用哪包证据、哪本规则、哪个工具 |

候选用轻量结构，**不需要** `evidence_refs`：

```json
{
  "candidate_id": "CAND-014",
  "type": "possible_internal_inconsistency",
  "description": "Table 1 各类计数之和为 30，声明分母 n=28",
  "locations": ["Table 1"],
  "confidence": "medium",
  "suggested_modules": ["M2", "M4"]
}
```

通读时至少覆盖这些**裸模型也该看出来**的类型：
表格分母与计数是否自洽、同一结局在不同位置数值/P 值是否一致、
结论是否超出数据、纳入标准与基线表是否矛盾、盲法是否可能被识破、
安全性结论与随访时长是否匹配、方法与结果是否对得上。

**跨节矛盾**（两个 section 互相冲突）标 `suggested_modules: ["RECONCILE"]`，
直接进 Layer 4 —— 单个专家只看自己那一包，看不见跨节矛盾。

### 2.1 候选生命周期（硬性要求）

**每个候选最终必须有归宿**，写入 `candidate_resolution_log[]`：

```
pending | promoted_to_finding | merged | rejected | unresolved | blocked_by_system_limitation
```

- `rejected` **必须**给 `rejection_reason`
- `promoted_to_finding` **必须**指向 `final_finding_id`
- `merged` **必须**指向 `merged_into`
- 定位不到证据记 `unresolved`，**不得**记 `rejected` ——
  那是我们没定位到，不是问题不存在

**此前的实现会在发现与渲染之间静默丢掉有效问题，这张台账就是为了让丢失可见。**

---

## 3. Layer 2 · 路由专家审阅

每个专家是一次**独立的、限定范围的执行**，只拿到：

```
自己那一包证据  +  路由给它的候选  +  00-runtime-contract.md  +  自己那一本规则库
```

**不得**把全文塞给每个专家，**不得**要求专家读别的模块的规则库。

M1 前置抽取层用 `references/01-structured-extraction.md`，
它**不产 finding**，职责是抽出字段与可核验标识符，供下游专家与 X1 使用。

| 专家 | 规则库 | 主要证据包 |
| --- | --- | --- |
| M2 宏观逻辑 | `references/02-macro-logic.md` | 跨节包、参考文献包、声明包 |
| M3 实验方法 | `references/03-experimental-methods.md` | 方法包、方法标识符包 |
| M4 统计 | `references/04-statistics.md` | 统计包 |
| M5 图表 | `references/05-figures-and-charts.md` | 图包 |
| M6 伦理 | `references/06-ethics-compliance.md` | 伦理包 |
| M7 结论 | `references/07-conclusions-discussion.md` | 主张-证据包 |

**M2–M6 并行；M7 必须最后跑** —— 它要消费 M2–M6 的 findings 判断结论可信度。

每包必带轻量全局上下文（研究设计、`experiment_id`、支撑哪条主张、
关联图表、总样本量、随访时长），否则专家会做出局部正确、整体荒谬的判断。

专家的产物是 `provisional_finding`：已做规则判定与证据绑定，
但**尚未**去重、聚簇、定最终 severity。**不在这一层渲染报告。**

### 3.1 参考文献读取的正确指标

**不要追求 `references_read = 8/8`。** 一篇纯生信论文根本不需要读伦理规则库。

正确指标是**路由召回率**：

```
reference_routing_recall = 本次路由要求读的 reference 中实际读了的比例
```

目标 100%。要求之外的不读**不是缺陷，是设计**。

---

## 4. Layer 3 · 确定性核验

工具不是「碰巧存在的全局工具」，而是**定向的取证仪器**。
每次调用登记为 `tool_task`：

```json
{
  "tool_task_id": "TOOL-07",
  "tool": "statistical_forensics",
  "target": "Table 1",
  "requested_checks": ["table_total_mismatch", "count_percentage_consistency"],
  "triggered_by": ["CAND-014"],
  "proactive": false,
  "status": "executed"
}
```

`status` 取 `executed` / `not_applicable` / `failed` / `skipped`，
后两者**必须**给 `skip_reason`。
**不得让一次该跑的工具悄无声息地消失** —— 跳过和没触发是两回事。

### 4.1 两种触发模式，主动扫描不可省

| 模式 | 触发 |
| --- | --- |
| 候选验证 | 专家怀疑某处有问题 → 请求工具核算 |
| **主动扫描** | 解析出结构化对象即自动跑，**不等候选** |

主动扫描尤其重要：**真正的增益往往来自裸模型根本不会想到去做的确定性检查。**
对象与工具的对应见 `00-routing.md` §5，**不得**因为「没有候选指向它」而跳过。

### 4.2 要运行，不要只读

`scripts/` 下六个脚本是**可执行工具**，不是参考资料。
实测模型倾向于把它们当源码阅读而从不执行 —— 那样贡献为零。

**中间文件一律写在当前工作目录，禁止写 `/tmp` 或工作目录之外的路径。**
实测教训：模型把脚本输入写到 `/tmp/xxx.json`，被运行时以
`permission requested: external_directory (/tmp/*); auto-rejecting` 直接拒绝，
整条取证链断掉、脚本一次都没跑成。评测沙箱同样可能限制，**不要赌它允许**。

```bash
if [ -z "${BIOMED_REVIEW_SKILL_DIR:-}" ]; then
  BIOMED_REVIEW_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 2
  BIOMED_REVIEW_SKILL_DIR="${BIOMED_REVIEW_REPO_ROOT}/skills/biomed-paper-review"
fi
export BIOMED_REVIEW_SKILL_DIR
test -f "${BIOMED_REVIEW_SKILL_DIR}/SKILL.md" || exit 2

# 单位归一化
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/normalize_biomed_units.py" --compare 'mg/mL' 'g/L'

# 统计取证：12+18≠28
printf '%s' '[{"check":"table_total","counts":[12,18],"declared_total":28,"categories_exhaustive":true,"target":"Table 1"}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/statistical_forensics.py" --input -

# 伦理筛查
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/ethics_compliance_check.py" \
  --input structured_result_v2.json > ethics_signals.json

# 序列与标识符
printf '%s' '[{"check":"accession","accession":"NCT123","database":"clinicaltrials"}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/sequence_identifier_audit.py" --input -

# 图像完整性
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/figure_integrity_audit.py" --input figures > figure_integrity.json

# 外部核验（按需联网，只查正文真的出现过的标识符）
printf '%s' '[{"check":"cell_line","cell_line":"MDA-MB-435","evidence_refs":["EV-001"]}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/external_figure_validation.py" --input -
```

退出码非 0 即视为工具未完成，登记 `system_limitation`，
**禁止把空 stdout 解释为「未发现问题」**。

| 脚本 | 作用 |
| --- | --- |
| `normalize_biomed_units.py` | 单位归一化（fail-closed，只做同量纲确定性换算） |
| `statistical_forensics.py` | p 反算 / CI 自洽 / 计数-百分比 / GRIM / 表格合计 |
| `ethics_compliance_check.py` | 伦理规范库筛查 |
| `sequence_identifier_audit.py` | HGVS、位点、登录号、基因符号、引物 QC |
| `figure_integrity_audit.py` | 重复区域、拼接、异常均匀区块。**只出候选，禁止自动定性** |
| `external_figure_validation.py` | X1 外部核验，十四条检查、十个数据库 |

---

## 5. Layer 4 · 全局校正

**不是把各专家产物拼起来。** 它的职责是发现**单个专家看不到的跨节矛盾**。

输入：`paper_map`、`experiment_map`、`claim_map`、候选清单、
各专家 `provisional_finding`、工具 signal、`system_limitation`。

必须显式核对这些关系：

```
Abstract ↔ Results          Methods ↔ Results         Methods ↔ 基线表
Results ↔ Tables            Results ↔ Figures         Tables ↔ Discussion
Results ↔ Discussion        Discussion ↔ Conclusion
随访时长 ↔ 安全性主张        研究人群 ↔ 外推主张
注册记录 ↔ 稿件              Supplement ↔ 正文
```

**这些正是裸模型能发现而分块审阅会漏掉的高价值问题**，例如：

- Methods 写纳入 ASA I–III，基线表却只有 II/III
- 表里一个 p 值，Discussion 里另一个
- 随访只有 48 小时，结论却称「未见严重并发症」

产物：`reconciled_findings[]`、`candidate_resolution_log[]`、`cross_section_findings[]`。

**每个候选在这一步必须结清。** 还没结清的一律记 `unresolved` 并说明原因。

---

## 6. Layer 5 · 契约归一与渲染

**到这一步才做完整契约处理**，此前不得用 schema 约束发现：

```
证据登记表归一 → finding schema 归一 → 去重 → 聚簇
→ severity 协调 → 置信度计算 → 覆盖率计算 → 报告渲染
```

四类对象层层收敛，**不要混为一谈**：

```
discovery 对象  →  provisional 对象  →  已核验记录  →  最终契约记录
（轻量、高召回）   （已绑证据）        （工具确认）    （完整 schema）
```

完整契约见 `references/00-contracts.md`；机器校验以 `schemas/*.json` 为准。

### 6.1 每条 finding 必须标注来源

```
discovery | specialist_rule | deterministic_tool | external_validation | multiple_sources
```

这是判断规则库是否值得保留的唯一依据。若绝大多数 finding 来自
`deterministic_tool` 与 `external_validation`，说明规则库贡献有限，
应据此**裁剪**，而不是继续加规则。

### 6.2 运行时利用率遥测（必须输出）

```json
{
  "runtime_utilization": {
    "references_required": ["04-statistics", "06-ethics-compliance"],
    "references_read": ["04-statistics", "06-ethics-compliance"],
    "scripts_required": ["statistical_forensics", "external_figure_validation"],
    "scripts_executed": ["statistical_forensics", "external_figure_validation"],
    "scripts_failed": [],
    "candidate_count_discovery": 17,
    "candidate_count_promoted": 9,
    "candidate_count_rejected": 6,
    "candidate_count_unresolved": 2,
    "tool_generated_signals": 4,
    "rule_generated_findings": 5,
    "cross_section_findings": 3,
    "finding_origin_breakdown": {
      "discovery": 3, "specialist_rule": 2,
      "deterministic_tool": 3, "external_validation": 1
    }
  }
}
```

关键比率：

```
reference_routing_recall  = |read ∩ required| / |required|      目标 1.0
tool_execution_recall     = |executed ∩ required| / |required|  目标 1.0
candidate_survival_rate   = promoted / discovery
tool_contribution_rate    = 来自工具的 finding / 全部 finding
rulebook_contribution_rate= 来自规则的 finding / 全部 finding
```

**不要优化「读满所有 reference」，要优化「路由要求的一个不漏」。**

---

## 7. 模块关系（不要说错）

七个模块：**M1 是前置抽取层，M2–M6 并行审核，M7 最后跑。**
M2–M7 全部消费 M1 经合并后的产物，因此 M1 与它们**不是并行关系**。
可以说「一个抽取层 + 六个审核模块」，**不要**说「七个模块相互独立」。

Figure Parser（解析，产 records，**不产 finding**）与
M5 Reviewer（评判，产 findings）是**两个执行角色**，共用同一份规则文件。
**不得**说「解析阶段产出 M5 findings」。

## 8. 评分

三个分数互不替代：`manuscript_risk_score`（稿件风险）、
`extraction_coverage`（抽取覆盖率）、`review_confidence` / `output_confidence`。
公式与聚簇规则见 `references/00-contracts.md`。
`system_limitation` **不计入**风险分 —— 我们的能力限制不是稿件的问题。
