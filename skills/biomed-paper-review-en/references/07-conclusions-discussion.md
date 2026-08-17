# M7 · Conclusions & Discussion Soundness

**Owner: MY (Minyi)** · Status: **Phase-1 rulebase populated**

The **closing module** of the whole pipeline. Core question: is every claim the paper makes supported by its own data?

**Current delivery boundary**: offline, only the **claim ↔ evidence alignment** is judged. The X1 contract has landed but the connector
is not yet implemented, so we still do not query external evidence, do not judge novelty, and do not perform common-sense checks. Conclusions that violate basic
common sense are flagged as `claim_beyond_evidence` and routed to manual review.

Those three capabilities can serve as Phase-1 online enhancements, and this module is their home; rules in §11. None of them is currently implemented,
and all of them rest on "having already accurately extracted every claim and its supporting evidence"; if that step is done poorly,
connecting external databases only means comparing the wrong claims against them.

**This file depends on `00-contracts.md`.** The finding structure, `evidence_refs[]`, severity enum, and
evidence registry are all defined there. An M7 finding **must** independently provide manuscript evidence in `evidence_refs[]`;
it must not cite only a signal id.

## Contents

- §1 Inputs; §2 Prerequisites for claim parsing
- §3 Evidence tiers and claim tiers; §4 Assertion strength
- §5 Rulebase; §6 Interplay with lower modules; §7 Boundary with M2
- §8 Category slugs; §9 Positive/negative examples; §10 TODO; §11 Phase-1 online enhancement

---

## 1. Inputs

| Source | Purpose |
| --- | --- |
| `structured_result_v2.conclusion.claims[]` | Full set of claims; each has `claim_id` / `statement` / `scope` / `supported_by[]` / `evidence_refs[]` |
| `structured_result_v2.article_design` | **Primary basis for determining the evidence tier** (§3.1) |
| `structured_result_v2.key_data[]` | Verify whether the values pointed to by `supported_by` actually support the claim |
| `structured_result_v2.conclusion.limitations` | Adjudicate `limitations_evasive` |
| `figure_records[]` | When a claim cites a figure, verify the figure actually shows that conclusion |
| `claim_without_resolved_evidence_link` in `m1_extraction_signals[]` and `merge_extraction_signals[]` | Flags which claims have a broken support chain. **Only these two arrays produce this type** — Stage 3 produces only figure-integrity candidates and X1 produces only external candidates; you will not find it there. **Do not consume `all_extraction_signals[]`**: that is a Stage 5 aggregation product, and M7 runs in Stage 4 — reading it would create a temporal cycle |
| **Findings from M2–M6** | A conclusion's credibility depends on whether the layers beneath it have collapsed (§6) |

**M7 must run last.** It is the only module that needs to consume other review modules' outputs.
In the parallel execution of Stage 4, M7 is scheduled after M2–M6.

---

## 2. Prerequisites for claim parsing

### 2.1 Every claim must first be assigned four attributes

| Attribute | Values | Determined from |
| --- | --- | --- |
| `claim_tier` | C0–C6, see §3.2 | The semantics of `statement` |
| `assertion_mode` | `assertive` / `hedged` | The wording of `statement`, see §4 |
| `scope_qualified` | `true` / `false` | Whether the `scope` field states species/dose/population/time-window qualifiers |
| `location` | `abstract` / `discussion` / `conclusion` | In `evidence_refs[]`, select the evidence whose `quote` covers the claim's original text, then read its locator; do not default to the array's first item |

All four are indispensable — the overreach determination (§5.1) depends on all four attributes at once.

### 2.2 Boundaries of claim extraction

M7 **does not re-extract** claims — `claims[]` is produced by M1 in Stage 2.
If `claims[]` is an empty array while the manuscript clearly has a conclusion section, M1 extraction failed.
M7 **must not** raise a finding on that basis, nor invent its own "observation" records; terminate M7, request a Stage 2 rerun,
and confirm whether Stage 2 already has a `parse_failed`-type `system_limitation`. Stage 4 has no authority to write
`system_limitation` records, so a missing record should be returned to the orchestrator as a pipeline input-contract error.

---

## 3. Evidence tiers and claim tiers (core of this module)

### 3.1 Evidence tier: evidence_tier

Determined by `article_design`. When a paper has multiple `design_components[]`,
**each claim takes the tier of the experiment its `supported_by` actually points to**,
not the paper's highest tier — this is the most common source of misjudgment.

| tier | Name | Corresponding `design.type` |
| --- | --- | --- |
| `E0` | Computational / predictive | `bioinformatics`, `prediction_model`, `simulation` |
| `E1` | Molecular / cell-free system | `in_vitro` (biochemical assays, no live cells) |
| `E2` | Cell | `in_vitro` (cell lines or primary cells) |
| `E3` | Organoid / ex vivo tissue | `organoid`, `ex_vivo` |
| `E4` | Animal in vivo | `in_vivo_animal` |
| `E5` | Human observational | `cohort`, `case_control`, `cross_sectional`, `case_series`, `case_report` |
| `E6` | Human interventional, non-randomized | `nonrandomized_trial`, `single_arm_trial` |
| `E7` | Human randomized controlled | `randomized_controlled_trial` |
| `E8` | Evidence synthesis | `systematic_review`, `meta_analysis` |

`diagnostic_accuracy` is treated separately: its evidence tier depends on the subject spectrum and reference standard;
treat it as `E5`, but see the §3.3 footnote for the diagnostic-performance claims it permits.

`evidence_tier` denotes only the **capability ceiling** the study subjects and design can provide; it is not a quality score. Risk of bias,
analysis failures, or evidence uncertainty can only lower that ceiling; it cannot be raised because the sample is large, the journal is prestigious, or a meta-analysis
was performed. `E8` must be traced back to the designs of the included studies that actually support the claim; evidence synthesis by itself creates no causal,
human, or recommendation capability.

### 3.2 Claim tier: claim_tier

| tier | Name | Typical wording |
| --- | --- | --- |
| `C0` | Descriptive observation | "We observed that X increased under condition Y" |
| `C1` | Association | "X is associated with Y"; "X levels correlate positively with Y risk" |
| `C2` | Mechanism | "X regulates Y through the Z pathway" |
| `C3` | Causation | "X causes / induces / drives Y"; "Knockout of X abolished Y" |
| `C4` | Translational potential | "X is a potential therapeutic target / biomarker" |
| `C5` | Clinical efficacy | "X is effective for treating Y"; "X improves patient outcomes" |
| `C6` | Clinical recommendation | "X should be used clinically"; "X is recommended as first-line therapy" |

### 3.3 Permission table (core Phase-1 criterion)

**`max_assertive_tier`**: the highest claim tier that may be **asserted outright** at that evidence tier.
**`max_hedged_tier`**: the highest claim tier that may be **proposed** with compliant qualifying language (§4).

| evidence_tier | max_assertive_tier | max_hedged_tier | Notes |
| --- | --- | --- | --- |
| `E0` pure simulation / pure prediction output | `C0` description | `C2` mechanistic hypothesis | May only describe model output; `C2` must be phrased as a hypothesis awaiting validation |
| `E0` bioinformatic association on empirical data / model validation | `C1` association | `C2` mechanistic hypothesis | Association is limited to the actual dataset; predictive performance goes through the diagnostic/prognostic footnote instead |
| `E1` molecular | `C2` mechanism | `C3` causation | Causation in a cell-free system is limited to that biochemical reaction itself |
| `E2` cell | `C3` causation* | `C4` translational potential | C3 is limited to the manipulated cell system; C4 must be explicitly framed as a candidate awaiting animal/human validation |
| `E3` organoid | `C3` causation | `C4` translational potential | Causation is limited to that model system |
| `E4` animal | `C3` causation | `C4` translational potential | **Causation must be species-qualified**; C5 clinical efficacy must not be asserted outright |
| `E5` case report / case series | `C0` description | `C4` translational hypothesis | Must not estimate association or efficacy; C4 denotes only a candidate awaiting validation arising from that case |
| `E5` cross-sectional / case-control / cohort | `C1` association | `C1` association** | Observational causal inference goes through §5.3 and is not automatically upgraded by soft wording |
| `E6` non-randomized controlled intervention | `C3` causation | `C5` clinical efficacy | C5 is limited to the target population with a concurrent control, a clearly defined time zero, and confounding control |
| `E6` single-arm intervention | `C0` description | `C4` translational potential | Observed response/change rates may be asserted outright; natural history or regression to the mean must not be presented as efficacy |
| `E7` RCT | `C5` clinical efficacy | `C5` clinical efficacy | Efficacy must be qualified by trial population, intervention/control, endpoint, and follow-up duration; a single RCT does not automatically support a recommendation |
| `E8` evidence synthesis | Inherits the ceiling of the synthesized evidence | Same; `C6` goes through EtD*** | A meta-analysis of observational studies is still observational evidence; when mixed designs are not stratified, automatically setting a ceiling is forbidden |

\* `E2 → C3` requires all of: an intervention, matched controls, a direct endpoint, and a rescue or a second orthogonal intervention;
with only expression correlation, a single drug treatment, or a single siRNA, the ceiling remains `C1/C2`.

\** Mendelian randomization, natural experiments, target trial emulation, etc. do not use a single three-item checklist; check
that design's own identification assumptions per §5.3. An ordinary longitudinal regression, even with temporality, control of measured confounders,
and one sensitivity analysis, does not automatically acquire causal capability.

\*** `E8 → C6` never enters automatic adjudication. Only when the manuscript explicitly executes an Evidence-to-Decision process, reporting at least
evidence certainty, absolute benefits and harms, values and preferences, resources/feasibility, and the applicable population, is the recommendation claim handed to manual confirmation;
for an ordinary systematic review / meta-analysis the ceiling is still determined by the included studies.

> `diagnostic_accuracy` footnote: diagnostic claims must not be forced onto the "association→efficacy" axis.
> "Under this study's subject spectrum and reference standard, sensitivity/specificity was X" is `C0`;
> replication in an external cohort supports only populations comparable to that cohort in case spectrum, setting, threshold, and reference standard, and does not automatically prove generalizability;
> demonstrating that using the test changes management and improves patient outcomes is `C5`; recommending it for screening is `C6`, which additionally requires benefit–harm
> evidence in the target screening population. AUC, sensitivity/specificity, or calibration alone cannot establish clinical utility.

> `safety` footnote: adverse-event occurrence is a `C0` description within the observation window; "safe for the target population" is checked as a `C5`
> clinical claim. Zero events does not mean zero risk, an animal NOAEL is not a safe human dose, and short-term common adverse events
> cannot cover rare, delayed, or subgroup-specific risks. A safety scope must at minimum be bound to species/population, dose, route of administration, exposure duration,
> sample size, and active/passive monitoring method.

### 3.4 Tier gap and severity

```
Δ = claim_tier − the ceiling permitted at that evidence tier
    (use max_assertive_tier in assertive mode, max_hedged_tier in hedged mode)

Δ ≤ 0          → no finding
Δ = 1          → major
Δ ≥ 2          → major; escalate only if the critical conditions below are met
```

For `E8`, first resolve the designs of the included studies that actually support the claim, then substitute that design's ceiling. When included designs are mixed and unstratified,
or the claim cannot be bound to a specific synthesis result, do not compute Δ; route to manual review. Do not default to `C5/C6`.

**Critical conditions** (any one suffices):

1. `E0–E4` evidence is used to assert `C5/C6` outright, and that sentence is the main conclusion of the abstract or the body;
2. all of the claim's direct support, after same-anchor verification per §6, is shown to be unusable for the inference, and the claim is still asserted outright as a main conclusion.

**Adjustments** (compute Δ first, then apply in order):

| Condition | Adjustment |
| --- | --- |
| `scope_qualified = false`, and the claim genuinely dropped the cell-line/species/population/dose/time-window/endpoint qualifiers present in the supporting evidence | Add 1 to Δ, at most once |
| Claim is in the Abstract's concluding sentence | Δ unchanged; raise `manual_review.priority` by one level, up to `P0` |
| Claim is in a future-directions paragraph and `hedged` | Δ unchanged; `hedged` is already accounted for in the ceiling — double-discounting is forbidden |
| A same-anchor upstream finding exists | Do not change Δ directly; per §6, judge item by item whether that finding invalidates the direct support |

`scope_qualified = true` only means there is no additional scope overreach; it **must not** automatically lower the mechanism, causation, efficacy, or recommendation tier
by one level. Location affects propagation risk and manual-review priority; it does not change whether a claim is scientifically warranted.

---

## 4. Assertion-strength determination (hedging)

### 4.1 Qualifying-verb whitelist (rated `hedged`)

Only when the qualifier syntactically modifies **the claim's core predicate** is the claim rated `hedged`; a string hit alone is not enough:

```
English: may / might / could / suggest(s) / indicate(s) that ... may /
      appear(s) to / seem(s) to / potential / potentially / possible /
      warrants further study / merits investigation /
      these findings raise the possibility / preliminary evidence
Chinese: 可能 / 提示 / 或可 / 有望 / 潜在 / 似乎 / 值得进一步研究 /
      初步提示
```

### 4.2 Assertive verbs (rated `assertive`)

```
English: demonstrate(s) / prove(s) / establish(es) / confirm(s) / shows that /
      causes / induces / drives / leads to / is effective / should be used /
      is recommended / therapeutic efficacy
Chinese: 证明 / 证实 / 确立 / 表明……导致 / 引起 / 驱动 / 有效 /
      应当 / 推荐 / 具有疗效
```

### 4.3 Determination rules

1. **Judge by the qualifier's scope, not by word-list priority.**
   "These results demonstrate that X may improve outcomes" is `hedged` with respect to "improving outcomes";
   "These results demonstrate a 30% reduction" is `assertive`. The negation in `did not demonstrate` or
   `failed to establish` must be parsed together with the verb; do not rate as assertive on a hit of `demonstrate/establish`.
2. **The qualifier must modify the claim itself, not a subordinate element.**
   "X significantly reduced tumor volume, which may involve apoptosis" —
   the claim "X reduces tumor volume" is `assertive` (`may` modifies only the mechanistic conjecture).
   Split into two claims and rate each separately.
3. **`is associated with` is an assertive `C1`, not hedging.**
   "X is associated with Y" is rated `C1 + assertive`; only "X may be associated with Y" is rated
   `C1 + hedged`. If the object itself contains a causal predicate ("associated with causing Y"), split the causal clause into a separate claim.
4. **Distinguish epistemic modals from normative modals.** `may/might/could` are hedging only when they express evidential uncertainty;
   `should be considered for routine use` and `may be recommended` are still `C6` recommendation claims and cannot be demoted to `C4` because of the modal.
   `potential/promising` change only the `assertion_mode`; if the object of the claim is a treatment, diagnostic
   use, or recommendation, the `claim_tier` is still rated by that object.
5. **First distinguish positive claims, negative claims, and uncertainty statements.** "No serious adverse events were observed" is a
   `C0` observation qualified by sample and time window; "X is safe" is a clinical safety claim; "cannot exclude benefit/harm" only states that the interval still permits
   some effect and must not be parsed as the corresponding positive efficacy/harm claim. `not associated` is an assertive `C1`
   null-association proposition, not hedging; then check its precision per §5.4.

---

## 5. Rulebase

Each rule specifies: trigger conditions, severity, and **evidence requirements** (the manuscript evidence M7 must independently provide).

### 5.1 `claim_beyond_evidence` · extrapolation beyond experimental conditions

- **Trigger**: Δ > 0 per §3.4, or the claim widens the cell-line/species/population/
  dose/time-window/endpoint qualifiers explicitly stated in the supporting evidence into a broader scope; and the case does not belong to the dedicated situations of §5.3 / §5.4.
- **severity**: per §3.4; `major` when there is only scope expansion without a tier overreach.
- **Evidence requirements**: at least two `present` entries —
  (1) the claim's original text (`evidence_refs` taken from `claims[].evidence_refs`);
  (2) the methodological text that establishes the evidence tier (e.g. "HepG2 cells were treated…").
  **The conclusion text alone is not enough** — the reviewer must be able to see "what tier of experiment this paper actually performed".
- **detail must state**: the measured evidence tier, the claim tier, the permitted ceiling, Δ, and the adjustments.

Scope axes are compared automatically only when **both the evidence scope and the claim scope have been resolved**. Judge axis by axis over species/model, population, intervention,
control, endpoint, dose, route of administration, and time window; scope expansion holds only if at least one axis proves the claim is a strict superset or dropped a qualifier.
If any relevant axis is `null`, a synonym mapping is not unique, or containment would rest only on domain-knowledge guessing,
route to manual review and do not add to Δ automatically. Containment between different diseases, cell lines, or drugs must not be established from name similarity alone.

Typical overreach patterns (Minyi's original table preserved, with tier mappings added):

| Overreach pattern | Tier expression |
| --- | --- |
| Cell experiment → direct claim of clinical efficacy | E2 → C5, Δ=2 and critical condition 1 met → critical |
| Single species/strain → claim about humans or a universal mechanism | Tier may not be exceeded, but a scope axis expands → major |
| Single-center small sample → population-level recommendation | E5/E6 → C6, Δ≥1 → major and up |
| Specific dose/time window → claim of efficacy under arbitrary conditions | `scope_qualified = false` and the scope genuinely widened → add 1 to Δ |
| Correlational study → causal claim | See §5.3 `causal_overreach` |

### 5.2 `unsupported_claim` · claim without data support

- **Trigger** (any one suffices):
  1. `claims[].supported_by` is an empty array, and after completing the target-section and figure/table-scope search per `00-contracts.md §1.2`
     no direct support can be found;
  2. a `claim_without_resolved_evidence_link` signal points to this `claim_id`, and M7, after re-checking
     every item in `supported_by`, confirms none can be resolved;
  3. `supported_by` points to a `conflicting` group and **every** candidate observation is incompatible with the claim's direction;
  4. the supporting value is opposite in direction to the claim.
- **Does not trigger**: `ambiguous` / `parse_failed` indicate extraction or capability limits, not "the manuscript has no evidence";
  M7 should skip automatic adjudication of that claim and require a human to read the original text. If even one candidate value in a `conflicting` group
  can support the claim, this rule must not be raised automatically either.
- **severity**: `major` by default; `critical` when the claim is the main conclusion of the abstract or body and all direct support is absent or opposite in direction.
- **Evidence requirements**: the claim's original text + `absence` evidence of the support search (cases 1 and 2),
  or `present` evidence pointing to all observations of that `key_data` (cases 3 and 4).
- **Note**: case 2 **must not** be closed by citing the signal id alone — you must yourself confirm that
  every item in `supported_by` truly cannot be resolved, and record the search process as `absence` evidence.

A magnitude inconsistent with the wording (e.g. "sub-micromolar" against 15 μM) uses
`claim_magnitude_mismatch` (`major`); it must not be escalated into `unsupported_claim` (`critical`).

#### 5.2.1 `claim_magnitude_mismatch` · magnitude or threshold inconsistent with the data

- **Trigger**: the claim gives a recomputable magnitude, fold change, directional threshold, or prespecified clinical threshold, while all direct support for the same endpoint, group,
  time point, analysis set, and estimand — after unit normalization and original-text rounding — falls outside that range.
- **Automatically comparable**: expressions with numeric boundaries such as `sub-micromolar`, `>50% reduction`, `two-fold`, prespecified MCID/diagnostic thresholds.
  Adjectives with no manuscript-prespecified boundary, such as `large`, `marked`, `robust`, must not have thresholds invented by this rule;
  handle per §5.5 or route to manual review.
- **Does not trigger**: any of the metric, unit, time point, analysis set, adjustment model, or denominator is incomparable; only one
  `ambiguous/parse_failed` observation was found; or at least one comparable observation is compatible with the claim's range.
- **severity**: `major`; must not be auto-escalated to `critical` on magnitude mismatch alone.
- **Evidence requirements**: the claim's original text + `present` evidence for all comparable direct support; detail states the comparison keys,
  normalized values/intervals, claim boundary, rounding rules, and rule version.

### 5.3 `causal_overreach` · correlation phrased as causation

- **Trigger**: `evidence_tier = E5` (human observational) and `claim_tier ≥ C3`, but path B below is not fully satisfied.
  - **A · Ordinary longitudinal observational evidence**: exposure precedes outcome; confounders were prespecified and appropriately controlled;
    at least one sensitivity analysis addressing unmeasured confounding or reverse causation is reported; the claim is qualified by target population, exposure,
    comparator, outcome, and time window. A complete path A supports only manual-review exemptions of the "results are consistent with a possible causal relationship" kind;
    it **cannot** let an ordinary regression's outright causal assertion pass automatically.
  - **B · Dedicated causal-design path**: the manuscript explicitly uses Mendelian randomization, a natural experiment, instrumental variables,
    regression discontinuity, difference-in-differences, or target trial emulation; specifies the target estimand; and reports, item by item, that design's
    identification assumptions, diagnostics, and at least one sensitivity analysis for a key assumption. If everything holds and M4 has not flagged the design as invalid,
    do not trigger; if any item cannot be confirmed, route to manual review or issue `major` under the previous rule — do not exempt on the design's name alone.
- **severity**: `major` by default. Escalate to `critical` per §3.4 condition 2 only when designs that cannot establish temporal order (cross-sectional / case series etc.) are used to assert
  a **main** causal conclusion outright, all direct support lacks temporal order, and no independent support exists. Case-control studies must not be mechanically rated
  `critical` on the design name alone.
- **Evidence requirements**: the claim's original text + the design-description text + `absence` evidence for the missing items.
- **Non-triggering cases**: the claim only states `associated with` / `predicts` with no interventional counterfactual implication;
  path B is complete and M4 has not flagged the identification assumptions/analysis as invalid; or path A is complete and the text only says "consistent with a possible causal relationship"
  while explicitly acknowledging residual confounding. Merely "self-declared limitations" or the use of `may` is insufficient to exempt an outright causal assertion.

### 5.4 `negative_result_misread` · non-significance misread as no difference

- **Trigger**: the primary analysis did not reach the superiority significance threshold, and the claim phrases the result as a **zero-effect, equivalence, or non-inferiority**
  proposition — "等效 / 相似 / 相当 / 无影响 / 无获益 / 不劣于 / equivalent / similar / comparable / does not affect /
  no benefit / not inferior" and the like — without satisfying any of:
  1. a prespecified equivalence margin, with the two-sided confidence interval falling entirely within the margin;
  2. a prespecified non-inferiority margin, using the analysis set and confidence interval consistent with the design, with the interval not crossing the margin;
  3. the claim is explicitly phrased as "no evidence supporting a difference/benefit/superiority was found", the manuscript reports the effect estimate and confidence interval
     for that comparison at a locatable position, and insufficiency of evidence is not rewritten as a zero effect.
- **Must not trigger on these phrasings alone**: `not statistically significant`, `did not show superiority`,
  `was not found to be superior`, `failed to demonstrate benefit`. When these only report an unsuccessful superiority test
  and the manuscript gives the estimate and interval, they are qualified statements about the test result; the rule triggers only if the text goes on to infer
  "therefore the two are the same / it is ineffective".
- **severity**: `major`.
- **Evidence requirements**: the claim's original text + the original statistical results for that comparison; equivalence/non-inferiority propositions additionally require the prespecified margin and analysis set,
  with the corresponding `absence` evidence registered when missing. For ordinary superiority results, "post-hoc lack of power" must not be required as the basis for the error.
- **Common form**: `p = 0.21` → "the two groups showed no significant difference, indicating X does not affect Y".
  **Non-significance only means no evidence of a difference; it is not evidence of no difference.**

Post-hoc power or a "sample-size justification" cannot prove equivalence; using them as non-trigger conditions is forbidden.

### 5.5 `significance_overstated` · overstated statistical significance

- **Trigger** (any one suffices):
  1. **effect-size** wording such as "potent / substantially improved / substantial / large effect" is used on the basis of a `p` value alone,
     without reporting the corresponding effect estimate and confidence interval; "statistically significant" by itself does not trigger;
  2. for continuous scales or patient-reported outcomes with a recognized MCID, the claim asserts a **clinically important improvement** outright
     without comparing the effect estimate/confidence interval against the prespecified MCID; hard endpoints such as death or hospitalization must not mechanically require an MCID —
     check the absolute risk difference, confidence interval, and benefit–harm instead;
  3. M4 has already reported `multiple_testing_control` on the same analysis, yet the claim presents exploratory subgroups/
     secondary endpoints as confirmatory "significant" results.
- **severity**: `major`.
- **Evidence requirements**: the claim's original text + `present` evidence at the locations of the `p` value, effect estimate, and interval
  (or compliant `absence` evidence for the effect estimate/MCID); case 3 additionally cites the manuscript-anchor evidence of the M4 finding.

### 5.6 `limitations_evasive` · evading core limitations

- **Trigger**: M2–M6 contain a finding listed in the table below that is directly related to the inference boundary with `severity ≥ major`,
  and `conclusion.limitations` satisfies either:
  1. `status = not_reported`;
  2. `status = reported`, but the text does not, per the table below, acknowledge both the **problem domain** and its impact on precision, attribution, or
     false-positive risk.

| Upstream category | Problem-domain search seeds | Impact search seeds |
| --- | --- | --- |
| M4 `sample_size` | 样本量 / sample size / underpowered | precision or CI / detection ability / uncertainty / generalizability |
| M3 `missing_control` | 对照 / comparator / placebo / control | cannot attribute / alternative explanation / causal inference limited |
| M4 `multiple_testing_control` | 多重比较 / 亚组 / exploratory / multiplicity | false positive / chance finding / needs independent validation |

The words in the table are used only to recall candidate sentences; a keyword miss **must not** directly prove the authors evaded the issue. The final determination must resolve two
semantic propositions: (1) the authors acknowledge the problem genuinely applies to this study; (2) the authors state which kind of inference it limits. Near-synonymous expressions can satisfy them;
negated or counterfactual expressions cannot: "the sample size was adequate" contains "sample size" but denies the problem; "multiple controls were used" contains "control"
but does not acknowledge the absence. If the authors describe mitigation measures, they must also state the residual limitation after those measures.
Categories not in the table (e.g. statistical-test errors, figure–text contradictions, missing ethics statements) are errors or compliance problems to be corrected,
not research boundaries resolvable by disclosure in Limitations, and **must not** trigger this rule.
- **severity**: neither problem domain nor impact covered → `major`; only one of the two covered → `minor`; both covered by affirmative propositions
  applicable to this study → no trigger.
- **Evidence requirements**: the `limitations` original text; if judged uncovered, additionally provide `absence` evidence whose `search_terms[]` start from the table's
  problem-domain and impact words and are supplemented with the manuscript's actual synonymous expressions; also cite the manuscript-anchor evidence of the evaded finding.
  If the fixed word-list search fails but a full-text semantic search has not been completed, a finding must not be raised.
- **Note**: this is the only M7 rule **triggered by other modules' findings**,
  but the evidence must still be provided independently — never write merely "M4 reported the problem and the authors did not mention it".

### 5.7 `selective_result_interpretation` · selective interpretation of the paper's own results

- **Trigger**: the Discussion summarizes the paper's results in one direction, while results for the same prespecified endpoint or the same overall population contain
  observations that are opposite in direction and explicitly incompatible, and the Discussion does not disclose that heterogeneity.
  An exploratory subgroup differing in direction from the primary population only prompts manual review; it does not trigger automatically.
- **Criterion for "explicitly incompatible"**: first require that the endpoint, estimand, effect scale, analysis population, and
  time window are comparable; then require that the confidence/rounding intervals do not intersect, or that a formal interaction/heterogeneity
  test supports the directional difference. Point estimates of opposite sign with wide, overlapping intervals do not trigger. If the Discussion uses
  universal quantifiers such as `all / every / consistently / across all`, a single locatable counterexample suffices to refute the universal proposition,
  with no further heterogeneity test needed.
- **severity**: `major`.
- **Evidence requirements**: the Discussion text + `present` evidence of the evaded own results.
- **Currently out of scope**: judging whether the authors omitted citations to external contradicting literature — that requires a literature database and belongs to §11.1;
  therefore the slug `selective_citation`, which would imply an external search was completed, must not be used.

### 5.8 `discussion_hollow` · Discussion merely restates results

- **Trigger**: runs automatically only for full-length original research; the Discussion has at least two substantive paragraphs,
  and sentence-by-sentence verification shows all of them are mere restatements of results, with none of the following elements: comparison with prior literature, alternative explanations,
  mechanistic speculation, limitations, clinical or research implications. A semantic-similarity score against the Results alone must not trigger.
- **severity**: `minor`.
- **Evidence requirements**: `present` evidence for all substantive Discussion paragraphs, with a functional label per paragraph in detail;
  when the Discussion cannot be fully read or sentence functions are ambiguous, do not raise this rule automatically.
- **Judge cautiously**: the discussion of brief reports and case reports is naturally short;
  when `primary_design.type ∈ {case_report, case_series}`, or the article is a protocol, methods/data descriptor,
  or explicitly labeled by the journal as a brief report, **this rule does not trigger**.

---

## 6. Interplay with lower modules (downgrade rule table)

M7 consumes the findings of M2–M6. **The interplay affects only the severity and
`review_confidence` of M7's own findings; it does not rewrite other modules' findings.**

| Upstream finding | Trigger condition | Effect on M7 |
| --- | --- | --- |
| M4 `statistical_test_selection` (critical) | The same analysis is the claim's entire direct support, and M4 explicitly states the estimate/test is uninterpretable | `unsupported_claim`; critical if a main conclusion, otherwise major |
| M4 `sample_size` (major) | The claim cites that analysis | Do not adjudicate unsupported automatically; only enters the limitations-disclosure check of §5.6 |
| M4 `multiple_testing_control` | The claim cites the same uncorrected exploratory subgroup/secondary endpoint | Triggers §5.5 case 3 |
| M3 `missing_control` | The same experiment is the entire direct support of a `C3+` claim | `claim_beyond_evidence`; major by default, mechanically adding to Δ forbidden |
| M3 `animal_use_unjustified` | —— | No effect on M7 (an ethics/design matter; it does not directly change the data's direction) |
| M5 `figure_text_contradiction` | The claim cites that figure, and the contradiction involves the direction/value the claim uses | `unsupported_claim` when no other support exists; major by default, critical when a main conclusion and the direction is opposite |
| M5 `chart_type_mismatch` | The claim cites that figure | Does not change M7 automatically; only when the issue makes the value impossible to read uniquely, cap the new M7 finding's `review_confidence` at medium |
| M5 `figure_should_be_main_text` | The claim cites that supplement figure | Severity unchanged; note in detail that core evidence is poorly placed |
| M2 `internal_inconsistency` | The claim cites conflicting values | Check all candidate values per §5.2 case 3; adjudicating unsupported at the sight of a conflict is forbidden |
| Any M6 finding | —— | No effect on M7 (ethics compliance does not change whether the conclusion holds) |
| **(Not implemented)** M5 `duplicate_region_within_paper` / `splice_artifact_suspected` | The claim cites that figure | Only generates an editorial manual-review candidate; before forensics is humanly confirmed, an M7 critical finding must not be generated automatically |

**Implementation constraint**: claim-level interplay executes only when all four hold: (1) the upstream finding and the claim point to the same `figure+panel`,
`table`, or `paragraph_id`; (2) that anchor is direct support in `supported_by`, not mere same-paragraph background;
(3) the upstream finding's `review_confidence ∈ {high, medium}`; (4) after checking the claim's other
`supported_by` entries, no independent direct support is confirmed. If any item fails, do not link. The M7 finding must cite
manuscript evidence anew and spell out its reasoning; the upstream severity must not be copied over.

§5.6 is a **study-level limitations-disclosure audit** and does not apply items (2)/(4) above; it consumes only the `major/critical` upstream findings in the closed snapshot
that relate to this study's inference boundary, and re-checks the Limitations against "problem domain + impact". M7 runs only once per
snapshot: M7 findings created in this round must not trigger another M7 rule again. If multiple upstream findings share
one root cause, keep their evidence separately but form a single M7 issue cluster; inflating the risk score through cascading is forbidden.

---

## 7. Boundary with M2

Both modules look at "logic"; the dividing line is:

| Situation | Owner | Rationale |
| --- | --- | --- |
| Two values in the body disagree | **M2** | Internal manuscript contradiction, unrelated to conclusion tiers |
| Results say A, Discussion says B | **M2** | Contradiction between sections |
| Results hold but the conclusion jumps to a higher tier | **M7** | Tier leap |
| Abstract conclusion inconsistent with body results | **M2** (contradiction) + **M7** (if also overreaching) | May share one issue_cluster |
| Missing section (no Discussion) | **M2** | Structural completeness |
| Discussion exists but is idle | **M7** | Content quality |
| A claim's `supported_by` chain is broken | **M7** | The signal is explicitly routed to M7 |
| Citing a nonexistent Figure 6 | **M2 / M5** | `unresolved_cross_reference` is not routed to M7 |

**One-sentence boundary**: M2 governs "whether the statements are consistent with each other"; M7 governs "whether the statements are borne out by the data".

---

## 8. Category slugs

| slug | Description | severity | Rule |
| --- | --- | --- | --- |
| `unsupported_claim` | Claim without data support | major / critical | §5.2 |
| `claim_beyond_evidence` | Extrapolation beyond experimental conditions | major / critical (per Δ) | §5.1 |
| `causal_overreach` | Correlation phrased as causation | major / critical | §5.3 |
| `negative_result_misread` | Non-significance misread as no difference | major | §5.4 |
| `significance_overstated` | Overstated statistical significance | major | §5.5 |
| `limitations_evasive` | Evading core limitations | major / minor | §5.6 |
| `selective_result_interpretation` | Selective interpretation of the paper's own results | major | §5.7 |
| `discussion_hollow` | Discussion merely restates results | minor | §5.8 |
| `claim_magnitude_mismatch` | Claim magnitude inconsistent with own data | major | §5.2 |

**Added by external enhancement** (must not be used before the connector and this module's consumption rules are complete): `claim_contradicted_by_literature`,
`claim_unreplicated`, `violates_domain_common_sense`.

---

## 9. Positive / negative examples

Each rule has at least one "should alert" and one "should not alert".

### 9.1 `claim_beyond_evidence`

**Should alert**: a HepG2 cell experiment (E2); the Discussion asserts outright
"Compound A is an effective therapy for hepatocellular carcinoma".
→ C5, `assertive`; E2's assertive ceiling is C2, Δ=3 → **critical**.

**Should not alert**: same experiment; the Discussion writes
"These in vitro findings suggest that Compound A may warrant further
evaluation as a potential therapeutic candidate in HCC models".
→ C4, `hedged` (`suggest` + `may` + `potential`); E2's `max_hedged_tier` = C4,
Δ=0 → **do not report**.

### 9.2 `causal_overreach`

**Should alert**: a cross-sectional study (E5) finds serum MHR associated with preeclampsia,
and the conclusion writes "Elevated MHR causes preeclampsia".
→ No temporal order, and that cross-sectional result is the entire support of the main causal conclusion → **critical**.

**Should not alert**: in a prospective cohort (E5), early-pregnancy MHR measurement precedes the occurrence of preeclampsia (temporality ✓),
multivariable logistic regression adjusts for BMI/age/blood pressure (confounding ✓), and a restricted cubic spline dose–response is reported (✓);
the conclusion writes "Higher early-pregnancy MHR was independently associated with increased
risk of preeclampsia" → this is `C1 + assertive` with no causal counterfactual implication → **do not report**.

### 9.3 `negative_result_misread`

**Should alert**: `p = 0.31`, n=8/group, no power analysis; the conclusion writes
"X has no effect on tumor growth" → **major**.

**Should not alert**: a prespecified equivalence margin (−10%, 10%); the measured difference's 95% CI is (−3.2%, 4.1%);
the equivalence test is completed on the prespecified analysis set; the conclusion writes "X is equivalent to Y within the prespecified equivalence margin" → **do not report**.

**Also should not alert**: a superiority trial's effect estimate is −1.2 (95% CI −3.8–1.4); the manuscript fully reports the interval and writes
"X was not found to be superior to Y", without going on to claim equivalence or no effect → superiority merely lacked evidence, **do not report**.

### 9.4 `significance_overstated`

**Should alert**: `p=0.04`, only the p value reported; the abstract writes "X produced a large clinically meaningful
improvement" → no effect size/CI given, and significance is treated as effect size → **major**.

**Should not alert**: the abstract writes "X reduced mean score by 6.2 points (95% CI 3.1–9.3), exceeding
the prespecified 5-point MCID" → effect size, precision, and MCID are all verifiable → **do not report**.

### 9.5 `unsupported_claim`

**Should alert**: the main conclusion claims X reduces mortality, but `supported_by=[]`; a full-text search of the body, tables, and figure captions with
{mortality, death, survival, X} yields nothing → compliant absence evidence exists, **critical**.

**Should not alert**: the only key_data group is `parse_failed`, corresponding to a low-resolution supplement; this is a system capability limitation,
not an unsupported manuscript → skip automatic adjudication and route to manual review, **no M7 finding**.

### 9.6 `limitations_evasive`

**Should alert**: M4 reports `sample_size` (major); `limitations` says only
"this was a single-center study", with no mention of sample size or power → **major**.

**Should not alert**: same situation, but `limitations` writes "the sample size was small and power was insufficient to detect small effects;
the results require validation in larger cohorts" → both the problem domain and the inferential impact are acknowledged → **do not report**.

### 9.7 `selective_result_interpretation`

**Should alert**: the prespecified primary endpoint is opposite in direction at two time points; the Discussion summarizes only the favorable time point and writes
"all analyses consistently favored X" → the paper's own results are not consistent → **major**.

**Should not alert**: one post-hoc exploratory subgroup is opposite in direction; the Discussion labels it exploratory and calls for independent validation
→ the heterogeneity is disclosed and the overall results are not phrased as "consistent across all subgroups" → **do not report**.

### 9.8 `discussion_hollow`

**Should alert**: all three Discussion paragraphs are restatements of Results values, with no literature comparison, no mechanism, no limitations.

**Should not alert**: the brief discussion of a `case_report` — §5.8 explicitly does not trigger.

---

## 10. TODO (Phase 1)

- [x] Populate the §3.3 evidence-tier ↔ claim-tier permission table (this module's top priority)
- [x] Define the concrete trigger-rule table for §6 interplay downgrading
- [x] Draw a clear boundary with M2 (§7)
- [x] Specify the "soft wording" whitelist (§4)
- [ ] Annotate claim_tier and evidence_tier paper by paper on the 10 corpora in `datasets/`,
      calibrating whether the §3.3 table and the §3.4 Δ thresholds are too strict
- [x] §5.6 admits only the three problem classes reasonably resolvable via Limitations disclosure, with the dual "problem domain + impact" condition defined
- [x] §6 category slugs verified against the current M3/M4/M5 references; unregistered slugs must not be used for interplay
- [ ] Supplement the English/Chinese wording tables in §4.1/§4.2 with variants observed in real corpora

---

## 11. Online enhancement (X1 connector **delivered**)

All three capabilities belong to this module. **For now, write only the criteria, not the implementation**; data sources uniformly go through the external evidence layer.
This section only declares "what data is needed" — do not implement the calls yourself.

### 11.1 Scientific truth verification of conclusions

- Data sources: PubMed / Europe PMC
- Draft criteria: extract each claim's core assertion → search prior research on the same topic → classify as
  `consistent` / `contradicted` / `novel_unreplicated` / `insufficient_evidence`
- Output categories: `claim_contradicted_by_literature` (critical) / `claim_unreplicated` (info)
- **Risk**: incomplete retrieval recall creates the false negative of "no counterevidence found = conclusion correct". The implementation must start
  at `review_confidence: low`, and such findings are always subject to mandatory manual review.

### 11.2 Domain novelty / significance

- Data sources: literature database + citation network
- Prerequisite: **first define a quantifiable novelty criterion**, or this degenerates into subjective scoring. Candidate directions:
  the claim's semantic distance from existing literature, whether the method combination appears for the first time, whether the study subject is an unexplored area
- Output positioning: never issue "high/low novelty" conclusions; give only **factual descriptions** such as "no comparable report of this claim was found within the search scope",
  leaving the value judgment to humans — online enhancement must not cross this line either.

### 11.3 Basic common-sense checks

- Data source: a domain common-sense rulebase (to be built in-house)
- How to build it: **first accumulate misjudgment samples from the current manual-review step**, distilling common-sense errors that actually occurred into rules,
  rather than enumerating common sense a priori. Manual-review records are the training material for future rules.
- Output category: `violates_domain_common_sense` (critical)

### 11.4 External evidence contract

Uniformly reuse the `external` evidence of `00-contracts.md §1` and the
`external_validation_candidate` of §6.2. M7 must not create external evidence; the sole producer is
`stage_3c_external_validation`. When M7 raises a finding from an external signal, `evidence_refs[0]`
must be in-manuscript `present`, citing alongside it the external evidence with `retrieval_status: resolved`;
it must also trace back to a signal with `comparison_result: mismatch` and `comparability: complete`.
`not_found`, `not_addressed`, interface failures, and incomparability must never automatically become findings.


### 11.1 Consuming X1 external-validation signals

X1 (`scripts/external_figure_validation.py`, Stage 3c) is delivered and routes two types to M7:

| X1 `check_type` | Database | Comparison result | M7 category slug |
| --- | --- | --- | --- |
| `cited_work_retracted` | Europe PMC | `mismatch` | `conclusion_rests_on_retracted_work` |
| `outcome_switching` | ClinicalTrials.gov | `needs_manual_review` | `conclusion_on_switched_outcome` |

**These two types belong to M7 because they undermine the footing of the conclusion, not merely a reporting flaw somewhere.**

- `cited_work_retracted`: **raise a finding only when the cited work genuinely underpins this paper's argument.**
  If the paper is discussing the retraction event itself, or already states the work is retracted, there is **no problem** —
  that is doing it right. The citation's location and context must be re-checked before deciding; `major` by default;
  take `critical` when the work supports a main conclusion.
- `outcome_switching`: always a candidate. Wording differences alone can cause keyword mismatches,
  so the registry record must be manually compared with the outcomes the paper reports. Take `critical` when switching is confirmed
  and the main conclusion rests on the switched outcome.
When X1 produces a `system_limitation`, register it per `00-contracts.md`; it must not be treated as a conclusion in either direction.
A finding promoted from a candidate must include both manuscript evidence and external evidence in `evidence_refs[]`.
