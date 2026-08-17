# Routing Specification: L0 Entries + Tool Signals → Specialists (Full Text + Rulebase + Index) → Deterministic Tools

> This table is the interface between L0/L0b and the L1 specialists: it decides who handles each class of issue, and which indexes and tools come along.
>
> Core principle (architectural axiom): **what is isolated is the review objective and the rules, not the paper body.**
> Every specialist gets the full text, but only **its own** rulebase.
> The metric is not "read all eight references"; it is "not a single reference required by this task is missed."

## 0. Why Explicit Routing Is Needed

The previous version had no routing layer, so the model decided on its own what to read — in an actual full-pipeline run it read only
`00-contracts` and none of the seven module rulebases. Nobody told it
"which questions in this paper should consult which rulebase," so it could only go by intuition, and intuition leans toward
"read the contract first," burning all attention on formalities.

Explicit routing makes this checkable: **whether what was required to be read was actually read can be computed as a ratio.**

## 1. Main Routing Table

| Candidate type | Specialist | Evidence pack | Rulebase | Deterministic tools |
| --- | --- | --- | --- | --- |
| `possible_internal_inconsistency` | M2 | Cross-section pack | `02-macro-logic` | `statistical_forensics` (when numbers are computable) |
| `possible_reporting_omission` | M2 | Methods pack + statements pack | `02-macro-logic` | — |
| `possible_data_leakage` | M2 | Methods pack (modeling portion) | `02-macro-logic` | — |
| `possible_reference_problem` | M2 | References pack | `02-macro-logic` | `external_figure_validation` (`reference_exists` / `cited_retracted`) |
| `possible_method_underreporting` | M3 | Methods pack | `03-experimental-methods` | — |
| `possible_cell_line_issue` | M3 | Methods identifiers pack | `03-experimental-methods` | `external_figure_validation` (`cell_line`) |
| `possible_identifier_issue` | M3 | Methods identifiers pack | `03-experimental-methods` | `sequence_identifier_audit` + X1 (`variant` / `gene_symbol` / `species` / `rrid`) |
| `possible_animal_necessity_issue` | M3 | Methods pack + ethics pack | `03-experimental-methods` | — |
| `possible_statistical_test_mismatch` | M4 | Statistics pack | `04-statistics` | — |
| `possible_sample_size_issue` | M4 | Statistics pack | `04-statistics` | `statistical_forensics` (when computable) |
| `possible_numeric_inconsistency` | M4 | Statistics pack + tables | `04-statistics` | `statistical_forensics` (**mandatory**) |
| `possible_multiplicity_issue` | M4 | Statistics pack | `04-statistics` | — |
| `possible_outcome_switching` | M4 | Statistics pack + registration info | `04-statistics` | X1 (`outcome_switching`) |
| `possible_figure_presentation_issue` | M5 | Figure pack | `05-figures-and-charts` | — |
| `possible_figure_duplication` | M5 | Figure pack (original images) | `05-figures-and-charts` | `figure_integrity_audit` (**mandatory**) |
| `possible_figure_text_contradiction` | M5 | Figure pack + related Results | `05-figures-and-charts` | — |
| `possible_blot_annotation_issue` | M5 | Figure pack | `05-figures-and-charts` | X1 (`blot_band`) |
| `possible_ethics_issue` | M6 | Ethics pack | `06-ethics-compliance` | `ethics_compliance_check` |
| `possible_registration_issue` | M6 | Ethics pack + registration info | `06-ethics-compliance` | X1 (`trial_registration`) |
| `possible_consent_issue` | M6 | Ethics pack | `06-ethics-compliance` | `ethics_compliance_check` |
| `possible_unsupported_claim` | M7 | Claim-evidence pack | `07-conclusions-discussion` | — |
| `possible_overgeneralization` | M7 | Claim-evidence pack + population description | `07-conclusions-discussion` | — |
| `possible_followup_overreach` | M7 | Claim-evidence pack + follow-up duration | `07-conclusions-discussion` | — |
| `possible_causal_overreach` | M7 | Claim-evidence pack + study design | `07-conclusions-discussion` | — |
| `possible_unit_dimension_issue` | M4 / M3 | Dose- and unit-related passages | Corresponding rulebase | `normalize_biomed_units` (**mandatory**) |

## 2. Ambiguity and Fallbacks

When a candidate type cannot be determined, apply the following fallbacks in order — **never drop it outright**:

1. **Candidate routable to multiple specialists** → route to all of them. The same issue gets a finding from each specialist,
   and Layer 4 global reconciliation merges them (`merged`) — safer than missing it.
2. **Candidate type not in the table above** → route to M2 (macro logic is the default recipient),
   and record `routing_fallback: true` in `candidate_resolution_log`.
3. **Candidate description too vague to locate evidence** → record status as `unresolved`,
   **never** `rejected` — we failed to locate it; that does not mean the issue does not exist.
4. **Cross-section issues** (two sections contradicting each other) → still go into the L4 global reconciliation queue for aggregation,
   but **no longer because specialists cannot see them** — specialists now have the full text and should also proactively report cross-section contradictions;
   L4's value shifts to **aggregation, deduplication, auditing**, and the final disposition of L0 entries.

## 3. Index Definitions (Formerly "Evidence Packs")

> **Important change (architectural axiom)**: specialists now **get the full text**. The table below is no longer "the specialist may only see these,"
> but "these locations are known to be relevant — start reading here." **The index is a starting point, not a boundary.**
> The old wording "never feed the whole paper to a specialist" is obsolete — real runs proved it makes the deepest scientific issues
> structurally undiscoverable (see SKILL.md §0.0).

| Pack | Contents |
| --- | --- |
| Methods pack | Full Methods section, reagent and equipment passages, sample sources, related Supplement methods |
| Methods identifiers pack | Cell lines, antibodies/RRIDs, gene symbols, species and strains, accession numbers, variant notations in Methods |
| Statistics pack | Statistical methods passages, related Results passages, tables, statistics in figure captions, sample sizes, tests, p values, CIs |
| Figure pack | The images themselves, figure captions, first in-text citation, related Results passages, related methods |
| Ethics pack | Study design summary, human/animal subjects methods, ethics statements, informed consent, registration info, conflict-of-interest and data-availability statements |
| Claim-evidence pack | Verbatim claim text, Results supporting the claim, associated tables/figures, follow-up duration, study population, limitations passages |
| References pack | Reference list, DOIs/PMIDs, in-text citation locations |
| Cross-section pack | `paper_map` + `claim_map` + relevant passages from the two or more sections involved |
| Statements pack | Funding, conflicts of interest, data availability, author contributions, registration numbers |

**Every index comes with lightweight global context** (see §4).

## 4. Global Context Every Specialist Must Carry

In addition to the full text, still provide this summary — it lets the specialist see at a glance what it is looking at, sparing it from re-inferring:

```json
{
  "study_design": "randomised controlled trial",
  "experiment_id": "EXP-02",
  "supports_claims": ["CL-05"],
  "related_figures": ["Figure 4"],
  "related_tables": ["Table 3"],
  "n_total": 89,
  "followup_duration": "48 hours"
}
```

The statistics specialist knows at a glance that Table 3 belongs to EXP-02 and supports CL-05, without having to infer this from scratch;
but **when the Discussion needs reading, it must still go read it** — the full text is in its hands.

## 5. Two Trigger Modes for Tools

Tools are **not only** for verifying LLM candidates — they must also **scan proactively**.
The latter matters most: the real uplift usually comes from deterministic checks a bare model (no-skill baseline) would never think to run.

| Mode | Trigger | Example |
| --- | --- | --- |
| **Candidate verification** | Specialist suspects a problem → requests tool verification | Suspects mismatched denominators → `statistical_forensics` recomputes |
| **Proactive scanning** | Runs automatically the moment a structured object is parsed, without waiting for candidates | Table parsed with count columns → automatically run `table_total_mismatch` |

Proactive-scanning target list:

| What is parsed | What runs automatically |
| --- | --- |
| Any table with mutually exclusive, exhaustive category counts | `statistical_forensics.table_total` |
| Any "count + percentage" | `statistical_forensics.count_percentage` |
| Any "mean + integer scale + n" | `statistical_forensics.grim` |
| Any test statistic + df + p | `statistical_forensics.test_statistic_p` |
| Any point estimate + CI | `statistical_forensics.ci_estimate` |
| Any cell line name | X1 `cell_line` |
| Any NCT registration number | X1 `trial_registration` + `outcome_switching` |
| All DOIs in the reference list | X1 `reference_exists` + `cited_retracted` |
| Any human gene symbol | X1 `gene_symbol` |
| Any image file | `figure_integrity_audit` |
| Any dose-unit pair | `normalize_biomed_units` |

**Proactive scanning must never be skipped because "no candidate points to it."**

## 6. Every Final Finding Must Be Labeled with Its Origin

```
global_review | specialist_rule | deterministic_tool | external_validation |
cross_section_reconciliation | multiple_sources
```

This is the sole basis for judging "does this architecture actually add uplift": whatever is unique to `global_review` is what the bare model (no-skill baseline)
already had — **it does not count as uplift**; only what is unique to the other origins does. If the uplift is small,
it means the five-thousand-line rulebase contributes little, and it should be trimmed accordingly rather than growing more rules.
