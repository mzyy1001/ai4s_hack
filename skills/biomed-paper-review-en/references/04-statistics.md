# M4 · Statistical Methods Review

**Owner: JY (Jiang Yun)** · Status: **Phase-1 rulebase populated**

> The domain-judgment portions of this file merge in JY's handwritten version `04-statistics-edited`:
> §3.5 severity-grading principles, §4.10 regression and model diagnostics, §5 risk-flagging criteria for sample size,
> §8 enumeration of multiple-testing situations, §9 slug table and grading rationale.
> The framework side contributed the three-step decision procedure, the acceptable-alternatives sets,
> and the undetermined false-positive-prevention mechanism.

Corresponds to "Layer 3: statistical methods review" in the meeting minutes. The core question is not "was the arithmetic correct" but
**what test this experimental design should have used, and whether the test the authors actually used is defensible**.

**This module's decision runs in three steps (§3)**: first derive the **expected test** from the data characteristics,
then compare against the **test actually used**, and finally assign a **reasonableness grade**.
Only a clear mismatch raises `statistical_test_selection`; when extraction of data characteristics is insufficient, **no finding is raised** —
output `partial_extraction` and hand off to a human. This is the module's most important false-positive-prevention mechanism.

**This file depends on `00-contracts.md`.** The finding structure, `evidence_refs[]`, and severity enum
are all defined there. M4 findings **must** independently provide manuscript evidence in `evidence_refs[]`.

---

## 1. Inputs

| Source | Purpose |
| --- | --- |
| `structured_result_v2.measurement.statistical_methods` | **Tests actually used** (each item `{test, applied_to, software, correction}`) |
| `structured_result_v2.article_design` | Design family and type, which determine the domain-specific reporting guideline (§6) |
| `structured_result_v2.design.arms[]` | Number of groups, pairing relationships, `replicate_type` |
| `structured_result_v2.key_data[]` | n, `uncertainty`, p values, `metric_family`, `reporting_completeness` |
| `evaluation_matrix.group_sizes[]` | Per-experiment, per-group sample sizes (**not** a single minimum) |
| `evaluation_matrix.multiple_comparison_correction` | Multiple-comparison correction status |
| `figure_records[]` | Error bar types, significance markers, and axes in figures |
| `extraction_signals[]` routed to M4 | See §2 |

**Consume `v2`, not `v1`** — `v1` does not contain figure/table-sourced values.
`evaluation_matrix` is used only for routing and evidence localization; before raising a finding you must go back and check `evidence_refs`.

## 2. Signals consumed by this module

| signal type | Source | What M4 must decide |
| --- | --- | --- |
| `source_value_conflict` | Stage 3b | Whether a numerical contradiction affects the statistical conclusions |
| `partial_extraction` | Stage 2 | Whether reporting is incomplete (e.g., n given without replicate type) |
| `ambiguous_extraction` | Stage 2 | Whether the statistical-method description is too vague to adjudicate |
| **`test_statistic_p_mismatch`** | `scripts/statistical_forensics.py` (relative to the Skill root) | Whether it constitutes a p-value reporting error |
| **`ci_estimate_mismatch`** | Same as above | Whether it constitutes an interval reporting error |
| **`count_percentage_mismatch`** | Same as above | Whether it constitutes a data reporting error |
| **`grim_incompatible_mean`** | Same as above | Whether it constitutes an impossible summary statistic |
| **`table_total_mismatch`** | Same as above | Whether the total of mutually exclusive, exhaustive categories contradicts the declared denominator |

> **The five bolded signals are deterministic forensics already implemented in Phase 1**
> (`scripts/statistical_forensics.py`, relative to the Skill root);
> they require no raw data — only the numbers the paper itself prints. They **have been moved up from Phase 2 to Phase 1**
> — an older version of this file listed them under "§5 Phase-2 extensions"; this has been corrected.
> The tool layer only produces signals; **M4 decides whether a finding is warranted and at what severity**.

### 2.1 Consumption gate for statistical forensics signals

The five forensics signals must not be translated into findings directly by type. M4 must, for each one:

1. Confirm `produced_by = stage_2` and `forensics.ran = true`, and recompute the inputs and intervals in `forensics`;
   for `test_statistic_p_mismatch`, `forensics` must retain `test_family`, `statistic`,
   `tail`, and the `df` or `df1/df2` required by that test family — if any is missing, do not convert to a finding;
2. Use manuscript evidence to confirm all inputs belong to the **same endpoint, same comparison, same analysis set, and same time point**; if binding is impossible, do not raise a finding — produce `partial_extraction`;
3. For `test_statistic_p_mismatch`, additionally confirm the test family, degrees of freedom, and one- vs two-tailed; for `count_percentage_mismatch`,
   additionally confirm the denominator definition and count semantics (number of subjects, events, or samples);
4. For `grim_incompatible_mean`, additionally confirm the paper reports an unadjusted arithmetic mean of equally weighted integer scores, and that n is the actual denominator of that mean;
5. For `table_total_mismatch`, additionally confirm the categories are mutually exclusive and exhaustive, belong to the same analysis set/time point, and that missing values are listed separately or included in the total; do not run it on multi-select items, overlapping event categories, or safety tables that allow multiple events per person;
6. When Stage 2 invokes the statistics script, the `observation_refs[]` / `evidence_refs[]` corresponding to the input numbers should be passed along;
   empty refs in legacy artifacts do not constitute a manuscript violation, but M4 must first re-bind them and include, in the finding, `present` evidence
   from within the manuscript reporting those numbers. A `partial_extraction` with `forensics.ran = false` only indicates the tool's prerequisites were unmet —
   it **must not** be automatically converted into a statistical-reporting defect.

---

## 3. Three-Step Decision Procedure (core of this module)

### 3.1 Step 1 · Characterize the data

First bind each `statistical_methods[]` item to a specific endpoint/comparison, then extract six characteristics from
`structured_result_v2`. Only the characteristics actually used by the current lookup-table row are required: for example, binary outcomes
do not require `distribution_evidence`, and a randomized two-group comparison without covariate adjustment does not require extracting confounders.
**If any characteristic required by the current row cannot be determined, see §3.4.**

| Characteristic | Values | Source |
| --- | --- | --- |
| `outcome_type` | `continuous` / `binary` / `count` / `ordinal` / `time_to_event` / `proportion` / `high_dimensional` | `key_data[].metric_family` + endpoint description |
| `n_groups` | `1` / `2` / `>=3` | `design.arms[]` or `group_sizes[]` |
| `relatedness` | `independent` / `paired_or_repeated` / `clustered` | Design description (pre/post, crossover, multiple cells from the same animal) |
| `design_shape` | `parallel` / `crossover` / `factorial` / `longitudinal` / `dose_response` / `matched_observational` | `article_design` + `arms[]`; a matched case-control requires evidence of matching variables and matched sets |
| `distribution_evidence` | `approximately_normal_supported` / `nonnormal_supported` / `not_assessed` | Model residual plots, Q-Q plots, descriptions of outliers and skewness; a formal normality test may serve only as one piece of evidence among these, and non-normality of the raw outcome cannot substitute for residual diagnostics |
| `covariate_adjustment` | `yes` / `no` | Whether confounder adjustment is declared |

**Endpoint-binding order**: first use `statistical_methods[].applied_to` to match the endpoint, time point, and comparison exactly; then disambiguate using
evidence locators in the same paragraph or table. If two or more candidates remain, do not force a match by nearest distance or name similarity — output
`ambiguous_extraction`. If the methods section only says "t-test for continuous variables, χ² for categorical variables" without a per-endpoint mapping,
proceed only if all applicable endpoints share the same design and relatedness structure; otherwise treat as `undetermined`.

**Test-name normalization**: keep the original wording first, then map to a method family; `unpaired t` / `independent-samples t`
map to independent-samples t, `paired t` must not be merged with it, `mixed model` must be further extracted for outcome family, link,
and random/cluster term, and `ANOVA followed by Tukey` must be split into an omnibus test plus post-hoc comparisons. When the text only says
`non-parametric test`, a software function name, or an abbreviation that cannot be uniquely resolved to a family, output `ambiguous_extraction`;
do not guess the test from common usage. A method not listed verbatim in the table but compatible in family, estimand, correlation structure, and variance handling
goes to humans per §3.4; do not automatically grade it `mismatch` merely because the string is not in `acceptable[]`.

### 3.2 Step 2 · Look up the expected test (§4 lookup tables)

From `(outcome_type, n_groups, relatedness, design_shape)`, look up:

- **`primary`** — a representative first choice compatible with the target estimand in that situation; it does not mean the only correct method
- **`acceptable[]`** — equally defensible alternatives (**do not constitute a finding**)
- **`conditional[]`** — valid only when prerequisites hold; unreported prerequisites trigger `statistical_assumption`
- **`misuse[]`** — known typical misuses

### 3.3 Step 3 · Assign the reasonableness grade

| Grade | Condition | Output |
| --- | --- | --- |
| `match` | Actual test ∈ `{primary} ∪ acceptable` | **No finding** |
| `conditionally_acceptable` | Actual test ∈ `conditional`, and prerequisites are reported | **No finding** |
| `assumption_unstated` | Actual test ∈ `conditional`, a key prerequisite was not assessed, and the risk gate in §3.4 holds | `statistical_assumption` (default minor; escalate to major only if the §9 escalation conditions are met) |
| `mismatch` | Actual test ∈ `misuse`, or fundamentally incompatible with `outcome_type` | `statistical_test_selection` (default major; escalate to critical only if the §9 escalation conditions are met) |
| `undetermined` | A characteristic required by the current lookup-table row cannot be determined | **No finding**; output `partial_extraction` |

**Two hard prerequisites for `mismatch`** (if either fails, downgrade to `undetermined`):

1. `outcome_type`, `n_groups`, and whichever of `relatedness` / `design_shape` the misuse determination actually depends on
   must be `reported` (not `ambiguous`/`parse_failed`);
2. The name of the test actually used must be uniquely resolvable (statements like "statistical analysis was performed using SPSS"
   are **not sufficient** to determine which test was used).

### 3.4 False-positive prevention: when not to judge

**"Correct" statistical methodology is often not unique.** The following situations are always `undetermined` and go to humans:

- The methods section names only software, not the test;
- The paper uses a method not covered by this table, or gives a rationale involving an identifiable but uncoded estimand, sampling mechanism,
  robust-variance/penalized estimation; **merely writing "following prior studies" or "data were non-normal" does not constitute automatic exoneration**;
- The data characteristic depends on figure readings whose source is `pixel_estimated`
  (`00-contracts.md §2.4`: pixel estimation **must not** be used for any statistical determination);
- The same experiment has multiple endpoints, each requiring a different test, and extraction cannot map to the specific endpoint.

**Failure to report a formal normality test does not by itself constitute a finding.** A `p > 0.05` from Shapiro-Wilk and similar tests
only means "normality was not rejected"; it cannot prove the distribution is normal, and test power is especially limited with small samples. Output
`statistical_assumption` only when all of the following hold: (1) the method used is sensitive to the assumption; (2) the sample is small or clearly unbalanced,
and raw points, residual plots, or textual descriptions suggest strong skewness/outliers; (3) no transformation, robust/permutation sensitivity analysis, or residual diagnostics are seen.

### 3.5 Severity is decided by "what is affected", not fixed by slug

The same problem is graded differently when it affects the primary endpoint versus only a secondary analysis; §9 gives grading rationale per problem family.

| Grade | Criterion | Typical situations |
| --- | --- | --- |
| `critical` | Evidence shows the error acts on the primary endpoint and could change the effect direction, significance classification, or effective analysis unit | Primary endpoint ignores censoring; subsamples confirmed counted as independent n; the primary model's direction or conclusion classification would change |
| `major` | May reduce result reliability, but the impact has not been recomputed or does not act on the primary endpoint | Insufficient sample-size justification, inadequate multiple-comparison control, risk evidence for a key statistical assumption, inadequate missing-data handling |
| `minor` | Mainly affects reporting transparency; insufficient to show a change in conclusions | Missing effect sizes, incomplete p-value expression, unclear error bar definitions |

**Before grading, confirm whether the problem affects the primary endpoint or a secondary/exploratory analysis.** When endpoint attribution is uncertain in extraction,
the `severity` ceiling is `major`, and `manual_review.action` must state that endpoint attribution must first be confirmed.

---

## 4. Data Type × Design → Expected-Test Lookup Tables

### 4.1 Continuous outcomes

| Situation | primary | acceptable | conditional (prerequisite) | Typical misuse |
| --- | --- | --- | --- | --- |
| One sample vs fixed reference value | One-sample t or a confidence interval consistent with the estimand | One-sample permutation/sign test, Wilcoxon signed-rank | One-sample t (prerequisite: the distribution of differences is compatible with the outlier situation) | Treating an external historical mean as an error-free constant while claiming a concurrent between-group comparison was performed |
| Two independent groups, approximately normal | Welch t | Permutation test, linear model, bootstrap CI | Student t (prerequisite: equal variance supported by design or diagnostics) | Using paired t; treating repeated observations from the same subject/experimental unit as independent |
| Two paired groups / pre-post | Paired t | Wilcoxon signed-rank, paired permutation, mixed-effects model | —— | **Using independent-samples t** (discards pairing information) |
| Two groups, strong skewness/outliers or very small samples | Permutation/robust method matched to the estimand | Welch t after transformation, bootstrap CI | Mann-Whitney (interpretable as a location difference only when distribution shapes are similar) | Mechanically swapping method names without stating whether the target is a mean, location, or distributional difference; obvious outliers with no robustness analysis |
| ≥3 independent groups | Welch ANOVA + Games-Howell, or a linear model matched to the design | Classical ANOVA + Tukey/Dunnett, permutation ANOVA, robust ANOVA | Classical ANOVA (prerequisite: residuals and variance structure sufficiently compatible) | **Pairwise t-tests without correction**; reporting only the omnibus test yet drawing specific between-group conclusions |
| ≥3 groups, strong skewness/outliers | Permutation or robust omnibus test + corrected comparisons | Kruskal-Wallis + Dunn, linear model after suitable transformation | Kruskal-Wallis (when group distribution shapes differ, cannot automatically be interpreted as a difference in medians) | Applying classical ANOVA to strongly skewed small samples with no residual diagnostics or robustness analysis |
| ≥3 paired groups / repeated measures | Linear mixed-effects model / GEE | Friedman + corrected comparisons, repeated-measures ANOVA | RM-ANOVA (prerequisite: with >2 within-subject levels, assess sphericity or use Greenhouse-Geisser/Huynh-Feldt correction) | **Treating as independent samples**; uncorrected pairwise comparisons at each time point |
| Two-factor factorial | Linear/generalized linear model with main effects and interaction | Two-way ANOVA, mixed-effects model, robust/permutation factorial tests | —— | Needing to compare effect differences but not testing the interaction; splitting into multiple uncorrected one-factor tests |
| Longitudinal, multiple time points | Linear mixed-effects model / GEE | RM-ANOVA on balanced complete data, corrected comparisons at pre-specified time points | RM-ANOVA (prerequisite: completeness and covariance/sphericity conditions compatible) | Treating each subject's time points as independent; per-time-point testing after LOCF only, with no missing-mechanism sensitivity analysis |
| Two-treatment two-period crossover | Linear model with treatment, period, sequence, and within-subject correlation structure | Within-subject difference analysis, paired t, or mixed-effects model when no suspected carryover and the design is simple | Analyzing only the first period (prerequisite: pre-specified in the protocol, or the second period is uninterpretable due to irreversible carryover; must be reported as a parallel design) | Analyzing all periods as two independent parallel groups; testing carryover first and ad hoc dropping the second period based on its p value |
| Randomized trial with baseline measurement | ANCOVA (follow-up value as outcome, baseline as covariate) | Mixed model including baseline, pre-specified change-score analysis | Change score (randomized and the target truly is mean change; usually less efficient than ANCOVA) | Percent change without handling baselines near 0; substituting within-group pre-post significance/non-significance for the between-group treatment effect |
| Observational study with baseline/confounders | Adjusted regression or weighted model consistent with the target estimand | Stratification, matching, standardization | —— | Comparing raw change scores alone and claiming an independent treatment effect |
| Dose-response: estimating IC50/EC50/slope | Nonlinear regression matched to the response shape + fit diagnostics | Emax, trend models, constrained splines/other pre-specified curves | Four-parameter logistic (prerequisite: upper and lower plateaus and monotone S-shape supported by the data) | Substituting between-group ANOVA significance for curve-parameter estimation; extrapolating beyond the tested dose range |
| Dose-response: only asking whether any dose differs from control | ANOVA/linear model + Dunnett contrasts | Trend test, permutation test | —— | **Must not be flagged merely for using ANOVA**; only if the manuscript simultaneously claims IC50/slope without fitting a curve does it become a misuse candidate |

> **Normality tests are underpowered in small samples.** `p>0.05` does not prove normality, but there is also no
> threshold such as n<15 that automatically switches between parametric/nonparametric methods. Judge jointly per §3.4 on skewness,
> outliers, between-group imbalance, estimand, and robustness evidence; do not raise an alert solely because "no Shapiro-Wilk was done" or "n is small".

### 4.2 Binary / proportion outcomes

| Situation | primary | acceptable | conditional | Typical misuse |
| --- | --- | --- | --- | --- |
| One-sample proportion vs fixed value | Exact binomial test or binomial-proportion CI | Score/Wilson methods | Normal approximation (prerequisite: expected numbers of successes and failures sufficient) | Using the uncorrected normal approximation for extremely rare events |
| Two independent groups | χ² or Fisher's exact test | N−1 χ², exact/Monte Carlo methods, binomial regression | χ² (2×2 usually requires each cell's expected frequency ≥5; larger tables require no cell <1 and cells <5 not exceeding 20%) | Using asymptotic χ² on sparse tables with no exact/Monte Carlo verification |
| Two paired groups | McNemar test | Exact McNemar | —— | **Using χ²** (ignores pairing) |
| Matched case-control | Conditional logistic regression | Matched-set conditional methods; McNemar can test exposure differences only for 1:1 without covariates | Unconditional logistic (prerequisite: all matching factors explicitly included and estimand compatibility demonstrated) | Treating matched sets as independent samples; mistaking frequency matching for individual matching and mechanically applying McNemar |
| Two-treatment crossover, binary | Marginal or conditional model preserving sequence/period and within-subject correlation | Mainland-Gart-type methods for a simple 2×2 crossover when prerequisites hold, binomial GEE/GLMM | —— | Treating each period's observations as independent 2×2 tables |
| ≥3 paired conditions | Cochran Q + corrected paired comparisons | Binomial GEE, generalized linear mixed model | —— | Treating as an independent r×c table |
| ≥3 independent groups | r×c χ² + corrected contrasts | Fisher-Freeman-Halton/Monte Carlo exact tests, binomial/multinomial regression | χ² (prerequisite: sparsity satisfies the rule in the row above) | Multiple 2×2 χ² tests without correction |
| Confounder adjustment needed | Logistic regression (report OR + 95% CI) | Stratified Mantel-Haenszel, penalized logistic, standardized/weighted models | Maximum-likelihood logistic (prerequisite: event count, number of parameters, separation, and nonlinearity assessed) | Claiming independent effects from univariable comparisons alone; interpreting p values as if from the unselected model after variable selection |
| Clustered/repeated binary | Binomial GEE or generalized linear mixed model | Cluster-robust variance, aggregation by independent experimental unit | —— | Treating observations within the same subject/animal/center as independent |
| Trend of a binary outcome across ordered exposure | Cochran-Armitage trend test | Binary logistic / log-binomial regression with a pre-specified ordinal score | —— | Post hoc trying multiple codings and reporting only the most significant trend; "ordinal logistic" applies to ordinal **outcomes**, not to this row's binary outcome |
| Aggregated proportions with per-unit numerator/denominator | Binomial regression (preserving denominators) | Quasi-binomial, beta-binomial, stratified/mixed binomial models | Treating the proportion as a continuous outcome (prerequisite: large denominators, far from 0/1, and variance handling and weights justified) | Discarding differing denominators and running an equal-weight t-test on bare percentages; conflating event proportions with rates that allow multiple events per person |

### 4.3 Count outcomes

| Situation | primary | acceptable | conditional | Typical misuse |
| --- | --- | --- | --- | --- |
| Counts, no overdispersion | Poisson regression | Exact Poisson test; quasi-likelihood/robust variance when dispersion is compatible | Poisson (prerequisite: mean-variance relation and exposure structure checked) | Running a t-test directly on raw counts despite clear sparsity, skewness, or many zeros; do not automatically flag a near-normal model applied to large counts after diagnostics |
| Counts, overdispersed | Negative binomial regression | Quasi-Poisson | —— | Insisting on Poisson, leading to underestimated SEs and spuriously small p values |
| Mixture of structural and sampling zeros | Zero-inflated or hurdle model matched to the generating mechanism | Two-part models that explain the zero mechanism | —— | Mechanically specifying zero inflation merely because "there are many zeros"; without demonstrated structural zeros, ordinary negative binomial may also be reasonable |
| With exposure time / person-time | Poisson with offset (rates) | —— | —— | Comparing raw counts without dividing by person-time |
| Clustered/repeated counts | Poisson/negative-binomial mixed models or GEE | Cluster-robust variance, conditional models | —— | Treating multiple counts within the same subject as independent; omitting the exposure offset |

### 4.4 Ordinal outcomes (e.g., Likert, graded scores)

| Situation | primary | acceptable | conditional | Typical misuse |
| --- | --- | --- | --- | --- |
| Single ordinal item, two groups | Mann-Whitney U | Ordinal logistic | Parametric treatment (prerequisite: enough levels, estimand and sensitivity analysis justified) | Treating a few-level single item as continuous without justification; at most raise `statistical_assumption` — do not grade `statistical_test_selection` on the method name alone |
| Single ordinal item, ≥3 groups | Kruskal-Wallis | Ordinal logistic (proportional odds), corrected ordinal contrasts | Parametric treatment (same prerequisite as above) | Same as above |
| Multi-item composite / validated scale total | Linear, robust, or ordinal model consistent with scale construction and estimand | t/ANOVA, permutation, mixed models | Parametric model (prerequisite: total-score levels, residuals, and boundary effects compatible) | **Do not automatically flag t/ANOVA as wrong just because raw items are Likert**; first confirm whether the analysis target is a single item or a composite score |
| Paired/repeated ordinal outcomes | Cumulative link mixed model / ordinal GEE | Wilcoxon signed-rank for two time points, Friedman for ≥3 | —— | Treating as independent groups; ignoring within-subject correlation |
| Adjustment needed | Proportional-odds model | —— | Proportional odds (prerequisite: proportional-odds assumption tested) | Proportional-odds assumption untested |

### 4.5 Survival / time-to-event outcomes

| Situation | primary | acceptable | conditional | Typical misuse |
| --- | --- | --- | --- | --- |
| Univariable between-group comparison | Kaplan-Meier + log-rank | Log-rank with pre-specified weights, restricted mean survival time (RMST) difference, parametric model consistent with the estimand | —— | **Comparing median survival with a t-test**; **comparing event counts with χ²** (both ignore censoring) |
| Multivariable | Cox proportional-hazards model (report HR + 95% CI) | Parametric/flexible parametric survival models, accelerated failure time models, RMST regression, time-varying effect models | Cox (prerequisite: **proportional-hazards assumption assessed**, e.g., Schoenfeld residuals and time-varying effects) | Summarizing with a single constant HR despite crossing hazards or clear time-varying effects, with no supplementary estimand; do not raise an alert solely because a specific formal PH-test name is not mentioned |
| Competing risks | Cumulative incidence function + Gray's test, or Fine-Gray / cause-specific Cox consistent with the estimand | Multi-state models | Fine-Gray (interpret subdistribution HR); cause-specific Cox (interpret instantaneous cause-specific hazard) | Using ordinary KM to estimate cause-specific cumulative incidence; treating the two HRs as the same estimand |
| Interval censoring | Interval-censored survival models | Turnbull nonparametric estimation, discrete-time models | —— | Using interval midpoints as exact event times without sensitivity analysis |
| Recurrent events | Andersen-Gill / PWP / frailty or other models matched to the problem | GEE count models, multi-state models | —— | Analyzing only first events yet concluding about "total recurrence burden"; treating a subject's events as independent |
| Reporting requirements | —— | —— | —— | KM curve **without a numbers-at-risk table**; follow-up duration unreported |

### 4.6 Correlation and agreement (a high-frequency misuse zone)

| Situation | primary | acceptable | Typical misuse |
| --- | --- | --- | --- |
| Linear correlation, bivariate normal | Pearson r (report r, 95% CI, n) | —— | Using Pearson on ordinal or strongly skewed data |
| Monotonic correlation / ordinal / non-normal | Spearman ρ | Kendall τ | —— |
| **Agreement between two measurement methods** | **Bland-Altman analysis** (bias + 95% limits of agreement) | Lin's concordance correlation coefficient, ICC | **Using Pearson r to prove "agreement"** (the classic error: high r only shows linear correlation, not agreement) |
| Categorical inter-rater agreement | Cohen's κ (two raters) / Fleiss κ (multiple raters) | Weighted κ (ordinal) | Using "percent agreement" instead of κ (chance agreement not removed) |
| Continuous inter-rater agreement | ICC matched to the target (must state single/average measures, consistency/absolute agreement) | Repeatability/reproducibility standard deviation, coefficient of variation, Lin CCC | Writing only "ICC=0.9" without the type; treating consistency ICC as absolute agreement |
| Correlation among repeated measures on the same subject | Repeated-measures correlation or mixed-effects model | GEE, decomposition into within-/between-subject effects | Pooling all points into Pearson/Spearman, ignoring within-subject clustering |

### 4.7 Diagnostic accuracy

| Item | Requirement | Typical misuse |
| --- | --- | --- |
| Basic metrics | Sensitivity and specificity **each with 95% CI**; provide the 2×2 table | Reporting only one metric; no CI |
| Summary metric | ROC curve + AUC (with CI) | Reporting AUC without CI |
| Comparing two models | Paired ROC may use DeLong or paired bootstrap; sensitivity/specificity differences use paired binary methods | Reporting AUCs separately without testing the difference; treating two models on the same subjects as independent |
| Optimal cutoff | After in-development-set selection, correct optimism via bootstrap/cross-validation; confirmatory claims require external validation | **Selecting the cutoff on the same data and treating apparent performance as validation performance** |
| Predictive values | PPV/NPV must state the prevalence assumed | Directly applying the study sample's PPV to a low-prevalence population |

### 4.8 High-dimensional / omics

| Item | Requirement | Typical misuse |
| --- | --- | --- |
| Multiple testing | **Must** report corrected p (FDR-BH q values or adjusted p) | **Reporting only raw p**; filtering by fold-change alone without statistical testing |
| Differential analysis | Use field-standard tools (limma / DESeq2 / edgeR) with versions stated | Running t-tests directly on count data |
| Batch effects | State whether checked and corrected | No mention of batch at all |
| Enrichment analysis | State the background gene set and the correction method | Using the whole genome as background without correction |
| Feature selection and modeling | Selection must be done **within the training set** | **Selecting features on the full data then cross-validating** (information leakage; linked to M2) |

### 4.9 Clustered data and pseudoreplication (common in biomedicine)

| Situation | primary | Typical misuse |
| --- | --- | --- |
| Multiple cells/sections/fields per animal | Mixed-effects model (animal as random effect) or first aggregate per animal | **Treating cell counts as n** (pseudoreplication; artificially inflates sample size, spuriously small p values) |
| Multiple lesions/tooth sites/eyes per subject | Generalized estimating equations (GEE) or mixed models | Treating lesion counts as independent samples |
| Cluster-randomized trials | Analyses accounting for the design effect | Analyzing by individual, ignoring intra-cluster correlation |
| Experiments repeated across batches | Batch as random effect, fixed blocking effect, or first aggregate per independent batch | Pooling technical wells across batches as independent replicates; **do not automatically flag simply because batch was not modeled as a random effect** |

> **Pseudoreplication is one of the most worthwhile catches for this module**: it requires no complex judgment — whenever
> multiple cells, sections, fields, or technical wells within the same independently allocated experimental unit are treated as independent n, it is highly suspect.
> `arms[].replicate_type = technical` can only trigger a candidate; you must still confirm from manuscript evidence the level at which the intervention was allocated,
> the inferential target, and the n actually entered into the model. Offspring, lesions, etc., may be biological subsamples rather than technical replicates,
> and can equally constitute clustering; the binary `replicate_type` label alone cannot rule this out. If the experimental unit cannot be determined, output
> `partial_extraction`; do not raise `replication_independence`.

---

### 4.10 Regression and model diagnostics (`model_specification`)

**This is a category entirely missing from the original framework version.** The tables above govern "which test was chosen";
this section governs "whether the model was built correctly" — specification errors in regression, survival, and prediction models
can bias effect estimates, but **failure to report a particular diagnostic by name is not itself a model error**.

| Model | Risk evidence and acceptable handling | Output gate |
| --- | --- | --- |
| Linear regression | When residuals suggest nonlinearity/heteroscedasticity/influential points, use transformation, splines, robust SE/regression, or sensitivity analysis; collinearity assessment is required only when multiple highly correlated predictors exist and interpretation depends on a single coefficient — VIF is not the only method | Risk evidence present with no handling → `statistical_assumption`; do not flag merely for not reporting VIF/normality tests |
| Logistic regression | Check functional form of continuous variables, sparsity/complete separation, candidate parameter degrees of freedom, and shrinkage; penalized estimation and pre-specified dimension reduction are acceptable | Do not flag by a fixed EPV threshold; only confirmed separation or clear overfitting left unhandled becomes `model_specification` |
| Cox regression | PH risk assessed via Schoenfeld, log-minus-log, time-varying effects, or curve shape; when violated, time-varying coefficients, stratification, RMST/AFT are acceptable | Alert only when PH risk evidence and a constant-HR conclusion coexist with no handling |
| Mixed effects / GEE | Random/working correlation structure must be compatible with allocation and repetition levels; convergence warnings, singular fits, or very few clusters need handling | Structure unextractable → `partial_extraction`; do not raise a finding merely because software convergence logs were not reported |
| Prediction models | Report internal validation, calibration, and discrimination, and prevent selection/tuning leakage; require external validation per the study aim | A development-only study lacking external validation is not automatically flagged; treating development performance as external performance is `model_specification` |
| Survival models | State time origin, censoring, competing risks, and the estimand; methods must be compatible with the target | Missing fields are first treated as reporting deficiencies; only explicitly using ordinary KM to estimate cause-specific cumulative incidence raises a methods finding |

**Criterion**: `critical` only when the model error is confirmed to act directly on the primary endpoint and there is reason to believe it would change effect direction,
significance classification, or the effective analysis unit; risk evidence alone with unrecomputed impact is `major`; merely not reporting a diagnostic name is
minor or no finding. If the model family/estimand/analysis-set binding is unclear, treat as `undetermined` per §3.4.

---

## 5. Sample Size

### 5.1 Adjudication standard: aims and precision, not hard thresholds

Sample size belongs to the "fuzzy scenarios with no clear unified standard". Two questions must first be separated:

1. Whether the manuscript, in applicable scenarios, reports a **sample-size/precision justification corresponding to the primary aim**;
2. Whether the stated inputs and planned n can be recomputed, or whether the actual information content supports its confirmatory claims.

Only after searching the methods, protocol/registration, and supplementary materials of the full text per the `absence` evidence rules, with no applicable justification found, may
`power_and_sample_size` be raised (default minor). **Small n by itself does not raise a finding**; when the aim, independent units, event counts, or
model degrees of freedom cannot be extracted, produce `partial_extraction` — do not rewrite "cannot verify" as "sample size insufficient". Only a recomputable
plan-vs-report contradiction, or a confirmatory main conclusion explicitly resting on an extremely wide interval crossing a clinical decision threshold, may escalate to major.
The `severity` ceiling is `major`, and `manual_review.who = statistical_reviewer`.

### 5.2 Entry points for review by study type

**There is no universal minimum n usable across effect sizes, variances, endpoints, model complexity, and study aims.** The old
`in_vivo_animal ≥5–6`, `diagnostic_accuracy ≥30–50 per group`, and `EPV ≥10` must not be used as
finding criteria; they would wrongly flag reasonable small exploratory studies and could also pass studies with small effects, high variance, or many parameters.
Use the table below to decide whether to enter manual review:

| Study type | Actionable condition for entering review | Conclusions that must not be drawn from it |
| --- | --- | --- |
| `in_vitro` | The manuscript makes confirmatory or generalizable inferences but does not state independent experimental units, replication levels, and uncertainty; if only technical wells are seen treated as n, review under §4.9 instead | Do not use fixed cutoffs like n=2 or n=3; method-development/exploratory studies are reviewed only against their declared aims |
| `in_vivo_animal` | No rationale for sample-size determination anywhere in the text for a confirmatory primary endpoint; only if the authors claim a power-based design, require that their effect, variance, α, power, and attrition/exclusion inputs be recomputable | Do not use "5–6 per group" as a boundary of sufficiency or insufficiency; missing ARRIVE reporting does not prove the experiment invalid |
| `randomized_controlled_trial` | A confirmatory trial gives no power/precision justification for the primary estimand; or planned vs actual enrollment/event counts disagree without explaining the impact on analysis | Pilot/feasibility trials are reviewed against feasibility aims and progression criteria; do not require them to be powered for efficacy testing |
| `cohort` / `case_control` | **Prediction models** not reporting total sample, events/non-events, and candidate parameter degrees of freedom; **etiological association models** reviewed by estimation precision, sparsity/separation, and pre-specified covariates — do not apply prediction-model thresholds | `EPV <10` can only trigger manual checking; `EPV ≥10` also cannot prove absence of overfitting; do not count every covariate as 1 df |
| `diagnostic_accuracy` | A confirmatory accuracy study gives no justification for sensitivity/specificity, prevalence, and target CI precision; or the primary metric's CI crosses a pre-specified clinically acceptable threshold | Do not substitute 30–50 per group for a precision calculation; small pilots may be used for parameter estimation |
| Omics | Confirmatory differential/prediction claims made without stating independent biological replicates, test family, and FDR plan; parameters exceeding independent units only triggers a model-stability review | Do not treat "≥3/≥5 per group" as a sufficient condition; missing dispersion details do not automatically equal a sample-size error |
| `case_report` / descriptive `case_series` | Not applicable | **Do not** raise sample-size findings against case reports that make no population inference |

When below historical convention but all three of the following hold, do not raise `power_and_sample_size`: the study is explicitly labeled exploratory/feasibility;
the primary aim is not confirming efficacy or precise estimation; and uncertainty, stopping/progression rules, or a sample-size rationale corresponding to that aim are reported.
If the manuscript uses the "pilot" label while drawing confirmatory efficacy conclusions, the problem should land on conclusion overreach or aim mismatch, not on small n alone.

### 5.3 Mandatory checks

- Is there a power analysis or sample-size justification? (`sample_size_justification`)
- Check `group_sizes[]` **per experiment, per group**; do **not** collapse to one global minimum.
- Is n biological or technical replication? `replicate_type = technical` used as n → §4.9.
- Clinical trials: planned vs actual enrollment, attrition rate, whether ITT/PP analyses were done and differences explained.
- **Only when the authors claim to have done a power/precision calculation** check whether its inputs are complete. For confirmatory superiority trials, verify the expected effect size, α, power, allocation ratio, and
  attrition; for precision-oriented studies, verify the target CI width; for pilot/feasibility studies, verify feasibility aims and progression
  criteria. Writing only "power=0.8" with no effect size/variance → `power_and_sample_size` (minor), because it cannot be verified.

---

## 6. Index of Domain-Specific Reporting Guidelines

When raising a finding, cite the corresponding guideline in `rule_ref` so the authors know the basis.

| Study type | Guideline | Items this module cares most about |
| --- | --- | --- |
| Randomized controlled trials | **CONSORT 2010** (and subsequent updates); **ICH E9** statistical principles; **ICH E9(R1)** estimand framework | Flow diagram, randomization method, sample-size justification, primary-endpoint analysis, ITT |
| Observational studies | **STROBE** | Confounding control, missing data, sensitivity analyses |
| Animal experiments | **ARRIVE 2.0** | Sample size, randomization, blinding, statistical methods of the Essential 10 |
| Diagnostic accuracy | **STARD 2015** | 2×2 table, CI, cutoff provenance, blinded interpretation |
| Prediction models | **TRIPOD** (2015) / **TRIPOD+AI** (2024) | Internal/external validation, calibration, event counts vs parameter complexity |
| Systematic reviews and meta-analyses | **PRISMA 2020** | Heterogeneity measures (I²), effect-model choice, publication bias |
| Tumor marker studies | **REMARK** | Marker validation, model building and reporting |
| qPCR | **MIQE** | Reference-gene selection and validation, amplification efficiency |
| High-throughput omics | **MIAME / MINSEQE** | Data availability, normalization methods |
| Case reports | **CARE** | —— |
| Clinical AI/ML | **CONSORT-AI / SPIRIT-AI / DECIDE-AI** | Data partitioning, external validation, performance metrics |

---

## 7. Reporting Completeness Checks

| Item | Requirement | Triggered slug |
| --- | --- | --- |
| p values | Report exact values (e.g., `p = 0.032`), not just `p < 0.05`; `p < 0.001` is acceptable | `p_value_reporting` (minor) |
| Test statistics and degrees of freedom | Should be reported (e.g., `t(18) = 2.31`) so the p value can be verified | `p_value_reporting` (minor) |
| Error type | SD / SEM / 95% CI must be explicitly labeled; **SEM in the figure while the text says SD is a common error** | `error_bar_reporting` (minor; escalate to major when figure and text contradict) |
| Effect sizes | Between-group comparisons should report effect sizes (Cohen's d, mean difference + CI, OR/RR/HR + CI) | `effect_size_reporting` (minor) |
| Clinical significance | **Statistical significance ≠ clinical significance.** Look up the commonly used clinical-significance standard for the metric (MCID) and compare against it | `effect_size_reporting` (major, when a key conclusion rests on p values alone) |
| Missing data | State the proportion missing and the handling method (complete case / multiple imputation / LOCF) | `missing_data_handling` (minor) |
| Test direction | One-tailed tests must be justified in advance | `one_sided_unjustified` (major) |
| Precision | Reported digits should be commensurate with measurement precision | `p_value_reporting` (info) |

> **Linkage between error-bar type and figures**: `figure_records[].significance_markers` and
> `experimental_conditions` provide in-figure information. A figure caption saying SEM while the text says SD is an
> **internal manuscript contradiction**, primarily owned by M2; M4 adds a finding only when it affects statistical interpretation,
> and the two are clustered into the same issue at Stage 5 (`00-contracts.md §9.3`).

---

## 8. Multiple Comparisons

| Check | Criterion |
| --- | --- |
| How many tests were run on the same dataset? | Inferred from `statistical_methods[].applied_to` and the number of comparisons in `key_data[]`. **Situations that count as multiple testing**: multi-gene analyses, multi-protein assays, multiple endpoints, subgroup analyses, multiple pairwise comparisons |
| Was correction applied? | The `correction` field; Bonferroni / Holm / Šidák / FDR-BH are all acceptable |
| Do omics report adjusted p / q? | §4.8 |
| Are post-hoc comparisons for ≥3 groups corrected? | Tukey / Dunnett / Games-Howell inherently include correction |
| Are only significant results reported? | Linked with M2 (selective reporting) |

**Non-triggering situation**: when the authors explicitly declare secondary endpoints as **exploratory analyses** with no inferential conclusions,
not correcting is acceptable — then check whether conclusions overreach (hand to M7), rather than raising an M4 finding.

---

## 9. Category slugs

**Naming follows JY's version** (more systematic). Severity is not hard-coded — per §3.5,
the same slug is `critical` when it affects the primary endpoint and `major` when it affects only secondary/exploratory analyses.

| slug | Example possible causes | Grading rationale |
| --- | --- | --- |
| `statistical_test_selection` | Test does not match the data type/design (§4.1–4.9) | Affects primary-endpoint analysis → critical; unreasonable method in secondary analysis → major |
| `model_specification` | Specification or construction errors in regression, survival, or prediction models (§4.10) | Primary effect estimate potentially biased → critical; inadequate model interpretation or adjustment → major |
| `statistical_assumption` | Normality/homogeneity of variance/sphericity/proportional hazards/overdispersion unverified | Seriously undermines result credibility → major; reporting deficiency only → minor |
| `power_and_sample_size` | Applicable sample-size/precision justification missing, or the authors' claimed calculation not recomputable (§5) | Confirmatory primary aim without justification, or clear plan-vs-actual contradiction → major; exploratory studies are not automatically flagged for lacking efficacy power |
| `multiple_testing_control` | Multiple comparisons uncorrected (§8) | High-dimensional omics data uncorrected → critical; ordinary multiple comparisons uncorrected → major |
| `replication_independence` | Subsamples/technical replicates within an independently allocated unit treated as independent n (§4.9) | Default major; critical only when evidence covers the allocation level, the analysis level, and impact on the main conclusion |
| `selective_significant_reporting` | Only significant results reported; pre-specified but non-significant analyses concealed (§8) | critical |
| `error_bar_reporting` | Error type unlabeled or figure-text inconsistent (§7) | Affects result interpretation → major; formatting-only → minor |
| `p_value_reporting` | Only `p<0.05` reported, no exact value or statistic (§7) | Affects result interpretation → major; formatting-only → minor |
| `effect_size_reporting` | Effect sizes unreported; or key conclusions rest on p values alone without comparison to a clinical-significance standard (§7) | Key conclusion supported by p value alone → major; missing for secondary metrics → minor |
| `missing_data_handling` | Missing-data handling not described (§7) | major |

**Four framework-side additions** (not covered by JY's version; retained):

| slug | Description | Grading rationale |
| --- | --- | --- |
| `agreement_by_correlation` | Using a correlation coefficient to prove agreement between two measurement methods (should be Bland-Altman, §4.6) | major |
| `censoring_ignored` | Survival data ignoring censoring (e.g., comparing median survival with a t-test, §4.5) | Default major; critical when it acts directly on the primary time-to-event outcome and could change conclusions |
| `cutoff_not_validated` | Cutoff chosen within the data without optimism correction, or development performance treated as confirmatory validation (§4.7) | major |
| `one_sided_unjustified` | One-tailed test without prior justification (§7) | major |

**Five slugs triggered by Phase-1 deterministic forensics signals** (§2):

| slug | Triggering signal | Grading rationale |
| --- | --- | --- |
| `p_value_inconsistent` | `test_statistic_p_mismatch` | Default major; critical when on the primary endpoint and the reported/recomputed p values fall on opposite sides of the pre-specified α, affecting conclusions |
| `ci_self_inconsistent` | `ci_estimate_mismatch` | major |
| `percentage_mismatch` | `count_percentage_mismatch` | Default minor; major when it changes the primary-endpoint denominator, effect size, or participant flow |
| `grim_violation` | `grim_incompatible_mean` | Default major; critical only after humans rule out adjusted means, denominator and rounding ambiguities, and the core conclusion is affected |
| `table_total_mismatch` | Signal of the same name | Default minor; major when it affects the primary endpoint, participant flow, or safety denominators; never critical |

> When raising a finding from a signal, you **must** independently provide manuscript evidence in `evidence_refs[]`
> (the original location where the value is reported); citing the signal id alone is not allowed (`00-contracts.md §6.1` rule 5).

### 9.1 Legacy slug migration

Names used earlier on the framework side are all rewritten to the tables above:

```
wrong_test                        -> statistical_test_selection
pseudoreplication                 -> replication_independence
assumption_unchecked              -> statistical_assumption
sample_size                       -> power_and_sample_size
no_multiple_comparison_correction -> multiple_testing_control
multiple_comparison_correction    -> multiple_testing_control
sample_size_reporting             -> power_and_sample_size
error_bar_ambiguous               -> error_bar_reporting
p_value_incomplete                -> p_value_reporting
no_effect_size                    -> effect_size_reporting
missing_data_unhandled            -> missing_data_handling
over_precision                    -> (merged into the minor tier of p_value_reporting)
```

---

## 10. Positive / Negative Examples

### 10.1 `statistical_test_selection`

**Should alert**: The same batch of mice has blood glucose measured once before and once after dosing (paired design, `relatedness = paired`),
and the methods section says "independent samples t-test" → `mismatch` → default **major**; escalate to `critical` only if recomputation proves it changes
the direction or significance classification of the main conclusion.

**Should not alert**: Two independent groups of mice compared; the authors use Welch t instead of Student t and note unequal variances
→ Welch is in the `acceptable` set → **no alert**.

### 10.2 `replication_independence`

**Should alert**: 6 mice, 10 fields counted per mouse, statistics written as `n = 60`,
the manuscript explicitly assigns treatment at the mouse level yet treats the 60 fields as independent samples → `replication_independence`; if it supports
the main conclusion and changes the significance classification, **critical**, otherwise default **major**.

**Should not alert**: 6 mice, 10 fields each, **first averaged per animal** then compared, `n = 6`
→ correct approach → **no alert**.
Also **no alert** when `replicate_type = unspecified`; output `partial_extraction` instead.

### 10.3 `statistical_assumption`

**Should alert**: Classical one-way ANOVA on 4 very small, unbalanced groups; raw points show strong skewness and outliers,
and nowhere in the text are residual diagnostics, transformation, Welch/robust analysis, or permutation sensitivity analysis seen → the §3.4 risk gate is met → **major**.

**Should not alert**: The same 4 groups, no formal normality test reported, but the residual Q-Q plot shows no clear deviation, group variances are similar,
and Welch ANOVA or a permutation analysis gives consistent results → sufficient diagnostics and robustness evidence → **no alert**.

### 10.4 `agreement_by_correlation`

**Should alert**: Comparing a new sphygmomanometer against a mercury sphygmomanometer, concluding "the two methods agree closely (r = 0.95, p < 0.001)"
→ using correlation to prove agreement → **major**; recommend Bland-Altman instead.

**Should not alert**: Same two methods, but the authors performed Bland-Altman and report bias with 95% limits of agreement,
with r attached only as a supplementary description → **no alert**.

### 10.5 `censoring_ignored`

**Should alert**: Comparing overall survival between two groups with "median survival 18.2 vs 14.6 months, t-test p = 0.03"
→ a t-test on time-to-event data, ignoring censoring → **critical**.

**Should not alert**: KM + log-rank with a numbers-at-risk table → **no alert**.

### 10.6 `power_and_sample_size` (illustrating the standard)

**Should alert (but with restrained wording)**: A confirmatory mouse tumor experiment with n = 3 per group gives no sample-size justification, expected effect,
variance, or uncertainty interval, yet draws a strong-efficacy conclusion from a single significance test
→ `power_and_sample_size` (major); the detail should say "very few independent experimental units, and no sample-size/precision justification
corresponding to the primary endpoint was found; **manual confirmation recommended** for estimate stability and conclusion scope". Do not cite the fixed 5–6 minimum.

**Should not alert**: A method-development `in_vitro` pilot uses 2 independent batches, explicitly aims to estimate process variability,
reports all raw points and wide intervals, and makes no confirmatory biological conclusions → do not raise a finding on a fixed n minimum; the report may
retain a note on its exploratory scope.

### 10.7 `table_total_mismatch`

**Should alert**: Table 1 for the same analysis set explicitly divides subjects into mutually exclusive, exhaustive mild/moderate/severe categories, with counts
12, 18, 9, the header declares `n = 42`, and there is no missing category → the total 39 contradicts the denominator 42 → default **minor**;
**major** if that denominator is used for the primary endpoint or safety incidence rates.

**Should not alert**: An adverse-event table lists counts by event type, and the same subject may have multiple events → categories are not mutually exclusive;
even if row totals exceed the number of subjects, **do not run** the check; produce `partial_extraction` only when the semantics cannot be confirmed.

---

## 10.1 Receiving X1 external validation signals (**severity pending JY's confirmation**)

`scripts/external_figure_validation.py` (Stage 3c) routes one `check_type` to M4:

| X1 `check_type` | Database | Comparison result | Suggested M4 category |
| --- | --- | --- | --- |
| `outcome_switching` | ClinicalTrials.gov | `needs_manual_review` | `registered_outcome_switched` |

**This one cannot be detected by reading the text alone** — the registered primary outcome exists only in the registry. It is one of two facets of the same bias
as the selective reporting in §8: **post hoc endpoint switching belongs to M2,
reporting only significant results belongs to M4's `selective_significant_reporting`,
and "reported outcome inconsistent with the registered outcome" is handled by this entry.**

**Always a candidate; never raise a finding directly.** Coarse keyword screening is fooled by wording differences
(the registry says "percentage of participants with local reactions",
the paper says "reactogenicity" — the same thing). The original registry record must be compared manually.
When switching is confirmed and the main conclusion is built on the switched outcome, use `critical`; otherwise `major`.

When X1 produces a `system_limitation` (primary outcome not registered in the registry, endpoint unreachable),
it must be treated neither as "no problem" nor as "problem"; register the limitation per `00-contracts.md`.

---

## 11. TODO (Phase 1)

- [x] Populate the §4 test-selection lookup tables (this module's top priority)
- [x] Populate §5.2 per-study-type review entry points, and explicitly ban fixed minimum n
- [x] Populate §6 index of domain-specific official guidelines
- [x] Move consistency checks requiring no raw data from Phase 2 up to Phase 1 and wire them to signals (§2, §9)
- [ ] Annotate the six §3.1 characteristics paper by paper on the ten-paper corpus in `datasets/`,
      and measure the proportion of `undetermined` — if it exceeds 50%, M1's
      `statistical_methods` extraction granularity is insufficient and fields need alignment with M1
- [ ] Confirm with M5 the extraction field for error-bar type (the §7 figure-text contradiction check depends on it)
- [x] Draw the boundary with M2 on "selective reporting": **post hoc endpoint switching belongs to M2's `selective_reporting`; reporting only significant results belongs to M4's `selective_significant_reporting`**. The two modules once shared one slug, making Stage 5 clustering unable to distinguish the source; now split per this entry
- [ ] Add decision rules for Bayesian methods and robust estimation (currently always `undetermined`)

---

## 12. Future Enhancements (not currently implemented; rules recorded first)

Forensics that "do not depend on raw data" are already implemented (§2). The capabilities in this section are no longer classified as Phase 2 by network access or the 12-hour timeout;
when raw data or external records are obtainable they may be included as optional Phase-1 enhancements, with contract-specified fallback when they are not.

### 12.1 Recomputation depending on raw data

- Prerequisite: the paper provides raw data (`data_availability` is `reported` and the data are obtainable)
- Scope: rerun the main analyses per the paper's declared methods and compare statistics and p values
- Output category: `recomputation_mismatch` (critical)
- **Risk**: differences in software versions, default parameters, and missing-value handling all cause numerical discrepancies that are not real errors.
  The implementation must distinguish "numerical discrepancy" (minor) from "conclusion direction differs" (critical).

### 12.2 Recomputation from figure-derived data

Linked with M5: take readings from `figure_records[].observations[]` and run consistency checks.
**Hard constraint**: values with `source_type = pixel_estimated` **must not** be used for recomputation
(`00-contracts.md §2.4`). Only values sourced from `explicit_figure_caption` / `axis_readable`
may enter.

### 12.3 SPRITE / GRIMMER extensions

GRIMMER (targeting SD) and SPRITE (reconstructing possible raw distributions) carry more assumptions and more
feasible solutions than GRIM. The implementation must **output candidates only and force manual review**; it must not pass judgment on the manuscript directly.

### 12.4 Checks requiring external data

| Check | Data source | Ownership |
| --- | --- | --- |
| Whether the registered outcome drifted from the paper's primary endpoint | ClinicalTrials.gov / ChiCTR | M4 + M6 |
| Whether the effect size is of a magnitude consistent with prior meta-analyses | Europe PMC | M4 + M7 |
| Whether the reported statistical software version has known defects | Software release records | M4 |
