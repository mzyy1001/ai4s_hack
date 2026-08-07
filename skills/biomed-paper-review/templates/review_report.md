# 论文审核报告 · {{paper.title}}

<!-- 渲染辅助函数不是机器 JSON 字段，不得写回契约。

1. collect_extracted_fields(structured_result)
   仅遍历 objective / population / design / measurement / design_specific /
   conclusion / declarations；遇到同时含 applicability、requiredness、status、value、
   evidence_refs、extraction_confidence 的对象即收录且不再下钻。arms[]、claims[]、
   key_data[] 不由此函数渲染。
2. collect_review_fields(structured_result, findings)
   从 collect_extracted_fields 的全集中仅保留：requiredness=required；或 status 属于
   not_reported/ambiguous/conflicting/parse_failed/unresolved；或字段 evidence_refs 与任一
   finding.evidence_refs 相交。按 field_path 字典序排列。count_omitted_review_fields 返回
   未进入 Markdown 的 reported / not_applicable recommended/optional 字段数；这些字段仍完整
   保存在 JSON，不得从结构化产物删除。
3. format_value / format_uncertainty / format_list / format_context
   把契约对象转成人类可读短文本；null、空数组与空字符串统一显示“—”。numeric_value
   分别渲染为点值、[low, high]、≥low、≤high 或分类标签，禁止直接倾倒 JSON。
   format_rate(rate) 在 total=0 时固定显示“不适用（0/0；契约哨兵 rate=1.0）”，否则显示
   resolved/total（rate）。localize_risk_band 使用固定中文映射，不直接展示内部枚举。
4. render_evidence_refs(refs, registry, mode)
   按 refs 原顺序解析并去重；任一 ref 不存在或不唯一时停止渲染并报契约错误。
   compact 每条单独显示：
   - present：`[EV-001｜PDF p.8｜Results ¶res-3｜Fig 3B]`；无 quote 不影响 compact。
   - absence：`[EV-002｜缺失检索：Methods + Supplement｜结果 no_match]`。
   - external：`[EV-003｜ClinicalTrials.gov NCT01234567｜resolved｜2026-08-07]`。
   expanded 在同一首行后追加：present 的 quote（最多 300 个 Unicode 字符；无 quote 固定写
   “无摘录；请按上述定位核对原文”）；absence 的实际 searched_locations、search_terms 与
   search_result；external 的 database、endpoint、record_id、retrieved_at、database_version、
   retrieval_status、response_sha256 前 12 位及每个 assertion 的 predicate/source_path。
   不显示整份 API 响应。定位字段固定按 PDF 物理页 → 印刷页 → section/subsection →
   paragraph_id/xml_id → figure/panel → table → supplement_id/supplement_page 排列并省略 null。
   quote 仅作定位摘录，完整条目保留在 JSON evidence_registry。
5. sort_issue_clusters / sort_review_plan
   issue cluster 按 critical > major > minor > info、cluster_id 排序；复核动作按
   P0 > P1 > P2、关联 finding 最高 severity、首个 finding_id 排序。不得依赖输入数组原顺序。
6. render_cluster_findings(member_ids, findings)
   按 severity、finding id 展开簇内每条 finding 一次；每条必须显示 id、severity、module、
   title、detail、review_confidence、rule_ref 与 manual_review。不得只展开 representative，
   也不得在第四节别处重复同一 finding。
7. render_plan_finding_packages(finding_ids, findings, registry)
   按 finding 自身 priority、severity、id 展开；每项显示 title、detail、自己的 priority 依据、
   以及自己的 evidence_refs expanded。禁止先求证据并集后失去 finding→evidence 对应关系。
   priority 依据固定为：critical→P0；major+P0→直接阻断核心解释；major+P1→其他实质修改项；
   minor/info→P2。若 severity/priority 组合不合法，停止渲染。
8. mode_notice(execution_scope) 必须逐字使用下列分支，禁止自由改写：
   - full_review：“已执行 M2–M7；‘未产出 finding’只表示本流程在已取得证据中未检出，不等于
     论文结论已被证实。”
   - structured_extraction：“本报告仅做结构化抽取，未执行 M2–M7，不包含稿件审核结论或
     稿件风险分。”
   - figure_analysis/interpretation_only：“本报告只解读指定图表，未执行审核模块；不得外推到
     其他图表或整篇稿件。”
   - figure_analysis/figure_review：“本报告只执行 M5 图表审核；M2/M3/M4/M6/M7 未执行，局部
     finding 与分数不得代表整篇稿件。”
   - targeted_check：“本报告只覆盖 executed_modules 与 scope_rationale 声明的定向范围；
     未执行模块没有被判定为‘无问题’。”
   no_finding_notice 必须同时给 mode_notice，并写“已执行范围内未产出 finding”。
9. top_review_actions 只取排序后的 P0/P1 前 N 项；每项用
   render_action_finding_briefs(finding_ids, findings, registry) 显示
   finding id/severity/title，并用各 finding 的首条 evidence_ref compact 给出起始定位。
   finding_counts、review_plan_counts、signal_counts、limitation_counts 只做确定性计数。
10. localize_reviewer 固定映射：statistical_reviewer=统计审稿人、domain_reviewer=领域审稿人、
    ethics_committee=伦理委员会、editor=编辑、author=作者。single(x) 对 null 返回 []，否则
    返回 [x]。其余 render_* 只查找、格式化与去重；找不到被引用 id 必须终止渲染。 -->

> DOI：{{format_value paper.doi}} ｜ 期刊：{{format_value paper.journal}} ｜
> 输入格式：`{{paper.input_format}}`

## 一、执行摘要

> {{disclaimer}}

### 本报告能回答什么

> {{mode_notice execution_scope}}

| 执行模式 | submode | 已执行审核模块 | 未执行审核模块 |
| --- | --- | --- | --- |
| `{{execution_scope.mode}}` | `{{format_value execution_scope.submode}}` | {{format_list execution_scope.executed_modules}} | {{format_list execution_scope.skipped_modules}} |

- 范围依据：{{execution_scope.scope_rationale}}
- 已执行阶段：{{format_list execution_scope.executed_stages}}

### 审稿人先看

{{#if manuscript_risk_score}}
{{#if manuscript_risk_score.partial}}
- 范围内问题权重合计：`{{manuscript_risk_score.value}}/100`；本次不作全稿分段。
> ⚠️ 这是已执行模块范围内的局部筛查分，`comparable_to_full_review=false`。
> 未执行模块没有被判定为“无问题”；本分数不得与任何其他报告的风险分横向比较或排序，
> 包括不同定向核查范围的 partial 分数。
{{else}}
- 稿件风险筛查分：`{{manuscript_risk_score.value}}/100`；分段：
  {{localize_risk_band manuscript_risk_score.band}}。
{{/if}}
- 评分边界：{{manuscript_risk_score.threshold_caveat}}
{{else}}
- 稿件风险筛查分：本模式未执行审核模块，不输出；不得据此推断稿件风险低。
{{/if}}
- findings：{{finding_counts all_findings}}；复核动作：{{review_plan_counts manual_review_plan}}。
- 抽取覆盖率计算值：`{{extraction_coverage.value}}`；必须结合第七节分子/分母解释，
  不是稿件质量概率。
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

### 优先处理（最多三项）

{{#each (top_review_actions manual_review_plan 3)}}
- [ ] **[{{priority}}] {{action}}**（{{localize_reviewer who}}）
  - 关联判断：{{render_action_finding_briefs finding_ids @root.all_findings @root.evidence_registry}}
{{else}}
当前没有 P0/P1 人工复核动作；这只适用于已执行范围。
{{/each}}

## 二、结构化结果表

{{#if structured_result}}
结构化结果版本：`{{structured_result.version}}`；
`stage_3b_executed={{structured_result.stage_3b_executed}}`。本节只展示条件必填、未解析/
缺失及与 finding 证据相交的字段；另有 {{count_omitted_review_fields structured_result all_findings}}
个已报告或不适用的 recommended/optional 字段仅保留在 JSON。

| 字段 | 适用性 / 必填性 | 状态 | 值 / 单位 | 抽取置信度 | 原文定位 |
| --- | --- | --- | --- | --- | --- |
{{#each (collect_review_fields structured_result @root.all_findings)}}
| `{{field_path}}` | `{{applicability}}` / `{{requiredness}}` | `{{status}}` | {{format_value value}} {{format_value unit}} | `{{extraction_confidence}}` | {{render_evidence_refs evidence_refs @root.evidence_registry "compact"}} |
{{else}}
| — | — | — | 本次范围内没有需要放入审稿人视图的字段 | — | — |
{{/each}}

### 核心数据观测组摘要

| 观测组 / 指标 | 上下文 | 状态 | canonical | 报告完整性 / 缺失要素 |
| --- | --- | --- | --- | --- |
{{#each structured_result.key_data}}
| `{{id}}` · {{metric_name}} (`{{metric_family}}`) | {{format_context grouping_key}} | `{{status}}` | {{render_canonical_observation this}}；{{format_value canonical_rationale}} | `{{reporting_completeness}}`；{{format_list missing_elements}} |
{{else}}
| — | — | 本次范围内没有核心数据观测组 | — | — |
{{/each}}

### 需要回查来源的观测组

{{#each (key_data_needing_source_review structured_result.key_data)}}
#### {{id}} · {{metric_name}} · `{{status}}`

| observation | 值 / 单位 | 不确定度 / n / 重复类型 | 来源 | 置信度 | 人工核对 | 原文定位 |
| --- | --- | --- | --- | --- | --- | --- |
{{#each observations}}
| `{{observation_id}}` | {{format_value value}} {{format_value unit}} | {{format_uncertainty uncertainty}}；n={{format_value n}}；{{format_value replicate_type}} | `{{provenance.source_type}}` | `{{extraction_confidence}}` | `{{manual_review_needed}}` | {{render_evidence_refs (single provenance.evidence_ref) @root.evidence_registry "compact"}} |
{{else}}
| — | 无可用观测 | — | — | — | — | — |
{{/each}}

{{else}}
所有核心数据组均已得到单一或多来源兼容的 canonical，且没有观测要求人工回查。
{{/each}}
{{else}}
本模式未执行 Stage 2，不产出结构化结果；这不表示稿件未报告相关信息。
{{/if}}

## 三、图表解读与原图定位

> 本节记录 Stage 3 的可见事实与只读解读，不是 M5 审核判断；图表问题只在第四节以
> finding 展示。

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

- 类别：{{format_list categories}}
- 关联判断（每条 finding 仅在此展开一次）：

{{render_cluster_findings member_findings @root.all_findings}}

- 证据包：

{{render_evidence_refs evidence_refs @root.evidence_registry "expanded"}}

{{else}}
{{no_finding_notice execution_scope}}
{{/each}}

## 五、抽取信号

> 本节是机器观察与下游路由轨迹，不是稿件问题，不是稿件 finding，没有 severity，
> 也不直接进入风险分。共 {{signal_counts all_extraction_signals}}。

{{#each all_extraction_signals}}
- `{{id}}` · `{{type}}`：{{detail}}
  - 目标：{{format_context target}}；路由：{{format_list routed_to}}；产出阶段：`{{produced_by}}`
  - 证据：{{render_evidence_refs evidence_refs @root.evidence_registry "compact"}}
{{else}}
执行范围内无抽取信号。
{{/each}}

## 六、系统限制

> 本节说明系统或输入“哪些地方没看清”。这些条目不是稿件问题，不得据此推断作者遗漏或违规。
> 共 {{limitation_counts all_system_limitations}}；有受影响目标时，相关“未发现问题”表述一律无效。

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

| 子率 | 分子 / 分母（rate） |
| --- | ---: |
| 条件必填字段解析率 | {{format_rate extraction_coverage.field_resolution}} |
| 图表可读率 | {{format_rate extraction_coverage.asset_readability}} |
| 补充材料可得率 | {{format_rate extraction_coverage.supplement_accessibility}} |
{{#if extraction_coverage.recommended_field_coverage}}
| 推荐字段覆盖率（不进加权） | {{format_rate extraction_coverage.recommended_field_coverage}} |
{{/if}}

- 已解析的条件必填字段：{{format_list coverage_breakdown.resolved_fields}}
- 未解析的条件必填字段：{{render_unresolved_fields coverage_breakdown.unresolved_required_fields}}
- 不可读图表：{{format_list coverage_breakdown.unreadable_assets}}
- 不可得补充材料：{{format_list coverage_breakdown.inaccessible_supplements}}

> `not_reported` 表示已完成规定范围检索并确认稿件未报告，属于“已解析”；
> `parse_failed` 表示系统没读出来，属于“未解析”。两者不得互换。
> 分母为 0 时 schema 内的 `rate=1.0` 只是计算哨兵，报告显示“不适用”，不得解释为 100% 完成。

## 八、人工复核建议

优先级固定解释如下：

| 优先级 | 排序依据 | 完成时点 |
| --- | --- | --- |
| P0 | 全部 critical；以及不先核对就无法可靠解释核心结论、伦理授权或数据完整性的 major | 形成审稿结论前 |
| P1 | 其他 major：会改变 finding 的成立、严重度或作者必须完成的分析/材料补充 | 给出修改要求前 |
| P2 | minor/info 的报告澄清、定位核对或编辑性修正，不改变当前核心推断 | 常规修订清单中 |

同一优先级内按 finding severity 降序，再按 finding id 排序。P0/P1/P2 是人工核对顺序，
不是稿件 severity，也不进入风险分。一个动作关联不同优先级 finding 时，按其中最高优先级排序；
逐 finding 的依据与证据分别列出。

{{#each (sort_review_plan manual_review_plan @root.all_findings)}}
### [ ] [{{priority}}] {{action}}

- 执行者：{{localize_reviewer who}}
- 排序依据：{{render_plan_priority_basis finding_ids @root.all_findings}}
- 逐 finding 核对包：

{{render_plan_finding_packages finding_ids @root.all_findings @root.evidence_registry}}

{{else}}
执行范围内没有进入报告级复核计划的动作。若本次为非 `full_review`，未执行模块仍未审核；
若存在系统限制，先按第六节恢复输入后再判断相关内容。
{{/each}}
