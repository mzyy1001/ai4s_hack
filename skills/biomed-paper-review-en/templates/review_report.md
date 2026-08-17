# Paper Review Report · {{paper.title}}

<!-- Rendering helper functions are not machine JSON fields and must not be written back into the contract.

1. collect_extracted_fields(structured_result)
   Traverse only objective / population / design / measurement / design_specific /
   conclusion / declarations; whenever an object simultaneously contains applicability,
   requiredness, status, value, evidence_refs, and extraction_confidence, collect it and do
   not descend further. arms[], claims[], and key_data[] are not rendered by this function.
2. collect_review_fields(structured_result, findings)
   From the full set produced by collect_extracted_fields, keep only: requiredness=required;
   or status in not_reported/ambiguous/conflicting/parse_failed/unresolved; or fields whose
   evidence_refs intersect any finding.evidence_refs. Sort by field_path in lexicographic
   order. count_omitted_review_fields returns the number of reported / not_applicable
   recommended/optional fields that did not enter the Markdown; these fields remain fully
   preserved in the JSON and must not be deleted from the structured output.
3. format_value / format_uncertainty / format_list / format_context
   Convert contract objects into short human-readable text; null, empty arrays, and empty
   strings are uniformly displayed as "—". numeric_value is rendered as a point value,
   [low, high], ≥low, ≤high, or a categorical label respectively; dumping raw JSON is
   forbidden. format_rate(rate) displays a fixed "Not applicable (0/0; contract sentinel
   rate=1.0)" when total=0, otherwise displays resolved/total (rate). localize_risk_band
   uses a fixed English mapping and never displays internal enums directly.
4. render_evidence_refs(refs, registry, mode)
   Resolve refs in their original order and de-duplicate; if any ref does not exist or is
   not unique, stop rendering and report a contract error.
   compact displays each entry on its own:
   - present: `[EV-001 | PDF p.8 | Results ¶res-3 | Fig 3B]`; a missing quote does not affect compact.
   - absence: `[EV-002 | absence search: Methods + Supplement | result no_match]`.
   - external: `[EV-003 | ClinicalTrials.gov NCT01234567 | resolved | 2026-08-07]`.
   expanded appends after the same first line: for present, the quote (at most 300 Unicode
   characters; when there is no quote, write the fixed text "No excerpt; verify against the
   original text at the location above"); for absence, the actual searched_locations,
   search_terms, and search_result; for external, the database, endpoint, record_id,
   retrieved_at, database_version, retrieval_status, the first 12 characters of
   response_sha256, and each assertion's predicate/source_path.
   Do not display the full API response. Location fields are always ordered as PDF physical
   page → printed page → section/subsection → paragraph_id/xml_id → figure/panel → table →
   supplement_id/supplement_page, omitting nulls. The quote is only a locating excerpt; the
   complete entry is preserved in the JSON evidence_registry.
5. sort_issue_clusters / sort_review_plan
   Issue clusters are sorted by critical > major > minor > info, then cluster_id; review
   actions are sorted by P0 > P1 > P2, then the highest severity among associated findings,
   then the first finding_id. Never rely on the original order of the input arrays.
6. render_cluster_findings(member_ids, findings)
   Expand each finding in the cluster exactly once, ordered by severity then finding id;
   each entry must display id, severity, module, title, detail, review_confidence, rule_ref,
   and manual_review. Do not expand only the representative, and do not repeat the same
   finding elsewhere in Section 4.
7. render_plan_finding_packages(finding_ids, findings, registry)
   Expand by each finding's own priority, severity, and id; each item displays title,
   detail, its own priority basis, and its own evidence_refs expanded. Taking the union of
   evidence first and losing the finding→evidence correspondence is forbidden.
   The priority basis is fixed as: critical→P0; major+P0→directly blocks the core
   interpretation; major+P1→other substantive revision items; minor/info→P2. If the
   severity/priority combination is invalid, stop rendering.
8. mode_notice(execution_scope) must use the following branches verbatim; free rewording is forbidden:
   - full_review: "M2–M7 were executed; 'no finding produced' only means this pipeline did
     not detect issues within the evidence obtained, and does not mean the paper's
     conclusions have been verified."
   - structured_extraction: "This report performs structured extraction only; M2–M7 were not
     executed, and it contains no manuscript review conclusions or manuscript risk score."
   - figure_analysis/interpretation_only: "This report only interprets the specified
     figures/tables and did not execute any review modules; do not extrapolate to other
     figures/tables or the manuscript as a whole."
   - figure_analysis/figure_review: "This report only executes the M5 figure/table review;
     M2/M3/M4/M6/M7 were not executed, and local findings and scores must not be taken to
     represent the whole manuscript."
   - targeted_check: "This report only covers the targeted scope declared by
     executed_modules and scope_rationale; modules that were not executed have not been
     judged as 'no issues'."
   no_finding_notice must be accompanied by mode_notice and must state "no finding was
   produced within the executed scope".
9. top_review_actions takes only the first N P0/P1 items after sorting; each item uses
   render_action_finding_briefs(finding_ids, findings, registry) to display
   finding id/severity/title, and uses each finding's first evidence_ref in compact mode to
   give the starting location. finding_counts, review_plan_counts, signal_counts, and
   limitation_counts perform deterministic counting only.
10. localize_reviewer fixed mapping: statistical_reviewer=Statistical reviewer,
    domain_reviewer=Domain reviewer, ethics_committee=Ethics committee, editor=Editor,
    author=Author. single(x) returns [] for null, otherwise [x]. All other render_* helpers
    only look up, format, and de-duplicate; if a referenced id cannot be found, rendering
    must terminate. -->

> DOI: {{format_value paper.doi}} | Journal: {{format_value paper.journal}} |
> Input format: `{{paper.input_format}}`

## 1. Executive Summary

> {{disclaimer}}

### What this report can answer

> {{mode_notice execution_scope}}

| Execution mode | submode | Executed review modules | Skipped review modules |
| --- | --- | --- | --- |
| `{{execution_scope.mode}}` | `{{format_value execution_scope.submode}}` | {{format_list execution_scope.executed_modules}} | {{format_list execution_scope.skipped_modules}} |

- Scope rationale: {{execution_scope.scope_rationale}}
- Executed stages: {{format_list execution_scope.executed_stages}}

### For reviewers, read this first

{{#if manuscript_risk_score}}
{{#if manuscript_risk_score.partial}}
- Total weighted issues within scope: `{{manuscript_risk_score.value}}/100`; no full-manuscript banding is assigned in this run.
> ⚠️ This is a partial screening score limited to the executed modules, with
> `comparable_to_full_review=false`. Modules that were not executed have not been judged
> as "no issues"; this score must not be compared or ranked against the risk score of any
> other report, including partial scores from different targeted-check scopes.
{{else}}
- Manuscript risk screening score: `{{manuscript_risk_score.value}}/100`; band:
  {{localize_risk_band manuscript_risk_score.band}}.
{{/if}}
- Scoring boundary: {{manuscript_risk_score.threshold_caveat}}
{{else}}
- Manuscript risk screening score: not produced because this mode executed no review modules; do not infer low manuscript risk from its absence.
{{/if}}
- findings: {{finding_counts all_findings}}; review actions: {{review_plan_counts manual_review_plan}}.
- Computed extraction coverage: `{{extraction_coverage.value}}`; it must be interpreted together with the numerators/denominators in Section 7,
  and is not a probability of manuscript quality.
{{#if review_confidence}}
- Review confidence: `{{review_confidence.value}}`. This is an uncalibrated evidence-support index, not the probability that a finding
  is correct, nor a probability of manuscript quality.
{{#if review_confidence.weak_evidence_warning}}
> ⚠️ {{review_confidence.weak_evidence_warning}}
{{/if}}
{{else}}
- Output confidence: `{{output_confidence.value}}`. This value only indicates how firmly the evidence supports this extraction/interpretation,
  not that the manuscript's scientific conclusions are correct.
{{/if}}

### Handle first (at most three items)

{{#each (top_review_actions manual_review_plan 3)}}
- [ ] **[{{priority}}] {{action}}** ({{localize_reviewer who}})
  - Associated findings: {{render_action_finding_briefs finding_ids @root.all_findings @root.evidence_registry}}
{{else}}
There are currently no P0/P1 manual review actions; this applies only to the executed scope.
{{/each}}

## 2. Structured Result Table

{{#if structured_result}}
Structured result version: `{{structured_result.version}}`;
`stage_3b_executed={{structured_result.stage_3b_executed}}`. This section shows only conditionally required fields, unresolved/
missing fields, and fields whose evidence intersects a finding; another {{count_omitted_review_fields structured_result all_findings}}
reported or not-applicable recommended/optional fields are preserved in the JSON only.

| Field | Applicability / Requiredness | Status | Value / Unit | Extraction confidence | Source location |
| --- | --- | --- | --- | --- | --- |
{{#each (collect_review_fields structured_result @root.all_findings)}}
| `{{field_path}}` | `{{applicability}}` / `{{requiredness}}` | `{{status}}` | {{format_value value}} {{format_value unit}} | `{{extraction_confidence}}` | {{render_evidence_refs evidence_refs @root.evidence_registry "compact"}} |
{{else}}
| — | — | — | No fields need to enter the reviewer view within this scope | — | — |
{{/each}}

### Key data observation group summary

| Observation group / Metric | Context | Status | canonical | Reporting completeness / Missing elements |
| --- | --- | --- | --- | --- |
{{#each structured_result.key_data}}
| `{{id}}` · {{metric_name}} (`{{metric_family}}`) | {{format_context grouping_key}} | `{{status}}` | {{render_canonical_observation this}}; {{format_value canonical_rationale}} | `{{reporting_completeness}}`; {{format_list missing_elements}} |
{{else}}
| — | — | No key data observation groups within this scope | — | — |
{{/each}}

### Observation groups requiring source re-check

{{#each (key_data_needing_source_review structured_result.key_data)}}
#### {{id}} · {{metric_name}} · `{{status}}`

| observation | Value / Unit | Uncertainty / n / Replicate type | Source | Confidence | Manual check | Source location |
| --- | --- | --- | --- | --- | --- | --- |
{{#each observations}}
| `{{observation_id}}` | {{format_value value}} {{format_value unit}} | {{format_uncertainty uncertainty}}; n={{format_value n}}; {{format_value replicate_type}} | `{{provenance.source_type}}` | `{{extraction_confidence}}` | `{{manual_review_needed}}` | {{render_evidence_refs (single provenance.evidence_ref) @root.evidence_registry "compact"}} |
{{else}}
| — | No observations available | — | — | — | — | — |
{{/each}}

{{else}}
All key data groups have a canonical value from a single source or from compatible multiple sources, and no observation requires manual re-check.
{{/each}}
{{else}}
This mode did not execute Stage 2 and produces no structured result; this does not mean the manuscript failed to report the relevant information.
{{/if}}

## 3. Figure/Table Interpretation and Original-Figure Location

> This section records Stage 3 visible facts and read-only interpretation, not M5 review judgments; figure/table issues appear only
> as findings in Section 4.

{{#each figure_records}}
### {{figure_id}} · {{chart_type}}

- Original figure: {{render_evidence_refs (single location.evidence_ref) @root.evidence_registry "compact"}};
  first cited in text: {{render_evidence_refs (single location.first_cited_at) @root.evidence_registry "compact"}}
- Scientific question: {{scientific_question}}
- Conditions and axes: {{format_context experimental_conditions}}; {{format_context axes}}
- Read-only interpretation: {{interpretation}}
- Quantitative observations: {{render_observations observations @root.evidence_registry}}
- Extraction confidence: `{{extraction_confidence}}`; manual review: `{{manual_review_needed}}`
- Parse limitations: {{render_limitation_refs parse_limitations @root.all_system_limitations}}
{{else}}
This mode did not execute Stage 3, or there are no figure records within the executed scope; do not interpret this as the manuscript's figures being free of issues.
{{/each}}

{{#each table_records}}
{{render_table_record this @root.evidence_registry}}
{{/each}}

## 4. Review Findings

{{#each (sort_issue_clusters issue_clusters)}}
### [{{max_severity}}] {{cluster_id}} · {{finding_title representative_finding @root.all_findings}}

- Categories: {{format_list categories}}
- Associated findings (each finding is expanded here exactly once):

{{render_cluster_findings member_findings @root.all_findings}}

- Evidence package:

{{render_evidence_refs evidence_refs @root.evidence_registry "expanded"}}

{{else}}
{{no_finding_notice execution_scope}}
{{/each}}

## 5. Extraction Signals

> This section is a trace of machine observations and downstream routing; these are not manuscript issues, not manuscript findings,
> carry no severity, and do not enter the risk score directly. Total: {{signal_counts all_extraction_signals}}.

{{#each all_extraction_signals}}
- `{{id}}` · `{{type}}`: {{detail}}
  - Target: {{format_context target}}; routed to: {{format_list routed_to}}; produced by stage: `{{produced_by}}`
  - Evidence: {{render_evidence_refs evidence_refs @root.evidence_registry "compact"}}
{{else}}
No extraction signals within the executed scope.
{{/each}}

## 6. System Limitations

> This section describes where the system or its input "could not see clearly". These entries are not manuscript issues, and must not
> be used to infer author omission or misconduct.
> Total: {{limitation_counts all_system_limitations}}; when affected targets exist, any related "no issues found" statement is void.

{{#each all_system_limitations}}
- `{{id}}` · `{{category}}`: {{impact}}
  - Affected modules: {{format_list affected_modules}}; targets: {{format_list affected_targets}};
    fields: {{format_list affected_fields}}
  - Recovery action: {{recommended_action}}
  - Location: {{render_evidence_refs evidence_refs @root.evidence_registry "compact"}}
{{else}}
No known system limitations within the executed scope; this does not mean the unexecuted scope has been checked.
{{/each}}

## 7. Coverage Breakdown

| Sub-rate | Numerator / Denominator (rate) |
| --- | ---: |
| Conditionally required field resolution rate | {{format_rate extraction_coverage.field_resolution}} |
| Figure/table readability rate | {{format_rate extraction_coverage.asset_readability}} |
| Supplement accessibility rate | {{format_rate extraction_coverage.supplement_accessibility}} |
{{#if extraction_coverage.recommended_field_coverage}}
| Recommended field coverage (not weighted in) | {{format_rate extraction_coverage.recommended_field_coverage}} |
{{/if}}

- Resolved conditionally required fields: {{format_list coverage_breakdown.resolved_fields}}
- Unresolved conditionally required fields: {{render_unresolved_fields coverage_breakdown.unresolved_required_fields}}
- Unreadable figures/tables: {{format_list coverage_breakdown.unreadable_assets}}
- Inaccessible supplements: {{format_list coverage_breakdown.inaccessible_supplements}}

> `not_reported` means the prescribed search scope was completed and the manuscript was confirmed not to report the item; it counts as "resolved".
> `parse_failed` means the system failed to read it out; it counts as "unresolved". The two must never be interchanged.
> When the denominator is 0, the in-schema `rate=1.0` is only a computational sentinel; the report displays "Not applicable" and it must not be interpreted as 100% completion.

## 8. Manual Review Recommendations

Priorities have the following fixed interpretation:

| Priority | Ordering basis | Deadline |
| --- | --- | --- |
| P0 | All critical findings; plus major findings without whose verification the core conclusions, ethics authorization, or data integrity cannot be reliably interpreted | Before forming the review conclusion |
| P1 | Other major findings: those that would change whether a finding holds, its severity, or analyses/materials the authors must supply | Before issuing revision requests |
| P2 | minor/info reporting clarifications, location checks, or editorial corrections that do not change the current core inference | In the routine revision checklist |

Within the same priority, sort by finding severity descending, then by finding id. P0/P1/P2 is the manual verification order,
not manuscript severity, and does not enter the risk score. When one action is associated with findings of different priorities, sort it by the highest of them;
the per-finding basis and evidence are listed separately.

{{#each (sort_review_plan manual_review_plan @root.all_findings)}}
### [ ] [{{priority}}] {{action}}

- Owner: {{localize_reviewer who}}
- Ordering basis: {{render_plan_priority_basis finding_ids @root.all_findings}}
- Per-finding verification package:

{{render_plan_finding_packages finding_ids @root.all_findings @root.evidence_registry}}

{{else}}
No actions entered the report-level review plan within the executed scope. If this run was not `full_review`, the unexecuted modules remain unreviewed;
if system limitations exist, restore the input per Section 6 before judging the related content.
{{/each}}
