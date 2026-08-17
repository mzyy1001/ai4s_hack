# M1 · Structured Extraction (Upstream Layer)

**Owner: MZYY (Chen Hongrui)** · Status: **contract finalized, rulebase being populated**

M1 is the pipeline's **upstream extraction layer**, not a review module parallel to M2–M7.
M2–M7 all consume M1's output (after the Stage 3b merge), so errors here are amplified sixfold.
The only safe policy is: **prefer marking a status over inferring a fill-in value.**

**This file depends on `00-contracts.md`.** The **definitions** of the evidence registry, numeric
variants, the three field dimensions, observation groups, the three record kinds, execution scope,
and the scoring formulas all live there; this file only defines M1's **field inventory,
design routing, and operational rules**. Where the two conflict, `00-contracts.md` prevails.

---


> **Position in the layered architecture (2026-08-07)**: M1 is the extraction layer between Layer 1
> and Layer 2. It **produces no findings**; its job is to extract fields and **verifiable
> identifiers** (cell lines, UniProt accessions, human gene symbols, species scientific names,
> RRIDs, compound names, PDB IDs, NCT registration numbers, data accession numbers,
> reference DOIs) and register them as query entry points for Layer 3 external validation.
> Without this step, X1's proactive scanning has nothing to trigger on — and proactive scanning
> is the main source of uplift over the bare model.
> Extraction itself does not require reading the M2–M7 rulebases.


## 1. Responsibilities and non-responsibilities

### 1.1 What M1 does

| Responsibility | Output |
| --- | --- |
| Extract structured facts from **textual sources** (body text, tables, figure caption text) | `structured_result_v1` |
| Assign applicability / requiredness / status plus evidence for every important field | `extracted_field` (§3) |
| Determine the study design and, based on it, decide which fields apply | `article_design` (§4) |
| Organize numeric values into observation groups, preparing for the Stage 3b merge | `key_data[]` (§6) |
| Record machine-level observations for downstream interpretation | `m1_extraction_signals[]` (§9) |
| Record system capability limitations | `stage2_system_limitations[]` (§10.2) |
| Register all evidence | append entries to the `evidence_registry` (§10.1) |
| Provide a routing index | `evaluation_matrix` (§11) |
| Provide raw coverage data | `coverage_inputs` (§12.2) |

### 1.2 What M1 does **not** do

**M1 produces no `finding` of any kind.** This is a hard contract, no exceptions.
`00-contracts.md §6.1` stipulates that `finding.module` may only take `M2`–`M7`; `M1` is illegal.

For the same phenomenon, M1 only describes "what was observed"; the corresponding module decides
"whether this constitutes a manuscript problem":

| Phenomenon | M1 output | Decided by | What is decided |
| --- | --- | --- | --- |
| Two values disagree | `source_value_conflict` signal | **M2** | Whether it constitutes an internal contradiction in the manuscript |
| A claim has no supporting evidence to be found | `claim_without_resolved_evidence_link` signal | **M7** | Whether it constitutes an unsupported claim |
| No randomization description found | `randomization.status = not_reported` + absence evidence | **M3 / M4** | Whether it constitutes a design flaw |
| No ethics statement found | `ethics_statement.status = not_reported` + absence evidence | **M6** | Whether it constitutes a compliance problem |
| No sample size justification found | `sample_size_justification.status = not_reported` | **M4** | Whether it constitutes a statistical reporting deficiency |
| Study design clues contradict each other | `ambiguous_study_design` signal | **M2 / M3 / M4** | Whether it constitutes an unclear design description |
| Field is present but no unique reading can be obtained | `ambiguous_extraction` signal | **M2 / M4** | Whether it constitutes unclear wording |
| Conditionally required field ultimately unresolved | `coverage_inputs.unresolved[]` entry (**not a record**) | —— | Only lowers coverage |
| Image unreadable / paragraph cannot be extracted | `system_limitation` | —— | Not a manuscript problem; only lowers coverage |

> **Migration note**: an older version of M1 produced `extraction_quality_findings[]` (containing
> two "finding" kinds, `ambiguous_extraction` and `required_field_unresolved`).
> That array is **abolished**: the former is now a signal; the latter is now a
> `coverage_breakdown` entry. Full mapping in `00-contracts.md §10`.

---

## 2. Extraction order (v1 stage)

1. **Methods first**; do not start from the Abstract — the abstract is the authors' sales pitch;
   the methodology is the source of facts.
2. Results body text → add `key_data` observations, tagged `explicit_main_text`.
3. Tables → add observations, tagged `explicit_table`.
4. Figure caption **text** → add observations, tagged `explicit_figure_caption`.
5. Declarations / Ethics / Funding / Data availability → fill declaration-type fields.
6. Read the Abstract **last**, **for cross-checking only**. When abstract and body values disagree,
   the abstract **must not** override the body — both observations go into the same observation
   group, and Stage 3b decides compatibility per `00-contracts.md §5.4`.
7. **Image content itself is not read in the v1 stage** — that is Stage 3's (Figure Parser's)
   responsibility, and the results flow back in Stage 3b. Fields absent from text but possibly
   present in figures are marked `unresolved` (§7).

---

## 3. The three field dimensions (local conventions)

Dimension definitions are in `00-contracts.md §3`. M1's operational points:

### 3.1 The order of determination must not be reversed

```
1. Determine applicability   ← decided by §4 design routing + §5 applicability rules
2. Determine requiredness    ← decided by the §5 conditional routing tables
3. Determine status          ← decided by the actual search outcome
```

**Determine applicability before searching.** A field with `applicability = not_applicable` is
**neither searched nor given absence evidence**; write `status: not_applicable` + `na_reason` directly.

### 3.2 The only legitimate basis for `not_applicable`

`not_applicable` may be set only when the §5.3 conditional routing tables explicitly determine that
the field is **conceptually undefined** for the current design:

```json
{
  "field_path": "design.randomization",
  "applicability": "not_applicable",
  "requiredness": "optional",
  "status": "not_applicable",
  "value": null,
  "na_reason": "article_design.primary_design.type = case_report; a single-case report has no arms, so the concept of randomization does not apply",
  "evidence_refs": []
}
```

**Expressly forbidden**: marking a field `not_applicable` because it "does not enter the coverage
denominator". The coverage denominator is controlled by `requiredness` (`00-contracts.md §8.2`) and
has nothing to do with applicability.
An `applicable + optional` field must still be searched and may still be `not_reported`;
it simply does not enter the main denominator.

When `primary_design.status = "ambiguous"` or `primary_design.alternatives[]` is non-empty,
run §5.3 for each candidate design in turn: if all candidates yield the same
applicability / requiredness for a field, keep that shared result; if the candidate results differ
at all, write the field as
`applicability: "applicability_uncertain"`, `status: "ambiguous"`, and reference the
`ambiguous_study_design` signal. `not_applicable` **must not** be assigned merely because the
design is undetermined. For `family: "other"`, all design-specific fields still take this
uncertainty branch per §4.4.

### 3.3 Absence-evidence requirements

`status: not_reported` requires `absence` evidence, and the search must cover **all** locations
listed in each field's `search_scope` column in §5:

```json
{
  "id": "EV-019",
  "type": "absence",
  "scope": "document",
  "searched_locations": [
    {"section": "methods", "scope": "section"},
    {"section": "declarations", "scope": "section"},
    {"supplement_id": "S1", "scope": "supplement"}
  ],
  "search_terms": ["randomization", "random allocation", "randomly assigned",
                   "随机分组", "随机化"],
  "search_result": "no_match",
  "created_by": "stage_2"
}
```

**Four rules**

1. `absence` evidence **must not** contain a `quote` or `locator`. Never fabricate a quotation for
   content that does not exist.
2. When the search scope is incomplete, absence **must not** be asserted; downgrade to
   `parse_failed` and explain the uncovered portion in `system_limitation.impact`.
3. **When supplementary material is unavailable, every field that depends on it is `parse_failed`
   without exception; it must not be marked `not_reported`** — we have not seen the supplementary
   material, so we cannot say it is not written there. Also produce a
   `supplement_inaccessible` `system_limitation`.
4. `search_result: partial_match_ambiguous` is **insufficient** to support an absence conclusion;
   reclassify as `ambiguous` and produce an `ambiguous_extraction` signal.

---

## 4. Study design routing

### 4.1 Hierarchical enumeration

```
experimental
  in_vitro | ex_vivo | organoid | in_vivo_animal | preclinical_mixed

human_interventional
  randomized_controlled_trial | nonrandomized_trial | single_arm_trial

human_observational
  cohort | case_control | cross_sectional | diagnostic_accuracy
  case_series | case_report

evidence_synthesis
  systematic_review | meta_analysis | scoping_review

computational
  bioinformatics | prediction_model | simulation | method_development | benchmark_study

mixed
  mixed_multi_family

other
  other_unclassified
```

**`family` and `type` must appear as a matching pair.** Giving a family without a type is a
contract violation.

### 4.2 Storage form: article_design

**Distinguish "the article contains multiple designs" from "the extractor is uncertain"** — the old
contract stuffed both into `alternatives[]`, leaving M3/M4/M6 unable to know which rule set to run
against which experiment.

```json
"article_design": {
  "primary_design": {
    "family": "experimental",
    "type": "preclinical_mixed",
    "status": "reported",
    "evidence_refs": ["EV-003"],
    "extraction_confidence": "high",
    "alternatives": []
  },
  "design_components": [
    {"experiment_id": "EXP-01", "family": "experimental", "type": "in_vitro",
     "evidence_refs": ["EV-005"], "extraction_confidence": "high"},
    {"experiment_id": "EXP-02", "family": "experimental", "type": "in_vivo_animal",
     "evidence_refs": ["EV-007"], "extraction_confidence": "high"}
  ]
}
```

| Purpose | Field | Semantics |
| --- | --- | --- |
| The paper **genuinely** contains multiple designs | `design_components[]` | One entry per `experiment_id`, each routed independently |
| The extractor is **uncertain** among several readings | `primary_design.alternatives[]` | Each item `{family, type, evidence_refs}`; also emit an `ambiguous_study_design` signal |

**The two must never be mixed.** A non-empty `design_components[]` states a factual multi-design
paper, irrespective of confidence; a non-empty `alternatives[]` means we failed to read it
precisely and a signal is mandatory.

Selection rules for `primary_design` (ordered; stop at the first hit):

1. The design of the experiment that carries the `primary_endpoint`;
2. The design the manuscript's title or abstract self-declares (e.g. "a randomized controlled trial");
3. The design of the experiment occupying the largest share of the Results;
4. If none of the above resolves it, first distinguish two causes: multiple confirmed design
   components with no single primary design → classify as `mixed` per §4.4; the extractor is
   uncertain among several candidate readings → write
   `primary_design.alternatives[]` and emit an `ambiguous_study_design` signal.
5. Only when the design fits none of the families and types in §4.1 may it be classified `other` (§4.4).

### 4.3 Applicability routing precedence

```
1. Experiment-level type rules   the dedicated rules of design_components[].type for that experiment_id
2. Article-level dedicated rules the dedicated rules of primary_design.type (e.g. case_report)
3. Family-level rules            the rules of primary_design.family
4. Default rules                 the generic field inventory of §5.1
```

**Stop at the first hit; a higher-priority rule fully overrides lower ones.**

Example: `primary_design.type = case_report` (family `human_observational`).
The family-level rules require `confounders` and `follow_up`, but the dedicated `case_report`
rules mark both `not_applicable` — **the dedicated rules win**; no spurious absence may be produced.

Example: `primary_design.type = preclinical_mixed`, with `EXP-01` `in_vitro` and
`EXP-02` `in_vivo_animal`. `ethics_statement` is applicable and required for `EXP-02`
but not applicable to `EXP-01` — **decide per experiment**, splitting into two entries in the
`evaluation_matrix` (each with its own `applies_to`); do not take the "or".

### 4.4 Storage semantics of mixed and other

**`family: "mixed"`** is legal only when **both** of the following hold:

1. `design_components[]` contains ≥2 entries with **different families**;
2. No single component carries all of the `primary_endpoint` (i.e. rules 1–3 of §4.2 fail to
   identify a primary design).

In that case `primary_design = {"family": "mixed", "type": "mixed_multi_family"}`, and
applicability routing **takes the union of the component families' rules**:
if a field is `applicable` for **any** component, it is `applicable` at the article level;
`requiredness` takes the **highest** level among the components
(`required` > `recommended` > `optional`).

**`family: "other"`** means the design **cannot be classified** into any of the above families,
and requires all of:

1. Fill in `other_description` (free text stating the design as self-described by the manuscript);
2. Set the `applicability` of every design-specific field (§5.2) to `applicability_uncertain`;
3. Emit an `ambiguous_study_design` signal with `routed_to: ["M2", "M3", "M4", "M6"]`.

**`other` is not a fallback option.** Whatever can be assigned to a family must be;
if `other` exceeds 5% of the corpus, the §4.1 enumeration needs expansion (see §13 TODO).

---

## 5. Field inventory and conditional routing

### 5.1 Generic field inventory

All fields use the `extracted_field` structure of `00-contracts.md §3.3`.
`search_scope` defines the **minimum** search range for `absence` evidence.

#### 5.1.1 objective · Research objective

| Field | Description | search_scope |
| --- | --- | --- |
| `research_question` | The question the paper aims to answer, in one sentence | abstract, introduction, discussion |
| `hypothesis` | An explicitly stated hypothesis | introduction, methods |
| `primary_endpoint` | Primary endpoint / primary outcome measure | abstract, methods, results |
| `secondary_endpoints` | Secondary endpoints (array) | methods, results |

> `article_design` is not in this table — it has its own dedicated storage structure (§4.2) and is
> not an ordinary `extracted_field`. It is the **master routing field**: M3 uses it to decide
> whether to run the animal-experiment necessity check, M4 uses it to select the statistical
> specification table, M6 uses it to decide ethics requirements, and M1 itself uses it to decide
> which fields apply. Extracting it wrong sends the wrong rule sets running in four places.

#### 5.1.2 population · Study subjects

| Field | Description | search_scope |
| --- | --- | --- |
| `subjects` | Species/strain/cell line/population, including provenance | methods |
| `inclusion_criteria` | Inclusion criteria | methods |
| `exclusion_criteria` | Exclusion criteria | methods |
| `participant_spectrum` | Participant spectrum (disease-severity distribution, recruitment setting) | methods |

#### 5.1.3 design · Design and intervention

| Field | Description | search_scope |
| --- | --- | --- |
| `arms` | Trial arms / experimental groups (array, see §5.4) | methods, figure captions |
| `interventions` | Interventions (array) | methods |
| `controls` | Control setup (array) | methods |
| `exposure` | Exposure factor (observational studies) | methods |
| `confounders` | Confounders and adjustment method | methods, statistics |
| `follow_up` | Follow-up duration and loss to follow-up | methods, results |
| `randomization` | Description of the **randomization method** (how the sequence was generated) | methods |
| `allocation_concealment` | **Allocation concealment** (how the sequence was hidden from recruiters) | methods |
| `blinding` | Blinding: `none`/`single`/`double`/`triple` | methods |
| `registration` | Registration number and registration date | abstract, methods, declarations |

> **The old contract's `allocation` field is abolished.** It conflated "randomization" with
> "allocation concealment", which are two mutually independent items in CONSORT (randomized but
> without concealed allocation is a common flaw).
> Always split into the two fields `randomization` + `allocation_concealment`.

#### 5.1.4 measurement · Measurement and analysis

| Field | Description | search_scope |
| --- | --- | --- |
| `assays` | Each item `{name, purpose, reference_citation}` | methods |
| `index_test` | Test under evaluation (diagnostic studies) | methods |
| `reference_standard` | Reference standard / gold standard (diagnostic studies) | methods |
| `target_condition` | **Target disease / condition to be diagnosed** (diagnostic studies) | title, abstract, methods |
| `statistical_methods` | Each item `{test, applied_to, software, correction}` | methods, figure captions |
| `sample_size_justification` | Power analysis or sample size rationale | methods |
| `missing_data_handling` | Handling of missing data | methods, statistics |

> **`target_condition` is a new field correcting a misuse in the old contract.** The old table had
> diagnostic accuracy studies stuff the "target disease" into `primary_endpoint`, though the two
> have entirely different semantics:
> `target_condition` is **the thing being diagnosed** (e.g. "pulmonary tuberculosis"), while
> `primary_endpoint` is **the accuracy metric** (e.g. "sensitivity and specificity"). Both are
> required and neither may stand in for the other.

#### 5.1.5 conclusion · Conclusions

| Field | Description | search_scope |
| --- | --- | --- |
| `claims` | Each item `{claim_id, statement, scope, supported_by[]}` | abstract, discussion, conclusion |
| `limitations` | Limitations acknowledged by the authors | discussion |
| `generalization_scope` | The scope of applicability the authors claim | discussion, conclusion |

`claims[].supported_by[]` stores `key_data.id` values or `evidence_ref`s;
when none can be resolved, see §9 and emit `claim_without_resolved_evidence_link`.

#### 5.1.6 declarations · Declarations

| Field | search_scope |
| --- | --- |
| `ethics_statement` (incl. approval number, approving body) | declarations, methods, ethics |
| `informed_consent` | declarations, methods |
| `funding` | declarations, funding |
| `conflict_of_interest` | declarations |
| `data_availability` | declarations, data_availability |

### 5.2 design_specific field definitions

The fields below **apply only to specific design families** and are stored under the
`structured_result.design_specific` block, likewise with the `extracted_field` structure.
**Every field appearing in the §5.3 routing tables must be defined here or in §5.1.**

#### 5.2.1 evidence_synthesis specific

| Field | Description | search_scope |
| --- | --- | --- |
| `databases_searched` | List of databases searched (PubMed / Embase / CENTRAL / CNKI…) | methods |
| `search_date` | Date the search was run, or its cutoff date | methods, abstract |
| `search_strategy` | Full search string (often in supplementary material) | methods, supplement |
| `risk_of_bias_method` | Risk-of-bias assessment tool (RoB 2 / ROBINS-I / NOS / QUADAS-2) | methods |
| `synthesis_method` | Synthesis method (fixed/random effects model, heterogeneity measure, qualitative synthesis) | methods |
| `protocol_registration` | Protocol registration number (PROSPERO etc.) | methods, declarations |

#### 5.2.2 computational specific

| Field | Description | search_scope |
| --- | --- | --- |
| `dataset` | Dataset source, size, version, accessibility | methods, data_availability |
| `split_strategy` | Train/validation/test split method and ratio; whether split by subject | methods |
| `baselines` | List of baseline methods compared against | methods, results |
| `metrics` | List of evaluation metrics (AUC / F1 / MAE…) | methods, results |
| `validation_protocol` | Validation protocol (cross-validation folds, external validation cohort, temporal validation) | methods |

> `split_strategy` and `validation_protocol` are the primary inputs to M2's data-leakage scenario
> library (see `02-macro-logic.md`). M1 only extracts; it does **not** decide whether leakage exists.

### 5.3 Conditional routing tables

**Column meanings**: `applicability rule` gives the condition determining applicability;
`requiredness` gives the required level;
`applicable study types` gives the designs the rule applies to; `review consumer` gives the main
downstream module. Generic fields not appearing in these tables default to
`applicable + optional` (**not** `not_applicable`).

**Conditional execution semantics**

1. Fields joined with `/` within a table row must be split into independent fields, each
   materialized and counted toward coverage individually; the whole row must not be stored as one field.
2. The normative lower bound of `search_scope` is §5.1 / §5.2; the same-named column in the routing
   tables may only add locations, never narrow the range.
   Absence searches use the union of the two.
3. Conditions containing "applies only to …" or "applies when … is present" are executed with
   three-valued `true / false / unknown` semantics:
   `true` uses the row's result; `false` writes `not_applicable + optional` with a concrete
   `na_reason`; `unknown` writes `applicability_uncertain + ambiguous`, retains the row's
   requiredness level, and emits a `partial_extraction` or `ambiguous_study_design` signal.
   `unknown` must never be treated as `false`.
4. If a row's "applicable designs" lists only some design types and does not explicitly declare
   the rest inapplicable, unlisted types fall through to the next priority level;
   e.g. the dedicated required rule for `controls` in `case_control` does not turn cohort's
   optional controls into not-applicable.

**Closed criteria for the conditional predicates**

| Predicate | `true` | `false` | `unknown` |
| --- | --- | --- | --- |
| Statistical analysis present | Any of: test statistics / p-values / CIs, regression or survival models, correlation analysis, meta-analysis pooling, curve-fitting parameters | The full text reports only raw counts or descriptive summaries, with no between-group / between-timepoint inference | Statistics section, table notes, or supplementary methods unavailable |
| Loss to follow-up or missing values present | Any of: participant attrition, missing cells, denominators shrinking over timepoints, complete-case / imputation / missingness descriptions | All expected measurements have complete flow or count evidence, and denominators do not shrink at any timepoint | Participant flow, analysis denominators, or tables cannot be recovered |
| Delayed-type reference standard | Reference status is determined by events during a follow-up period or by outcomes later than the index test | The reference standard is obtained within the same diagnostic window | Temporal relationship not reported |
| Regulated primary material used | Newly collected human samples, patient-derived cells / organoids, or material obtained by sacrificing animals for this study | Established commercial cell lines, public de-identified data, or pre-existing non-regulated material | Material source or new-vs-existing status not reported |
| Case received an intervention | The case received treatment, surgery, or a diagnostic procedure performed for that case, and the manuscript evaluates its process or outcome | Pure natural history, phenotype, or prior medical-record description, with no procedure evaluated by this study | Case timeline or purpose of the procedure cannot be recovered |

#### 5.3.1 Common to all designs (default rules, priority 4)

| Field | applicability rule | requiredness | Applicable designs | search scope | review consumer |
| --- | --- | --- | --- | --- | --- |
| `research_question` | Always applicable | `required` | All | abstract, introduction | M2, M7 |
| `hypothesis` | Always applicable | `optional` | All | introduction, methods | M2, M7 |
| `primary_endpoint` | Always applicable | `required` | All | abstract, methods, results | M2, M4, M7 |
| `secondary_endpoints` | Always applicable | `optional` | All | methods, results | M4, M7 |
| `subjects` | Always applicable | `required` | All | methods | M3, M6 |
| `statistical_methods` | Applicable when any statistical comparison exists | `required` | All | methods, figure captions | M4 |
| `claims` | Always applicable | `required` | All | abstract, discussion | M7 |
| `limitations` | Always applicable | `recommended` | All | discussion | M7 |
| `generalization_scope` | Always applicable | `optional` | All | discussion, conclusion | M7 |
| `funding` | Always applicable | `recommended` | All | declarations, funding | M2 |
| `conflict_of_interest` | Always applicable | `recommended` | All | declarations | M2 |
| `data_availability` | Always applicable | `recommended` | All | declarations | M2 |
| `missing_data_handling` | Applicable when loss to follow-up or missing values exist | `recommended` | All | methods, statistics | M4 |

#### 5.3.2 human_interventional family (priority 3)

| Field | applicability rule | requiredness | Applicable designs | search scope | review consumer |
| --- | --- | --- | --- | --- | --- |
| `arms` | Always applicable | `required` | Whole family | methods | M3, M4 |
| `interventions` | Always applicable | `required` | Whole family | methods | M3 |
| `controls` | Not applicable to `single_arm_trial` | `required` | RCT, nonrandomized | methods | M3, M4 |
| `randomization` | RCT only | `required` | RCT | methods | M3, M4 |
| `allocation_concealment` | RCT only | `required` | RCT | methods | M4 |
| `blinding` | Always applicable (may be `none`) | `required` | Whole family | methods | M3, M4 |
| `registration` | Always applicable | `required` | Whole family | abstract, methods, declarations | M6, M4 |
| `sample_size_justification` | Always applicable | `required` | Whole family | methods | M4 |
| `inclusion_criteria` / `exclusion_criteria` | Always applicable | `required` | Whole family | methods | M3, M6 |
| `follow_up` | Always applicable | `required` | Whole family | methods, results | M4 |
| `ethics_statement` | Always applicable | `required` | Whole family | declarations, methods | M6 |
| `informed_consent` | Always applicable | `required` | Whole family | declarations, methods | M6 |
| `exposure` | Not applicable to interventional studies (the intervention is `interventions`) | `optional` | —— | —— | —— |

#### 5.3.3 human_observational family (priority 3)

| Field | applicability rule | requiredness | Applicable designs | search scope | review consumer |
| --- | --- | --- | --- | --- | --- |
| `exposure` | Always applicable | `required` | cohort, case_control, cross_sectional | methods | M3, M4 |
| `controls` | For `case_control`, the control source and selection rules are always applicable | `required` | case_control | methods | M3, M4 |
| `confounders` | Always applicable | `required` | cohort, case_control, cross_sectional | methods, statistics | M4 |
| `follow_up` | **Longitudinal designs only**; **not applicable** to `cross_sectional` and `case_control` | `required` | cohort | methods, results | M4 |
| `inclusion_criteria` / `exclusion_criteria` | Always applicable | `required` | Whole family | methods | M3, M6 |
| `ethics_statement` | Always applicable | `required` | Whole family | declarations, methods | M6 |
| `informed_consent` | Retrospective de-identified data may be exempt → `applicable + recommended` | `recommended` | Whole family | declarations, methods | M6 |
| `sample_size_justification` | Always applicable | `recommended` | Whole family | methods | M4 |
| `randomization` / `allocation_concealment` / `arms` | Not applicable to observational studies | `optional` | —— | —— | —— |

> **`cross_sectional` must not be required to have `follow_up`.** A cross-sectional study measures
> at a single timepoint; the concept of follow-up does not apply. Mark
> `not_applicable` + `na_reason: "cross-sectional design has no follow-up period"`.
> The old contract's blanket `follow_up` requirement for the whole `human_observational` family
> was wrong. Same for `case_control` — it samples by outcome status; the study may be retrospective
> or nested within a prospective cohort, but follow-up after the index timepoint is not an
> essential concept of that design.

#### 5.3.4 diagnostic_accuracy dedicated rules (priority 2)

| Field | applicability rule | requiredness | search scope | review consumer |
| --- | --- | --- | --- | --- |
| `target_condition` | Always applicable | `required` | title, abstract, methods | M3, M4 |
| `index_test` | Always applicable | `required` | methods | M3 |
| `reference_standard` | Always applicable | `required` | methods | M3, M4 |
| `participant_spectrum` | Always applicable | `required` | methods | M4 |
| `primary_endpoint` | Always applicable; **means the accuracy metric**, not the target disease | `required` | abstract, methods, results | M4 |
| `blinding` | Whether index test and reference standard were interpreted blind to each other | `required` | methods | M3, M4 |
| `exposure` / `confounders` | Not applicable to diagnostic accuracy studies | `optional` | —— | —— |
| `follow_up` | Applicable only with a delayed-type reference standard | `optional` | methods | M4 |

#### 5.3.5 case_report / case_series dedicated rules (priority 2, overriding family level)

| Field | applicability | requiredness | na_reason template |
| --- | --- | --- | --- |
| `subjects` | `applicable` | `required` | —— |
| `primary_endpoint` | `applicable`; means the clinical outcome the case report focuses on; no pre-specified statistical endpoint required | `recommended` | —— |
| `inclusion_criteria` / `exclusion_criteria` | `case_series`: `applicable`; `case_report`: `not_applicable` | `case_series`: `required`; `case_report`: `optional` | A single case has no enrollment or exclusion criteria; a case series must have its case-selection rules extracted |
| `interventions` | `applicable` when the case received an intervention, otherwise `not_applicable` | `required` when triggered, otherwise `optional` | A purely natural-history/phenotype description has no intervention evaluated by this study |
| `informed_consent` | `applicable` | **`required`** | —— |
| `ethics_statement` | `applicable` | `recommended` | —— |
| `limitations` | `applicable` | `recommended` | —— |
| `arms` | **`not_applicable`** | `optional` | A single-case/small-series report has no arm structure |
| `randomization` | **`not_applicable`** | `optional` | No arms, so the concept of randomization does not apply |
| `allocation_concealment` | **`not_applicable`** | `optional` | No random allocation |
| `controls` | **`not_applicable`** | `optional` | A descriptive report has no control group |
| `sample_size_justification` | **`not_applicable`** | `optional` | A descriptive case report/series performs no pre-specified inferential sample size estimation |
| `confounders` | **`not_applicable`** | `optional` | No statistical adjustment |
| `follow_up` | `applicable` | `recommended` | —— |
| `statistical_methods` | Applicable only when comparisons beyond descriptive statistics exist | `optional` | A purely descriptive report has no statistical tests |

#### 5.3.6 experimental family (priority 3, incl. experiment-level breakdown)

| Field | applicability rule | requiredness | Applicable designs | review consumer |
| --- | --- | --- | --- | --- |
| `subjects` | Always applicable (cell lines / species and strains) | `required` | Whole family | M3, M6 |
| `interventions` | Always applicable | `required` | Whole family | M3 |
| `controls` | Always applicable | `required` | Whole family | M3, M4 |
| `assays` | Always applicable | `required` | Whole family | M3 |
| `arms` | Always applicable (incl. replicate count and replicate type) | `required` | Whole family | M4 |
| `ethics_statement` | Always applicable for `in_vivo_animal`; for `in_vitro` / `ex_vivo` / `organoid` applicable only when human material or freshly obtained primary material from research animals is used; `applicability_uncertain` when the source is unclear | `required` | in_vivo_animal; in_vitro, ex_vivo, organoid using regulated primary material | M6 |
| `informed_consent` | Applicable when human primary material is used; the value may be consent given or an approved waiver; not applicable to established commercial cell lines and purely animal material; `applicability_uncertain` when the source is unclear | `required` | in_vitro, ex_vivo, organoid using human primary material | M6 |
| `randomization` | **`in_vivo_animal` only** | `required` | in_vivo_animal | M3, M4 |
| `blinding` | **`in_vivo_animal` only** | `recommended` | in_vivo_animal | M3, M4 |
| `sample_size_justification` | **`in_vivo_animal` only** | `required` | in_vivo_animal | M4, M6 |
| `inclusion_criteria` / `exclusion_criteria` | Always applicable for `in_vivo_animal`, used to extract pre-specified inclusion and removal criteria | `recommended` | in_vivo_animal | M3 |
| `registration` | Not applicable to experimental studies | `optional` | —— | —— |

> `preclinical_mixed` has no row of its own in this table — it must be expanded into
> `design_components[]` and routed per experiment-level type (`in_vitro` / `in_vivo_animal`).
> Example: `ethics_statement` is `applicable + required` for `EXP-02` (in_vivo_animal),
> and `not_applicable` for `EXP-01` (in_vitro).

> An established commercial cell line does not automatically trigger participant consent just
> because it is described as "human-derived".
> M1 must first extract the material source from `subjects` (established cell line / human
> primary material / research-animal material / unclear), then route the two fields above;
> an unclear source must not be marked `not_applicable`.

#### 5.3.7 evidence_synthesis family (priority 3)

| Field | applicability rule | requiredness | Applicable designs | review consumer |
| --- | --- | --- | --- | --- |
| `databases_searched` | Always applicable | `required` | Whole family | M2, M3 |
| `search_date` | Always applicable | `required` | Whole family | M2 |
| `search_strategy` | Always applicable | `recommended` | Whole family | M3 |
| `inclusion_criteria` / `exclusion_criteria` | Always applicable | `required` | Whole family | M2, M3 |
| `risk_of_bias_method` | Always applicable for systematic_review / meta_analysis; scoping_review may perform it but is not obliged to | systematic_review, meta_analysis: `required`; scoping_review: `optional` | Whole family | M4 |
| `synthesis_method` | Always applicable | `required` | Whole family | M4 |
| `protocol_registration` | Always applicable | `recommended` | Whole family | M2, M6 |
| `subjects` | Means the populations of the included studies | `required` | Whole family | M3 |
| `ethics_statement` | Not applicable to secondary-literature research | `optional` | —— | —— |
| `informed_consent` | Not applicable to secondary-literature research | `optional` | —— | —— |
| `arms` / `randomization` / `follow_up` | Not applicable at the review level | `optional` | —— | —— |

> `scoping_review` is not obliged to perform a risk-of-bias assessment, but the concept still
> holds. It must therefore be marked `applicable + optional`; when unreported it is
> `not_reported`, not `not_applicable`, and it does not enter the main coverage denominator.

#### 5.3.8 computational family (priority 3)

| Field | applicability rule | requiredness | Applicable designs | review consumer |
| --- | --- | --- | --- | --- |
| `dataset` | Always applicable | `required` | Whole family | M2, M3 |
| `split_strategy` | **`prediction_model` / `benchmark_study` only** | `required` | prediction_model, benchmark_study | **M2** (leakage), M4 |
| `baselines` | Applicable to `method_development` / `benchmark_study` | `required` | method_development, benchmark_study | M2, M4 |
| `metrics` | Always applicable | `required` | Whole family | M4 |
| `validation_protocol` | **`prediction_model` / `benchmark_study` only** | `required` | prediction_model, benchmark_study | **M2** (leakage), M4 |
| `statistical_methods` | Applicable when statistical comparisons exist | `recommended` | Whole family | M4 |
| `data_availability` | Always applicable | **`required`** (reproducibility prerequisite for computational studies) | Whole family | M2 |
| `ethics_statement` | Applicable when human-subject data are used | `required` | Those using human data | M6 |
| `arms` / `randomization` / `follow_up` | Not applicable to computational studies | `optional` | —— | —— |

### 5.4 arms[] · Experiment-level structure

`arms[]` retains **experiment-level** context; it is never collapsed into a single global value:

```json
{
  "experiment_id": "EXP-01",
  "arm_name": "vehicle",
  "n": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": {"type": "point", "number": 6},
    "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  },
  "replicate_type": "biological",
  "intervention": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": "0.9% saline", "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  },
  "dose": {
    "applicability": "not_applicable", "requiredness": "optional",
    "status": "not_applicable", "value": null,
    "na_reason": "vehicle control arm has no administered dose", "evidence_refs": []
  },
  "route": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": "i.p.", "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  },
  "duration": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": "14 d", "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  }
}
```

`replicate_type` enumeration: `biological` / `technical` / `unspecified`.
When the manuscript does not state it, use `unspecified` and emit a `partial_extraction` signal
(consumed by M4) — `biological` **must not** be filled in by default.

---

## 6. key_data observation groups

### 6.1 M1's responsibilities in the v1 stage

Structure defined in `00-contracts.md §5.2`. **M1 only creates groups and deposits observations;
it makes no merge decisions**:

1. Create one `observation` for every numeric value extracted from textual sources, with full
   `provenance` (including `derivation`).
2. Deposit observations into the matching `key_data` group by the §6.2 `grouping_key`;
   create the group if it does not exist.
3. **Group `status` in the v1 stage**:
   - Only one observation in the group → `reported`, with `canonical_observation` pointing to it.
   - Multiple observations in the group → **always `ambiguous`, `canonical_observation: null`**.
     Compatibility determination is Stage 3b's responsibility; M1 does not do it.
   - The group expects a value to be supplied from a figure → `pending_visual_resolution` (§7).
4. `reporting_completeness` in the v1 stage is always `not_assessed`, with `missing_elements: []`
   — it can only be assessed per §6.3 after Stage 3b fixes the canonical observation.

**M1 never deletes or overwrites any observation.**

### 6.2 Metric identity + the five-key grouping_key

```
experiment_id | group | comparison | timepoint | endpoint
```

First require identical `metric_family` and normalized `metric_name`; then require **all five keys**
to be equal for observations to belong to the same group (`null` equals `null`; `null` on one side
and a value on the other counts as unequal).
`metric_name` stores the canonical name from the project metric vocabulary; the original alias is
preserved in the evidence `quote`.

**Key-filling rules**

| Key | How to fill | When it cannot be determined |
| --- | --- | --- |
| `experiment_id` | The manuscript's experiment label, or an M1-assigned `EXP-nn` | `null` + `partial_extraction` signal |
| `group` | Group name, taken from `arms[].arm_name` | `null` |
| `comparison` | The comparison relation, e.g. `"Compound A vs vehicle"` | `null` (a single-group descriptive value inherently has no comparison) |
| `timepoint` | Measurement timepoint, e.g. `"72h"` / `"day 28"` | `null` (single-timepoint study) |
| `endpoint` | Name of the endpoint the value corresponds to | `null` + `partial_extraction` signal |

**Common mistake**: forcing "the IC50 in Fig 2C" and "the IC50 in Table 1" into one group when
their `experiment_id`s differ — those are two values from two experiments, not a conflict.
**Non-matching keys mean two groups.**

### 6.3 Metric-family completeness rules

**The old "every value needs unit + n + error" three-element rule is withdrawn** — it fails for
counts, proportions, and dimensionless metrics. `reporting_completeness` is judged per
**metric family** (executed after Stage 3b fixes the canonical observation):

| metric_family | Elements required for complete reporting | Notes |
| --- | --- | --- |
| `continuous_summary` | value + unit (when dimensioned) + n + dispersion(SD/SEM/IQR/range) | Dimensionless metrics do not require unit |
| `effect_estimate` | estimate + CI + reference_group + model | Mean differences, OR, RR |
| `count` | count + population_or_denominator_context | No unit required, no error required |
| `proportion` | (numerator + denominator) or (proportion + n) | No unit required |
| `p_value` | p_value + test + comparison | No n required (n attaches to the compared data points) |
| `correlation` | coefficient + n + method(Pearson/Spearman/…) | No unit required |
| `time_to_event` | HR + CI + reference_group + model | Median survival is counted separately as `continuous_summary` |
| `dose_response` | IC50/EC50 + unit + fitting_method + CI (when reported in the original) | An unreported CI does not lower extraction_confidence |
| `classification_metric` | metric_name + value + evaluation_set + threshold_or_averaging (when relevant) | AUC/F1/accuracy, dimensionless |
| `diagnostic_accuracy` | sensitivity + specificity + CI + reference_standard + 2×2 counts (when obtainable) | Reporting only one metric is incomplete |

**Determination rules**

- All elements present → `complete`.
- Missing elements → `incomplete`, with each missing item listed in `missing_elements[]`
  (e.g. `["dispersion", "n"]`).
- Missing elements the family does not require → **not counted** in `missing_elements`;
  no effect on completeness.
- `canonical_observation` is `null` → always `not_assessed`, `missing_elements: []`.

`reporting_completeness: "incomplete"` is an **M4 finding lead**; M1 only records it and raises no finding.

### 6.4 Extraction confidence and reporting completeness are orthogonal

| Scenario | extraction_confidence | reporting_completeness |
| --- | --- | --- |
| Figure caption explicitly states `IC50 = 12.4 μM (95% CI …)` + fitting method | `high` | `complete` |
| Figure caption explicitly states `IC50 = 12.4 μM`, no CI, no fitting method | `high` (confident we read it correctly) | `incomplete` (missing fitting_method) |
| Only readable as roughly 12–15 μM off a log-scale axis | `low` (estimated read) | Judged separately by the elements reported in the original |
| Relevant text exists but is self-contradictory | Group `status: ambiguous` (v1) | `not_assessed` |

---

## 7. Pending visual-resolution lifecycle

Contract in `00-contracts.md §4`. M1's operational rules:

### 7.1 When to mark `unresolved`

`unresolved` in this section refers specifically to `extracted_field.status`; numeric observation
groups use `key_data.status: "pending_visual_resolution"`. Both carry a `resolution_state` of the
same shape, but the enumerations are not interchangeable.

The mark may be applied only when **all** of the following hold:

1. The field has `applicability = applicable`;
2. It was not found after a **complete search** of the textual sources (body text, tables,
   figure caption text);
3. The manuscript **contains** an identifiable visual source that may carry the value
   (the body says "as shown in Fig 2C", or the figure's type typically carries this kind of
   value per `05-figures-and-charts.md`).

```json
{
  "field_path": "objective.primary_endpoint",
  "applicability": "applicable",
  "requiredness": "required",
  "status": "unresolved",
  "value": null,
  "resolution_state": {
    "state": "pending_visual_resolution",
    "pending_stage": "stage_3",
    "expected_sources": ["fig:2C"]
  },
  "evidence_refs": ["EV-022"],
  "extraction_confidence": "high",
  "system_limitation_ref": null
}
```

`evidence_refs` points to `present` evidence for the **cross-reference itself** (the body sentence
"see Fig 2C"), proving we have grounds to expect the figure to carry the value.

### 7.2 Three prohibitions

1. **Never** mark `parse_failed` — Stage 3 has not been attempted yet, so there is no failure to speak of.
2. **Never** fill `system_limitation_ref` — this is not a system limitation.
3. **Never** produce `absence` evidence — we have not finished looking, so we cannot claim absence.

### 7.3 What to do when condition 3 is not met

Not found in text, and **no identifiable visual source at all** (no cross-reference, and the figure
types do not carry this kind of value)
→ mark `not_reported` + `absence` evidence as usual. **Do not** hang every unfound field as
`unresolved` — that would hand Stage 3b a pile of unresolvable attachment points that all degrade
to `parse_failed`, spuriously depressing coverage.

### 7.4 Stage 3b's convergence obligation

Stage 3b **must** resolve every `unresolved` into one of `reported` / `not_reported` /
`ambiguous` / `conflicting` / `parse_failed`.
**No `unresolved` may remain in `structured_result_v2`** (a lint item, `00-contracts.md §11`).

| Stage 3 outcome | status in v2 | Accompanying output |
| --- | --- | --- |
| Read from the figure, no conflict with text (or text had no value) | `reported` | —— |
| Read from the figure and incompatible with existing observations | `conflicting` | `source_value_conflict` signal |
| Figure readable, but confirmed not to carry the value | `not_reported` | Add `absence` evidence (search scope includes the figure) |
| Figure unreadable / panel missing | `parse_failed` | `system_limitation` (`figure_unreadable`) + `system_limitation_ref` |
| Mode ends at v1; neither Stage 3 nor 3b executed | keep `unresolved` (legal in v1 only) | Counted in `coverage_breakdown.unresolved_required_fields[]` |

In modes requiring v2, if `unresolved` exists within the scope, scoped Stage 3 must not be skipped.
Stage 3b must not converge it to `not_reported` or `parse_failed` without attempting `expected_sources[]`.

---

## 8. structured_result_v1 and v2

| Version | Produced by | Data source | May contain `unresolved` | Consumers |
| --- | --- | --- | --- | --- |
| `structured_result_v1` | **M1 (Stage 2)** | Text only: body, tables, figure caption **text** | ✅ | Stage 3 (context), Stage 3b; `structured_extraction` may output it directly when no visual needs exist |
| `structured_result_v2` | **Stage 3b** | v1 + figure/chart parsing results, conflicts resolved | ❌ | **All of M2–M7** |

**M1 does not produce v2.** M1's responsibility ends at v1; merging is Stage 3b's responsibility.
**M2–M7 consume v2 without exception** — reading v1 directly would miss all figure-derived values
and could run into `unresolved`.

The v1 top level must carry `"version": "v1"` and `"stage_3b_executed": false`,
rewritten by the output-assembly step to `"version": "v2"` / `true` at v2.

---

## 9. extraction_signals

The array M1 produces is named **`m1_extraction_signals[]`** (stage-local, aggregated at Stage 5).
**Signals carry no `severity` and are not conclusions.** The structure and all fifteen current
types are in `00-contracts.md §6.2`; this section lists only the subset directly involved in M1's
core extraction flow.

### 9.1 The five signals M1 may produce

| type | M1 trigger condition | Routed to |
| --- | --- | --- |
| `source_value_conflict` | **Not produced** in the v1 stage — compatibility determination is Stage 3b's responsibility | —— |
| `claim_without_resolved_evidence_link` | `claims[].supported_by` resolves to no `key_data.id` or `evidence_ref` | M7 |
| `ambiguous_study_design` | Conflicting design clues, non-empty `primary_design.alternatives[]`, or family classified `other` | M2, M3, M4, M6 |
| `unresolved_cross_reference` | A figure/table/supplement cited in the body resolves to no entity (Fig 6 cited but only 5 figures exist) | M2, M5 |
| `partial_extraction` | Field partially extracted: n without group attribution, dose without unit, `replicate_type` unstated | M4, M5 |
| `ambiguous_extraction` | Field `status: ambiguous`; relevant text exists but yields no unique reading | M2, M4 |

> **M1 does not produce `source_value_conflict`.** When abstract and body disagree, M1 deposits
> both observations into the same `key_data` group and marks the group `ambiguous`; **Stage 3b**
> determines compatibility per `00-contracts.md §5.4` and then decides whether to escalate to
> `conflicting` and emit the signal.
> This corrects the old contract's contradiction between "M1 directly emits
> source_value_conflict" and "compatibility determination belongs to Stage 3b".

### 9.2 Example

```json
{
  "id": "SIG-007",
  "type": "ambiguous_study_design",
  "target": "article_design.primary_design",
  "detail": "Title self-describes as 'a prospective cohort study', but Methods §2.1 describes intervention allocation by the envelope method; the evidence for the two readings is of comparable strength.",
  "observation_refs": [],
  "evidence_refs": ["EV-003", "EV-009"],
  "routed_to": ["M2", "M3", "M4", "M6"],
  "produced_by": "stage_2"
}
```

**Rule**: when a downstream module raises a finding based on a signal, it must provide manuscript
evidence **independently** in that finding's `evidence_refs[]`; citing only the signal id is not
allowed (`00-contracts.md §6.1` rule 5).

---

## 10. Evidence registration and system limitations

### 10.1 Using the evidence_registry

M1 **appends** entries **to** the `evidence_registry` established by Stage 1, with
`created_by: "stage_2"`.

**Four operational rules**

1. **Register first, reference second.** Any id in `evidence_refs` must already exist in the registry.
2. **Reuse over create.** Evidence with the same locator + same quote reuses the existing entry
   rather than creating a new one — this is the precondition for Stage 5's cross-module clustering
   to align on primary anchors.
3. **Never modify existing entries.** Once an id is assigned, the content is immutable; to correct
   something, create a new entry.
4. **Absence evidence must be registered too.** It is the only legitimate support for
   `not_reported`; without registration the field's status is invalid.

### 10.2 stage2_system_limitations[]

Produced when extraction fails for technical reasons; structure and the twelve-value enumeration
are in `00-contracts.md §6.3`. Common M1 triggers:

| category | Scenario |
| --- | --- |
| `parse_failed` | Paragraph cannot be extracted, garbled encoding |
| `table_unparseable` | Table structure cannot be reconstructed |
| `supplement_inaccessible` | Supplementary material is cited but cannot be obtained |
| `ocr_low_quality` | Insufficient OCR quality on a scanned document |
| `input_truncated` | Input truncated; some sections missing |
| `section_missing_from_input` | The input itself lacks the section (e.g. only Methods was provided) |

**Under `supplement_inaccessible`, every field depending on the supplementary material is
`parse_failed` without exception; it must not be marked `not_reported`** — we have not seen it, so
we cannot say it is not written there.
And the field **must** have `system_limitation_ref` pointing to this limitation.

---

## 11. evaluation_matrix

### 11.1 Purpose and limits

The `evaluation_matrix` is a **routing and index** tool for M2–M7, letting downstream modules
decide which rules to run and where to find evidence without rereading the full text.

1. It **may** be used to decide which rule sets to run and to locate relevant evidence.
2. Findings **must not** be raised from it alone. M2–M7 must go back to the registry entries
   pointed to by `evidence_refs` and independently provide `evidence_refs[]` in the finding.
3. Experiment-level information **must not** be collapsed into a single global number.

### 11.2 Entry structure

Every entry is a **status-aware object**, not a bare boolean, and carries all three dimensions:

```json
"randomization": {
  "applicability": "applicable",
  "requiredness": "required",
  "status": "not_reported",
  "applies_to": ["EXP-01", "EXP-02"],
  "evidence_refs": ["EV-018"],
  "extraction_confidence": "high"
}
```

`status` takes the seven-value enumeration of `00-contracts.md §3.1`. `applies_to` lists the
experiments the judgment covers;
**when statuses differ across experiments, split into multiple entries — never take the "or"**:

> **A matrix entry is a pure index, not a copy of the field.** It **must not** carry `value`,
> `na_reason`, or `system_limitation_ref` — those three are properties of the field itself, and
> copying them into the matrix inevitably drifts from the field.
> A downstream module wanting `na_reason` follows `evidence_refs` and the field path back to the
> original field. An entry **must** carry `applies_to` (this is its shape boundary against
> `extracted_field`).

```json
"ethics_statement": [
  {"applicability": "applicable", "requiredness": "required", "status": "reported",
   "applies_to": ["EXP-02"], "evidence_refs": ["EV-031"], "extraction_confidence": "high"},
  {"applicability": "not_applicable", "requiredness": "optional", "status": "not_applicable",
   "applies_to": ["EXP-01"], "evidence_refs": [], "extraction_confidence": "high"}
]
```

### 11.3 Entry inventory

| Key | Consumers | Notes |
| --- | --- | --- |
| `has_animal_experiment` | M3, M6 | |
| `has_human_subjects` | M6 | |
| `ethics_statement` | M6 | May be an array (split per experiment) |
| `informed_consent` | M6 | |
| `registration` | M6, M4 | |
| `randomization` | M3, M4 | |
| `allocation_concealment` | M4 | |
| `blinding` | M3, M4 | |
| `sample_size_justification` | M4 | |
| `multiple_comparison_correction` | M4 | |
| `has_ml_model` | M2, M4 | Triggers M2's data-leakage scenario library |
| `has_split_strategy` | M2 | Used together with `has_ml_model`; a missing split description is a high-risk leakage signal |
| `has_external_validation` | M2, M4 | Taken from `validation_protocol` |
| `data_availability` | M2 | |
| `conflict_of_interest` | M2 | |
| `all_figures_cited_in_text` | M2, M5 | |
| `figure_count` / `table_count` | M5 | Count fields; take the integer directly |
| `group_sizes` | M4 | **Array**, see §11.4 |

### 11.4 group_sizes: preserving experiment-level context

**The old single-integer `min_group_n` is withdrawn** — it squashed all experiments into one
number, losing exactly the information M4 actually needs: "which group of which experiment has
the small sample size".

```json
"group_sizes": [
  {"experiment_id": "EXP-01", "group": "vehicle", "n": 6,
   "replicate_type": "biological", "evidence_refs": ["EV-021"]},
  {"experiment_id": "EXP-01", "group": "treated", "n": 6,
   "replicate_type": "biological", "evidence_refs": ["EV-021"]},
  {"experiment_id": "EXP-03", "group": "siRNA", "n": 3,
   "replicate_type": "technical", "evidence_refs": ["EV-034"]}
]
```

M4 computes minima and distributions per experiment on its own; **M1 makes no aggregate judgment**.

---

## 12. Operational log and coverage data

### 12.1 gaps[] · Operational log (not a record)

`gaps[]` is an **operational log** recording troubleshooting leads for unresolved extraction
problems, used for tuning and debugging.
**It is not a way of representing field status** (status is carried by §3's `status`);
**it is not a finding** and enters no score.

```json
{
  "field_path": "measurement.sample_size_justification",
  "status_assigned": "not_reported",
  "attempts": ["full-text search of methods §2.6", "search of supplement S1", "search of figure captions"],
  "search_terms": ["power", "sample size", "样本量", "效能"],
  "resolution": "confirmed_absent",
  "note": "M4 will rely on the absence evidence in EV-019 for its assessment"
}
```

`resolution` enumeration: `confirmed_absent` / `unresolved` / `resolved_in_stage3b` /
`blocked_by_system_limitation`.

### 12.2 coverage_inputs · Raw coverage data

M1 outputs the **raw counts** needed to compute `extraction_coverage`,
which Stage 5 assembles into `coverage_breakdown` (`00-contracts.md §7.2`).

```json
"coverage_inputs": {
  "fields_in_scope": ["objective.research_question", "measurement.sample_size_justification"],
  "resolved": ["objective.research_question"],
  "unresolved": [
    {"field_path": "measurement.sample_size_justification", "status": "parse_failed",
     "reason_ref": "SYS-007"}
  ],
  "required_applicable_total": 2,
  "recommended_applicable_total": 5
}
```

**Rules**

1. `fields_in_scope` must be a subset of `execution_scope.fields`.
2. **Only fields with `applicability = applicable ∧ requiredness = required` enter
   `required_applicable_total`** (the main denominator).
3. `status ∈ {reported, not_reported}` counts as resolved;
   among `{ambiguous, conflicting, parse_failed, unresolved, not_applicable}`,
   the first four count as unresolved, and `not_applicable` **enters neither numerator nor denominator**.
4. The combined length of `resolved` + `unresolved` must equal `required_applicable_total`.

---

## 13. TODO (phase 1)

- [ ] Fill in boundary examples for the §4.1 hierarchical enumeration: distinguishing `ex_vivo`
      from `organoid`, the applicability conditions of `preclinical_mixed`, the boundary between
      `prediction_model` and `benchmark_study`
- [x] The unit normalizer is implemented in `scripts/normalize_biomed_units.py`; Stage 3b must
      invoke it per `00-contracts.md §5.4`, and no second hand-written unit table is maintained
- [ ] Fill in the search-term vocabularies (bilingual, Chinese and English) for each field's
      `search_scope`, for use in absence searches
- [ ] Confirm with M5 the field-level integration list for §7 `expected_sources`:
      which `metric_family` should expect which figure types to carry it
- [ ] Run over the 10-paper corpus in `datasets/`, compute `field_resolution_rate` broken down by
      `primary_design.type`, and calibrate whether the `requiredness` in the §5.3 tables is too strict
- [ ] Track the usage rate of `other_unclassified`; if it exceeds 5%, expand the §4.1 enumeration
- [ ] Write 1 complete + 1 incomplete example for each `metric_family` in §6.3
- [ ] Write 1 "should be not_applicable" + 1 "should not be" contrastive example for each routing
      table in §5.3

---

## 14. Online enhancement: identifier authenticity validation (X1 connector **delivered**)

M1's responsibility in this chain is **extracting the verifiable identifiers** (cell line names,
UniProt accessions, gene symbols, species scientific names, RRIDs, compound names, PDB IDs,
NCT registration numbers, data accession numbers, reference DOIs) and registering them as X1
query entry points. **M1 itself produces no findings and receives no X1 signals**
— without this step, none of the subsequent external queries can be triggered.

The current `scripts/sequence_identifier_audit.py` already checks, offline, common accession-number
formats, a supported subset of HGVS, sequence alphabets, and ranges plus reference residues against
versioned complete reference sequences. When a sequence lacks an accession, version, or
completeness declaration, only `partial_extraction` is produced; a fragment must not be treated as
a complete reference sequence. It **cannot prove that the record really exists**. The online
enhancement, once connected to authoritative data sources, validates existence and metadata item by
item. Online results are uniformly written as `external` evidence and
`external_validation_candidate` (see `00-contracts.md §1`, §6.2), and must not modify M1 provenance.

| Identifier | Validation data source | What it finds | Interpretation owner |
| --- | --- | --- | --- |
| Clinical trial registration number | ClinicalTrials.gov / ChiCTR / WHO ICTRP | Number does not exist, endpoints deviate from registration, registration later than enrollment | **M6** |
| Cell line name | Cellosaurus / ICLAC | Known misidentified or cross-contaminated cell lines | **M3** |
| Antibody / reagent | RRID (Antibody Registry) | Whether RRID, vendor, catalog number, target, host, reactive species, and registry warnings are consistent; a registry record not listing an application only means unknown — it cannot prove lack of specificity | **M3** |
| Gene / protein symbol | HGNC / UniProt | Symbol deprecated or misspelled, species mismatch | **M2** |
| References | Crossref / PubMed / Retraction Watch | Reference does not exist, has been retracted or corrected | **M2** |
| Protocol registration number | PROSPERO | Review protocol unregistered or deviating from the registered protocol | **M2** |

The external evidence layer only validates identifier facts and produces severity-free signals;
**it draws no review conclusions**. All connectors reuse the single type
`external_validation_candidate`; no parallel `identifier_verification` type may be added.
Comparison results take only `match/mismatch/not_comparable/needs_manual_review`;
network or interface failures produce an X1 `system_limitation` and must not be treated as
`not_found` or a mismatch.
