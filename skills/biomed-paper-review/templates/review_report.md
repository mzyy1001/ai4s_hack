# 论文审核报告 · {{paper.title}}

<!-- `collect_extracted_fields` 是渲染辅助函数，不是机器 JSON 字段，不得写回契约。
     固定算法：仅遍历 objective / population / design / measurement / design_specific /
     conclusion / declarations；遇到同时含 applicability、requiredness、status、value、
     evidence_refs、extraction_confidence 的对象即收录且不再下钻；最后按 field_path
     字典序排列。arms[]、claims[]、key_data[] 不由此函数渲染。 -->

> DOI：{{paper.doi}} ｜ 期刊：{{paper.journal}} ｜ 输入格式：{{paper.input_format}}

## 一、执行摘要

> {{disclaimer}}

| 执行模式 | submode | 已执行阶段 | 已执行模块 | 跳过模块 |
| --- | --- | --- | --- | --- |
| {{execution_scope.mode}} | {{execution_scope.submode}} | {{execution_scope.executed_stages}} | {{execution_scope.executed_modules}} | {{execution_scope.skipped_modules}} |

**范围依据**：{{execution_scope.scope_rationale}}

{{#if manuscript_risk_score}}
- 稿件风险分：`{{manuscript_risk_score.value}}/100`（`{{manuscript_risk_score.band}}`；
  `partial={{manuscript_risk_score.partial}}`；
  `comparable_to_full_review={{manuscript_risk_score.comparable_to_full_review}}`）
- 阈值声明：{{manuscript_risk_score.threshold_caveat}}
{{else}}
- 稿件风险分：本模式未执行审核模块，不输出。
{{/if}}
- 抽取覆盖率：`{{extraction_coverage.value}}`
{{#if review_confidence}}
- 审核置信度：`{{review_confidence.value}}`
{{#if review_confidence.weak_evidence_warning}}
> ⚠️ {{review_confidence.weak_evidence_warning}}
{{/if}}
{{else}}
- 输出置信度：`{{output_confidence.value}}`
{{/if}}

## 二、结构化结果表

{{#if structured_result}}
结构化结果版本：`{{structured_result.version}}`；
`stage_3b_executed={{structured_result.stage_3b_executed}}`。

{{#each (collect_extracted_fields structured_result)}}
| 字段 | applicability | requiredness | status | 值 | 单位 | extraction_confidence | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| {{field_path}} | {{applicability}} | {{requiredness}} | {{status}} | {{value}} | {{unit}} | {{extraction_confidence}} | {{evidence_refs}} |
{{/each}}

### 核心数据观测组

{{#each structured_result.key_data}}
- `{{id}}` · {{metric_name}}（`{{metric_family}}`）：status=`{{status}}`；
  canonical=`{{canonical_observation}}`；依据：{{canonical_rationale}}
  - grouping_key：{{grouping_key}}
  - observations：{{observations}}
  - compatible：{{compatible_observations}}；conflicting：{{conflicting_observations}}
  - reporting_completeness=`{{reporting_completeness}}`；缺失要素：{{missing_elements}}
{{/each}}
{{else}}
本模式未执行 Stage 2，不产出结构化结果。
{{/if}}

## 三、图表解读与原图定位

{{#each figure_records}}
### {{figure_id}} · {{chart_type}}

- 原图证据：{{location.evidence_ref}}；正文首次引用：{{location.first_cited_at}}
- 科学问题：{{scientific_question}}
- 解读：{{interpretation}}
- 观测：{{observations}}
- 抽取置信度：`{{extraction_confidence}}`；`manual_review_needed={{manual_review_needed}}`
- 解析限制：{{parse_limitations}}
{{else}}
本模式未执行 Stage 3，或执行范围内没有图记录。
{{/each}}

{{#each table_records}}
{{this}}
{{/each}}

## 四、审核发现

{{#each issue_clusters}}
### [{{max_severity}}] {{cluster_id}} · 代表 finding {{representative_finding}}

- 成员：{{member_findings}}
- 类别：{{categories}}
- 主锚点：{{anchor}}
- 证据：{{evidence_refs}}
{{else}}
{{#if execution_scope.executed_modules}}
执行范围内未产出 finding。
{{else}}
本模式未执行审核模块。
{{/if}}
{{/each}}

{{#each all_findings}}
- `{{id}}`（{{module}} / {{category}} / {{severity}} / {{review_confidence}}）：
  {{title}}。{{detail}} 证据：{{evidence_refs}}；规则：`{{rule_ref}}`
{{/each}}

> 证据渲染规则：逐个解析 `evidence_refs[]`。`present` 展开 locator 与原文；
> `absence` 只展开检索范围、检索词与检索结果，禁止生成引文。

## 五、抽取信号

{{#each all_extraction_signals}}
- `{{id}}` · `{{type}}`：{{detail}}；目标：{{target}}；证据：{{evidence_refs}}；
  路由：{{routed_to}}
{{else}}
无抽取信号。
{{/each}}

## 六、系统限制

{{#each all_system_limitations}}
- `{{id}}` · `{{category}}`：{{impact}}；受影响目标：{{affected_targets}}；
  建议动作：{{recommended_action}}
{{else}}
无已知系统限制。
{{/each}}

## 七、覆盖率明细

| 子率 | resolved | total | rate |
| --- | ---: | ---: | ---: |
| 条件必填字段解析率 | {{extraction_coverage.field_resolution.resolved}} | {{extraction_coverage.field_resolution.total}} | {{extraction_coverage.field_resolution.rate}} |
| 图表可读率 | {{extraction_coverage.asset_readability.resolved}} | {{extraction_coverage.asset_readability.total}} | {{extraction_coverage.asset_readability.rate}} |
| 补充材料可得率 | {{extraction_coverage.supplement_accessibility.resolved}} | {{extraction_coverage.supplement_accessibility.total}} | {{extraction_coverage.supplement_accessibility.rate}} |

- 已解析字段：{{coverage_breakdown.resolved_fields}}
- 未解析必填字段：{{coverage_breakdown.unresolved_required_fields}}
- 不可读图表：{{coverage_breakdown.unreadable_assets}}
- 不可得补充材料：{{coverage_breakdown.inaccessible_supplements}}

## 八、人工复核建议

{{#each manual_review_plan}}
- **[{{priority}}]** {{action}}（执行者：`{{who}}`；对应 findings：{{finding_ids}}）
{{else}}
执行范围内没有需要列入复核计划的 `major` / `critical` finding。
{{/each}}
