# M3 · Experimental Methods: Method Reconstruction and Logic Audit (v3)

**Owner: Peter** · Status: **v3 full rewrite (2026-08-08)**

**Core principle**: Reconstruct before you evaluate. Understand what every step does before looking for problems. Do not begin by searching for flaws.

**This file depends on `00-contracts.md`.**

---

## Execution Order (must not be reversed)

```
Phase 1:  Evidence scope + step decomposition
          → understand every step's purpose, output, role, and assumptions
Phase 1b: Per-role requirements audit
          → check fundamental requirements for each step's role
Phase 2:  Method provenance tracing
          → verify that citations support the specific methods attributed to them
Phase 3:  Step connection audit
          → trace input–output continuity and evidentiary level between consecutive steps
Phase 4:  Domain-specific sanity checks
          → biological entities, doses, confounders, controls, selection bias
Phase 5:  Measurement and endpoint validity
          → distinguish what was physically measured from what is claimed
Phase 6:  Finding synthesis
          → self-resolution, severity calibration, finding output
Phase 7:  Final synthesis
          → workflow reconstruction and overall assessment
```

**No finding candidates may be recorded until Phase 1 is complete.**
All findings are produced only at Phase 6. Phases 1–5 produce internal candidate ledger entries only.

**Phase 1b vs. Phase 4 scope**: Phase 1b checks whether each individual step meets the fundamental requirements for its role (controllability, reproducibility). Phase 4 checks the overall experimental design logic (causal chain, confounders, control completeness). The same gap may surface in both phases; consolidate into one finding at Phase 6, taking the highest severity.

---

## Phase 1 · Evidence Scope and Step Decomposition

### 1.1 Evidence scope

Review all available methodological sources in this order:

1. Main paper, including figures, tables, legends, footnotes, and references.
2. Supplementary materials and supporting tables.
3. Methods papers or protocols explicitly cited by the authors.
4. Authoritative external protocols or primary literature describing the same method, if the cited source does not provide enough detail.
5. Relevant curated databases, when biological entities, strains, genes, reagents, interactions, or annotations require verification.

Do not report a method as missing merely because it is absent from the main text if it is adequately described in the supplement or a clearly cited protocol.

Do not silently fill gaps using a generic protocol. Every reconstructed detail must carry one of the following labels:

- **explicitly reported**: stated in the main text, supplement, or clearly cited source
- **incorporated by citation**: taken from a cited methods paper that directly supports this step
- **reasonably inferred**: derivable from context, field conventions, or the assay class
- **unresolved**: cannot be determined from any available source

If a cited protocol has multiple versions, identify which version was available and likely used at the time of the study. Distinguish limitations recognisable at the time from those identified only by later methodological work.

### 1.2 Step decomposition

Divide the complete method into numbered steps (S01, S02, …). Include computational, biological, measurement, and statistical steps.

For each step, record:

```
step_id        : S01, S02, … (globally unique, incrementing)
text_excerpt   : verbatim method text (≤150 words)
skill_type     : see §1.3 Lab Skill categories
step_role      : see §1.4 Step Role taxonomy
protocol_source: see §1.5 Protocol source hierarchy
purpose        : what question does this step answer?
input          : what material, data, strain, sample, or intermediate result enters this step?
action         : what is done to the input?
output         : what result is produced?
decision_role  : how is the output used in the next step?
controls       : positive, negative, loading, procedural, or biological controls present
quality_checks : how is successful execution demonstrated?
assumptions    : what must be true for the output to support the intended interpretation?
role_req_status: PASS / PARTIAL / FAIL / UNKNOWN (filled at Phase 1b)
notes          : any flag or question to examine in later phases
```

**Granularity**: one operational unit = one method applied to one sample in one independent treatment. Parallel treatments of the same reagent on the same sample may be merged; different conditions must be separate entries. Do not decompose to the pipetting level; retain the "centrifuge → collect supernatant" level.

### 1.3 Lab Skill categories (skill_type)

| code | Category | Example steps |
|------|----------|---------------|
| `CELL_CULTURE` | Cell culture and maintenance | thaw, passage, freeze, media change |
| `CELL_TREAT` | Cell treatment / stimulation | drug addition, siRNA transfection, lentiviral infection, irradiation |
| `CELL_VIABILITY` | Cell viability assay | CCK-8, MTT, MTS, trypan blue, LDH |
| `COLONY_FORM` | Colony formation / proliferation | soft agar, plate colony, BrdU/EdU labelling |
| `APOPTOSIS_DETECT` | Apoptosis / cell death | Annexin V/PI, AO/EB, TUNEL, caspase activity |
| `PROTEIN_EXPR` | Protein expression | Western blot, ELISA, intracellular flow |
| `PROTEIN_INTERACT` | Protein interaction | Co-IP, pulldown, proximity ligation |
| `NUCLEIC_ACID` | Nucleic acid analysis | PCR, qPCR, RT-PCR, RNA-seq, ChIP-seq |
| `MICROSCOPY` | Microscopy and imaging | confocal, fluorescence, brightfield, EM, histological sections |
| `HISTOPATH` | Histopathology | H&E, Masson, IHC, special stains, scoring |
| `FLOW_CYTOM` | Flow cytometry | surface markers, DNA content, multi-colour panel |
| `ANIMAL_MODEL` | Animal model establishment | surgery, injection model, drug induction, genetic engineering |
| `ANIMAL_BEHAV` | Animal behaviour | OFT, EPM, MWM, FST, NOR, open field |
| `BIOCHEM_ASSAY` | Biochemical activity | SOD/CAT/POD, MDA, ATP, ROS |
| `CHROMATOGRAPHY` | Chromatographic analysis | HPLC, LC-MS, GC-MS |
| `IN_SILICO` | Computational / bioinformatic | docking, target prediction, pathway analysis, network pharmacology |
| `SAMPLE_PREP` | Sample preparation | lysis, centrifugation, homogenisation, fixation, embedding, sectioning |
| `ADMIN_ROUTE` | Administration route | gavage, IP injection, IV injection, inhalation, transdermal |
| `CLINICAL_PROC` | Clinical procedure | blood draw, biopsy, imaging, questionnaire, physical examination |
| `SURVIVAL_ANAL` | Survival analysis | lifespan assay, Kaplan-Meier curve, log-rank test |
| `STATS_INFER` | Statistical inference | t-test, ANOVA, non-parametric tests, multiple comparison correction |
| `SEQ_BIOINF` | Sequence bioinformatics | motif search, alignment, comparative genomics, genome annotation |
| `OTHER` | Other | cannot be categorised above; explain in notes |

### 1.4 Step Role taxonomy

Every step must be assigned one primary role. The role determines which Phase 1b requirements apply.

| role | Meaning | Typical examples |
|------|---------|-----------------|
| `INTERVENTION` | Imposes the experimental variable — treatment, dosing, genetic manipulation, surgery, stimulation. **Direct source of observed differences.** | drug dosing (IP/oral/aerosol), siRNA transfection, CRISPR editing, OVA sensitisation, model creation |
| `DETECTION` | Measures or quantifies an outcome endpoint — produces raw numeric or image data. **Direct basis for conclusions.** | Western blot, ELISA, qPCR, CCK-8, flow cytometry, behavioural scoring, pathology scoring |
| `PROCESSING` | Intermediate sample transformation that does not itself produce outcome data — must be applied uniformly to all groups | tissue lysis, centrifugation, RNA extraction, paraffin embedding, sectioning, protein quantification |
| `VALIDATION` | Confirms that a model, reagent, or step is valid — a prerequisite gate for proceeding | model success assessment (behavioural signs), transfection efficiency check, mycoplasma testing, positive control response |
| `CALIBRATION` | Provides a quantitative reference for a DETECTION step — without it, DETECTION gives only relative values | ELISA standard curve, WB loading control, flow FMO control, histology positive-control section |
| `ANALYSIS` | Data processing and statistical inference — converts raw numbers to conclusions | ImageJ quantification, GraphPad statistics, scoring systems, image threshold segmentation |

A step may serve multiple roles; assign the **primary role** and note secondary roles in the `notes` field.

**Key rules**:
- Every `DETECTION` step must have a corresponding `CALIBRATION` step (or inline calibration).
- Every `INTERVENTION` step must have a corresponding paired control condition.
- Every `VALIDATION` step must have pre-defined success/failure criteria.
- Missing correspondence → candidate ledger entry `ROLE_REQ_MISSING`.

### 1.5 Protocol source hierarchy

For each step, try the following levels in order and stop at the first that applies:

| Level | Source | Record |
|-------|--------|--------|
| **L1** | Methods paper explicitly cited ("following ref [X]") | citation number; verify via X1 that the cited paper contains this method |
| **L2** | Commercial kit or instrument standard protocol ("per manufacturer's instructions") | vendor + catalogue number; if vendor only and no catalogue → candidate ledger |
| **L3** | Field-recognised standard protocol (MIQE / ARRIVE / CONSORT etc.) | standard name and version |
| **L4** | Paper self-described protocol (complete in the methods section) | excerpt of key parameters |
| **L5** | No traceable source | mark `PROTOCOL_MISSING`; enter candidate ledger |

L5 does not automatically produce a finding; criticality depends on the step's centrality (judged at Phase 6).

---

## Phase 1b · Per-Role Requirements Audit

After completing the Phase 1 step table, check every step against the fundamental requirements for its `step_role`. Record status in `role_req_status`:
- `PASS`: all applicable requirements met
- `PARTIAL`: some met, some unreported (non-fatal)
- `FAIL`: at least one critical requirement clearly violated
- `UNKNOWN`: insufficient information to judge

`FAIL` and `PARTIAL` items enter the candidate ledger with their failure code. They do not automatically become findings (severity is determined at Phase 6).

**Anti-false-positive rule**: unreported ≠ absent. Only enter a candidate when absence is confirmed; ambiguous wording → `UNKNOWN`, not a candidate.

### 1b.1 INTERVENTION requirements

A controlled experiment requirement: change one variable, hold all others constant.

| Requirement | Check | Failure code |
|-------------|-------|-------------|
| **Paired control exists** | Is there a concurrent condition that omits or substitutes the variable? (vehicle control, empty vector, sham surgery, saline group) | `MISSING_PAIRED_CONTROL` |
| **Variable uniqueness** | Does this step change multiple variables simultaneously without single-variable comparator groups? | `CONFOUNDED_VARIABLE` |
| **Dose/concentration/duration/route all recorded** | Any of the four missing | `INTERVENTION_UNDERSPECIFIED` |
| **Consistent operator across groups** | Different groups handled by different personnel or batches without disclosure? | `OPERATOR_BATCH_UNREPORTED` |
| **Random assignment** | Are subjects/samples randomly assigned to intervention groups, or is a rationale given for non-random assignment? | `RANDOM_ASSIGNMENT_MISSING` |

### 1b.2 DETECTION requirements

Reproducibility requirement: identical samples measured repeatedly should give consistent values.

| Requirement | Check | Failure code |
|-------------|-------|-------------|
| **Paired CALIBRATION step** | Is there a corresponding `CALIBRATION` step in the same experimental run (loading control, standard curve, positive control)? | `CALIBRATION_MISSING` |
| **Reproducibility evidence** | Are technical replicate counts (replicate wells/tubes) or intra-run CV reported? | `REPRODUCIBILITY_UNREPORTED` |
| **Objectivity or blinding** | If the result depends on subjective judgment (pathology scoring, behavioural timing, band reading), is blinding or algorithmic evaluation described? | `SUBJECTIVITY_UNCONTROLLED` |
| **Pre-defined quantification criteria** | Are cut-offs, scoring thresholds, or counting rules defined prior to data acquisition (not driven by the data)? | `QUANTIFICATION_CRITERIA_UNDEFINED` |
| **Detection range coverage** | Does the assay's linear range cover the expected concentration or signal of the analyte? | `DETECTION_RANGE_CONCERN` |

### 1b.3 PROCESSING requirements

Uniformity requirement: all groups must share identical processing history.

| Requirement | Check | Failure code |
|-------------|-------|-------------|
| **All groups processed in the same batch** | Are all samples processed concurrently? Or is there batch separation (different days, different operators)? | `BATCH_EFFECT_UNCONTROLLED` |
| **Key parameters recorded** | Duration, temperature, speed (centrifuge), buffer composition — all present? | `PROCESSING_UNDERSPECIFIED` |
| **Sample stability window** | Is the interval between the prior step and this step within the analyte's known stability window (especially protein, RNA, cytokines)? | `STABILITY_WINDOW_VIOLATED` |
| **No differential processing** | Do any groups receive extra processing steps not applied to others? | `DIFFERENTIAL_PROCESSING` |

### 1b.4 VALIDATION requirements

A VALIDATION step is a gate. Without it, the premise of subsequent measurements cannot be confirmed.

| Requirement | Check | Failure code |
|-------------|-------|-------------|
| **Pre-defined success criteria** | Are pass/fail criteria stated in the methods or a cited reference? (e.g. "≥5 coughs in 3 min = model success") | `VALIDATION_CRITERIA_UNDEFINED` |
| **Applied equally to all groups** | Is the validation step applied uniformly to all groups, including controls? | `VALIDATION_SELECTIVELY_APPLIED` |
| **Handling of failures described** | If validation fails, how is that animal/sample handled (excluded? replaced?)? | `VALIDATION_FAILURE_UNADDRESSED` |
| **Results reported** | Is the outcome of the validation step presented in the results or methods (not merely claimed)? | `VALIDATION_RESULT_UNREPORTED` |

### 1b.5 CALIBRATION requirements

A CALIBRATION step is the reference frame for DETECTION results.

| Requirement | Check | Failure code |
|-------------|-------|-------------|
| **Concurrent with DETECTION** | Is the calibration run in the same experimental run as the samples? (Cross-run reuse of a standard curve is a common error.) | `CALIBRATION_NOT_CONCURRENT` |
| **Range coverage** | Does the standard curve or reference range cover the expected concentration/signal of the samples? | `CALIBRATION_RANGE_INSUFFICIENT` |
| **Reference material documented** | Are the source, concentration, and lot of the standard/reference antibody/positive control recorded? | `CALIBRATION_SOURCE_MISSING` |
| **Linear range only** | Is interpolation confined to the linear range (no extrapolation beyond the curve)? | `EXTRAPOLATION_CONCERN` |

### 1b.6 ANALYSIS requirements

Transparency requirement: others can reproduce the same conclusion using the same rules.

| Requirement | Check | Failure code |
|-------------|-------|-------------|
| **Software + version recorded** | Name and version of analysis software stated? | `SOFTWARE_VERSION_MISSING` |
| **Parameters / thresholds recorded** | ImageJ thresholds, segmentation parameters, cut-off values — all stated? | `ANALYSIS_PARAMETER_UNDEFINED` |
| **Blinding (subjective analysis)** | If analysis involves subjective judgment (histology scoring), was the analyst blinded to group assignments? | `SUBJECTIVITY_UNCONTROLLED` |
| **Inter-rater reliability** | If multiple scorers are involved, is inter-rater agreement (Cohen's κ or ICC) reported? | `INTER_RATER_UNREPORTED` |
| **Pre-specified, not data-driven** | Were analysis parameters defined before looking at the data (not adjusted until results "look good")? | `POST_HOC_PARAMETER_TUNING` |

---

## Phase 2 · Method Provenance Tracing

For each step, determine whether the cited source actually describes the specific procedure attributed to it.

**When a citation is present**:
- Verify that the cited paper or protocol supports the specific method attributed to it, not a related but different procedure.
- Check whether the experimental system, organism, assay format, and conditions are sufficiently comparable to the current study. A method validated in one system may not transfer without modification.
- Identify any important modifications made by the current authors. If the modification is material to the result and undisclosed, enter `PROTOCOL_ADAPTED_UNDISCLOSED`.
- Do not assume that a citation resolves details it does not contain.
- If the cited protocol has multiple versions, identify which was available at the time of the study.

**When no adequate cited method is available**:
- Search for an authoritative protocol or primary methods paper for context.
- Use external material only to understand the method and expected controls — not to assume the authors performed unreported procedures.
- If the procedure remains unavailable, record `PROTOCOL_MISSING` rather than inventing detail.

**Candidate ledger entries from Phase 2**:

| Code | Condition | Default severity |
|------|-----------|-----------------|
| `METHOD_CITATION_MISMATCH` | Cited paper does not describe the attributed method, or describes it only for a different organism/assay system | major |
| `PROTOCOL_ADAPTED_UNDISCLOSED` | Authors made material changes to a cited protocol without disclosing modifications | minor |
| `PROTOCOL_MISSING` | No traceable source for a non-trivial step | escalate to major if step is critical |

---

## Phase 3 · Step Connection Audit

After completing Phase 1, check every consecutive step pair (Sn → Sn+1) for logical and evidentiary continuity.

### 3.1 Connection validity checks

| Check | Criterion | Candidate code |
|-------|-----------|----------------|
| **Output–input match** | Does Sn's output become Sn+1's required input? Is the material identity, genotype, treatment state, tissue, and time point preserved? | `FLOW_BREAK` |
| **Evidentiary level preserved** | Is a computational candidate being treated as an experimentally validated target? Is an association being treated as a causal mechanism? Is a qualitative screen used to justify quantitative downstream claims? | `FLOW_BREAK_EVIDENTIARY` |
| **Selection bias** | Does selection at Sn introduce bias into Sn+1? Were thresholds or inclusion criteria defined before candidate follow-up, or derived from inspecting the results? | `POST_HOC_SELECTION` |
| **Negative result interpretability** | Could a null result in Sn reflect technical failure rather than true biological absence? | `TECHNICAL_NEGATIVE_AMBIGUOUS` |
| **Temporal plausibility** | Are intervals between steps consistent with the biology (incubation, wash, freeze, fixation timing)? | `TIMELINE_ANOMALY` |
| **Reagent compatibility** | Does anything introduced in Sn interfere with Sn+1's chemistry (e.g. DMSO carry-over, ionic strength, competing substrates)? | `REAGENT_CARRY_OVER` |
| **Independent confirmation** | Does the central inference have at least one independent confirmation step in the workflow? | flag if absent |

`FLOW_BREAK` and `FLOW_BREAK_EVIDENTIARY` are the highest-priority candidate types. A broken output–input connection or an illicit evidentiary jump severs the experimental chain.

### 3.2 Overall workflow completeness

- Does the experiment have a defined starting material (animal, cell, sample source)?
- Does it have a defined endpoint with a corresponding detection step?
- Does every major claimed endpoint have a corresponding measurement step?
- Is there a step that independently confirms the central inference?

---

## Phase 4 · Domain-Specific Sanity Checks

Apply only the checks relevant to the study type.

### 4.1 Biological entity verification

For cells, organisms, viruses, animals, genes, proteins, or other biological entities, verify using curated databases (via X1 when available).

| Category | Checks | Candidate codes |
|----------|--------|-----------------|
| **Animal / organism** | Species/strain fits the disease model; age, sex, developmental stage suit the research question; species has known responses to the treatment or assay; behavioural norms correctly understood; group size accounts for expected attrition | `ORGANISM_MODEL_MISMATCH` |
| **Cell line** | Supplier + catalogue/ATCC/RRID given; mycoplasma-free declared; STR validation mentioned; culture conditions match known requirements; line not on misidentification/contamination lists (Cellosaurus/ICLAC); passage number given for primary cells | `CELL_LINE_SOURCE_MISSING`, `MYCOPLASMA_UNREPORTED`, `STR_UNREPORTED`, `CULTURE_CONDITION_MISMATCH`, `CELL_LINE_IDENTITY_UNVERIFIED`, `PASSAGE_UNREPORTED` |
| **Reagent / drug** | Mechanism consistent with intended effect; solvent compatible with downstream assay; final solvent concentration acceptable; source + catalogue given; unstable reagents have storage conditions stated | `AGENT_MECHANISM_MISMATCH`, `SOLVENT_ISSUE`, `REAGENT_NO_CATALOG`, `STABILITY_UNREPORTED` |
| **Gene / protein annotation** | Known biological activity and localisation; expected interaction with treatment or assay; database annotations support assumed orthology, function, sequence, interaction, or regulatory relationship | verify via X1; note if modern annotations differ from those at time of study |

When modern annotations differ from those available at the time of the study, report this as a **historical limitation** — not an original error.

### 4.2 Interaction plausibility

For every major entity–entity interaction in the method (drug–target, stimulus–cell, treatment–model), check:

1. **Direction**: Is the predicted effect direction consistent with established biology?
2. **Magnitude**: Is the dose/concentration within the known active range? (A compound with IC₅₀ = 10 µM tested at 0.1 µM is likely below its effective range.)
3. **Context match**: Does the substrate, environment (liquid vs. agar, temperature, pH, ionic strength) match the cited method and the assay's known requirements?
4. **Toxicity mimicry**: Could the treatment produce toxicity, developmental delay, starvation, stress, reduced movement, or altered feeding that mimics the intended endpoint?

Candidate codes: `INTERACTION_IMPLAUSIBLE`, `INTERACTION_CONTEXT_MISMATCH`.

### 4.3 Dose and treatment reasonableness

| Check | Criterion | Candidate code |
|-------|-----------|----------------|
| **Dose gradient** | Dose-response studies with fewer than 4 non-zero dose points | `DOSE_GRADIENT_INSUFFICIENT` |
| **Dose rationale** | No stated basis for dose selection (pilot experiment, literature, MTD, IC₅₀) | `DOSE_RATIONALE_MISSING` |
| **Species-appropriate dose** | Dose exceeds safe range for this species and route (near MTD/LD₁₀; DMSO > 0.5%) or is below the effective range | `DOSE_OUT_OF_RANGE` |
| **Single time-point kinetics** | Single time-point used to draw kinetic or persistence conclusions | coordinate with M7 |

### 4.4 Controls

| Situation | Required control | If absent |
|-----------|-----------------|-----------|
| Drug / compound treatment | Vehicle control (same volume and concentration solvent) | `MISSING_CONTROL` (critical) |
| Gene knockdown (siRNA/shRNA) | Non-targeting control (scrambled/NC) | `MISSING_CONTROL` (critical) |
| Overexpression | Empty vector control | `MISSING_CONTROL` (critical) |
| Antibody experiments (IP/IHC/IF) | Isotype IgG / primary antibody omission | `MISSING_CONTROL` (major) |
| Surgical model | Sham surgery | `MISSING_CONTROL` (critical) |
| Fluorescence staining | Negative control (unstained / secondary antibody only) | `MISSING_CONTROL` (major) |
| Behavioural assay | Untreated/blank control + positive drug control (if evaluating treatment effect) | `MISSING_CONTROL` (major) |

**Anti-false-positive rule**: if controls information is parse_failed or ambiguous, do not enter a candidate. Not read ≠ not present.

### 4.5 Confounders

Ask: does the experimental design include factors that could produce unexpected influences on the result, with neither control nor disclosure given?

Common confounders (non-exhaustive):
- Solvent toxicity (DMSO, ethanol, methanol) without a vehicle control
- Sequential behavioural tests on the same cohort (order effects, fatigue, habituation)
- Model-induction toxicity affecting the measured physiological endpoint
- Gavage stress on behavioural outcomes
- Multiple freeze-thaw cycles on a sample used across multiple assays
- Time-of-day effects for immune cell functional assays
- Known redundancies or compensatory pathways in the model system that could mask the intended effect

Candidate codes: `CONFOUND_UNREPORTED` (no control and no disclosure), `CONFOUND_CONTROLLED` (disclosed and controlled → no finding).

### 4.6 Assay minimum reporting elements

Check only the elements listed for the assay type; do not apply cross-assay requirements.

| Assay | Required elements (absent → major) | Recommended elements (absent → minor) |
|-------|-------------------------------------|---------------------------------------|
| **Western blot** | antibody source + catalogue, dilution, loading amount, loading control | transfer conditions, blocking buffer, gel percentage (required when spanning wide MW range), exposure time |
| **qPCR** | primer sequence or catalogue, reference gene, quantification method (2^−ΔΔCt etc.) | amplification efficiency, melt curve, RNA quality (RIN) |
| **ELISA** | kit vendor + catalogue, detection range (linear range), standard curve | intra/inter-assay CV, dilution factor, storage conditions |
| **IHC / IF** | antibody catalogue + dilution, antigen retrieval, positive/negative controls | quantification method, blinding of scoring |
| **Flow cytometry** | antibody panel (fluorochrome + clone), gating strategy, isotype/FMO controls | compensation scheme, live/dead staining, cell count acquired |
| **CCK-8 / MTT / MTS** | seeding density, treatment duration, absorbance wavelength, vehicle control | replicate count, background subtraction |
| **Histology (H&E/Masson/special)** | fixation method, section thickness, staining protocol, scoring criteria | number of scorers, blinding, fields per sample |
| **RNA-seq / ChIP-seq** | platform, library kit, sequencing depth/read length, alignment software + version, reference genome version | QC metrics (Q20/Q30), batch information |
| **Animal behaviour** | apparatus dimensions/material, test duration, environmental conditions (light/noise/temperature), blinding of scoring | habituation period, test order randomisation, time of day |
| **Co-IP / pulldown** | antibody catalogue, lysis buffer composition, IgG control | wash stringency, input proportion |
| **HPLC / LC-MS** | column type, mobile phase composition, flow rate, detection wavelength or mass range, standard source | retention time, response factor, recovery rate |
| **In silico docking** | target PDB ID and resolution, docking software + version, grid/search space definition, scoring function | validation against known ligand, binding pocket selection rationale |
| **Colony formation** | seeding cell count, culture duration, fixation/staining protocol, counting threshold (≥X cells) | wells per group (distinguish biological vs. technical replicates) |
| **Survival assay** | statistical test used (log-rank preferred over t-test for censored data), censoring criteria, n per group | daily scoring method, exclusion criteria |
| **AO/EB staining** | AO/EB concentration or ratio, staining duration, cells counted per group, classification criteria (live/early/late apoptotic/necrotic) | blinding, fields acquired |

> **Across all assays**: key reagents (antibodies, compounds, cell lines) should have source + catalogue/lot. Vendor only without catalogue → `reagent_traceability_incomplete` (minor).

### 4.7 Randomisation, blinding, and replication

| State | Action |
|-------|--------|
| Method reported | No finding |
| Not reported | `randomization_blinding_unreported` (minor; coordinates with M6 ARRIVE) |
| Explicitly absent with justification | No finding |
| Explicitly absent without justification | major |

### 4.8 Multiple testing and selection bias

| Situation | Check | Candidate code |
|-----------|-------|----------------|
| Multiple comparisons from a single dataset | Is an appropriate correction applied (Bonferroni, FDR, etc.)? | `MULTIPLE_TESTING_UNCORRECTED` |
| Candidates selected for follow-up based on initial result inspection | Were selection criteria pre-specified, or chosen after inspecting the data? | `POST_HOC_SELECTION` |
| Subset highlighted from a large initial screen | Is the statistical framing adjusted for the actual search space? | `POST_HOC_SELECTION` |

---

## Phase 5 · Measurement and Endpoint Validity

For every major endpoint, clearly distinguish:

1. **What was physically measured** — the raw instrument signal or observation
2. **What biological construct the authors claim it represents** — the interpretation
3. **What evidence connects the measurement to that construct** — the assay validation basis

**Construct validity check**: does this assay measure the biological variable it is claimed to measure? A visually clear or statistically significant difference does not validate an assay that may measure the wrong variable.

**Construct validity concern required when**:
- The assay is used outside its validated conditions (species, sample type, treatment context)
- Modern literature has identified the assay as unreliable for the claimed measurement in this system
- The assay has known cross-reactivity or non-specific effects in this experimental context

**Do not reject a qualitative assay** solely because it lacks modern quantification, provided:
- The claimed conclusion is explicitly qualitative
- Adequate controls support the direction of the effect
- The authors do not over-interpret the result as quantitatively precise

For each major endpoint, produce a construct validity entry:

```
endpoint    : the measurement made
construct   : the biological variable claimed
link_type   : direct / proxy / indirect
evidence    : what supports the assay→construct link
concern     : any reason to doubt the link
resolution  : whether the concern is resolved by controls, supplementary data, or citations
```

---

## Phase 6 · Finding Synthesis

### 6.1 Self-resolution criteria

For each candidate, search the paper, supplement, cited methods, figures, tables, and legends for resolving information.

**A concern may be cancelled or downgraded when**:
- The missing detail is explicitly supplied elsewhere in the paper or supplement
- A control directly rules out the alternative explanation
- An independent assay confirms the same conclusion by a different method
- Figure or table data adequately support an otherwise underexplained step
- The authors appropriately limit the claim to what the method actually demonstrates

**A concern may NOT be downgraded merely because**:
- The method was common practice for its era — historical context explains why the gap exists but does not increase the evidentiary strength of the experiment
- The result looks visually convincing
- The P value is small
- The authors acknowledge the limitation
- A generic protocol could theoretically have included the missing control

Era context is relevant to the `recommended_action` field (where a gap in a published study may be irreversible) and to the fairness of the framing. It does not alter the severity rating.

### 6.2 Finding format

Each finding must include:

| Field | Content |
|-------|---------|
| `id` | F01, F02, … |
| `severity` | critical / major / minor / informational |
| `slug` | from §6.4 |
| `step_refs` | step IDs from Phase 1 (at least one required) |
| `evidence_refs` | explicit evidence for the presence or absence of the element |
| `finding` | one sentence stating the problem |
| `evidence` | what specifically supports this finding |
| `impact` | how this changes the interpretation of the results |
| `alternative_explanation` | the strongest alternative reading of the data given this gap |
| `self_resolution` | whether and where the paper resolves this concern |
| `scope` | `whole_paper` / `central_conclusion` / `specific_subclaim: [name]` |
| `confidence` | `high` / `medium` / `low` |

**No finding without `step_refs`.** If no corresponding step can be found, Phase 1 decomposition is incomplete — complete Phase 1 first.

A finding at `confidence: low` must include a specific condition under which it would be upgraded or resolved (e.g. "resolved if SOM confirms fixed-worm Nile Red protocol").

### 6.3 Severity calibration

**Assign severity only after determining how the issue changes the interpretation.**

Assess severity separately for:
1. **The paper's overall conclusion** — could this issue reverse or remove the paper's principal claim?
2. **The particular subclaim directly affected** — could this issue invalidate this specific result?

A flaw may be major for one subclaim but minor for the paper as a whole. Report both assessments when they differ.

| Severity | Definition |
|----------|-----------|
| `critical` | Breaks a necessary link in the core experimental logic; invalidates a central measurement; permits a strong alternative explanation; or could substantially reverse a central conclusion. Cannot be resolved by a reporting clarification alone. |
| `major` | Weakens the reliability of a key result or introduces a significant validation gap; material and unlikely to be resolved by generic conventions. |
| `minor` | Incomplete reporting or a localised gap unlikely to change the principal conclusion; readily correctable or indirectly supported by other evidence. |
| `informational` | A reproducibility or transparency observation with little expected effect on conclusions. Do not use for a genuine validity problem. |
| `no_finding` | The concern is adequately resolved by the paper, supplement, cited protocol, controls, or data. |

**Do not use finding count as a proxy for overall quality.** Weight findings by their position in the causal chain and their likely effect on the results.

### 6.4 Finding slug catalogue

#### Experimental design slugs (Phases 3–5)

| slug | Description | Default severity |
|------|-------------|-----------------|
| `missing_control` | Critical control absent at the whole-design level | critical |
| `flow_break` | Step output–input mismatch; material or sample identity chain broken | major |
| `flow_break_evidentiary` | Computational candidate treated as experimentally validated; association treated as causal | major |
| `post_hoc_selection` | Candidate or parameter selected after inspecting results, without pre-specification | major |
| `multiple_testing_uncorrected` | Multiple comparisons without statistical correction | major |
| `construct_validity_concern` | Assay may not measure the biological construct it is claimed to measure | major |
| `interaction_implausible` | Entity–entity interaction contradicts established biology | major |
| `interaction_context_mismatch` | Interaction plausible but substrate, parameters, or environmental context do not match | major |
| `dose_out_of_range` | Dose exceeds safe range or is below effective range | major |
| `endpoint_missing` | A node in the main hypothesis has no corresponding detection step | major |
| `endpoint_proxy_questionable` | Measurement does not directly represent the claimed biological variable | minor / major |
| `confound_unreported` | Known confounder present with neither control nor disclosure | major / minor |
| `method_citation_mismatch` | Cited method paper does not describe the attributed procedure | major |
| `method_reporting_incomplete` | Assay minimum elements (§4.6) absent | major / minor |
| `protocol_adapted_undisclosed` | Material protocol modification not disclosed | minor |
| `protocol_missing` | No traceable source for a critical step | major |
| `animal_use_justification_unclear` | Animal experiment necessity not justified | major |
| `dose_gradient_insufficient` | Fewer than 4 non-zero dose points in a dose-response study | major |
| `dose_rationale_missing` | No stated basis for dose selection | minor |
| `replicate_type_unclear` | Biological vs. technical replicates not distinguished | major |
| `randomization_blinding_unreported` | Randomisation or blinding not reported | minor / major |
| `cell_line_unauthenticated` | Cell line source/authentication unreported | minor |
| `reagent_traceability_incomplete` | Key reagent missing source or catalogue number | minor |
| `technical_negative_ambiguous` | A null result cannot be distinguished from technical failure | minor / major |
| `timeline_anomaly` | Interval between steps inconsistent with biology | major / minor |
| `missing_intermediate_step` | A necessary intermediate processing step is absent from the workflow | major / minor |

#### Per-role requirement slugs (Phase 1b)

These arise from Phase 1b single-step role checks. At Phase 6, consolidate with experimental design slugs — do not double-count the same gap.

| slug | Role | Description | Default severity |
|------|------|-------------|-----------------|
| `missing_paired_control` | INTERVENTION | Intervention step has no concurrent control condition | critical |
| `confounded_variable` | INTERVENTION | Single step changes multiple variables without comparator groups | major |
| `intervention_underspecified` | INTERVENTION | Dose/duration/route/conditions incomplete | major / minor |
| `random_assignment_missing` | INTERVENTION | Subjects not randomly assigned to groups | major |
| `calibration_missing` | DETECTION | DETECTION step has no paired CALIBRATION | major |
| `reproducibility_unreported` | DETECTION | Technical replicate count or intra-run CV not reported | minor |
| `subjectivity_uncontrolled` | DETECTION / ANALYSIS | Subjective judgment step lacks blinding or algorithmic evaluation | major |
| `quantification_criteria_undefined` | DETECTION | Threshold/scoring criteria not pre-defined | major |
| `detection_range_concern` | DETECTION | Analyte concentration outside assay linear range | major |
| `batch_effect_uncontrolled` | PROCESSING | Groups processed in different batches without disclosure | major |
| `processing_underspecified` | PROCESSING | Key parameters (time/temperature/speed) absent | minor |
| `stability_window_violated` | PROCESSING | Sample held outside stability window | major |
| `validation_criteria_undefined` | VALIDATION | No pre-defined pass/fail criteria for model or reagent validation | major |
| `validation_result_unreported` | VALIDATION | Validation step outcome not presented | minor |
| `calibration_not_concurrent` | CALIBRATION | Calibration not in same experimental run as samples | major |
| `calibration_range_insufficient` | CALIBRATION | Standard curve does not cover sample concentration range | major |
| `calibration_source_missing` | CALIBRATION | Standard/reference material source not documented | minor |
| `software_version_missing` | ANALYSIS | Analysis software version not recorded | minor |
| `inter_rater_unreported` | ANALYSIS | Multiple scorers; inter-rater agreement not reported | minor |

---

## Phase 7 · Final Synthesis

Conclude with:

1. **Workflow reconstruction**: a concise description of the complete experimental workflow as reconstructed (not merely as written), including steps that were incorporated by citation or reasonably inferred.
2. **Strongest design elements**: which parts of the experimental design are well-controlled and provide reliable evidence.
3. **Weakest transition**: the single most critical gap or unsupported inferential step in the evidence chain — the link where the experimental logic is most exposed.
4. **Directly supported conclusions**: which specific claims are adequately supported by the methods as described.
5. **Candidate-level conclusions**: which claims are associative, exploratory, or based on a single unvalidated inference step. These are not necessarily wrong, but they are not mechanistically established.
6. **Contemporary vs. later limitations**: distinguish limitations that were recognisable and addressable at the time of publication from those that reflect methodological knowledge developed afterwards.
7. **Overall assessment**: is the method exploratory, confirmatory, or mechanistically definitive? This assessment must be justified by the specific findings and their positions in the causal chain, not by the count of findings alone.

---

## Module Boundaries

| Situation | Owner | Rationale |
|-----------|-------|-----------|
| Is animal experimentation **necessary**? | **M3** | methodological judgement |
| Is there an **ethics approval**? | **M6** | compliance judgement |
| Is the sample size **adequate**? | **M4** | statistical power |
| Technical replicates used as statistical n | **M4** (`pseudoreplication`); M3 flags as "not distinguished" | statistical inference issue |
| Method text **internally inconsistent** | **M2** | internal consistency |
| Conclusion **exceeds data support** | **M7** | conclusion-evidence alignment |
| Primer/accession number **format errors** | tool signal → **M3** judgement | `sequence_identifier_audit.py` |
| Numeric **internal inconsistency** (e.g. dose stated differently in two places) | **M2** + **M3** linked | M2 checks consistency; M3 judges which value is methodologically correct |

---

## Online Enhancement — X1 is **DELIVERED**, not a candidate

> **Status correction.** This section was originally written as "future candidates".
> X1 is implemented and has run live against a real paper
> (`scripts/external_figure_validation.py` — 12 databases, 14 checks;
> verified 43 reference DOIs plus a Dryad dataset DOI in a real run).
> **Call these now**; do not treat them as phase-2 ideas.
> Invocation: see `SKILL.md` §4. Evidence: `docs/results/realpaper-pmc11856280-*`.

| Function | Data source | New slug |
|----------|-------------|---------|
| Method citation verification | Crossref / PubMed via X1 | `method_citation_mismatch` (major) |
| Cell line misidentification | Cellosaurus / ICLAC via X1 | `cell_line_misidentified` (critical) |
| Antibody RRID verification | RRID Registry / Antibody Registry via X1 | `antibody_validation_issue` (major) |
| Dose vs. literature distribution | PubMed + ChEMBL via X1 | `dose_out_of_range` (produces external_validation_candidate; no direct finding) |

When an external source is unreachable, produce only `system_limitation`; do not change the manuscript risk score.

---

## Examples

### E1 · `flow_break_evidentiary` (Phase 3 → Phase 6)

**Report**:
> S02 (bioinformatic screen identifies 947-candidate gene set) → S04 (RNAi knockdown of specific candidates to test lifespan phenotype)

S02's output is a computationally predicted candidate set. S04 treats these as validated candidates without an intermediate experimental confirmation step. The evidentiary level is not preserved; a computational prediction and an experimentally confirmed target are not equivalent inputs for a mechanistic claim. The selection threshold is not pre-specified before follow-up. Severity: major for the claim that any observed RNAi phenotype reflects on-target activity.

**Do not report**:
> S03 (filter 947 candidates by conservation across species) → S04 (RNAi knockdown of conserved candidates)

Bioinformatic filtering is appropriate for prioritising candidates for experimental follow-up. The issue is whether candidates are treated as validated targets versus exploratory candidates. If the paper explicitly frames them as exploratory, this transition is acceptable.

### E2 · `dose_out_of_range` (Phase 4 → Phase 6)

**Report**:
> "Methamphetamine … administered by intraperitoneal injection to mice in a concentration of 40 mg/kg"

Mouse METH i.p. LD₅₀ ≈ 57 mg/kg. 40 mg/kg is near-lethal and cannot establish a chronic behavioural model. A separate methods text in the same paper gives "5 mg/kg/day" — M2 inconsistency; M3 flags dose plausibility independently. Severity: major (no self-resolution: no author explanation, no figure support).

**Do not report**:
> "Anethole 10.8 µM for CCK-8 assay"

Paper states IC₅₀ = 10.8 µM; concentration selection has explicit justification.

### E3 · Severity scope separation (Phase 6)

Finding: Western blot band quantification performed without blinding.
- **Severity for the specific subclaim (fold-change values)**: major — subjective quantification without blinding can systematically overestimate fold differences.
- **Severity for the paper's overall conclusion (directional claim: treatment reduces protein X)**: minor — the direction of the effect is unlikely to be reversed by blinding, and independent assays support the same directional conclusion.

Report both assessments in the `scope` field.

### E4 · Self-resolution restriction (era context, Phase 6)

Finding: No epistasis experiment to confirm that a RNAi phenotype requires intact daf-16 function.
- The authors do not address this gap.
- This limitation was methodologically addressable at the time of publication.
- Era context is noted in the `recommended_action` field.
- Severity is NOT reduced because it was 2003. The epistemic gap — inability to distinguish downstream-of-DAF-16 from parallel-to-DAF-16 — is the same regardless of when the paper was written.

---

## TODO (next phase)

- [ ] Supplement for TCM/multi-compound formulation special handling rules
- [ ] Supplement for medical device/imaging study requirements
- [ ] Run `tools/baseline_probe.py` to identify zero-uplift slugs across the 20-paper corpus
- [ ] Peter: review §4.6 assay minimum reporting elements
- [ ] Re-run X1 layer on the 3 PLOS papers post-analysis to validate offline hit rate
- [ ] Add Phase 7 synthesis template to `SKILL.md` Stage 4 output contract
