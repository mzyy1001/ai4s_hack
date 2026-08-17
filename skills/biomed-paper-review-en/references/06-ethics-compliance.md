# M6 · Ethics & Compliance

**Original owner: Peter** · Status: **Phase-1 rulebase completed legal-source and false-positive review (2026-08-07)**

Core questions: **should this study have been done**, **was authorization obtained before it was done**, and **does the manuscript state that authorization clearly**?

**Key difference between this module and the other review modules**: ethics requirements are **written norms**, not field conventions.
This module's determinations therefore rely not on experience but on a citable library of norms
— `resources/ethics_rules.json` (28 instruments, 22 structured requirements, three jurisdictions).
**Every finding must cite a specific provision of a specific instrument.**

**This file depends on `00-contracts.md`.** The finding structure, `evidence_refs[]`, and the severity enum
are all defined there.

---

## 1. Inputs

| Source | Purpose |
| --- | --- |
| `structured_result_v2.article_design` | Determine which norms apply (human / animal / cell / computational) |
| `structured_result_v2.population.subjects` | Species, population, cell source, whether a vulnerable group |
| `structured_result_v2.declarations.*` | Ethics statement, informed consent, funding, conflict of interest, data availability |
| `structured_result_v2.design.registration` | Clinical trial registration number |
| `evaluation_matrix.{has_animal_experiment, has_human_subjects, ethics_statement, informed_consent}` | Routing |
| **`ethics_requirement_unmet` signals** | Produced by `scripts/ethics_compliance_check.py` (relative to the Skill root), see §2 |
| `all_system_limitations[]` | When supplementary material is inaccessible, absence **must not** be adjudicated |

## 2. Rulebase and screening tool

```
resources/ethics_rules.json          Rulebase (data)
scripts/ethics_compliance_check.py   Screener (produces signals, not findings)
        ↓  ethics_requirement_unmet
M6 (this module)                     Decides whether it constitutes a finding, sets severity
```

This is the same pattern as `statistical_forensics.py → M4`:
**the tool layer emits the machine-level observation "the norm requires X; X was not seen in the manuscript"; M6 decides whether that constitutes a manuscript problem.**

**Why it can run offline**: the rulebase is a **structured requirements index**, not an external database query —
it falls squarely within the Phase-1 scope (`SKILL.md §0.2`: the paper's own content + a general-purpose rulebase).
Verifying the authenticity of approval numbers requires data sources that are still not connected; **the connector for registration-number timing validation has been delivered** (ClinicalTrials.gov, see §8).

### 2.1 Rulebase coverage

| Jurisdiction | Main instruments |
| --- | --- |
| International | Declaration of Helsinki, CIOMS 2016, ICH-GCP E6, ARRIVE 2.0, ISSCR 2021 (2025 SCBEM targeted update), Nagoya Protocol, ICMJE |
| United States | Common Rule (45 CFR 46), FDA (21 CFR 50/56), HIPAA, PHS-OLAW, Animal Welfare Act (9 CFR), NRC Guide, AVMA Guidelines for the Euthanasia of Animals, Belmont Report |
| China | Measures for Ethical Review of Life Science and Medical Research Involving Humans (2023), Measures for Science and Technology Ethics Review (Trial), Regulations on the Administration of Human Genetic Resources (2024 revision) and its Implementing Rules, GCP (2020), Regulations on the Administration of Laboratory Animals and the Measures for the Administration of Laboratory Animal Licenses, GB/T 35892-2018, Biosecurity Law, Regulations on the Biosafety Management of Pathogenic Microorganism Laboratories (2024 revision), Personal Information Protection Law, Ethical Guiding Principles for Human Embryonic Stem Cell Research |

Domains: `human_clinical` / `animal` / `human_derived_cells_tissue` / `cell_line_general` /
`stem_cell_embryo` / `genetic_resources` / `biosafety` / `data_privacy` /
`clinical_trial_registration`.

### 2.2 Discipline for using the rulebase

1. **Citations must be precise to the provision.** A finding's `rule_ref` is written as `ethics_rules#<rule_id>`,
   and `detail` lists that rule's `citations` (instrument name + provision).
2. **Mind `citation_confidence`.** The rulebase tags a confidence level on every citation;
   locations at `medium` or below must be manually checked against the original text before being written into a formal review opinion.
   Currently only the line items of GB/T 35892-2018, some locations in the 2003 Chinese human embryonic stem cell principles, and
   the Chinese-law basis of `ETH-BIO-002` have not been raised to `high`; they must not be rendered as settled legal conclusions.
3. **The rulebase is not legal advice.** Its output is a screening signal, not a compliance ruling.

---

## 3. Determination workflow

```
1. Applicability routing  ← article_design + population.subjects decide which rules apply
2. Status gating          ← field parse_failed / unresolved → do not adjudicate absence; emit a manual-review item
3. Reverse exemptions     ← commercial cell lines and similar cases proactively suppress false positives
4. Raise finding          ← independently provide manuscript evidence, citing the instrument's provision
```

### 3.1 Applicability routing

| Trigger condition | Applicable rule domains |
| --- | --- |
| `family ∈ {human_interventional, human_observational}` | `human_clinical` + `data_privacy` |
| `type = randomized_controlled_trial` and other interventional types | Add `clinical_trial_registration` |
| `design_components[]` contains `in_vivo_animal` | `animal` (**adjudicated per experiment**, not per article) |
| `population.subjects` contains primary human-derived material | `human_derived_cells_tissue` |
| `population.subjects` contains only established cell lines with clear provenance and permitted use | **Reverse-exemption candidate**, see §3.3 |
| Contains hESC / human embryos | `stem_cell_embryo` |
| Chinese-population samples + overseas collaboration / sample export | `genetic_resources` |
| Live pathogenic microorganisms | `biosafety` |

**Per-experiment adjudication**: when a paper contains `in_vitro` (EXP-01) + `in_vivo_animal` (EXP-02),
animal ethics applies only to EXP-02; EXP-01's `ethics_statement` should be `not_applicable`
(`01-structured-extraction.md §5.3.6`). `evaluation_matrix.ethics_statement`
is split into two entries — **do not take the logical OR**.

### 3.2 Status gating (the most important false-positive guard)

| Field status | M6 action |
| --- | --- |
| `reported` | Check whether the content satisfies the rule's requirement |
| `not_reported` (search fully completed) | A finding **may** be raised |
| `not_applicable` | Compliant; do not raise a finding |
| `parse_failed` / `unresolved` / `ambiguous` | **Never raise a finding** — emit a manual-review item stating "we could not see this clearly" |

**Iron rule when supplementary material is inaccessible**: many papers put the ethics approval number in Supplementary Methods.
Under `system_limitation: supplement_inaccessible`, every ethics field that depends on it is uniformly `parse_failed`,
and **must not** be adjudicated as `not_reported` — if we have not seen it, we cannot say the manuscript did not write it
(`00-contracts.md §6.4`). This is where this module is most likely to wrong an author.

### 3.3 Reverse-exemption rules

| Situation | Suppressed rules | Rationale |
| --- | --- | --- |
| Only established, non-identifiable cell lines with clear provenance/permitted use (HeLa/HEK293/HepG2/Huh7 etc.; the rulebase lists 29 names) | `ETH-CELL-001`, `ETH-HUM-001`, `ETH-HUM-002` | Established non-identifiable specimens generally do not constitute a human subject under the Common Rule; studies in China must additionally satisfy the provenance, authorization-scope, and exclusion conditions of Article 32 of the 2023 Measures |
| Purely computational / secondary literature research | All `human_clinical` and `animal` rules | No subjects |
| Case report | Registration and sample-size type requirements | See `01-…md §5.3.5` |
| Secondary analysis of public de-identified datasets | `ETH-HUM-002` (informed consent) | Instead, check whether the data source and usage license are stated |

Cell-line names are used only for offline recall; they are not a compliance whitelist. When any name is hit, still scan whether the same study also involves
primary tissue, HUVEC, patient-derived organoids, blood, or newly collected donor samples; the presence of any one of these forbids a whole-paper exemption.
Short names such as `CHO` are matched as standalone entities and must not hit ordinary words like `chondrocyte`. Unknown cell lines are not automatically added to the list,
nor is lawful provenance presumed merely because a line is "common"; first check catalog/RRID/CVCL and material-transfer restrictions.

---

## 4. Rule list (excerpted from the rulebase; full definitions in `resources/ethics_rules.json`)

### 4.1 Human research

| rule_id | Requirement | severity |
| --- | --- | --- |
| `ETH-HUM-001` | Ethics committee approval + approval number | major when not reported; critical when explicitly not approved and the rule applies |
| `ETH-HUM-002` | Informed consent | major when not reported; critical when consent/waiver explicitly not obtained and the rule applies |
| `ETH-HUM-003` | Waiver of informed consent must state its basis | major |
| `ETH-HUM-004` | Statement of adherence to the Declaration of Helsinki | info; missing only the declaration's name does not raise a finding |
| `ETH-HUM-005` | Prospective registration of interventional trials | major |
| `ETH-HUM-006` | Additional protections for vulnerable groups | major |
| `ETH-HUM-007` | Minors: guardian permission + the minor's own assent | major |
| `ETH-HUM-008` | De-identification of identifiable health data or a lawful basis | minor |

### 4.2 Animal experiments

| rule_id | Requirement | severity |
| --- | --- | --- |
| `ETH-ANI-001` | IACUC / animal ethics committee approval + protocol number | major when not reported; critical when explicitly not approved |
| `ETH-ANI-002` | 3R principles (Replacement/Reduction/Refinement) | reporting gap only is minor; non-implementation must not be inferred from absence of the literal "3R" |
| `ETH-ANI-003` | Species, strain, sex, age or body weight, source | major |
| `ETH-ANI-004` | Anesthesia, analgesia, and humane endpoints | major |
| `ETH-ANI-005` | Euthanasia method | major |
| `ETH-ANI-006` | Chinese laboratory animal license (SYXK/SCXK) | minor |

### 4.3 Cells, stem cells, and embryos

| rule_id | Requirement | severity |
| --- | --- | --- |
| `ETH-CELL-001` | Donor consent + ethics approval for human primary cells/tissue | major when not reported; critical when authorization explicitly not obtained |
| `ETH-CELL-002` | **Reverse rule**: commercial cell line exemption | info |
| `ETH-CELL-003` | hESC research category, provenance, and oversight pathway — **always route to manual review** | major by default; critical only when review was explicitly required but not conducted and legality is affected |
| `ETH-CELL-004` | In vitro culture limit for human embryos (14-day rule) — **always route to manual review** | critical |

### 4.4 Genetic resources and biosafety

| rule_id | Requirement | severity |
| --- | --- | --- |
| `ETH-HGR-001` | Chinese human genetic resources approval/filing | major |
| `ETH-HGR-002` | Nagoya Protocol PIC/MAT — **always route to manual review** | minor |
| `ETH-BIO-001` | Biosafety level for pathogenic microorganism experiments | major |
| `ETH-BIO-002` | Dual Use Research of Concern (DURC) — **always route to manual review** | critical |

> **What the four `manual_only` rules** (`ETH-CELL-003`, `ETH-CELL-004`,
> `ETH-HGR-002`, `ETH-BIO-002`) have in common is not "severe problems", but that automation lacks the jurisdictional
> or experiment-category facts needed to decide applicability. They produce only `partial_extraction` manual-review items,
> **must not produce `ethics_requirement_unmet`, and do not set severity automatically**.
> `ETH-CELL-003` is newly placed on the manual path: routine in vitro culture of established hESC lines can fall under ISSCR Category 1A,
> so the mere appearance of `hESC` cannot justify demanding dedicated continuing oversight or a critical rating.

---

## 5. Evidence requirements for findings

The evidence shape of ethics findings differs from other modules; pay special attention:

| Situation | Evidence requirement |
| --- | --- |
| No ethics statement seen in the manuscript | An `absence` evidence entry is **mandatory**; `searched_locations` must cover at least the `declarations` / `ethics` / `methods` sections, and `search_terms` must be bilingual (`ethics`, `IRB`, `IACUC`, `approval`, `伦理`, `批件`, `审查`) |
| Statement exists but lacks the approval number | `present` evidence pointing to the statement's original text; `detail` states which element is missing |
| Statement contradicts the design (e.g. claims no animal experiments but the Methods section has mice) | Two `present` evidence entries, pointing to the statement and the Methods section respectively |
| Supplementary material inaccessible | **Do not raise a finding**; state in the manual-review recommendation which material needs to be requested |

**`severity >= major` must have an actionable `manual_review.action`**,
stating "what to request from the authors" or "what to ask the ethics committee to verify".
For critical ethics issues, `manual_review.who` is usually `ethics_committee` or `editor`.

---

## 6. Positive / negative examples

### 6.1 `ETH-ANI-001` animal ethics approval

**Should alert**: the Methods section says "C57BL/6 mice were injected intraperitoneally…", and a full-text search of the declarations / ethics /
methods sections finds no IACUC, ethics committee, or approval number → **major reporting gap**,
`action: request from the authors the animal-experiment ethics approval number and the name of the approving institution`.
Escalate to `critical` only when the manuscript explicitly states approval was not obtained, or external validation confirms no approval exists and the rule applies.

**Should not alert**: same experiment, Supplementary Methods S1 is inaccessible and the main text says
"All animal procedures are described in Supplementary Methods S1"
→ `ethics_statement.status = parse_failed` + `SYS-xxx (supplement_inaccessible)`
→ **do not raise a finding**; only write in the manual-review recommendation "re-review after obtaining S1".

### 6.2 `ETH-CELL-001` consent for human-derived material

**Should alert**: the Methods section says "primary hepatocytes were obtained from patients undergoing hepatectomy",
with no donor informed consent or ethics approval seen → **major reporting gap**; "not obtained" must not be inferred from "not reported".

**Should not alert**: the Methods section says "HepG2 and Huh7 cells were purchased from ATCC"
→ hits the commercial cell line reverse exemption → **do not report**.
This is this module's most common source of false positives; the rulebase lists 29 common names for offline recall. HUVEC has been removed from the exemption list
because it is usually primary human umbilical vein endothelial cells.

### 6.3 `ETH-HUM-002` informed consent

**Should alert**: a prospective clinical trial with no informed-consent wording found anywhere → **major reporting gap**.

**Should not alert**: a retrospective medical-records analysis where the authors write "this study was approved by the ethics committee with a waiver of informed consent
(retrospective de-identified data)" → this is the compliant waiver path of `ETH-HUM-003` → **do not report**
(but check whether the basis for the waiver is stated).

### 6.4 `ETH-HUM-005` trial registration

**Should alert**: a randomized controlled trial with no registration number anywhere in the text → **major**.

**Should not alert**: an unregistered observational cohort study → `ETH-HUM-005`'s
`applies_when.design_family = human_interventional` does not hold → **not applicable, do not report**.

---

## 6.1 Consuming X1 external-validation signals (**severity pending Peter's review**)

`scripts/external_figure_validation.py` (Stage 3c) routes two `check_type` values to M6:

| X1 `check_type` | Database | Comparison result | Suggested M6 category |
| --- | --- | --- | --- |
| `prospective_registration` | ClinicalTrials.gov | `mismatch` | `retrospective_trial_registration` |
| `trial_registration_exists` | ClinicalTrials.gov | `needs_manual_review` | `trial_registration_unverifiable` |

**`prospective_registration` is the single check in the whole suite that best demonstrates the value of external validation.**
ICMJE requires registration before enrollment of the first participant, and both the registration date and the study start date **exist only in the registry** —
the paper's text almost never states them, so retrospective registration is impossible to detect from the text alone. Default `major`;
take `critical` when the paper simultaneously claims "this trial was prospectively registered per ICMJE requirements" (statement contradicts fact).

**Date-precision trap**: the registry's `startDate` often has only YYYY-MM precision, while the registration date is
YYYY-MM-DD. X1 compares at the coarser precision and requires strict inequality — start=2011-02, reg=2011-02-24
does not alert, because the study may well have started after the 24th. **Better to miss than to accuse on a guess.**

`trial_registration_exists` is always a candidate: it may be a typesetting error, registration on another platform
(ChiCTR / ISRCTN, not connected in this phase), or a registration record not yet public. It must be manually confirmed before being characterized.

---

## 7. TODO (Phase 1)

- [x] Build a citable three-jurisdiction rulebase (`resources/ethics_rules.json`)
- [x] Implement the offline screener and three false-positive guards
- [x] Populate the applicability routing table and status-gating rules
- [x] Provide positive/negative examples for each rule
- [x] Re-verify rulebase provisions, severity, and Chinese regulations: corrected the misquoted Article 32 of the 2023 Measures, the legal source for animal licenses, and the ARRIVE item; updated 2024/2025 version metadata
- [ ] Add detection rules for "ethics statement contradicts study design" (e.g. declaring no human research while patient data is present)
- [x] Stop blindly expanding the name list to 100+; remove HUVEC, and redirect expansion toward accession + provenance/permitted-use verification (see the Round 10 proposal)
- [ ] Draw a clear boundary with M3: animal **necessity** (whether the animal experiment should be done) belongs to M3;
      animal **authorization** (whether an approval exists) belongs to M6
- [ ] Empirically measure the false-positive rate on the `animal_invivo` and `rct_clinical` corpora in `datasets/`

---

## 8. Online enhancement (registration-number validation connector **delivered**; approval-number validation still not connected)

The current offline layer only checks "did the manuscript write it". Online enhancement checks "do external records support what the manuscript says".

| Capability | Data source | What it detects |
| --- | --- | --- |
| Clinical trial registration number validation | ClinicalTrials.gov API v2 / ChiCTR / WHO ICTRP | Number does not exist; endpoints inconsistent with the registration; **registration later than first enrollment** (retrospective registration) |
| Ethics approval number validation | Most institutions have no publicly queryable interface yet | When public records are unavailable, tell the user explicitly; authenticity must not be adjudicated |
| Institutional AAALAC accreditation status | AAALAC directory of accredited institutions | Whether the animal facility is accredited |
| Chinese human genetic resources approval | MOST administrative-licensing public disclosures | Whether approval/filing was performed |
| Retractions and ethics concerns | Retraction Watch / PubPeer | Whether this study or its predecessors have been flagged for ethics issues |

**False-positive risk of online enhancement**: registry records and the paper often differ in endpoint wording for legitimate reasons;
semantic inconsistencies go **to manual review only** and must not be automatically adjudicated as selective reporting.
"First submission later than enrollment start" is flagged as a `candidate`, not a conclusion — the meaning of registry timestamps
is not consistent across platforms.

**Contract**: reuse the `external` evidence of `00-contracts.md §1` and the
`external_validation_candidate` of §6.2. An M6 finding's `evidence_refs[0]` must be in-manuscript
`present`, citing the external evidence alongside; X1 failures and zero hits must not be converted into findings.
