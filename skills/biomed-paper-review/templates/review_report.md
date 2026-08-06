# 论文审核报告 · {{paper.title}}

<!-- 渲染辅助函数不是机器 JSON 字段，不得写回契约。

1. collect_extracted_fields(structured_result)
   仅遍历 objective / population / design / measurement / design_specific /
   conclusion / declarations；遇到同时含 applicability、requiredness、status、value、
   evidence_refs、extraction_confidence 的对象即收录且不再下钻；最后按 field_path
   字典序排列。arms[]、claims[]、key_data[] 不由此函数渲染。
2. format_value / format_uncertainty / format_list / format_context
   把契约对象转成人类可读短文本；null、空数组与空字符串统一显示“—”。numeric_value
   分别渲染为点值、[low, high]、≥low、≤high 或分类标签，禁止直接倾倒 JSON。
3. render_evidence_refs(refs, registry, mode)
   按 refs 原顺序解析；任一 ref 不存在或不唯一时停止渲染并报契约错误。
   mode=compact：显示 id + 定位/数据库记录；mode=expanded：present 证据显示 id、定位与 quote，
   absence 证据显示 id、实际检索范围、检索词与 search_result；external 证据显示 id、
   database、record_id、retrieved_at、database_version、retrieval_status、response_sha256
   前 12 位及 assertions 的 predicate/source_path，不显示整份响应。定位字段固定按
   PDF 物理页 → 印刷页 → section/subsection → paragraph_id/xml_id → figure/panel →
   table → supplement_id/supplement_page 排列并省略 null。quote 仅作定位摘录，显示
   最多 300 个 Unicode 字符；完整条目保留在 JSON evidence_registry。
4. sort_issue_clusters / sort_review_plan
   issue cluster 按 critical > major > minor > info、cluster_id 排序；复核动作按
   P0 > P1 > P2、首个 finding_id 排序。不得依赖输入数组原顺序。
5. finding_by_id / render_related_findings / evidence_refs_for_findings
   只做 id 解析与 refs 去重，不创建新 finding、signal 或 system_limitation。
6. mode_notice / no_finding_notice
   按 SKILL.md §1 与 §6 输出固定范围警示；不得把“未执行”渲染成“未发现问题”。
7. single(x) 对 null 返回 []，否则返回 [x]；finding_counts 按四级 severity 显示计数；
   top_review_actions 只取排序后的 P0/P1 前 N 项。localize_reviewer 使用固定映射：
   statistical_reviewer=统计审稿人、domain_reviewer=领域审稿人、ethics_committee=伦理委员会、
   editor=编辑、author=作者。finding/title/ref、canonical、observation、table、limitation 与
   unresolved-field 等其余 render_* 函数只做已有对象的查找、格式化与去重；找不到被引用 id
   时必须终止渲染，不得补写内容。 -->

> DOI：{{format_value paper.doi}} ｜ 期刊：{{format_value paper.journal}} ｜
> 输入格式：`{{paper.input_format}}`

## 一、执行摘要

> {{disclaimer}}

### 审核范围

| 执行模式 | submode | 已执行阶段 | 已执行审核模块 | 未执行审核模块 |
| --- | --- | --- | --- | --- |
| `{{execution_scope.mode}}` | `{{format_value execution_scope.submode}}` | {{format_list execution_scope.executed_stages}} | {{format_list execution_scope.executed_modules}} | {{format_list execution_scope.skipped_modules}} |

**范围依据**：{{execution_scope.scope_rationale}}

> {{mode_notice execution_scope}}

### 首屏结论

{{#if manuscript_risk_score}}
- 稿件风险筛查分：`{{manuscript_risk_score.value}}/100`；分段：
  `{{manuscript_risk_score.band}}`；`partial={{manuscript_risk_score.partial}}`。
{{#if manuscript_risk_score.partial}}
> ⚠️ 这是已执行模块范围内的局部筛查分，`comparable_to_full_review=false`。
> 未执行模块没有被判定为“无问题”，本分数不得与完整审核分数横向比较。
{{else}}
- 分段说明：{{manuscript_risk_score.threshold_caveat}}
{{/if}}
{{else}}
- 稿件风险筛查分：本模式未执行审核模块，不输出；不得据此推断稿件风险低。
{{/if}}
- finding 数：{{finding_counts all_findings}}。
- 抽取覆盖率：`{{extraction_coverage.value}}`；字段、图表与补充材料分子/分母见第七节。
{{#if review_confidence}}
- 审核置信度：`{{review_confidence.value}}`。这是未经校准的证据支撑指数，不是 finding
  正确概率，也不是稿件质量概率。
{{#if review_confidence.weak_evidence_warning}}
> ⚠️ {{review_confidence.weak_evidence_warning}}
{{/if}}
{{else}}
- 输出置信度：`{{output_confidence.value}}`。该值只表示本次抽取/解读的证据稳固程度，
  不表示稿件科学结论正确。
{{/if}}

### 优先处理

{{#each (top_review_actions manual_review_plan 3)}}
- **[{{priority}}]** {{action}}（{{localize_reviewer who}}；{{format_list finding_ids}}）
{{else}}
当前没有 P0/P1 人工复核动作；这只适用于已执行范围。
{{/each}}

## 二、结构化结果表

{{#if structured_result}}
结构化结果版本：`{{structured_result.version}}`；
`stage_3b_executed={{structured_result.stage_3b_executed}}`。

| 字段 | applicability | requiredness | status | 值 / 单位 | extraction_confidence | 原文定位 |
| --- | --- | --- | --- | --- | --- | --- |
{{#each (collect_extracted_fields structured_result)}}
| `{{field_path}}` | `{{applicability}}` | `{{requiredness}}` | `{{status}}` | {{format_value value}} {{format_value unit}} | `{{extraction_confidence}}` | {{render_evidence_refs evidence_refs @root.evidence_registry "compact"}} |
{{else}}
| — | — | — | — | 本次范围内没有可渲染字段 | — | — |
{{/each}}

### 核心数据观测组

{{#each structured_result.key_data}}
#### {{id}} · {{metric_name}}

- 指标族：`{{metric_family}}`；组状态：`{{status}}`；上下文：{{format_context grouping_key}}
- canonical：{{render_canonical_observation this}}；选择依据：{{format_value canonical_rationale}}
- 报告完整性：`{{reporting_completeness}}`；缺失要素：{{format_list missing_elements}}

##### 来源观测

| observation | 值 / 单位 | 不确定度 / n / 重复类型 | 来源 | 置信度 | 人工核对 | 原文定位 |
| --- | --- | --- | --- | --- | --- | --- |
{{#each observations}}
| `{{observation_id}}` | {{format_value value}} {{format_value unit}} | {{format_uncertainty uncertainty}}；n={{format_value n}}；{{format_value replicate_type}} | `{{provenance.source_type}}` | `{{extraction_confidence}}` | `{{manual_review_needed}}` | {{render_evidence_refs (single provenance.evidence_ref) @root.evidence_registry "compact"}} |
{{else}}
| — | 无可用观测 | — | — | — | — | — |
{{/each}}

{{else}}
本次范围内没有核心数据观测组。
{{/each}}
{{else}}
本模式未执行 Stage 2，不产出结构化结果；这不表示稿件未报告相关信息。
{{/if}}

## 三、图表解读与原图定位

{{#each figure_records}}
### {{figure_id}} · {{chart_type}}

- 原图：{{render_evidence_refs (single location.evidence_ref) @root.evidence_registry "compact"}}；
  正文首次引用：{{render_evidence_refs (single location.first_cited_at) @root.evidence_registry "compact"}}
- 科学问题：{{scientific_question}}
- 条件与坐标：{{format_context experimental_conditions}}；{{format_context axes}}
- 只读解读：{{interpretation}}
- 定量观测：{{render_observations observations @root.evidence_registry}}
- 抽取置信度：`{{extraction_confidence}}`；人工复核：`{{manual_review_needed}}`
- 解析限制：{{render_limitation_refs parse_limitations @root.all_system_limitations}}
{{else}}
本模式未执行 Stage 3，或执行范围内没有图记录；不得解释为稿件图表均无问题。
{{/each}}

{{#each table_records}}
{{render_table_record this @root.evidence_registry}}
{{/each}}

## 四、审核发现

{{#each (sort_issue_clusters issue_clusters)}}
### [{{max_severity}}] {{cluster_id}} · {{finding_title representative_finding @root.all_findings}}

{{#with (finding_by_id representative_finding @root.all_findings)}}
- 审核判断：{{detail}}
- 模块 / 类别 / 判断置信度：`{{module}}` / `{{category}}` / `{{review_confidence}}`
- 规则：`{{format_value rule_ref}}`
- 建议动作：{{manual_review.action}}（{{localize_reviewer manual_review.who}}；
  `{{format_value manual_review.priority}}`）
{{/with}}
- 同簇补充判断：{{render_related_findings member_findings representative_finding @root.all_findings}}
- 证据：

{{render_evidence_refs evidence_refs @root.evidence_registry "expanded"}}

{{else}}
{{no_finding_notice execution_scope}}
{{/each}}

## 五、抽取信号

> 本节是机器观察与下游路由轨迹，不是稿件 finding，没有 severity，也不直接进入风险分。

{{#each all_extraction_signals}}
- `{{id}}` · `{{type}}`：{{detail}}
  - 目标：{{format_context target}}；路由：{{format_list routed_to}}；产出阶段：`{{produced_by}}`
  - 证据：{{render_evidence_refs evidence_refs @root.evidence_registry "compact"}}
{{else}}
执行范围内无抽取信号。
{{/each}}

## 六、系统限制

> 本节说明系统或输入“哪些地方没看清”。这些条目不是稿件问题，不得据此推断作者遗漏或违规。

{{#each all_system_limitations}}
- `{{id}}` · `{{category}}`：{{impact}}
  - 受影响模块：{{format_list affected_modules}}；目标：{{format_list affected_targets}}；
    字段：{{format_list affected_fields}}
  - 恢复动作：{{recommended_action}}
  - 定位：{{render_evidence_refs evidence_refs @root.evidence_registry "compact"}}
{{else}}
执行范围内无已知系统限制；这不代表未执行范围也已检查。
{{/each}}

## 七、覆盖率明细

| 子率 | resolved | total | rate |
| --- | ---: | ---: | ---: |
| 条件必填字段解析率 | {{extraction_coverage.field_resolution.resolved}} | {{extraction_coverage.field_resolution.total}} | {{extraction_coverage.field_resolution.rate}} |
| 图表可读率 | {{extraction_coverage.asset_readability.resolved}} | {{extraction_coverage.asset_readability.total}} | {{extraction_coverage.asset_readability.rate}} |
| 补充材料可得率 | {{extraction_coverage.supplement_accessibility.resolved}} | {{extraction_coverage.supplement_accessibility.total}} | {{extraction_coverage.supplement_accessibility.rate}} |

- 已解析的条件必填字段：{{format_list coverage_breakdown.resolved_fields}}
- 未解析的条件必填字段：{{render_unresolved_fields coverage_breakdown.unresolved_required_fields}}
- 不可读图表：{{format_list coverage_breakdown.unreadable_assets}}
- 不可得补充材料：{{format_list coverage_breakdown.inaccessible_supplements}}

> `not_reported` 表示已完成规定范围检索并确认稿件未报告，属于“已解析”；
> `parse_failed` 表示系统没读出来，属于“未解析”。两者不得互换。

## 八、人工复核建议

优先级固定解释如下：

| 优先级 | 排序依据 | 完成时点 |
| --- | --- | --- |
| P0 | 不先核对就无法可靠解释核心结论、伦理授权或数据完整性；包括全部 critical，以及直接阻断核心结论解释的 major | 形成审稿结论前 |
| P1 | 不阻断其他结论阅读，但会改变 major finding 的成立、严重度或作者必须完成的分析/材料补充 | 给出修改要求前 |
| P2 | minor/info 的报告澄清、定位核对或编辑性修正，不改变当前核心推断 | 常规修订清单中 |

同一优先级内按 finding severity 降序，再按 finding id 排序。P0/P1/P2 是人工核对顺序，
不是稿件 severity，也不进入风险分。

{{#each (sort_review_plan manual_review_plan @root.all_findings)}}
### [{{priority}}] {{action}}

- 执行者：{{localize_reviewer who}}
- 对应 findings：{{render_finding_refs finding_ids @root.all_findings}}
- 核对证据：

{{render_evidence_refs (evidence_refs_for_findings finding_ids @root.all_findings) @root.evidence_registry "expanded"}}

{{else}}
执行范围内没有进入报告级复核计划的动作。若本次为非 `full_review`，未执行模块仍未审核；
若存在系统限制，先按第六节恢复输入后再判断相关内容。
{{/each}}
