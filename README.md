# AI Reviewer Skill for Biomedical Papers

**English** | [中文](README.zh-CN.md)

**Deliverable**: a self-contained Agent Skill package, available in two language versions:

- English version → [`skills/biomed-paper-review-en/`](skills/biomed-paper-review-en/)
- Chinese version → [`skills/biomed-paper-review/`](skills/biomed-paper-review/)

The two versions are functionally identical: scripts, schemas, and offline fixtures are equivalent; only the documentation language differs.

Given a biomedical paper (JATS XML / PDF / plain text), it does two things:

1. **Extracts a reusable structured fact table** — study design, subjects, intervention
   arms, measurements and endpoints, key numeric values, the claim list, and all
   declarations; every field carries applicability, requiredness, status, and evidence
   citations back to the original text.
2. **Reviews the paper**: reads the full text as a senior peer reviewer, then has six
   domain rulebases re-examine it independently, cross-validated by **deterministic
   computation** and **12 external authoritative databases**; when a visual channel is
   available, the figure module extracts values **from the original images** and locates
   them back to figure number / panel / page.

It outputs a structured result table, severity-graded findings traceable to their
location in the original text, extraction coverage and review confidence scores, and
prioritized suggestions for human review. Extraction and review can be used separately
(`structured_extraction` mode).

> This branch (`main`) contains only the deliverable itself. The development
> workspace — test corpora, evaluation tools, experiment records, design docs, and all
> real-run artifacts — lives on the [`dev`](../../tree/dev) branch.

---

## 1. What problem it solves, and why it is built this way

A bare model is already a **strong reviewer**. So the real question is not "how do we
make the model review papers," but "**once the Skill is attached, how do we guarantee
it beats not attaching it**."

We got this wrong once, and it is worth putting first.

### The failed version: compressing the paper into a candidate list

The first architecture was: a discovery layer reads the full text → compresses it into
a candidate issue list → each specialist only receives an evidence bundle sliced
according to that list. It sounds reasonable; in practice it was **worse than the bare
model**:

| Same real paper, same model, same full text | Findings | critical |
| --- | --- | --- |
| Bare model (full text + open-ended prompt) | 63 | 2 |
| **Old architecture** (discovery compresses → specialists get bundles) | 43 | **0** |
| **Current architecture** (every layer gets the full text) | **96** | **6** |

The failure mechanism is **double compression, with the second determined by the
first**: the discovery layer compresses the paper into a list, and the evidence bundles
then pull passages according to that list — so **paragraphs nobody flagged are never
read by any layer at all**. The two deepest issues the bare model caught (the knock-in
allele is simultaneously a full-length RAGE-null, so the claimed "independent genetic
validation" carries built-in confounding; a single 7 dpi time point cannot support
"accelerated regeneration"), the old architecture caught neither.

And the "isolation" was fake anyway: the sliced statistics bundle already covered 71%
of the full text, the claims bundle 52% — **we paid the recall cost without getting
real isolation.**

### The current architectural axiom

> **What the layers isolate is the "review objective and reasoning context," not the
> "paper text."**

```
L0   Global review    Full text + minimal prompt, no rulebase / no schema / no checklist
                      └ This IS the bare-model condition → the Skill's floor is pinned to the bare model
L0b  Mapping & routing  Full text; produces only a map and identifiers, finds no issues
L1   M2–M7            **Each gets the full text** + its own rulebase; must take a stance on every L0 item
L2   Deterministic tools + X1 external validation
L3   Continuation under the same task_id, letting specialists reconsider after seeing deterministic evidence
L4   Correction subsession  **Also gets the full text**; audits whether any L0 item silently disappeared
L5   Contract normalization and report rendering
```

**Additivity guarantee**: the final result ⊇ L0's conclusions, minus only those items
explicitly rejected with stated reasons. Verified in practice — L0 produced 70 items:
60 promoted to findings, 17 merged, 2 blocked by system limitations (reasons stated),
**0 rejected, 0 evaporated**.

### Uplift can only come from two places

Pure-text internal consistency checks are something the bare model already does — that
part of the uplift is structurally zero or negative. Real gains can only come from
things the model **structurally cannot do**:

**1. Deterministic computation.** Example: Table 5 of a clinical RCT is labeled
`*ITT`, but the mean 43.68±3.5 is **mathematically impossible** on an integer scale
with n=39 — it is only compatible with n=34/37/38, and n=34 happens to be the
completer count. GRIM-style arithmetic **falsified a methodological label**; pure
reading cannot do that.

**2. External authoritative data.** Example: a paper's Introduction cites
`10.1002/jcp.26311` in support of a claim, but that reference was **retracted on
2024-08-26**. The retraction postdates the paper under review by four years — it is
not in the manuscript, not in the metadata, and cannot be in the model's training
corpus — **only a database lookup can find it**.
(Cross-checked both ways via Crossref `updated-by` and Europe PMC `Retraction in`.)

`scripts/external_figure_validation.py` (X1) queries **12 databases, 14 checks** on
demand: Cellosaurus, ClinicalTrials.gov, Europe PMC, Crossref, UniProt, ChEMBL,
PubChem, RCSB PDB, HGNC, SciCrunch/RRID, NCBI E-utilities, PRIDE.
**No dataset is pre-bundled**: a query is issued only when an identifier actually
appears in the manuscript.

When an external source is unreachable, it always produces a `system_limitation` and
**never** turns into a finding — "not found in the database" does not mean "the paper
is wrong."

### Figure reading: read the original image when a visual channel exists, degrade honestly when it doesn't

M5's figure parsing (Stage 3 Figure Parser) extracts experimental conditions and key
values **from the images themselves**, and locates them back to the original figure:

- **Image source priority**: `original_figure_file > extracted_pdf_figure >
  rendered_pdf_page > text_only_caption`;
- **Numeric evidence hierarchy**: `explicit_main_text > explicit_table >
  explicit_figure_caption > axis_readable > pixel_estimated`, with
  `provenance.source_type` labeled truthfully;
- **Hard constraints on pixel estimation**: always `extraction_confidence: low`,
  **must be written as an interval** (point values forbidden), sets
  `manual_review_needed`; log axes require confirming the axis type before reading;
  error bars must not be assumed to be SD/SEM; asterisk significance thresholds must
  be checked against the caption definition;
- **Original-figure locating**: every `figure_record` gives figure number, panel, PDF
  page, and first-citation location.

**When images genuinely cannot be obtained, it does not pretend to have seen them**
(not provided with the manuscript, unreadable format, etc.): it registers
`system_limitation(figure_unreadable)`, falls back to caption / main-text / source-XML
cross-validation plus the deterministic pixel audit of `figure_integrity_audit.py`
(duplication / splicing / abnormally uniform regions), and states in the report that
pixel-level criteria were not covered in this run. This fallback path has its own
selftest.

### Structured extraction: not just a review precursor, a reusable product in itself

`structured_result` is a **machine-consumable fact table of the paper**, organized per
`structured_result.schema.json`; on a real paper it extracts about 16 KB:

| Field family | Content |
| --- | --- |
| `article_design` | Study design family/type (e.g. `experimental` / `in_vivo_animal`) with the basis for the determination |
| `population` | Subjects, inclusion/exclusion criteria, sample size accounting |
| `design` | Arms, interventions, controls, randomization and blinding |
| `measurement` | Assay methods, endpoints, time points |
| `key_data` | Key numeric values with grouping keys (experiment / arm / comparison / time point / endpoint) and normalized observations |
| `conclusion.claims[]` | Itemized claims (`CLM-01`…), for M7's evidence-hierarchy comparison |
| `declarations` | Ethics, registration, informed consent, conflicts of interest, data availability |

**Every field carries a four-tuple**: `applicability` (does it apply),
`requiredness` (is it required), `status` (reported / not_reported / parse_failed),
and `evidence_refs` (source locations). So "not written in the paper" and "we failed
to extract it" are two different things at the data-structure level and are never
conflated.

Measured field parse rate: **22/23 = 95.7%**. The overall `extraction_coverage` score
is lower than this, because it also counts image readability and supplementary
material availability — both constrained by the runtime environment, **not extraction
failures**, and each is listed separately, never blended into the field parse rate.

---

## 2. Minimal reproduction steps

> Commands below use the English version `skills/biomed-paper-review-en/`;
> substitute `skills/biomed-paper-review/` for the Chinese version — behavior is
> identical.

### 1. Offline selftest (no network, no model, no installation)

```bash
cd skills/biomed-paper-review-en
for f in scripts/*.py; do python3 "$f" --selftest; done
```

Expected: all seven scripts pass. **This step needs no third-party dependencies.**

### 2. Offline replay of X1 external validation

```bash
python3 scripts/external_figure_validation.py --offline --selftest
```

Strictly replays recorded real responses; any cache miss is an error, and it **never
falls back to the network**. Boundary: all-green offline only proves the parsing and
decision logic is intact — **it does not prove the upstream APIs are still available**.

### 3. Validate a single identifier online (optional, needs allowlisted network)

```bash
# Cell line misidentification (Cellosaurus)
printf '%s' '[{"check":"cell_line","cell_line":"MDA-MB-435","evidence_refs":["EV-001"]}]' \
  | python3 scripts/external_figure_validation.py --input -

# Is a cited reference retracted? (Crossref / Europe PMC)
printf '%s' '[{"check":"cited_retracted","doi":"10.1002/jcp.26311","evidence_refs":["EV-001"]}]' \
  | python3 scripts/external_figure_validation.py --input -
```

### 4. Run structured extraction only (no findings, minutes-scale)

```bash
opencode run --dir . --model <your model> \
  "Use the biomed-paper-review-en skill in structured_extraction mode:
   extract the structured result only — no review judgments, no findings,
   no risk score."
```

Produces `structured_result` (with the field parse rate) and `output_confidence`.
**This mode does not output `manuscript_risk_score`** — issuing a risk score without
running the review modules would be baseless.

### 5. Run a full review (needs opencode + model credentials)

```bash
mkdir -p run && cd run
curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11856280/fullTextXML" -o paper.xml
mkdir -p .claude/skills && cp -R ../skills/biomed-paper-review-en .claude/skills/
opencode run --dir . --model <your model> \
  "Use the biomed-paper-review-en skill to run a full review (full_review)
   of the paper in the current directory."
```

Produces `review_report.json` (machine-validatable) and `review_report.md`
(human-readable).

**Runtime profile (measured on qwen3.8-max)**: a full review of a real paper takes
about 80–110 minutes, of which the six specialist subsessions run **in parallel** in
about 7 minutes (serial would take ~60 minutes) — the critical path is
`max(per-wave)` rather than the sum, and parallelization cut total time from 2h20m to
1h48m. Targeted-check and figure-analysis modes return in minutes.

---

## 3. Package layout

```
skills/biomed-paper-review-en/     English version (skills/biomed-paper-review/ is the equivalent Chinese version)
├── SKILL.md                    Single entry point: orchestration, module routing, shared contracts (~500 lines)
├── references/                 11 rulebases (00 contracts / routing / runtime; 01 extraction; 02–07 six review modules)
├── scripts/                    7 deterministic tools, all with --selftest
│   ├── statistical_forensics.py      5 statistical forensics checks (table_total / GRIM / p recomputation / CI / counts)
│   ├── external_figure_validation.py X1 external validation: 12 databases / 14 checks
│   ├── ethics_compliance_check.py    Ethics rulebase screening (three jurisdictions)
│   ├── animal_model_compliance.py    Animal welfare red lines and 3R audit
│   ├── sequence_identifier_audit.py  Sequences / HGVS / accession numbers / primers
│   ├── figure_integrity_audit.py     Image duplication / splicing / abnormally uniform regions
│   └── normalize_biomed_units.py     Unit normalization, fail-closed
├── schemas/                    12 JSON Schemas (inter-module integration contracts)
├── resources/                  Ethics rulebase + X1 offline replay fixtures
└── templates/review_report.md  Report rendering template
```

**Self-contained**: the package references no paths outside itself; all internal
references resolve.

**Dependencies: no `requirements.txt`, and that is deliberate.**
Six scripts are pure standard library; `figure_integrity_audit.py` optionally uses
`numpy` + `Pillow` (needed only for the pixel-level audit) and, when they are missing,
registers `system_limitation(figure_unreadable)` and **exits normally (exit 0)** with
the rest of the review unaffected — this fallback path has its own selftest.
Shipping a `requirements.txt` would amount to requesting a pip install in the sandbox:
under an allowlisted network, an install failure would escalate "one optional check
degraded" into "the whole run is at risk."

---

## 4. Boundary statement (must be written verbatim into every report)

- This tool **does not replace peer review** and produces no accept/reject decisions;
- Every finding must be traceable to a location in the original paper text; arguments
  **must not** be built on generated content;
- "Not reported" does not mean "not performed"; "we did not obtain it" does not mean
  "the manuscript did not state it";
- Tool failures, unreachable external sources, and unreadable images are always
  registered as `system_limitation` and **never blamed on the manuscript**;
- The three scores (manuscript risk score / extraction coverage / review confidence)
  **do not substitute for one another** and must not be merged into a single number;
  partial scores must not be compared side by side with full-review scores.
