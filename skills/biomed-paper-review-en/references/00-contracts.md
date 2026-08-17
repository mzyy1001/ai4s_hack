# 00 · Shared Contracts (Common to All Modules)

**This file defines the data contracts shared by Stages 1–5, the optional external validation layer X1, and M1–M7. Any module output that does not conform to the definitions here is invalid, without exception.**

Referenced by `SKILL.md §3`. Modifying this file is equivalent to modifying the interfaces of every module and requires synchronization across the whole team.
Every example in this file **must** pass the contract lint checklist in §11.

**Terminology convention**: in this file, "record" refers specifically to the three top-level record types of §6 (`finding` / `extraction_signal` /
`system_limitation`). The objects in §7 (`execution_scope` / `coverage_breakdown`) are **not records**:
they must not be called findings and must not carry `severity`.

---


## 0. Object Hierarchy of the Layered Architecture (added 2026-08-07)

This Skill executes according to the five layers in `SKILL.md` §0. **Four object types converge as the layers progress and must not be conflated**:

| Layer | Object | schema | Evidence requirement |
| --- | --- | --- | --- |
| Layer 1 discovery | `candidate_issue` | `discovery.schema.json` | `evidence_refs` **not required** |
| Layer 2 specialist | `provisional_finding` | same as above (lenient) | Evidence already bound; not yet deduplicated or graded |
| Layer 3 tools | `extraction_signal` + `tool_task` | `extraction_signal.schema.json` / `discovery.schema.json` | Signals must carry evidence |
| Layer 5 final | `finding` | `finding.schema.json` | **Full evidence contract** |

**The discovery stage is deliberately lenient**: requiring Layer 1 to satisfy the full evidence contract up front lets structuring crowd out discovery —
in real runs, the Skill-equipped path has raised fewer issues than the bare model (no-skill baseline), and those issues were a strict subset.
The contract's job is to **organize and validate issues that have already been discovered**, not to consume attention before discovery happens.

Two companion runtime files:

- `00-runtime-contract.md` — the minimal subset excerpted from this file, for use by the specialist channel.
  **It is not a second source of truth**; on conflict, this file and the schemas prevail.
- `00-routing.md` — the mapping from issue type → specialist → index → rulebase → tools (specialists receive the full text).

Every candidate must be closed out in `candidate_resolution_log[]` (see `discovery.schema.json`),
and every run must emit `runtime_utilization` telemetry.

---

## 1. Evidence Registry (evidence_registry)

### 1.1 Why a registry is needed

The same piece of evidence is often referenced by multiple fields, multiple findings, and multiple signals. If each site inlines its own copy,
the same paragraph ends up with seven differently worded locators, and deduplication and clustering have nothing to align on.

**Rule: the canonical storage of evidence is the registry; every other location stores only an `evidence_ref` string.**

```json
{
  "evidence_registry": {
    "EV-018": {
      "id": "EV-018",
      "type": "present",
      "locator": {
        "section": "methods",
        "subsection": "2.4",
        "paragraph_id": "methods-p17",
        "pdf_file_page": 7,
        "printed_page": 1043,
        "xml_id": "para-0042",
        "scope": "paragraph"
      },
      "quote": "Data are presented as mean ± SEM (n = 3).",
      "created_by": "stage_2"
    },
    "EV-019": {
      "id": "EV-019",
      "type": "absence",
      "scope": "document",
      "searched_locations": [
        {"section": "methods", "scope": "section"},
        {"section": "declarations", "scope": "section"},
        {"supplement_id": "S1", "scope": "supplement"}
      ],
      "search_terms": ["randomization", "random allocation", "randomly assigned", "随机分组", "随机化"],
      "search_result": "no_match",
      "created_by": "stage_2"
    }
  }
}
```

### 1.2 Three evidence types

| type | Used for | Required | Forbidden |
| --- | --- | --- | --- |
| `present` | Content that exists in the manuscript | `locator` object | — |
| `absence` | Content that does not exist in the manuscript | `scope` + `searched_locations[]` + `search_terms[]` + `search_result` | **`quote`**, **`locator`** |
| `external` | Facts X1 obtained from public scientific data sources | `database` + `endpoint` + `query` + `retrieval_status` + response hash/version + `assertions[]` | Manuscript `locator`/`quote`, API keys, cookies, Authorization headers, the full response body |

**`search_result` enum**: `no_match` / `partial_match_ambiguous`.
The latter is **not sufficient** to support a conclusion of absence; any field citing it must be judged `ambiguous`, not `not_reported`.

**`external.retrieval_status` enum**: `resolved` / `not_found` / `not_addressed`.
`not_found` is reserved for a **well-formed exact identifier** that received an authoritative 404 or an explicit zero-record result within a successful response;
zero hits for name, keyword, or semantic queries may only be recorded as `not_addressed`. DNS failures, timeouts, TLS errors, allowlist blocks,
401/403, 429, 5xx, or response-structure drift **must not create external evidence**; produce a
`system_limitation` per §6.3 instead. Database silence is not counter-evidence.

### 1.3 Hard rules for the registry

1. Every `evidence_ref` **must** resolve to **exactly one** entry in the `evidence_registry`.
   Failure to resolve is a contract violation; the finding / signal in question is discarded outright.
2. Evidence ids are stable **within a single review run**, formatted `EV-<three or more digits>`, globally incrementing, never reused.
3. Entries with `type: "absence"` are **forbidden** from containing a `quote`. **Never fabricate a quotation for content that does not exist.**
4. The `searched_locations[]` of an `absence` entry must reflect searches that were **actually performed**.
   Content outside the searched scope must not be claimed "missing"; produce a `system_limitation` instead.
5. `created_by` takes `stage_1` / `stage_2` / `stage_3` / `stage_3b` /
   `stage_3c_external_validation` / `M2`…`M7`, for troubleshooting; `external` may only be created by
   `stage_3c_external_validation`.
6. Evidence with the same locator + the same quote **reuses the existing entry**; do not create a new one.
7. `external.assertions[]` stores only atomic facts from the external response together with their `source_path`; comparisons between
   manuscript values and external values go into `extraction_signal.external_check`, and comparison conclusions must not be disguised as database source text.

### 1.4 Reference rule: evidence_refs[] is the only canonical form

| Location | Storage form |
| --- | --- |
| `finding` | `evidence_refs[]` (**required, non-empty**) |
| `extraction_signal` | `evidence_refs[]` + optional `observation_refs[]` |
| `system_limitation` | `evidence_refs[]` (may be an empty array: cases like input truncation have nothing to point at) |
| `extracted_field` | `evidence_refs[]` |
| `provenance` | `evidence_ref` (a **single** string) |
| `evaluation_matrix` entry | `evidence_refs[]` |

The **rendering layer** (`templates/review_report.md`) is responsible for expanding refs into quotations and page numbers;
the **machine-readable JSON keeps the refs**, while attaching the full `evidence_registry` at the top level so the JSON is self-contained and verifiable.

Inlining `evidence[]` object arrays at any of the above locations is **forbidden**. The old contract's inline form is covered by the migration table in §10.

#### 1.4.1 `evidence_refs[]` must be **specific per finding**, never a shotgun blast of the full set

The meaning of `evidence_refs[]` is "**the evidence that supports this particular finding**",
not "all evidence collected in this run".

**Real counterexample** (from an actual run): in one paper's report, **every finding carried all 24
evidence references**, including external records with no relation to the finding at hand. Formally fully compliant — non-empty, every ref resolvable —
but **auditability drops to zero**: the reader cannot answer "which external record supports the judgment that 'the cited reference has been retracted'?"
For a tool whose selling point is auditability, this is far worse than citing a few pieces of evidence too few.

**Rules**:

1. Attach only evidence that **directly supports this specific judgment**; anything that can be removed without affecting the finding must be removed.
2. When a finding cites **multiple external evidence entries**, the `detail` must explain what each one proves.
3. Assigning the full key set of `evidence_registry` to any finding's `evidence_refs` is **forbidden**.

**L5 selftest (mandatory before rendering)**: tally each finding's `evidence_refs` set;
if **more than half of the findings share an identical reference list**, judge it shotgun citation,
narrow each finding's list before rendering; for entries that cannot be narrowed, prefer keeping only the single most direct reference
over attaching the full set.

### 1.5 external evidence example

```json
{
  "id": "EV-120",
  "type": "external",
  "database": "ClinicalTrials.gov",
  "endpoint": "https://clinicaltrials.gov/api/v2/studies/NCT01234567",
  "query": {"query_kind": "trial_registration", "normalized_input": "NCT01234567"},
  "record_id": "NCT01234567",
  "retrieved_at": "2026-08-07T03:20:00Z",
  "database_version": "2026-08-07",
  "http_status": 200,
  "retrieval_status": "resolved",
  "response_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "parser_version": "clinicaltrials_gov/1.0.0",
  "assertions": [{
    "predicate": "study_first_submit_date",
    "subject": "NCT01234567",
    "external_value": "2021-05-04",
    "unit": null,
    "source_path": "protocolSection.statusModule.studyFirstSubmitDate"
  }],
  "created_by": "stage_3c_external_validation"
}
```

### 1.6 X1 retrieval, caching, and retry contract

1. X1 accepts only `lookup_request`s issued after Stage 3b is closed: `request_id`, `connector`,
   `query_kind`, `normalized_input`, manuscript `present` evidence refs, and the requested assertions. X1 produces only
   `external` evidence, `external_validation_candidate` signals, or X1-local
   `system_limitation`s; **producing findings is forbidden**.
2. The cache key is `sha256(connector_version + HTTP method + endpoint template + sorted normalized parameters
   + Accept)`; the response body's SHA-256 is computed over the raw bytes. The cache stores the status code, ETag/Last-Modified from the response headers,
   retrieval time, database version, and parser version; it stores no credentials. The cache directory is specified by a run parameter and does not enter the submission package.
3. Within a single review run, the first successful response is frozen and not refreshed during the run. `resolved` cache entries default to a 24-hour TTL;
   `not_found` for exact identifiers and `not_addressed` for semantic queries are cached for at most 1 hour; expired entries are preferentially revalidated with
   `If-None-Match` / `If-Modified-Since`. 429, 5xx, network exceptions, and parse failures must not be negatively cached as
   `not_found`.
4. Retry only on connection timeouts, read timeouts, 429, 502, 503, and 504, at most 4 times, waiting 1, 2, 4 seconds;
   when `Retry-After` is present, honor it up to a cap of 120 seconds. Do not retry 400/401/403/404; record 401/403/allowlist blocks
   as `external_access_denied`; record 404 as `not_found` only when the exact-identifier rule is satisfied.
5. Every connector performs local format validation before going online, and obeys the rate limits published by the data source; without credentials, do not
   circumvent rate limiting by raising concurrency. In offline mode, or when X1 does not execute, Stages 1–5 must still complete fully.

### 1.7 locator field table

| Field | Description |
| --- | --- |
| `section` | Normalized section name, from the Stage 1 enum |
| `subsection` | Subsection number, e.g. `"2.4"` |
| `paragraph_id` | Paragraph id assigned by Stage 1 |
| `pdf_file_page` | **Physical PDF page number** (counting from 1); required for PDF input |
| `printed_page` | **Printed page number**; fill in if recognizable, otherwise `null` |
| `supplement_page` | Page number within supplementary material |
| `figure` / `panel` | Figure number and panel number |
| `table` | Table number |
| `supplement_id` | Supplementary material identifier, e.g. `"S1"` |
| `xml_id` | JATS/XML element id; required for XML input |
| `scope` | `document` / `section` / `paragraph` / `figure` / `panel` / `table` / `supplement` |

**Rendered form** (for display only, not for storage): `fig:3B | p.7 | sec:methods§2.4`;
the absence type renders as `absence:document`. Using free text as the sole stored form of a locator is **forbidden**.

---

## 2. Numeric Contract

### 2.1 numeric value variants (the single global form)

**Every numeric value must use a `type`-tagged object; bare numbers and string ranges are forbidden.**

```
point | interval | lower_bound | upper_bound | categorical
```

| type | Shape | Used for |
| --- | --- | --- |
| `point` | `{"type": "point", "number": 12.4}` | Explicitly reported point value |
| `interval` | `{"type": "interval", "low": 40, "high": 50}` | Pixel-based estimation, ranges given in the source text |
| `lower_bound` | `{"type": "lower_bound", "low": 100}` | `> 100`, `≥ LLOQ` |
| `upper_bound` | `{"type": "upper_bound", "high": 0.001}` | `p < 0.001`, `< LOD` |
| `categorical` | `{"type": "categorical", "label": "not_detected"}` | `ND` / `n.s.` / graded labels |

**Explicitly forbidden**: `"value": "40–50"`, `"value": 12.4`, `"value": "<0.001"`.
See §10 for migration of legacy string ranges.

### 2.2 unit and uncertainty

```json
{
  "unit": "μM",
  "unit_normalized": "uM",
  "uncertainty": {"type": "95CI", "low": 9.8, "high": 15.7}
}
```

- `unit` preserves the manuscript's original spelling; `unit_normalized` stores the `ucum_code` returned by the normalizer, and is merely an audit trail
  of unit spelling — it does **not** mean `value` has been converted. Compatibility comparisons must call the normalizer to obtain
  `factor_a_to_b` and convert a working copy of the values per §5.4; comparing unconverted raw values just because two `unit_normalized`
  strings are identical is forbidden. Dimensionless metrics use `unit: null`,
  `unit_normalized: null`.
- **Normalization is performed by `scripts/normalize_biomed_units.py`, path relative to the Skill root**
  (a phase-1 capability, standard library only).
  It is fail-closed: it performs only **same-dimension** deterministic conversion; unregistered aliases return `unknown_unit`,
  upon which the caller judges `ambiguous` — **no guessing**. Three dimension boundaries that are never merged:
  dose `mg/kg` ≠ rate `mg/kg/day`; per body weight `mg/kg` ≠ per body surface area `mg/m2`;
  mass concentration ↔ molar concentration **requires** both the analyte and an explicit molecular weight,
  otherwise it returns `conversion_requires_molecular_weight` — **never substitute an approximate molecular weight**.
- `uncertainty.type` enum: `SD` / `SEM` / `95CI` / `IQR` / `range` / `none`.
  `SD` / `SEM` use `{"type": "SD", "value": 1.2}`; interval types use `low` / `high`.

### 2.3 provenance (including derivation, required)

**Every numeric result must carry `provenance`, and `provenance.derivation` is required** —
otherwise the pixel / OCR dependency rates in §8.3 cannot be computed.

```json
{
  "source_type": "explicit_figure_caption",
  "source_id": "fig:2C",
  "evidence_ref": "EV-014",
  "derivation": {
    "extraction_method": "caption_parse",
    "ocr_used": false
  }
}
```

**`source_type` enum (globally unique, five values; all files and examples must be consistent)**:

```
explicit_main_text | explicit_table | explicit_figure_caption | axis_readable | pixel_estimated
```

**`derivation.extraction_method` enum**:

```
text_parse | table_parse | caption_parse | axis_read | visual_estimation | ocr_text
```

**`derivation.ocr_used`**: boolean; `true` means the value passed through an OCR text layer.
`extraction_method = ocr_text` if and only if `ocr_used = true`; for the other five methods,
`ocr_used` must be `false`.

**Legal `source_type` × `extraction_method` combinations** (all other combinations are contract violations):

| source_type | Allowed extraction_method |
| --- | --- |
| `explicit_main_text` | `text_parse`, `ocr_text` |
| `explicit_table` | `table_parse`, `ocr_text` |
| `explicit_figure_caption` | `caption_parse`, `ocr_text` |
| `axis_readable` | `axis_read` |
| `pixel_estimated` | `visual_estimation` |

**Two-level source classification** (the basis for canonical selection in §5.5):

```
explicit_reported  = {explicit_main_text, explicit_table, explicit_figure_caption}
visually_derived   = {axis_readable, pixel_estimated}
```

### 2.4 Mandatory constraints for pixel_estimated

When `source_type: "pixel_estimated"`, **all** of the following must hold; missing any one is a contract violation:

1. `value.type` must be `interval` with `low < high`; `lower_bound` / `upper_bound` may be used only when the visible range of the image clips the true value
   beyond its boundary and only a one-sided constraint can be supported; a zero-width interval with `low == high` or a one-sided
   bound must not be used to disguise a `point`;
2. `extraction_confidence` must be `low`;
3. `manual_review_needed` must be `true`;
4. It must **not** serve as input to any M4 statistical recomputation or consistency check;
5. Any finding citing it has a `review_confidence` cap of `medium`.

`axis_readable` allows `point`, but its `extraction_confidence` is capped at `medium`.

---

## 3. Field Contract (extracted_field)

### 3.1 Three orthogonal dimensions

The old contract conflated "applicability" and "requiredness" in a single `not_applicable` value, causing
"not in the coverage denominator" to be miswritten as "not applicable to this study". **The three are stored independently**:

| Dimension | Field | Question it answers |
| --- | --- | --- |
| applicability | `applicability` | Does this concept **even make sense** for this study/experiment? |
| requiredness | `requiredness` | To what degree **should** this design report it? |
| extraction status | `status` | What did we **actually extract**? |

```
applicability : applicable | not_applicable | applicability_uncertain
requiredness  : required | recommended | optional
status        : reported | not_reported | not_applicable | ambiguous
                | conflicting | parse_failed | unresolved
```

**Fixed order of determination**: first determine `applicability` (per the routing priority in §9.1),
then `requiredness`, and finally let the search result determine `status`.

### 3.2 Combination semantics (the only legal mapping)

| applicability | Search result | status | Additional requirement |
| --- | --- | --- | --- |
| `applicable` | Explicit report found | `reported` | ≥1 `present` evidence |
| `applicable` | Confirmed unreported after full search | `not_reported` | ≥1 `absence` evidence |
| `applicable` | Relevant text exists but yields no unique reading | `ambiguous` | ≥1 `present` (pointing at the ambiguous text) |
| `applicable` | Multiple sources incompatible | `conflicting` | See §5 (key_data) or `candidate_refs[]` |
| `applicable` | Awaiting Stage 3 visual parsing | `unresolved` | `resolution_state` block, see §4 |
| `applicable` | Technically impossible to extract | `parse_failed` | `system_limitation_ref` |
| `not_applicable` | — (no search) | `not_applicable` | `na_reason` |
| `applicability_uncertain` | — | `ambiguous` | Associated `ambiguous_study_design` signal |

**`requiredness` does not change `status`**; it only changes the coverage denominator (§8.2) and the downstream severity baseline.

### 3.3 Structure

```json
{
  "field_path": "measurement.sample_size_justification",
  "applicability": "applicable",
  "requiredness": "required",
  "status": "not_reported",
  "value": null,
  "unit": null,
  "evidence_refs": ["EV-019"],
  "extraction_confidence": "high",
  "na_reason": null,
  "resolution_state": null,
  "system_limitation_ref": null,
  "candidate_refs": [],
  "alternatives": []
}
```

- `value` is a numeric object per §2.1, a string, a structured object, or `null`.
  When `status ∈ {not_reported, not_applicable, ambiguous, conflicting, parse_failed, unresolved}`,
  `value` **must** be `null`.
- `alternatives[]`: **the extractor's different readings of the same fact** (we are uncertain), each item `{value, evidence_refs}`.
- `candidate_refs[]`: when `status: conflicting`, points to `observation_id`s of §5.
- Encoding multiple missingness states with a bare `null` is **forbidden**.

### 3.4 Three boundaries that must not be confused

1. **`not_reported` ≠ `parse_failed`** — the former means the **manuscript** did not write it (confirmed by search),
   and it **may** ground findings from M2/M4/M6; the latter means **we** failed to read it,
   and it must **never** ground a manuscript finding — it only lowers `extraction_coverage` and confidence.
   When you cannot tell which it is, always use `parse_failed` — better to admit we could not see clearly than to wrong the manuscript.

2. **`not_reported` ≠ `not_applicable`** — the former is "should have been written but was not"; the latter is "never needed to be written".
   A field must **not** be judged `not_applicable` merely because it is outside the coverage denominator (§3.1).

3. **`ambiguous` ≠ `conflicting`** — the former is **one** passage of text that yields no unique reading;
   the latter is **multiple** sources fighting each other, already judged incompatible per §5.4.
   When comparability between sources **cannot be established**, use `ambiguous`; do **not** automatically judge `conflicting`.

### 3.5 Extraction confidence vs. reporting completeness (orthogonal)

| Concept | Field | Answers |
| --- | --- | --- |
| Extraction confidence | `extraction_confidence`: `high`/`medium`/`low` | Is the value we read the value the manuscript wrote? |
| Reporting completeness | `reporting_completeness`: `complete`/`incomplete`/`not_assessed` | Did the manuscript report this value fully? |

Example: a figure caption states `IC50 = 12.4 μM` but has no CI or fitting method →
`extraction_confidence: "high"` + `reporting_completeness: "incomplete"`.
**Neither may contaminate the other.**

---

## 4. Pending Lifecycle (unresolved)

When M1 in Stage 2 encounters a field that is "absent from the text but possibly present in a figure", it must **not** judge `parse_failed`
— Stage 3 has not yet been attempted, so there is no failure to speak of. Use the `unresolved` lifecycle status:

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

**Rules**

1. `status: "unresolved"` is **only allowed in `structured_result_v1`**.
2. It is **not** a `system_limitation`, and `system_limitation_ref` must **not** be filled. Modes that will still execute
   Stage 3b do not settle coverage early; if `structured_extraction` outputs v1 as its final state,
   count it into `unresolved_required_fields[]` per the rule at the end of this section.
3. `resolution_state.state` has only one value in phase 1: `pending_visual_resolution`.
   `pending_stage` is always `stage_3`. `expected_sources[]` has at least one item, of the form `fig:2C` / `table:3`.
4. **Stage 3b must resolve every `unresolved` into** one of:
   `reported` / `not_reported` / `ambiguous` / `conflicting` / `parse_failed`.
5. **`status: "unresolved"` must not appear in `structured_result_v2`**,
   nor may a non-null `resolution_state`. This is a mandatory check item of the §11 lint.
6. Only when Stage 3 has **genuinely attempted and failed** (unreadable image, missing panel) may it be converted to `parse_failed`,
   and it **must** be associated with a `system_limitation`.

**When Stage 3b is not executed** (e.g. `structured_extraction` in a mode without visual needs):
output stops at v1, `unresolved` legitimately remains, but the field counts into
`coverage_breakdown.unresolved_required_fields[]`, and the output must be annotated `stage_3b_executed: false`.

**Modes requiring v2**: if any `unresolved` exists within v1's current scope, the orchestrator must first execute
a Stage 3 covering its `expected_sources[]` before entering Stage 3b. When Stage 3 has not executed,
Stage 3b must not change the item to `not_reported` or `parse_failed`: the former lacks a full search,
the latter lacks a genuine parse attempt; both violate the state machine.

---

## 5. key_data Observation-Group Contract

### 5.1 Why a "group" rather than a "point"

The same IC50 may appear simultaneously in a figure caption, the main text, and a table. The old contract's flat `key_data` could store only one value,
so merging inevitably overwrote silently. **Each element of `key_data[]` is an observation group**:
the group retains all sources internally, and the group itself carries the merged conclusion.

### 5.2 Structure

```json
{
  "id": "KD-007",
  "metric_name": "IC50",
  "metric_family": "dose_response",
  "grouping_key": {
    "experiment_id": "EXP-02",
    "group": "Compound A",
    "comparison": "Compound A vs vehicle",
    "timepoint": "72h",
    "endpoint": "cell_viability"
  },
  "status": "conflicting",
  "canonical_observation": null,
  "canonical_rationale": null,
  "observations": [
    {
      "observation_id": "OBS-014",
      "value": {"type": "point", "number": 12.4},
      "unit": "μM",
      "unit_normalized": "uM",
      "uncertainty": {"type": "95CI", "low": 9.8, "high": 15.7},
      "n": 3,
      "replicate_type": "biological",
      "provenance": {
        "source_type": "explicit_figure_caption",
        "source_id": "fig:2C",
        "evidence_ref": "EV-014",
        "derivation": {"extraction_method": "caption_parse", "ocr_used": false}
      },
      "extraction_confidence": "high",
      "manual_review_needed": false
    },
    {
      "observation_id": "OBS-015",
      "value": {"type": "point", "number": 15.1},
      "unit": "μM",
      "unit_normalized": "uM",
      "uncertainty": {"type": "none"},
      "n": 3,
      "replicate_type": "biological",
      "provenance": {
        "source_type": "explicit_main_text",
        "source_id": "results-p8",
        "evidence_ref": "EV-015",
        "derivation": {"extraction_method": "text_parse", "ocr_used": false}
      },
      "extraction_confidence": "high",
      "manual_review_needed": false
    }
  ],
  "compatible_observations": [],
  "conflicting_observations": ["OBS-014", "OBS-015"],
  "reporting_completeness": "not_assessed",
  "missing_elements": [],
  "signal_refs": ["SIG-002"]
}
```

### 5.3 Group status enum

```
reported | compatible_multiple_sources | conflicting | ambiguous
| pending_visual_resolution | parse_failed
```

| status | Meaning | `canonical_observation` |
| --- | --- | --- |
| `reported` | Single source, normally reported | that sole `observation_id` |
| `compatible_multiple_sources` | Multiple sources, judged compatible | id chosen per §5.5 |
| `conflicting` | Multiple sources, judged incompatible | **`null`** |
| `ambiguous` | Comparability cannot be established within the group (units non-normalizable / numeric variants incomparable) | **`null`** |
| `pending_visual_resolution` | Legal only in v1, awaiting Stage 3 | **`null`** |
| `parse_failed` | Still unreadable after Stage 3 attempt | **`null`** |

**`pending_visual_resolution` must not appear in v2** (same as §4 rule 5).
`pending_visual_resolution` and `parse_failed` have empty `observations[]`; the former must carry
`resolution_state`, the latter must carry `system_limitation_ref`. `reported` has exactly one observation;
`compatible_multiple_sources` and `conflicting` have at least two.

### 5.4 Grouping and compatibility determination (executed by Stage 3b)

**Step 1 · Grouping.** Stage 2 text observations use the `grouping_key` of the group they belong to; Stage 3 figure observations
must carry `metric_family`, a normalized `metric_name`, and a `target_grouping_key`. Stage 3b first requires
the metric identity of two observations to match, then compares **all five keys for equality**:
`experiment_id` / `group` / `comparison` / `timepoint` / `endpoint`
(`null` equals `null`; one side `null` and the other side valued counts as **unequal**).
Mismatched metric identity or grouping key → two different `key_data` entries, **not a conflict**.
`metric_name` uses the canonical name from this project's metric vocabulary (e.g. `IC50`); the original wording is preserved in
the observation's evidence and `quote`; raw casing or aliases do not participate in grouping.

A Stage 3 figure observation that exactly matches an existing group merges into it; with no exact match, create a new group — never
guess-match by similar names. On merging, remove the three temporary routing fields `target_grouping_key` / `metric_name` / `metric_family`,
which are carried by group-level fields; all remaining `observation_core` fields must be preserved verbatim, field by field, including
`observation_id` / `value` / `unit` / `unit_normalized` / `uncertainty` / `n` /
`replicate_type` / `provenance` / `extraction_confidence` / `manual_review_needed` / `quote`.
When the same `observation_id` appears in two Stage 3 copies, all fields including the three routing fields must be
identical; its persisted copy in `structured_result_v2.key_data` must be identical to the
`observation_core` after removing the three routing fields, and the target group's metric identity and five keys must equal the original routing fields. On any inconsistency,
Stage 3b must halt the merging of that id and produce a `system_limitation` with `category: "parse_failed"`,
writing that `observation_id` into `affected_targets[]`; it must not pick one copy to overwrite, nor compare only `value` /
`provenance`. Every Stage 3 figure observation in `structured_result_v2` must land in exactly one `key_data`
group, or be explicitly rejected by such a Stage 3b limitation; neither persisted nor listed in `affected_targets[]` constitutes
untraceable data loss.

**Step 2 · Comparability.** Within a group, judge every unordered observation pair, pair by pair, in a fixed order;
each pair must yield exactly one of `compatible` / `conflicting` / `ambiguous`:

1. **Unit gating and working-value conversion.** If both sides have `unit` `null`, or the original unit strings are identical,
   the conversion factor is 1. In all other cases run `scripts/normalize_biomed_units.py --compare`.
   When calling, pass the unit of the lexicographically larger `observation_id` as `unit_a` and the smaller as `unit_b`.
   When it returns `comparable`, always convert the larger id's observation into the smaller id's unit:
   multiply, at the same ratio using `factor_a_to_b`, its `value`'s `number/low/high`, its `uncertainty`'s
   `value/low/high`, and the original-precision unit `u` — forming a working copy for this comparison only, without rewriting
   `observations[]`. `unknown_unit` / `incomparable_dimension` /
   `conversion_requires_molecular_weight` all → `ambiguous`. Mass concentration ↔ molar concentration may be passed to the script only when
   both the analyte and a positive molecular weight explicitly stated in the manuscript are present.
2. **Categorical values.** Both `categorical` with exactly identical `label` → `compatible`;
   different labels → `ambiguous`. `categorical` combined with any numeric type → `ambiguous`.
3. **Compare the numeric body first.** Both `point`: take the unit `u` of the last significant digit of the
   lower-precision representation, `tol = 0.5 × u`. `|a − b| ≤ tol` → numeric bodies compatible;
   otherwise → `conflicting`. If the two numeric JSON values are exactly equal, treat the bodies as compatible directly; otherwise, when the source text
   is insufficient to recover `u` → `ambiguous`. Example: `12.4` vs `12.43` gives `tol = 0.05`,
   difference `0.03` → compatible; `12.4` vs `15.1` → conflict.
4. **Interval and bound-type numeric bodies.** Interpret `interval`, `lower_bound`, `upper_bound`
   as the closed constraints `[low, high]`, `[low, +∞)`, `(-∞, high]` respectively; interpret a point value as
   `[number − tol, number + tol]`. Non-empty intersection of the two constraints → numeric bodies compatible, otherwise →
   `conflicting`; when a point value's `tol` cannot be recovered → `ambiguous`.
5. **Then check uncertainty.** Execute only when the numeric bodies are already compatible. If either side is `none`,
   or the two types differ, do not let uncertainty override the body result. When both are `SD` / `SEM`, compare
   `value`; when both are `95CI` / `IQR` / `range`, compare the corresponding `low` and `high` respectively.
   If the corresponding JSON values are equal, it passes; otherwise judge by the rounding intervals of each original representation: pass only if the rounding intervals
   intersect; no intersection → `conflicting`; precision unrecoverable → `ambiguous`.
   **Never substitute overlap of two 95% CIs for consistency checking of point estimates and interval endpoints**;
   CI overlap only means the two uncertainty ranges intersect — it cannot prove the manuscript reported the same value in both places.
6. **Fallback.** Any required branch uncovered or unexecutable → `ambiguous`. Never default to conflict.

**Step 3 · Group status and archiving.** `compatible_observations[]` collects ids that participate in at least one
`compatible` pair; `conflicting_observations[]` collects ids that participate in at least one
`conflicting` pair; the same id may appear in both. Arrays are deduplicated and sorted lexicographically by id.

- Exactly one observation → `reported`;
- Any `conflicting` pair exists → `conflicting`;
- No conflict but any `ambiguous` pair exists → `ambiguous`;
- At least two observations and all pairs `compatible` → `compatible_multiple_sources`.

**All observations are retained in `observations[]`, without exception; deletion or silent overwriting is forbidden.**

**Step 4 · Emit signals.** If `conflicting_observations[]` is non-empty → produce one
`source_value_conflict` signal (§6.2) and backfill `signal_refs[]`. Default routing is M2/M4; if the conflicting group
contains at least one `axis_readable` or `pixel_estimated` observation, `routed_to` must additionally include M5,
which re-examines the original figure and judges whether it constitutes a `figure_text_contradiction`. Stage 3b produces only signals, never findings.

### 5.5 Selecting canonical_observation

**Do not use the absolute order "main text > table > figure caption > axis > pixel".** That order is wrong in the common case where
"the main text is a rounded narrative summary and the table holds the complete result".

**The only absolute rule retained**: `explicit_reported` always takes precedence over `visually_derived`.
If a group contains both classes and they have been judged compatible, the canonical must come from `explicit_reported`.

Only `reported` and `compatible_multiple_sources` may select a canonical: the former directly selects its sole observation;
the latter first applies the absolute source rule, then performs **stable layer-by-layer filtering** by the criteria below. Each layer keeps only the
candidates best on that criterion; stop when one remains; proceed to the next layer only on a tie. **Apply a layer only when its criterion can be
recovered from each remaining candidate's observation and `evidence_ref`**; if any candidate lacks that layer's information,
skip the layer for all candidates — "unknown" must not be treated as "worse".

| # | Criterion | Explanation |
| --- | --- | --- |
| 1 | Explicitly designated by the manuscript as the primary numeric result | e.g. the table or paragraph containing "primary outcome" / "primary endpoint" |
| 2 | Carries uncertainty information | Having CI/SD/SEM beats a bare point value |
| 3 | Higher significant-figure precision | `12.43` beats `12.4` |
| 4 | Not a narrative rounded summary | Complete results in tables/figure captions beat the main text's "about 12 μM" |
| 5 | More complete elements for the metric family | Per `01-structured-extraction.md §6.3` |
| 6 | All of the above tied | Take the lexicographically smallest `observation_id`, guaranteeing reproducibility |

For a single observation, the rationale reads `single_observation`. After a multi-source selection, the
`canonical_rationale` **must** state the first layer that eliminated the other candidates: when the absolute source rule fires, write
`"source_class: explicit_reported over visually_derived"`; when a table criterion fires, write the criterion number and reason,
e.g. `"criterion_2: fig:2C carries a 95% CI, results-p8 is a bare point value"`; when everything ties, write
`"criterion_6: observation_id lexical minimum"`.

For `ambiguous` / `conflicting` / `pending_visual_resolution` / `parse_failed`,
`canonical_observation` is always `null`; the ranking above must not be run in these states.

### 5.6 reporting_completeness and metric families

The element table for metric families is in `01-structured-extraction.md §6.3`.
`reporting_completeness` is judged at the **group level**, based on the element completeness of the `canonical_observation`;
when `canonical_observation` is `null`, it is always `not_assessed` and `missing_elements` is an empty array.

---

## 6. Three Top-Level Record Types (never interchangeable)

**The sole criterion for classification: is this a problem of the manuscript, an observation of ours, or a limitation of our capability?**

| Contract | Producer | Has severity | Impact |
| --- | --- | --- | --- |
| `finding` | **M2–M7 only** | ✅ `critical`/`major`/`minor`/`info` | Manuscript risk score |
| `extraction_signal` | Stage 2, Stage 3, Stage 3b, optional X1 | ❌ none | Routed downstream for judgment; not itself a conclusion |
| `system_limitation` | Stage 1 / 2 / 3 / 3b, optional X1 | ❌ none | Discloses capability limits; does not increase manuscript risk |

**M1 produces no `finding` whatsoever.** The old contract's `extraction_quality_findings[]` is abolished;
see the migration mapping in §10.

### 6.1 finding · manuscript-level review judgment

```json
{
  "id": "M4-003",
  "module": "M4",
  "category": "power_and_sample_size",
  "severity": "major",
  "title": "Between-group comparison lacks sample-size justification and effect size",
  "detail": "Fig 3B compares three groups with one-way ANOVA; each group has n=3 without stating whether replicates are biological or technical; neither the main text nor the methods section shows a power analysis or effect-size report.",
  "evidence_refs": ["EV-018", "EV-019"],
  "rule_ref": "04-statistics#sample-size-reporting",
  "review_confidence": "high",
  "derived_from_signals": ["SIG-004"],
  "related_findings": [],
  "manual_review": {
    "action": "Verify whether n=3 refers to biological or technical replicates; ask the authors to supply a power analysis or effect sizes",
    "who": "statistical_reviewer",
    "priority": "P1"
  }
}
```

**Enums (no inventing new values)**

- `module`: `M2` / `M3` / `M4` / `M5` / `M6` / `M7`. **`M1` is illegal.**
- `severity`: `critical` (conclusion does not hold / ethics violation / suspected misconduct) > `major` (requires the authors to supply materials or redo analyses)
  > `minor` (wording and reporting-standard issues) > `info` (advisory)
- `review_confidence`: `high` / `medium` / `low` — the reliability of **this judgment itself**.
- `category`: must be a slug already registered in that module's reference file.
- `manual_review.who`: `statistical_reviewer` / `domain_reviewer` / `ethics_committee` /
  `editor` / `author`
- `manual_review.priority`: `P0` / `P1` / `P2`

**The single standard for manual-review priority**

- `P0`: the core conclusion, ethics authorization, or data integrity cannot be reliably interpreted without checking first; all criticals are fixed at
  P0, and majors that directly block interpretation of the core conclusion may also be P0.
- `P1`: does not block reading other conclusions, but would change whether a major finding holds, its severity, or the
  analyses/materials the authors must submit. A major that does not meet the P0 condition is fixed at P1.
- `P2`: reporting clarifications, locator checks, or editorial corrections for minor/info; does not change the current core inference.

P0/P1/P2 is a checking order, not a severity, and does not enter the risk score. Within the same priority, order by severity descending, then
finding id ascending.

**Hard rules**

1. `evidence_refs[]` **must be non-empty**, and every item must resolve in the registry.
2. Findings with `severity >= major` **must** have a non-empty `manual_review.action`.
3. Findings whose evidence includes `pixel_estimated` or points at an `ambiguous` field have a
   `review_confidence` cap of `medium`.
4. **A `system_limitation` must not be converted into a finding.** If a finding truly must be raised at the same location,
   manuscript evidence (`present` or compliant `absence`) must be supplied **separately**.
5. `derived_from_signals[]` is for provenance only and must **not** substitute for `evidence_refs[]`
   — raising a finding on a signal id alone is a contract violation.
6. A critical's `manual_review.priority` must be P0; a major may only be P0/P1; minor/info, if a priority is set,
   may only be P2. Every critical/major must enter the report-level `manual_review_plan`; minor/info entries with
   P2 set and a non-empty action must enter it too.
7. Any finding citing `external` evidence must have `evidence_refs[0]` resolve to an in-manuscript
   `present` evidence, and the refs must include at least one `present` and one `external`. External records can only validate
   claims, identifiers, or values that **actually appear in the manuscript**; `absence + external` cannot substitute for an in-manuscript anchor.
8. `external.retrieval_status ∈ {not_found, not_addressed}`, an X1 `system_limitation`, or
   `external_check.comparison_result ∈ {not_comparable, needs_manual_review}` may never alone support a
   finding. A database miss, an interface failure, or semantic incomparability never means the manuscript has a problem.

### 6.2 extraction_signal · machine-level observation

```json
{
  "id": "SIG-002",
  "type": "source_value_conflict",
  "target": "key_data.KD-007",
  "detail": "IC50 in the figure caption is 12.4 μM (95% CI 9.8–15.7); the main text gives 15.1 μM with no interval; rounding tolerance 0.05, difference 2.7, judged incompatible.",
  "observation_refs": ["OBS-014", "OBS-015"],
  "evidence_refs": ["EV-014", "EV-015"],
  "routed_to": ["M2", "M4"],
  "produced_by": "stage_3b"
}
```

**`type` enum (fifteen values)**

| type | Trigger condition | Routed to | What downstream judges |
| --- | --- | --- | --- |
| `source_value_conflict` | Multiple sources in the same observation group are incompatible (§5.4) | M2 (primary), M4; also M5 when a visual source is involved | Whether it constitutes an internal contradiction in the manuscript; M5 judges figure-text contradiction |
| `claim_without_resolved_evidence_link` | A claim's `supported_by` resolves to no `key_data.id` or evidence | M7 | Whether it constitutes an unsupported claim |
| `ambiguous_study_design` | Design cues conflict or are insufficient for unique classification | M2, M3, M4, M6 | Whether it constitutes an unclear design description |
| `unresolved_cross_reference` | A figure/table/supplement cited in the text resolves to no entity | M2, M5 | Whether it constitutes a citation error |
| `partial_extraction` | A field is partially extracted (n without group assignment, dose without unit) | M4, M5 | Whether it constitutes incomplete reporting |
| `ambiguous_extraction` | Field `status: ambiguous`: text exists but yields no unique reading | M2, M4 | Whether it constitutes unclear wording |
| `test_statistic_p_mismatch` | The p recomputed from the test statistic and degrees of freedom falls outside the rounding interval of the reported value | M4 | Whether it constitutes a statistical reporting error |
| `ci_estimate_mismatch` | A point estimate falls outside its own reported confidence interval, or interval endpoints are invalid | M4 | Whether it constitutes a result-reporting error |
| `count_percentage_mismatch` | Counts and percentages are inconsistent (count exceeds denominator, or percentage outside its rounding interval) | M4, M2 | Whether it constitutes a data-reporting error |
| `grim_incompatible_mean` | An integer-scale mean has no feasible integer sum for the given n (GRIM) | M4 | Whether it constitutes an impossible summary statistic |
| `table_total_mismatch` | Mutually exclusive, exhaustive category counts do not sum to the declared denominator | M4, M2 | Whether it constitutes a table-count error |
| `ethics_requirement_unmet` | An ethics requirement in the rulebase applies, but no corresponding report is found in the manuscript | M6 | Whether it constitutes an ethics-compliance issue |
| `sequence_identifier_inconsistent` | Variant nomenclature/sequence/accession/gene symbol has a definite violation, or the expression exceeds the locally parsed subset and needs manual review | M2, M3 | Whether it constitutes a wording or methodological error |
| `figure_integrity_candidate` | Image audit detects candidate duplicated regions, background-splice discontinuities, or abnormally uniform blocks | M5 | After manual checking of the original figure, figure caption, and any legitimate-reuse statement: whether it constitutes an image-integrity issue |
| `external_validation_candidate` | X1 has completed a comparability judgment between a manuscript `present` fact and an `external` atomic fact | M2–M7 (excluding M1) | After re-checking the manuscript and external record: whether an identity, registration, statistical, or claim inconsistency exists |

> The five statistical-forensics signals (`test_statistic_p_mismatch`, `ci_estimate_mismatch`,
> `count_percentage_mismatch`, `grim_incompatible_mean`, `table_total_mismatch`) are produced by
> `scripts/statistical_forensics.py` in Stage 2 (path relative to the Skill root);
> they **require no raw data**
> and are deterministic consistency checks feasible in phase 1 (`produced_by: "stage_2"`, `routed_to: ["M4"]`).
> They **remain signals only** — the tool layer draws no manuscript conclusions; whether they constitute manuscript problems is judged by M4.
> The applicability preconditions of each check are in that script's documentation; **when preconditions are unmet, always produce `partial_extraction` rather than guessing**.
> When Stage 2 constructs the script input, it should also pass in the already-bound `observation_refs[]` / `evidence_refs[]`; the script preserves
> these refs as-is but never generates locators on its own. `test_statistic_p_mismatch.forensics` must store
> `test_family`, `statistic`, `tail`, and the corresponding degrees of freedom, so M4 can recompute independently.

`ethics_requirement_unmet` and `sequence_identifier_inconsistent` are produced in Stage 2 by
`scripts/ethics_compliance_check.py` and `scripts/sequence_identifier_audit.py` respectively.
The sequence tool treats only position out-of-bounds, definite reference-residue mismatch, format violations for supported databases, and illegal alphabets as
deterministic checks; of these, position out-of-bounds and reference-residue mismatch additionally require a complete reference sequence, accession, and version.
When a sequence is given but the reference context is incomplete, produce `partial_extraction`; do not treat a sequence fragment as a complete reference and rule it wrong.
Expressions beyond its HGVS subset must be marked `candidate: true` and must not be treated as syntax errors.

**Rules**

1. Signals **have no `severity`** and do **not directly** affect `manuscript_risk_score`.
2. `produced_by` takes `stage_2` / `stage_3` / `stage_3b` /
   `stage_3c_external_validation`.
   `stage_3` is used **only** for the image-integrity audit — a pixel-level machine observation
   that naturally arises during image parsing; `stage_3c_external_validation` is used **only** for
   `external_validation_candidate`; neither **produces findings**.
3. The `target` of `claim_without_resolved_evidence_link` must carry target metadata:
   `{"claim_id": "CLM-03", "unresolved_refs": ["Fig 5D"]}`;
   **no separate** `unresolved_evidence_links[]` array (§10).
4. The old `parse_failure` type is **abolished** — a parse failure is a `system_limitation`, not a signal (§10).
5. `external_validation_candidate` requires `external_check` and must simultaneously reference at least one in-manuscript
   `present` and one `retrieval_status: resolved` `external` evidence; the top-level
   `evidence_refs[]` must exactly cover the two ref sets of `external_check`. `not_found` / `not_addressed`
   have no comparable atomic facts and must not create a signal. `comparison_result` takes only `match` / `mismatch` /
   `not_comparable` / `needs_manual_review`; only `mismatch` may enter downstream finding candidacy, and the
   receiving module must still independently re-check the evidence. **X1 may route to M2/M3/M4/M5/M6/M7, never to M1** (M1 only extracts identifiers for X1's use and produces no findings itself).
   Every `check_type` must have its consumption criteria registered in the receiving module's reference, otherwise the runtime model receives a signal with nowhere to put it.

> **Qualitative prohibition for the image-integrity audit.** For `figure_integrity_candidate`,
> `image_audit.severity_hint` is **always `null`**, `candidate` is always `true`,
> and `manual_review_required` is always `true`. Image duplication has many legitimate explanations (reuse of the same control group,
> templated schematics, magnified insets); automating it into an accusation of academic misconduct is the highest reputational-risk action in this project.
> When M5 raises a finding from it, the original figure **must** first be checked manually; and silence does not mean the images are clean
> — the method covers only grid-aligned duplication, not rotation or scaling.

### 6.3 system_limitation · system capability limitation

```json
{
  "id": "SYS-004",
  "category": "figure_unreadable",
  "impact": "Panel B of Figure 4 cannot be parsed; the M4 and M5 review of this figure is incomplete",
  "affected_modules": ["M4", "M5"],
  "affected_targets": ["fig:4B"],
  "affected_fields": ["key_results.tumor_volume_day28"],
  "evidence_refs": ["EV-041"],
  "recommended_action": "Obtain the original high-resolution figure files or a vector PDF and re-parse",
  "produced_by": "stage_3"
}
```

**`category` enum (twelve values)**

```
parse_failed | figure_unreadable | table_unparseable | supplement_inaccessible
| section_missing_from_input | ocr_low_quality | encoding_error | input_truncated
| external_source_unavailable | external_access_denied | external_rate_limited
| external_response_unparseable
```

**Hard rules**

1. **No `severity` field.** It is not a manuscript problem.
2. Stage 1–3b limitations do not directly deduct points on their own; only when they cause an in-scope field to become `parse_failed`, an asset to be unreadable,
   supplementary material to be unavailable, or an observation to depend on pixel/OCR, do they lower
   `extraction_coverage` and confidence via the variables declared in §8. X1 limitations only lower the future
   `external_validation_coverage` (display-only until it lands); they **must not alter the existing three scores**, and certainly must not raise
   `manuscript_risk_score`.
3. It must **not** be converted into a manuscript defect without independent manuscript evidence (§6.1 rule 4).
4. The report must include a dedicated section — so readers can see "where we could not see clearly".
5. `produced_by` takes `stage_1` / `stage_2` / `stage_3` / `stage_3b` /
   `stage_3c_external_validation`; the four `external_*` categories may only be produced by X1.

### 6.4 Boundary matrix (the single ruling for contested cases)

| Situation | Correct contract | Wrong practice |
| --- | --- | --- |
| Supplement is cited but cannot be downloaded | `system_limitation: supplement_inaccessible`; dependent fields `parse_failed` | Judging `not_reported` and raising a missingness finding |
| Image too blurry to read coordinates | `system_limitation: figure_unreadable` | Raising a "poor figure quality" finding |
| Manuscript genuinely lacks an ethics statement (full-text search done) | Field `not_reported` + `absence` evidence → M6 raises a finding | Judging `parse_failed` |
| Main text and figure caption values clash | `source_value_conflict` signal → M2 judges | M1 directly raising an `internal_inconsistency` finding |
| Field awaiting Stage 3 parsing | `status: unresolved` | `parse_failed` + `pending_visual_resolution: true` |
| Units non-normalizable, comparison impossible | Group status `ambiguous` | Group status `conflicting` |
| External host not allowlisted, 429, 5xx, or response-structure drift | X1 `system_limitation`; offline flow continues | `not_found`, a mismatch signal, or a finding |
| Authoritative 404 for an exact accession | `external: not_found`; at most goes to manual checking, no automatic finding | Declaring the identifier fake or the data unavailable |
| Zero hits for a name/semantic query | `external: not_addressed` | Treating it as external counter-evidence |

---

## 7. Non-Record Objects

Neither of the following is a record: they must not be called findings and must not carry `severity`.

### 7.1 execution_scope · execution scope

**Every denominator of coverage and confidence is taken from this object.** Required in all modes.

```json
{
  "execution_scope": {
    "mode": "targeted_check",
    "submode": null,
    "executed_stages": ["stage_1", "stage_2", "stage_3b"],
    "executed_modules": ["M6"],
    "skipped_modules": ["M2", "M3", "M4", "M5", "M7"],
    "fields": ["declarations.ethics_statement", "declarations.informed_consent",
               "population.subjects"],
    "assets": [],
    "observations": [],
    "supplements": ["S1"],
    "scope_rationale": "User asked only whether the ethics declarations are complete"
  }
}
```

| Field | Description |
| --- | --- |
| `mode` | `full_review` / `structured_extraction` / `figure_analysis` / `targeted_check` |
| `submode` | Used only by `figure_analysis`: `interpretation_only` / `figure_review`; otherwise `null` |
| `executed_stages[]` | `stage_1` / `stage_2` / `stage_3` / `stage_3b` / `stage_3c_external_validation` / `stage_4` / `stage_5`; omit the X1 value when X1 did not run |
| `executed_modules[]` | Review modules actually run; empty array in non-review modes |
| `skipped_modules[]` | Empty array under `full_review` |
| `fields[]` | The full set of field paths entering the coverage denominator |
| `assets[]` | Figure/table ids entering the `asset_readability_rate` denominator |
| `observations[]` | The full set of `observation_id`s entering the pixel/OCR-rate and conflict-count denominators |
| `supplements[]` | Supplement ids entering the `supplement_accessibility` denominator |

**Hard rule**: no stage may **consume upstream artifacts not declared in `executed_stages[]`**.
This is a mandatory check item of the §11 lint.

### 7.2 coverage_breakdown · coverage detail

```json
{
  "coverage_breakdown": {
    "resolved_fields": ["population.subjects", "declarations.informed_consent"],
    "unresolved_required_fields": [
      {"field_path": "declarations.ethics_statement", "status": "parse_failed",
       "reason_ref": "SYS-007"}
    ],
    "unreadable_assets": [],
    "inaccessible_supplements": ["S1"],
    "scope_denominators": {
      "required_fields_total": 3,
      "assets_total": 0,
      "supplements_total": 1
    }
  }
}
```

**Rules**

1. Entries of this block are **not findings**: they do not enter `issue_clusters[]` and do not affect `manuscript_risk_score`.
2. The sum of `resolved_fields[]` and `unresolved_required_fields[]`
   **must** equal `scope_denominators.required_fields_total`.
3. The `reason_ref` of `unresolved_required_fields[]` points to a `system_limitation.id`
   or `extraction_signal.id`; fields with `status: not_reported` **count as resolved** and go into `resolved_fields[]`.

---

## 8. Scoring Contract

The three metrics **are not substitutes for one another and are output separately**; the report must not merge them into a single number.
It is **forbidden** to call the manuscript risk score a "confidence".
The current weights, category caps, band thresholds, penalty coefficients, and the `0.5` warning threshold are all **initial expert parameters
not calibrated on a corpus**. What this section guarantees is deterministic recomputation, not empirical calibration; the report must not present scores as probabilities,
validated measurements of manuscript quality, or accept/reject cutoffs.

### 8.1 manuscript_risk_score · manuscript risk score (0–100)

Scoring uses the `issue_clusters[]` of §9.3 as the unit (preventing one issue from being split into multiple findings to inflate the score).
Each cluster is scored only under the `category` of its `representative_finding`; `categories[]` is for display only —
the same cluster must not score under multiple categories:

```
Per-cluster weight w: critical 25 / major 10 / minor 3 / info 0
  (take the highest severity within the cluster, counted once)
Cumulative cap per category: 30
manuscript_risk_score = min(100, Σ_category min(30, Σ_cluster w))
```

It does **not** rise because a PDF is unreadable or parsing failed — that belongs to coverage and confidence.

**partial semantics**

```json
{
  "manuscript_risk_score": {
    "value": 22,
    "partial": true,
    "executed_modules": ["M6"],
    "skipped_modules": ["M2", "M3", "M4", "M5", "M7"],
    "comparable_to_full_review": false,
    "band": "partial_not_classified",
    "priority_manual_review": false,
    "threshold_caveat": "Band thresholds are unvalidated initial heuristics and must not be presented as an automated accept/reject decision."
  }
}
```

- Whenever `executed_modules` does not cover all six review modules, `partial` **must** be `true`.
- A score with `partial: true` is **forbidden** from being compared side-by-side or ranked against any other report's risk score, including
  partial↔partial and partial↔`full_review`; both the report and the JSON must carry
  `comparable_to_full_review: false`, and `band` is fixed at `partial_not_classified` —
  the full-review bands must not be applied.
- Only when `executed_modules` covers exactly M2–M7 may `partial` be `false` and
  `comparable_to_full_review` be `true`, with `band` generated per the table below.
- When `executed_modules` is an empty array, this item **must not be output** (see SKILL.md §1 mode constraints).

**The bands below apply only to full reviews with `partial: false`, and only as a screening signal**
(thresholds are not empirically validated; the report must say so):

| Score | Label |
| --- | --- |
| 0–19 | `routine_review` |
| 20–49 | `clarification_needed` |
| 50+ | `major_revision_suggested` |

When any `critical` cluster appears, regardless of score, `priority_manual_review = true`.

### 8.2 extraction_coverage · extraction coverage (0.0–1.0)

**All denominators come from `execution_scope` (§7.1)**; using a full-text denominator to evaluate a single-figure task is forbidden.

```
field_resolution_rate
  numerator   = |fields in execution_scope.fields with applicability=applicable ∧ requiredness=required
          ∧ status ∈ {reported, not_reported}|
  denominator = |fields in execution_scope.fields with applicability=applicable ∧ requiredness=required|
  (status ∈ {ambiguous, conflicting, parse_failed, unresolved} counts as unresolved)
  (fields with applicability = not_applicable or applicability_uncertain enter neither numerator nor denominator)
  denominator 0 → 1.0 (same rule for the two sub-rates below; e.g. interpreting a single figure with no unconditionally required fields in scope)

asset_readability_rate
  numerator   = |readable assets in execution_scope.assets|
  denominator = |execution_scope.assets|
  denominator 0 → 1.0

supplement_accessibility
  numerator   = |available items in execution_scope.supplements|
  denominator = |execution_scope.supplements|
  denominator 0 → 1.0

extraction_coverage = 0.60 × field_resolution_rate
                    + 0.25 × asset_readability_rate
                    + 0.15 × supplement_accessibility
```

Each sub-rate's `rate` and the three final decimal scores are computed from the **unrounded numerators/denominators**, rounded at the end to
three decimal places; do not chain-multiply the already-displayed three-decimal sub-rates. `manuscript_risk_score` stays an integer.

**The report must give explicit numerators and denominators**, not just the weighted result:

```json
{
  "extraction_coverage": 0.78,
  "field_resolution": {"resolved": 12, "total": 15, "rate": 0.80},
  "asset_readability": {"resolved": 6, "total": 8, "rate": 0.75},
  "supplement_accessibility": {"resolved": 0, "total": 1, "rate": 0.0},
  "recommended_field_coverage": {"resolved": 4, "total": 7, "rate": 0.571}
}
```

`recommended_field_coverage` is an **optional** side metric counting fields with
`requiredness = recommended`; it does **not** enter the `extraction_coverage` weighting.

### 8.3 confidence · two mutually exclusive metrics

**At least one review module ran** → output `review_confidence`;
**none ran** (`structured_extraction`, `figure_analysis / interpretation_only`)
→ output `output_confidence`. **The two must never be output together.**

**`output_confidence`** (no review conclusion exists; reflects only the robustness of the extraction itself):

```
pixel_share = |ids in execution_scope.observations with source_type = pixel_estimated|
              / max(1, |execution_scope.observations|)
ocr_share   = |ids in execution_scope.observations with derivation.ocr_used = true|
              / max(1, |execution_scope.observations|)

Q_out = max(0, 1 − 0.30 × pixel_share − 0.20 × ocr_share)
output_confidence = extraction_coverage × Q_out
```

**`review_confidence`** (the system's strength of support for its own review conclusions):

```
pixel_dependency_rate = |findings whose evidence_refs link to an in-scope pixel_estimated observation|
                        / max(1, |total findings|)
ocr_dependency_rate   = |findings whose evidence_refs link to an in-scope ocr_used=true observation|
                        / max(1, |total findings|)
low_conf_finding_rate = |findings with review_confidence = low| / max(1, |total findings|)

Q = max(0, 1 − 0.30 × pixel_dependency_rate
              − 0.20 × ocr_dependency_rate
              − 0.10 × low_conf_finding_rate)
C = max(0, 1 − 0.10 × min(|key_data groups with status=conflicting and unresolved|, 5))

review_confidence = extraction_coverage × Q × C
```

**The linking algorithm is fixed as follows**: first obtain the in-scope observations via `execution_scope.observations[]`,
then intersect each observation's `provenance.evidence_ref` with each finding's `evidence_refs[]`; a non-empty intersection
means the finding depends on that observation. An observation id that appears in both `structured_result` and
`figure_records` counts once; the duplicated copies' `value` and `provenance` must be exactly identical.
`total findings` is the length of `all_findings[]`. The conflict count tallies only
`key_data.status = conflicting` groups containing at least one in-scope observation.

**Computability guarantee**: every variable above is directly computable from already-declared fields —
`provenance.source_type` (§2.3), `provenance.derivation.ocr_used` (§2.3),
`finding.review_confidence` (§6.1), `key_data.status` (§5.3).
Defining scoring variables that cannot be derived from the schema is **forbidden**.

When `review_confidence < 0.5`, the first screen of the report must warn:
"This review's evidence base is weak; conclusions are for reference only."

---

## 9. Routing Priority, Aggregation, and Clustering

### 9.1 Applicability routing priority (highest to lowest, stop at first hit)

```
1. Experiment-level type rules   dedicated rules of design_components[].type for that experiment_id
2. Article-level dedicated rules dedicated rules of article_design.primary_design.type (e.g. case_report)
3. Family-level rules            rules of article_design.primary_design.family
4. Default rules                 the generic field checklist
```

The field checklists and rules at each level are in `01-structured-extraction.md §5`.
**Dedicated rules override family-level rules**: `case_report`'s `not_applicable(randomization)`
overrides the generic requirement of the `human_observational` family.

### 9.2 Stage-local artifacts and final aggregation

**Every array has exactly one producer.** Same-named arrays across stages are always split into stage-local arrays,
then merged by a single aggregator — this addresses the root cause of the old contract's "one artifact, one producer" being violated.

`execution_scope` is not a Stage 5 artifact: it is initialized by the execution-planning step before Stage 1; when encountering a conditional stage,
the planning step must first add that stage to `executed_stages[]` before the stage may read upstream artifacts. Stage 5 only reads it and
writes it verbatim into the final report; it must not rebuild or rewrite execution history.

| Stage-local array | Producer |
| --- | --- |
| `stage1_system_limitations[]` | Stage 1 |
| `stage2_system_limitations[]` | Stage 2 (M1) |
| `stage3_system_limitations[]` | Stage 3 (Figure Parser) |
| `stage3b_system_limitations[]` | Stage 3b |
| `external_system_limitations[]` | X1 (`stage_3c_external_validation`) |
| `m1_extraction_signals[]` | Stage 2 (M1) |
| `stage3_extraction_signals[]` | Stage 3 (image-integrity audit) |
| `merge_extraction_signals[]` | Stage 3b |
| `external_validation_signals[]` | X1 (`stage_3c_external_validation`) |
| `m2_findings[]` … `m7_findings[]` | The corresponding review module |

| Aggregated artifact | **Sole aggregator** | Composition |
| --- | --- | --- |
| `all_system_limitations[]` | **Stage 5** (the output-assembly step in non-`full_review` modes) | The four Stage 1/2/3/3b arrays + optional `external_`, concatenated in ascending id order |
| `all_extraction_signals[]` | Same as above | `m1_` + `stage3_` + `merge_` + optional `external_validation_` concatenated |
| `all_findings[]` | **Stage 5** | The six arrays `m2_`…`m7_` concatenated |
| `issue_clusters[]` | **Stage 5** | §9.3 applied to `all_findings[]` |

**Abolished redundant arrays**: `source_conflict_signals[]`, `unresolved_evidence_links[]`,
`extraction_quality_findings[]`. See §10 for migration.

### 9.3 Deduplication and clustering (Stage 5, fixed order)

1. **Sub-clusters within a module** — findings within the same module with the same `category` and the same **primary anchor** join the same sub-cluster.
   **Primary anchor definition**: the evidence resolved from `evidence_refs[0]`, comparing its locator's
   `figure`+`panel` (when a figure exists), or `paragraph_id` (when not), or `table`; when none of these locators exists,
   or the evidence is `absence`, fall back to comparing `evidence_refs[0]` itself.
   Keep the highest-`severity` member as the representative; on a severity tie, take the lexicographically smallest finding id;
   the other ids go into the representative's `related_findings[]`. **This step does not delete, merge, or rewrite `all_findings[]`**;
   otherwise §9.2's "six local arrays concatenated in order" and score recomputation would lose their raw input.
2. **Cross-module clustering** — findings from different modules hitting the same primary anchor with overlapping semantics form one `issue_cluster`.
   Keep the highest-`severity` one as the cluster representative; on a severity tie, take the lexicographically smallest finding id.
   **Do not report the same issue six times.**
3. **Cluster-level evidence union** — `issue_cluster.evidence_refs[]` takes the union of all members' `evidence_refs[]`,
   deduplicated by id; do not write back to or rewrite any finding's `evidence_refs[]`.

```json
{
  "cluster_id": "CL-002",
  "representative_finding": "M4-003",
  "member_findings": ["M4-003", "M2-011"],
  "categories": ["power_and_sample_size", "internal_inconsistency"],
  "max_severity": "major",
  "anchor": {"figure": "3", "panel": "B"},
  "evidence_refs": ["EV-018", "EV-019", "EV-020"]
}
```

`issue_clusters[]` is the sole scoring unit of §8.1.

---

## 10. Migration Table (old contract → new contract)

**No backward-compatible aliases are retained.** Old fields are rewritten per the table below, then deleted.

| Old form | New form | Notes |
| --- | --- | --- |
| `extraction_quality_findings[]` of `ambiguous_extraction` | `extraction_signal` type `ambiguous_extraction` | §6.2 |
| `extraction_quality_findings[]` of `required_field_unresolved` | `coverage_breakdown.unresolved_required_fields[]` | §7.2, non-record |
| `source_conflict_signals[]` | type `source_value_conflict` in `merge_extraction_signals[]` | §9.2 |
| `unresolved_evidence_links[]` | `target` metadata of signal `claim_without_resolved_evidence_link` | §6.2 rule 3 |
| Signal type `parse_failure` | `system_limitation` (category `parse_failed`) | §6.3; value removed from the signal enum |
| Inline `evidence[]` object arrays | `evidence_refs[]` + top-level `evidence_registry` | §1.4 |
| Inline `provenance.locator` | `provenance.evidence_ref` | §2.3 |
| `source_type: "text"` | `explicit_main_text` | §2.3 |
| `source_type: "table"` | `explicit_table` | §2.3 |
| `source_type: "figure"` / `"figure_caption"` | `explicit_figure_caption` | §2.3 |
| `source_type: "figure_axis"` | `axis_readable` | §2.3 |
| `source_type: "figure_pixel"` | `pixel_estimated` | §2.3 |
| `"value": "40–50"` | `{"type": "interval", "low": 40, "high": 50}` | §2.1 |
| `"value": 12.4` | `{"type": "point", "number": 12.4}` | §2.1 |
| `status: parse_failed` + `pending_visual_resolution: true` | `status: unresolved` + `resolution_state` block | §4 |
| Flat single-value `key_data` object | Observation group (`observations[]`) | §5.2 |
| `evaluation_matrix.min_group_n` integer | `group_sizes[]` array | `01-…md §11.4` |
| `reporting_completeness: "not_applicable"` | `not_assessed` | §3.5 |
| Absolute source order "main text > table > caption > axis > pixel" | Two-level classification + §5.5 ordered criteria | §5.5 |

---

## 11. Contract Lint Checklist

**Run this selftest item by item before outputting any structured content; failing any item makes the output invalid.**

```
[ ] All enum values legal (source_type 5 values / extraction_method 6 / status 7 /
    applicability 3 / requiredness 3 / severity 4 / signal type 15 /
    system_limitation category 12 / key_data status 6 / numeric type 5)
[ ] All internal §x.y references resolve to sections that actually exist in this repository
[ ] Every evidence_ref / evidence_refs[] resolves to exactly one entry in evidence_registry
[ ] Every observation_refs[] resolves within the corresponding key_data.observations[]
[ ] Every array artifact has a sole producer or sole aggregator declared in §9.2
[ ] No stage consumes artifacts outside execution_scope.executed_stages[]
[ ] structured_result_v2 contains no status = "unresolved" and no non-null resolution_state
[ ] structured_result_v2 contains no key_data.status = "pending_visual_resolution"
[ ] No system_limitation carries severity
[ ] No finding has module M1
[ ] Every finding's evidence_refs[] is non-empty
[ ] Every finding with severity >= major has a non-empty manual_review.action
[ ] No evidence with type = "absence" has a quote field
[ ] All type = "external" evidence is created by X1, carries a response hash/version, and contains no credentials or manuscript locator/quote
[ ] Findings citing external evidence anchor first on present evidence and include both present + external
[ ] X1 failures produce only external_* system_limitations, never mismatch signals or findings
[ ] All numeric values are §2.1 numeric objects; no bare numbers, no string ranges
[ ] All pixel_estimated values satisfy the five mandatory constraints of §2.4
[ ] All provenance carries derivation, and the source_type × extraction_method combination is legal
[ ] All coverage and confidence denominators come from execution_scope
[ ] Modes that ran no review module output neither review_confidence nor manuscript_risk_score
[ ] manuscript_risk_score.partial = true whenever executed_modules does not cover the six review modules
[ ] No partial risk score is compared side-by-side or ranked against any other report's risk score
[ ] No coverage_breakdown entry is called a finding
[ ] resolved_fields + unresolved_required_fields = scope_denominators.required_fields_total
```
