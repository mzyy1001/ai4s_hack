# M5 · Figure Parsing and Chart Usage Standards

**Owner: MY (Minyi)** · Status: **Phase-1 rulebase populated (v1)**

This file serves two mutually exclusive execution roles:
**(A) Stage 3 Figure Parser** — extracts experimental conditions and key values from each figure and locates the original image,
producing only `figure_records[]`, stage-local signals, and system limitations;
**(B) Stage 4 M5 Reviewer** — consumes the sealed `figure_records[]` and judges whether chart type, presentation, and placement meet the standards,
producing only `m5_findings[]`. The Parser must not produce findings; the Reviewer must not rewrite `figure_records[]`.

**Role definition**: an experienced biomedical peer reviewer + scientific-visualization quality-control expert, with long experience creating and reviewing
statistical plots, experimental workflow diagrams, micrographs, and multi-panel result figures. First determine the **scientific question** each figure is trying to answer,
then judge whether the current chart type is sufficient to support that question, and finally check statistical and presentation standards.

**Evidence boundary (consistent with SKILL.md §0)**: extract only information supported by the image, figure caption, main text, tables, or readable axes.
Do not fill in invisible values from domain knowledge, do not infer raw data, do not write visual trends as established mechanisms, and do not write correlation as causation.
Do not extend into medical efficacy or clinical recommendations.

---

## A. Figure Parsing

### A.1 Parsing workflow

1. **Locate the scientific question** — keep the original label (`Figure 2A` / `Fig. 3B` / `Extended Data Fig. 1c`),
   scan the figure caption plus the related passages of the main text, and clarify what question the figure is meant to answer and what the key variables and data nature are.
   > Example: the caption of `Figure 3A` reads "effect of different concentrations of osimertinib on proliferation of EGFR-mutant lung cancer cells",
   > so the research aim is a dose-effect relationship, with concentration as the independent variable and cell viability as the dependent variable.
2. **Record the chart type** — classify by the `chart_type` enum in §A.2; do not judge appropriateness at this stage.
3. **Extract conditions and visible results** — record axes, legends, sample sizes, error type, and provenance.
4. **Register parsing limitations** — when something is unreadable, unmappable, or requires visual estimation, produce a stage-local signal / limitation.
5. **Output** `figure_records[]`; outputting `finding[]` is forbidden.

Multi-panel figures are **output per panel first**, then given a whole-figure interpretation.

### A.1a Visual-input priority rule

If the current execution model supports visual input, the Stage 3 Figure Parser should preferentially read the original image evidence, rather than relying only on PDF text or OCR.

Image source priority:

```text
original_figure_file > extracted_pdf_figure > rendered_pdf_page > text_only_caption
```

**If no readable image can actually be obtained this round** (the image was not provided with the manuscript, the format is unreadable,
or the current runtime provides no image channel), do not pretend to have seen the figure: register a
`system_limitation` (`figure_unreadable`) per `00-contracts.md`, fall back to cross-checking the figure caption / main text / source XML
plus the deterministic pixel audit of `figure_integrity_audit.py`, and state in the report that
pixel-level criteria were not covered this run. **Try the original-image-first path before falling back** —
do not assume up front that the figures cannot be read.

### A.2 Chart-type knowledge base

Judge by research scenario whether the chart matches the research aim, and apply that scenario's mandatory checks.
`chart_type` takes enum values from `figure_record.schema.json`.

| Research scenario | Common charts | Mandatory checks | chart_type |
| --- | --- | --- | --- |
| Omics and high-dimensional results | Heatmap, volcano plot, PCA, UMAP/t-SNE, pathway enrichment plot, network graph | Thresholds, color bar, dimension interpretation, group labels, gene set/pathway names, **multiple-testing correction** (→ M4) | `heatmap` |
| Between-group comparisons | Scatter plot, box plot, violin plot, bar chart with overlaid individual points | Whether individual points are retained, sample size, error-bar definition, statistical test; **flag information loss when a continuous distribution is shown only as bars** | `statistical_plot` |
| Time-course experiments | Line chart, area chart, repeated-measures plot | Time-axis units, sampling interval, error range, **n at each time point**, treatment start point | `statistical_plot` |
| Composition or proportion | Stacked bar chart, percentage bar chart, composition heatmap; pie charts only suit simple proportions | Total base, percentage definition, color mapping | `statistical_plot` |
| Microscopy or spatial evidence | Brightfield, fluorescence, IHC/IF, FISH, spatial transcriptomics sections | **Scale bar**, magnification, channel names, stained markers, merged images, ROI, color lookup table, quantification method | `micrograph` |
| Pharmacodynamics / toxicity / dose response | Dose-response curve, IC50/EC50 curve, cell-viability curve, inhibition-rate curve | Dose units, **log axis**, fitted curve, response range, normalization baseline, whether IC50/EC50 is readable | `dose_response` |
| Survival or clinical endpoints | Kaplan-Meier, forest plot, cumulative-event curve | **Risk table**, censoring marks, HR/CI, p value, group definitions, follow-up time | `survival` |
| Correlation or association analyses | Scatter plot, regression plot, correlation matrix | Correlation coefficient type, fitting method, confidence interval, outliers, axis variable definitions | `statistical_plot` |
| Experimental workflow or study design | Workflow, experimental timeline, sample-screening flow, CONSORT-like flow | Steps, groups, time points, interventions, assay endpoints, **whether inclusion/exclusion counts are conserved** | `workflow` |
| Molecular experiment results | Western blot, qPCR, ELISA, flow cytometry, gel images | **Loading control**, normalization approach, gating strategy, number of replicates, statistical annotations | `blot` / `flow_cytometry` |
| Spatial transcriptomics / spatial omics | Spatial feature plot, spot map, cell type fraction map, niche map | Spot scale, color bar, normalization approach, spatial coordinates, tissue-section correspondence, cluster/niche definitions, sample origin | `heatmap` / `micrograph` / `statistical_plot` |
| Cell communication / ligand-receptor | Chord diagram, bubble plot, network graph, sender-receiver heatmap | Ligand/receptor names, directionality, score definition, thresholds, correction method, database source | `heatmap` / `schematic` / `statistical_plot` |
| Enrichment analysis | Bubble plot, bar plot, dot plot, ridge plot | Gene set names, NES/OR/p value/FDR, ranking basis, background gene set, multiple-testing correction | `statistical_plot` / `heatmap` |
| Flow cytometry | Gating plot, UMAP, histogram, MFI bar plot | Gating strategy, positivity threshold, compensation, representative plots, n, MFI/percent definition | `flow_cytometry` |
| IHC/IF/mIF quantification | Representative image + quantification | Scale bar, channels/markers, ROI, thresholds, samples per group, number of fields, quantification method | `micrograph` / `statistical_plot` |
| Animal tumor curves | Tumor volume curve, endpoint tumor weight, growth inhibition | n, randomization, time axis, error bars, endpoint definition, repeated measures, individual curves | `statistical_plot` |

### A.3 Evidence grading for value extraction

Take values strictly in this priority order, and record it truthfully in `provenance.source_type`
(enum in `00-contracts.md` §1.4, globally unique):

```
explicit_main_text > explicit_table > explicit_figure_caption > axis_readable > pixel_estimated
```

**Hard rules**:
- Values sourced from `pixel_estimated` always get `extraction_confidence: low` and must be written as an interval
  (e.g., `"40–50"`); **giving a point value is forbidden**. Also set `manual_review_needed = true` and
  explain the reason in `manual_review.action`.
- When an axis is a log axis, linear estimation is necessarily wrong — confirm the axis type before reading values.
- Error bar lengths must not be reported directly as SD/SEM unless the figure caption states so.
- In-figure significance asterisks must be checked back against the asterisk definitions in the figure caption (the `*p<0.05` threshold differs by journal).
- Write `not specified` or `unreadable` for unconfirmable information; **do not leave fields blank**.
- When only a lone image is provided with no caption or text, the output must declare the limited information source.

### A.4 Original-figure localization

Every `figure_record` must provide (locator syntax in `00-contracts.md` §1.2):

```json
"location": {
  "figure_label": "Figure 3",
  "panel": "B",
  "placement": "main_text",
  "locator": {"figure": "3", "panel": "B", "pdf_file_page": 7, "scope": "panel"},
  "first_cited_at": {"section": "results", "subsection": "3.2", "scope": "paragraph"},
  "image_file": "figures/g003.jpg"
}
```

For PDF input, `locator.pdf_file_page` is required; a locator missing the page number is invalid.
The `locator` is always stored as a **structured object**; `fig:3B | p.7` is only a report-rendering form —
cross-module deduplication relies on aligning the object fields; do **not** describe locations in free text.

### A.5 Output

`figure_record`; schema in `../schemas/figure_record.schema.json`. Beyond localization and values it also includes:
`interpretation` — a brief per-panel description of **the experiment shown, what is compared, the visible results, and the evidence boundary**,
kept reviewer-style, restrained, and traceable, without exaggerating biological significance.

> **Note**: this module **does not output a full report**. The four sections — structured result table, figure interpretations, issue list, manual-review recommendations —
> are rendered uniformly by Stage 5 per `templates/review_report.md`. The Stage 3 Figure Parser produces only
> `figure_records[]` and stage-local signals / limitations; the Stage 4 M5 Reviewer produces only `m5_findings[]`.

---

## B. Chart Usage Standards Review

This section is executed only by the Stage 4 M5 Reviewer. The Reviewer must check back against the manuscript evidence a `figure_record` points to
before raising a finding; the Parser's signals or `manual_review_needed` cannot be automatically converted into severity.

### B.1 Terminology and figure-text consistency

The same group, drug, dose unit, endpoint, abbreviation, marker, cell line, or animal model
should not change without explanation across the **figure, figure caption, and main text**. On its first occurrence, an abbreviation's full form should be findable in the caption or text.

Explicitly distinguish four kinds of information — do not conflate them: **experimental conditions / observed results / statistical support / authors' interpretation**.

### B.2 Placement fit between main text and supplement

Main-text figures should carry the paper's **mainline evidence**: key conclusions, core mechanisms, key models, or the main experimental design.
Supplementary figures should carry **validation, extension, replication, parameter supplements, methodological detail**, or other non-mainline supporting information.

| Situation | Recommendation | slug |
| --- | --- | --- |
| A main-text figure provides only marginal information, duplicates other main-text figures, or is mostly methodological detail | Recommend moving to the supplement | `figure_should_be_supplementary` |
| A supplementary figure provides key evidence, key controls, key statistics, or key mechanisms supporting a core conclusion | Recommend promoting to the main text | `figure_should_be_main_text` |

> This dimension is a check MY added beyond the original framework; it occurs frequently in real peer review and is enabled in Phase 1.

### B.3 Design-standard checks

- **Axes and units**: are x/y axis labels, units, log transformation, normalization baseline, percentage definition, color bar, and thresholds clear?
  Is the y axis truncated (a truncated axis exaggerates differences)?
- **Statistical information**: are p values, significance asterisks, error-bar meaning, sample size, replicate type, statistical test, and multiple-correction method identifiable?
  (Whether the method itself is **correct** belongs to M4; here only check **identifiability**.)
- **Chart-type fit**: are continuous distributions, paired data, time series, or proportion data obscured by an unsuitable chart form?
- **Experimental workflow diagrams**: consistent with the workflow described in the text?
- **Legends and colors**: are color mapping, group ordering, legend names, panel labels, and text references consistent?
  Do similar colors cause misreading? Is it friendly to color-vision deficiency?
- **Microscopy completeness**: are the scale bar, channels, stained targets, ROI, magnification, and quantified regions clear?
- **Information redundancy**: duplicated panels, duplicated charts, decorative elements, excessive unnecessary colors, multiple no-gain presentations of the same result.
- **Caption self-sufficiency**: can the figure be understood without the main text?

### B.4 Field-convention benchmarking

When giving review recommendations, list the chart types commonly used in the last 3 years by high-impact papers in the same field for the same kind of scientific question
(e.g., dose-response questions commonly use dose-response curves; spatial-localization questions commonly use micrographs with scale bars and channel annotations).

**The literature-database connector needed for field-convention benchmarking is still unimplemented, so this section runs in fallback mode** (X1's other connectors are delivered; see §C.1): when no actual retrieval was performed, you must explicitly write
`literature benchmark not performed` or `no recent benchmark found`;
passing off general knowledge as "highly cited paper conventions" is strictly forbidden.** Optional Phase-1 online enhancement in §F.4.

Benchmarking format:

```
panel_id | scientific_question | current_chart_type | recent_field_convention | benchmark_basis | recommendation
```

`benchmark_basis` holds the retrieval basis or representative literature leads (year, journal, paper type, DOI/PMID/URL);
when no actual retrieval was performed, fill in `literature benchmark not performed`.

---

## C. Category slugs and severity

**Severity must use the global enum `critical / major / minor / info`** (see `00-contracts.md` §2.1).
The `high / medium / low` in MY's first draft are mapped per the table below before use:

| Draft | Global enum | Criterion |
| --- | --- | --- |
| `high` | `critical` or `major` | Could change understanding of conclusions, cause wrong extraction, or create figure-text contradictions → `critical` if the conclusion's validity is affected, `major` if the authors need to supplement |
| `medium` | `major` or `minor` | Affects readability, reproducibility, or statistical interpretation without changing the main conclusion → generally `minor`; `major` when reproducibility is involved |
| `low` | `minor` or `info` | Formatting, redundancy, or slight presentation issues |

| slug | Description | severity |
| --- | --- | --- |
| `chart_type_mismatch` | Chart type does not match the research aim | major |
| `continuous_data_as_bar` | Continuous distribution shown only as bars, obscuring the distribution | minor |
| `truncated_axis` | Truncated y axis exaggerates differences | major |
| `axis_unit_unclear` | Axis labels/units/normalization baseline unclear | major |
| `missing_scale_bar` | Micrograph without a scale bar | major |
| `micrograph_info_incomplete` | Channels/magnification/ROI/quantification method missing | major |
| `missing_loading_control` | WB/gel without a loading control | major |
| `missing_risk_table` | Survival curve without a numbers-at-risk table | major |
| `error_bar_undefined` | Error bar type undefined | minor |
| `significance_undefined` | Asterisk significance threshold undefined | minor |
| `n_not_shown_in_figure` | Sample size not annotated in the figure | minor |
| `figure_terminology_inconsistency` | Terminology inconsistent across figure/caption/text | minor |
| `legend_color_confusing` | Legend or color scheme prone to misreading | minor |
| `caption_not_self_contained` | Figure caption not self-sufficient | minor |
| `figure_text_contradiction` | Figure contradicts the caption/text | major |
| `workflow_text_mismatch` | Workflow diagram inconsistent with the workflow described in the text | major |
| `figure_should_be_supplementary` | Main-text figure should move to the supplement | minor |
| `figure_should_be_main_text` | Supplementary figure contains key evidence for a main conclusion | major |
| `redundant_presentation` | Redundant chart information | info |
| `panel_reference_broken` | Panel references missing/duplicated/out of order | major |
| `figure_unreadable` | Insufficient resolution; text or axes unreadable | major |

### C.1 Receiving X1 external validation signals

`scripts/external_figure_validation.py` (Stage 3c) routes external validation results to M5.
They are signals with `type=external_validation_candidate`, and **the signal itself carries no severity**.

X1 performs only recomputable comparisons of "manuscript facts vs external authoritative facts"; whether to promote to a finding, and at what severity,
must be decided by M5 after checking back against the original figure, figure caption, main text, methods description, and external evidence.

| X1 `check_type` | Database | Comparison result | M5 category slug | M5 suggested severity after confirmation |
| --- | --- | --- | --- | --- |
| `blot_band_molecular_weight` | UniProt | `needs_manual_review` | `blot_band_mw_implausible` | `major`; no finding if explicable by modification/cleavage/glycosylation; `minor` if only a suspected labeling typo |
| `ic50_order_of_magnitude` | ChEMBL | `needs_manual_review` | `reported_activity_off_reference` | `major`; no finding if explicable by differing cell line, endpoint, time, or assay conditions |
| `compound_molecular_weight` | PubChem | `needs_manual_review` | `compound_mw_mismatch` | `major`; no finding if explicable by salt form/hydrate/isotope labeling/prodrug form |
| `compound_name_valid` | PubChem | `needs_manual_review` | `compound_not_found_in_reference` | `minor`; may rise to `major` if the authors claim a known compound but no authoritative record can be found |
| `pdb_entry_exists` | RCSB PDB | `mismatch` | `pdb_entry_not_found` | `major` |
| `gene_symbol_valid` | HGNC / NCBI Gene | `mismatch` / `needs_manual_review` | `gene_symbol_not_found_or_deprecated` | `minor`; may rise to `major` if the wrong gene symbol affects interpretation of a core figure |
| `protein_name_accession_match` | UniProt | `mismatch` / `needs_manual_review` | `protein_accession_mismatch` | `major`; may be `minor` or no finding if only an alias/isoform labeling difference |
| `antibody_catalog_exists` | vendor page / Antibody Registry | `mismatch` / `needs_manual_review` | `antibody_catalog_not_found` | `major`; may be `minor` if the vendor/catalog number is incompletely written but manually confirmable |
| `cell_line_identity_valid` | Cellosaurus | `mismatch` / `needs_manual_review` | `cell_line_not_found_or_misidentified` | `major` |
| `cell_line_contamination_flag` | Cellosaurus / ICLAC | `mismatch` | `cell_line_contamination_risk` | `major`; may be `minor` if the cell line is used only for marginal validation |
| `geo_accession_exists` | GEO | `mismatch` | `dataset_accession_not_found` | `major` |
| `sra_accession_exists` | SRA / ENA | `mismatch` | `dataset_accession_not_found` | `major` |
| `clinical_trial_id_exists` | ClinicalTrials.gov / WHO ICTRP | `mismatch` | `clinical_trial_id_not_found` | `major` |

**Processing rules**

1. **No `needs_manual_review` candidate may ever be raised as a finding directly.**
   M5 must check back against the original figure, caption, text, and methods description; if a reasonable explanation exists, discard the candidate or record it only as a manual-review note.

2. **A deterministic `mismatch` must not bypass the evidence chain either.**
   M5 may promote it to a finding faster, but must still cite both manuscript evidence and external evidence.
   For example, `pdb_entry_exists` returning an authoritative 404, a nonexistent GEO/SRA accession, or a nonexistent clinical trial ID
   can usually be promoted to `major`.

3. When X1 produces a `system_limitation` (endpoint unreachable, rate-limited, insufficient records),
   it must **not** be treated as "the manuscript is fine", nor as "the manuscript has a problem".
   Register the limitation per `00-contracts.md` and state in the report that this external validation was not covered.

4. Every finding promoted from an X1 candidate must include in `evidence_refs[]` both:
   the **manuscript evidence** and the **external evidence** registered by X1 — neither may be omitted.

5. If the external database result and the manuscript's statement differ in an explicable way — e.g., aliases, isoforms, salt forms, hydrates, cell-line-specific assays,
   vendor catalog-number format differences, outdated gene symbols — prefer downgrading to `minor` or raising no finding.

> **Severity note**:
> The table above gives M5's suggested severity after a candidate is confirmed, not the severity of the X1 signal.
> X1 never produces findings directly and never writes severity.
> M5 may raise, lower, or discard the suggested severity based on evidence weight, whether the entity supports a core conclusion, and whether reproducibility is affected.

---

## D. Mandatory Manual-Review Triggers

When Stage 3 hits any of the parsing conditions below, it only sets `figure_record.manual_review_needed = true` and produces the corresponding
signal / limitation. Only after the Stage 4 M5 Reviewer has separate manuscript evidence and decides to raise a finding does it state the review focus in
`finding.manual_review.action`:

- Low image resolution, heavy compression, unreadable text or axes
- Unclear axis values, legends, units, statistical symbols, or scale bar
- Contradictions among figure, caption, main text, and tables
- Panel references missing, duplicated, out of order, or unmatchable
- Evidence weight mismatched between main-text and supplementary figures
- Biological conditions cannot be reliably mapped to the groups in the figure
- **Values come from visual estimation** rather than direct annotation or readable data in the figure
- Micrographs with suspected duplicated regions, unclear cropping, unclear channels, or unclear quantification ROI
- The current chart type clearly diverges from chart types common in the same field over the last 3 years
- When field conventions cannot be confirmed — state the scope of the literature benchmarking needed (disease area, experimental model, study endpoint, years, journal tier)

When value extraction is requested but the image does not support precise reading, recommend using raw data, a vector PDF, supplementary tables, or manual review instead.

---

## E. TODO (Phase 1)

- [x] Populate the §A.2 research-scenario/chart-type knowledge base — MY's v1 completed
- [x] Populate the required-element checklists per chart type — merged into the mandatory-checks column of §A.2
- [x] Add the main-text/supplement placement-fit dimension (§B.2)
- [ ] Write 1 positive + 1 negative example for every slug in §C, for regression testing
- [ ] Align with M1 the interface for backfilling `key_data` from figures
- [ ] Validate the accuracy of the §A.2 classification rules on the 41 images in the `datasets/` corpus
- [ ] Draw the boundary with M4: whether a statistical method **is correct** belongs to M4; whether it **is clearly labeled** on the figure belongs to M5

---

## F. Implemented Candidate Screening and Future Enhancements

### F.1 Within-paper image forensics

The current `scripts/figure_integrity_audit.py` implements candidate screening for grid-aligned duplication, column-wise background discontinuities, and abnormally uniform blocks;
these only produce severity-free signals and force manual review. The following more robust capabilities are still unimplemented:

- Detection of duplicated regions across figures/panels under arbitrary cropping, offset, or mild compression
- Within-panel self-similar regions after rotation, mirroring, or scaling
- WB band splicing artifacts: background discontinuities, sharp band edges, abrupt local noise-distribution changes
- Overprocessing: histogram clipping, abnormal local contrast

> Image candidates **must all be marked `suspected` with mandatory manual review** —
> the false-positive cost of image forensics is extremely high (equivalent to an accusation of research misconduct); the Skill only marks suspicious regions and never draws conclusions.

### F.2 Cross-paper image comparison

- Data source: an image-fingerprint database (self-built or third-party)
- Check: whether this paper's images duplicate images from published papers
- High upfront cost; ranked after F.1.

### F.3 Improving value-back-inference precision

Reading values from figures currently relies on `axis_readable` and `pixel_estimated`; later, pixel-level measurement of curves/bar heights plus axis calibration could be introduced.
**Even so, the hard rules of §A.3 do not change**: back-inferred values are still marked `pixel_estimated`, still given as intervals,
and still must not be used for M4's statistical recomputation. Improved precision does not change the evidence grade.

### F.4 Field-convention benchmarking (full version)

Currently in fallback mode (§B.4). Once a Phase-1 connector to a literature database is wired in, retrieve in real time the chart-type distribution of comparable papers
by disease area + experimental model + study endpoint + year + journal tier, with `benchmark_basis` filled with real DOI/PMID.
The output should still be a **factual description** ("in this scenario, M of N comparable studies in the last 3 years used chart X"), not a direct "wrong chart type" verdict.

### F.5 Categories after candidates pass manual verification

| slug | Description | severity |
| --- | --- | --- |
| `duplicate_region_within_paper` | Duplicated image region within the paper (suspected) | critical |
| `splice_artifact_suspected` | Suspected splicing of WB bands | critical |
| `duplicate_image_across_papers` | Duplication of a published image (suspected) | critical |
| `chart_type_against_field_convention` | Chart type significantly diverges from field convention | minor |

When the image scripts hit, they only produce signals; the severities in this table must not be applied. Only after the M5 Reviewer has verified the original figure, ruled out legitimate reuse and
processing artifacts, and separately raised a finding may the first three categories be used; all three of the first entries force
`manual_review.who = editor`, with a `review_confidence` ceiling of `medium`.
