# 第二轮契约一致性审计结果

审计对象：`SKILL.md`、`references/00-contracts.md`、`references/01-structured-extraction.md`
及其配套 `schemas/*.json`。

**校验方式**：`python3 tools/validate_schemas.py` —— schema 层 11 项 + 四个模拟实例共
**111 项检查全部通过**（2026-08-07）。

---

## 1. 四个模拟的执行结果

| # | 模拟场景 | fixture | 结果 |
| --- | --- | --- | --- |
| ① | RCT 完整审核，PDF 完整、图像可读 | `tools/fixtures/sim1_rct_full_review.json` | ✅ 26 项通过 |
| ② | 单图解读请求（interpretation_only） | `tools/fixtures/sim2_figure_interpretation_only.json` | ✅ 21 项通过 |
| ③ | 定向核查伦理声明 + 补充材料不可得 | `tools/fixtures/sim3_targeted_ethics_supplement_inaccessible.json` | ✅ 27 项通过 |
| ④ | 正文与图注 IC50 不兼容 | `tools/fixtures/sim4_ic50_source_conflict.json` | ✅ 26 项通过 |

### ① RCT 完整审核

阶段序列 `1→2→3→3b→4→5`，六模块全跑。`manuscript_risk_score.partial = false`，
`comparable_to_full_review = true`，用 `review_confidence`。
`missing_data_handling` 因表述笼统判 `ambiguous` → 出 `ambiguous_extraction` signal →
M2 据**独立稿件证据**（EV-003）立 minor finding，M4 据 absence 证据（EV-005）立 major finding。
覆盖率 3 个条件必填字段中 2 个已解析，`field_resolution = 2/3`。

### ② 单图解读

阶段序列仅 `1→3`。**不跑 Stage 2、不跑 Stage 3b** —— 因此没有 `structured_result`，
也不存在「Stage 3b 消费不存在的 v1」这一旧缺陷。`executed_modules = []`，
故**不输出** `manuscript_risk_score`，改用 `output_confidence`。
拐点为像素估读：`value.type = interval`、`extraction_confidence = low`、
`manual_review_needed = true` 三项强制约束齐备。
分母只含被请求的 `fig:3`，`fields = []` → `field_resolution` 分母为 0 记 1.0
——**没有用全文分母评估单图任务**。

### ③ 定向伦理核查 + 补充材料不可得

阶段序列 `1→2→3b→4→5`（Stage 3 未跑，但 3b 仍执行以收敛 pending 并合并证据；
`stage_3b` 的前置 `stage_2` 已在 `executed_stages` 中，依赖图合法）。
`S1` 不可得 → `SYS-001 (supplement_inaccessible)`；依赖它的五个字段一律
`parse_failed` + `system_limitation_ref`，**没有一个判 `not_reported`** ——
我们没看过补充材料，就不能说稿件没写。
因此 `all_findings = []`、`manuscript_risk_score.value = 0`：
**解析失败没有抬高稿件风险分**，只把 `supplement_accessibility` 压到 0.0、
覆盖率压到 0.65。`partial = true` + `comparable_to_full_review = false`。
`informed_consent` 判 `not_applicable`（in_vitro + in_vivo_animal 无人体受试者）
而非 `not_reported`，避免了虚假缺失。

### ④ IC50 冲突

`KD-007` 组内三个观测全部保留：图注 12.4 (95% CI 9.8–15.7)、正文 15.1、摘要 15.1。
单位归一为 `umol/L`；正文与摘要差值 0 → `compatible_observations`；
图注与正文按四舍五入容差（精度较低方末位 0.1 → tol 0.05）判定差值 2.7 ≫ 0.05
→ `conflicting_observations`。组 `status = conflicting`、
`canonical_observation = null`、`reporting_completeness = not_assessed`。
`SIG-002` 由 **`stage_3b`** 产出（不是 M1 —— 兼容性判定不属于抽取层）。
M2 与 M7 各自据**独立稿件证据**立 finding，`derived_from_signals` 仅作溯源。

---

## 2. 一致性核对表

| # | 检查项 | 状态 | 修订文件中的依据 |
| --- | --- | --- | --- |
| 1 | 每个阶段只消费已产出的产物 | ✅ | `SKILL.md §1.1–1.4` 五张依赖图；`execution_scope.executed_stages[]` 是消费白名单（`00 §7.1`）；`execution_scope.schema.json` 用 `if/then` 强制 `stage_3b ⇒ stage_2`、`stage_4 ⇒ stage_3b`；validator「阶段依赖图合法」项。旧 `figure_analysis` 跳过 Stage 2 却跑 3b 的缺陷已由 `§1.3.1`（不跑 3b）与 `§1.3.2`（先跑 minimal Stage 2）拆解消除 |
| 2 | 每个最终产物有唯一聚合器 | ✅ | `00 §9.2` 阶段本地数组表（`stage1/2/3/3b_system_limitations[]`、`m1_/merge_extraction_signals[]`、`m2_–m7_findings[]`）+ 唯一聚合器表（`all_*` 一律 Stage 5）；`SKILL.md §2.4` 同源。冗余数组 `source_conflict_signals[]` / `unresolved_evidence_links[]` / `extraction_quality_findings[]` 已废除并列入 `00 §10` |
| 3 | M1 不产出稿件 finding | ✅ | `00 §6` 表格标注「仅 M2–M7」；`01 §1.2` 明写「无例外」；`finding.schema.json` 的 `id` pattern `^M[2-7]-[0-9]{3}$` + `module` 指向 `module_id_review`（M2–M7）；validator「finding 契约成立（无 M1…）」项 |
| 4 | 只有 finding 携带稿件 severity | ✅ | `extraction_signal.schema.json` 与 `system_limitation.schema.json` 均含顶层 `"not": {"required": ["severity"]}`；`00 §6.2`/`§6.3` 硬性规则；validator 两项独立检查 |
| 5 | 必填性与适用性分离 | ✅ | `00 §3.1` 三个正交维度表；`01 §3.2` 明令禁止「因不进分母就判 not_applicable」；`01 §5.3` 七张路由表逐字段给出 applicability rule × requiredness；`common.schema.json` 两个独立枚举 |
| 6 | 每个证据引用可解析 | ✅ | `00 §1` 证据登记表；`§1.3` 规则 1「必须解析到恰好一个条目」；`§1.4` 规定 `evidence_refs[]` 为唯一规范形式；`evidence.schema.json` 的 `propertyNames` pattern；validator「全部 evidence_ref 解析到登记表条目」项 |
| 7 | key_data 支持多来源与冲突 | ✅ | `00 §5.2` 观测组结构（`observations[]` + `compatible_/conflicting_observations[]` + `canonical_observation`）；`§5.4` 四步判定；`key_data.schema.json` 用 `if/then` 强制冲突态 canonical 为 null；模拟④实测 |
| 8 | pending 状态不能存活到 v2 | ✅ | `00 §4` 规则 5；`01 §7.4` 收敛义务表；`structured_result.schema.json` 顶层 `if version=v2 then key_data.status ≠ pending_visual_resolution ∧ stage_3b_executed=true`；validator 两项独立检查 |
| 9 | 每个枚举示例合法 | ✅ | `00 §11` lint 首项列出全部十类枚举；validator 校验 `common.source_type` / `field_status` / signal type 与契约逐字一致，并全文扫描已废弃标识符（`figure_axis` / `figure_pixel` / `figure_caption` / `min_group_n` 等）零命中 |
| 10 | 每个内部小节引用可解析 | ✅ | 旧文中的 `§4.5` / `§4.3` / `§6.1` / `§D` 悬空引用已全部改写：`§D` → `00 §10` 迁移表，`§4.5` → `00 §6`（M1 不产 finding），`§6.1` → `00 §8.1`。当前跨文件引用统一写成「`00-contracts.md §x`」「`01-structured-extraction.md §x`」形式 |
| 11 | 评分公式可由已声明字段算出 | ✅ | `00 §8.3` 逐变量给出来源：`pixel_*` ← `provenance.source_type`；`ocr_*` ← `provenance.derivation.ocr_used`（**为此新增 `derivation` 且设为必填**）；`low_conf_finding_rate` ← `finding.review_confidence`；`C` ← `key_data.status`。`common.schema.json` 的 `provenance` 把 `derivation` 列入 `required` |
| 12 | 非审核模式不声称审核置信度 | ✅ | `SKILL.md §1.5` 速查表逐模式指定置信度字段；`00 §8.3` 定义 `output_confidence` 与 `review_confidence` 互斥；`review_report.schema.json` 顶层 `not: {required: [两者]}` + `if executed_modules 非空 then 必填 review_confidence 且禁 output_confidence, else 反之`；模拟②实测 |
| 13 | partial 分数显式标记 | ✅ | `00 §8.1` partial 语义块；`review_report.schema.json` 的 `partial ⇒ comparable_to_full_review=false` 与 `len(executed_modules) ≤ 5 ⇒ partial=true`；`executed_modules` 为空时禁止输出本项；模拟②③实测 |
| 14 | 像素估读不表示为字符串 | ✅ | `00 §2.1` 五种 numeric 变体 + 明令禁止 `"40–50"`；`§2.4` pixel 四项强制约束；`common.schema.json` 的 `numeric_value` 用 `oneOf` 五分支且 `additionalProperties:false`；`key_data.schema.json` 强制 pixel ⇒ `value.type ∈ {interval, lower_bound, upper_bound}`；validator 两项独立检查 |
| 15 | 解析失败不能降低稿件质量 | ✅ | `00 §6.3` 规则 2「不降低 manuscript_risk_score」；`§6.4` 边界矩阵逐情形给出正确/错误做法；`§8.1`「不因 PDF 不可读或解析失败而升高」；`review_report.schema.json` 删除旧 `extraction_gap_penalty`；模拟③实测（五个字段 parse_failed，风险分仍为 0） |

---

## 3. 本轮修掉的具体缺陷（对照第二轮审计 13 点）

| 审计点 | 旧问题 | 修法 |
| --- | --- | --- |
| 1 执行依赖图 | `figure_analysis` 跑 3b 却不跑 2；`targeted_check` 跑 3b 未必跑 3；图解读与图审核混为一谈 | `SKILL.md §1` 五张依赖图；`figure_analysis` 拆 `interpretation_only` / `figure_review` 两 submode；`execution_scope` 成为消费白名单并在 schema 层强制阶段依赖 |
| 2 三记录契约 | `extraction_quality_findings[]` 实为第四类记录 | 整体废除：`ambiguous_extraction` → signal；`required_field_unresolved` → `coverage_breakdown.unresolved_required_fields[]`（非记录） |
| 3 适用性 vs 必填性 | 「不在条件必填表内」一律判 `not_applicable` | 拆为 `applicability` × `requiredness` 两个独立枚举；`01 §5.3` 七张路由表六列重写；默认规则改为 `applicable + optional` 而非 `not_applicable` |
| 4 key_data 合并 | 扁平单值，无法表达多来源 / 冲突 / canonical | 改为观测组，新增 `observations[]` / `canonical_observation` / `canonical_rationale` / 兼容与冲突分组 |
| 5 证据登记表 | `evidence_refs: ["EV-018"]` 无处可解析 | 新增 `evidence_registry` + `evidence.schema.json`；`evidence_refs[]` 定为唯一规范形式，渲染层负责展开 |
| 6 pending 生命周期 | `parse_failed` + `pending_visual_resolution: true` 语义错误 | 新增 `status: unresolved` + `resolution_state` 块；仅 v1 合法；`01 §7.4` 给出五种收敛去向 |
| 7 产出者归属 | Stage 2 与 3b 都产 `extraction_signals[]`；三个阶段都追加 `system_limitations[]` | 全部拆为阶段本地数组，Stage 5 单一聚合（`00 §9.2`） |
| 8 枚举与引用 | `source_type: "figure_caption"`；`§4.5`/`§D` 悬空引用 | 全文改写；新增 `00 §11` lint 清单 + validator 全文扫描已废弃标识符 |
| 9 设计路由 | `allocation` 未定义；诊断研究误用 `primary_endpoint` 表示目标疾病；横断面被要求随访；`mixed`/`other` 无存储语义 | `allocation` 拆为 `randomization` + `allocation_concealment`；新增 `target_condition`；`cross_sectional` 与 `case_control` 的 `follow_up` 判 `not_applicable`；`mixed`/`other` 给出合法性条件与并集路由；11 个 design-specific 字段补齐定义 |
| 10 评分可计算 | pixel/OCR 依赖率无字段可算 | `provenance.derivation` 必填；全部分母移入 `execution_scope`；覆盖率报显式分子分母 |
| 11 来源可靠性 | 绝对顺序「正文 > 表 > 图注」 | 改为两级分类（explicit_reported > visually_derived）+ 六条有序判据 + 可辩护性要求 |
| 12 数值区间 | `"value": "40–50"` | 五种 numeric 变体对象，schema 层 `oneOf` 强制 |
| 13 图表角色 | 「Stage 3 由 M5 解析部分执行」并产出 M5 finding | 拆为 Figure Parser（Stage 3，不评判）与 M5 Reviewer（Stage 4）；`figure_record.schema.json` 顶层 `not` 禁止 `issues`/`findings` |

---

## 4. 已知的遗留项

以下**不是**本轮遗漏，是明确留到后续的工作：

1. **完整 JSON Schema 校验未接入。** 沙箱无 `jsonschema` 库，
   `tools/validate_schemas.py` 手工实现了契约关心的那部分约束（111 项）。
   `if/then` 分支的完整语义校验待环境具备后启用。
2. **M2–M7 的 `category` slug 表尚未登记齐全。** `finding.category` 目前只在 schema 中
   声明为「该模块 reference 已登记的 slug」，无法机器校验 —— 待各模块 reference
   填完后，把 slug 全集写入一个 `categories.json` 供 validator 交叉核对。
3. **`00 §5.4` 第 1 步依赖的单位归一化表**尚未编写（`01 §13` TODO 已登记）。
