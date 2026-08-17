# Minimal Runtime Contract

> **This file is not a new source of truth.** `schemas/*.json` and `00-contracts.md` remain authoritative at all times.
> This file merely extracts from them **the minimal set the specialist channel must know to produce records**,
> so that a specialist does not have to read the twelve-hundred-line full contract just to write one interoperable record.
>
> On any conflict, `00-contracts.md` and the schemas win. If this file disagrees with them, this file is wrong.

## Why This Layer Exists

Measured in practice: the full contract is 1209 lines, and the eight references total roughly five thousand lines. In one full-pipeline trace
the model read only `00-contracts` and none of the other seven — not because it was lazy,
but because **it was asked to swallow the entire specification before finding any problems**, and its attention was already spent.

The contract's job is to **organize and validate problems already found**, not to fill the context before discovery.
Hence: use lightweight structures during the discovery phase, and apply the full contract only to final records.

## 1. Three Record Types — Never Confuse Them

| Record | Produced by | Has severity | Meaning |
| --- | --- | --- | --- |
| `finding` | M2–M7 | **Yes** | A manuscript-level issue; must have auditable evidence |
| `extraction_signal` | Stages 2/3/3b/3c and deterministic tools | **No** | A recomputable observation, handed to modules for judgment |
| `system_limitation` | Any stage | **No** | A limitation of **our** capability, never blamed on the manuscript |

**The easiest mistake to make**: an unreachable external source, a failed script, an unparseable input — all of these are
`system_limitation`, **never** a finding.
`parse_failed ≠ not_reported`: "we could not read it" is not "the manuscript did not report it."

## 2. Minimal Shape of a finding

```json
{
  "id": "M4-003",
  "module": "M4",
  "category": "sample_size_unjustified",
  "severity": "major",
  "description": "…",
  "evidence_refs": ["EV-012"],
  "manual_review": {"action": "…", "who": "statistician"}
}
```

- `severity` enum: `critical` / `major` / `minor` / `info`
- `evidence_refs[]` **must not be empty**; `major` and above must provide `manual_review.action`
- Evidence has exactly one canonical store: `evidence_registry`. Everywhere else, write only `evidence_refs[]`

## 3. Minimal Shape of evidence

Three types — choose by "what this piece of evidence is saying":

| type | Used for | Key constraints |
| --- | --- | --- |
| `present` | The manuscript **contains** this content | Must give `locator`; `quote` optional |
| `absence` | The manuscript **lacks** this content | Must give search scope and search terms; **`quote` and `locator` forbidden** |
| `external` | A fact from a public data source | Must give endpoint, query, retrieval timestamp, response hash |

> **Never fabricate a quotation for content that does not exist.** Forbidding `quote` on absence-type evidence exists precisely to prevent this.

## 4. Minimal Shape of an extraction_signal

```json
{
  "id": "SIG-042",
  "type": "table_total_mismatch",
  "target": "Table 1",
  "detail": "…",
  "evidence_refs": ["EV-007"],
  "routed_to": ["M4", "M2"],
  "produced_by": "stage_2"
}
```

**No severity.** A signal only states "the computation does not check out"; whether it constitutes a manuscript issue is for the module to judge.

## 5. Minimal Shape of a system_limitation

```json
{
  "id": "SYS-003",
  "category": "external_source_unavailable",
  "impact": "…validation not completed",
  "affected_modules": ["M3"],
  "recommended_action": "Re-run after recovery; until then, draw no conclusion about this claim",
  "produced_by": "stage_3c_external_validation"
}
```

**No severity.**

## 6. confidence Enum

`high` / `medium` / `low`.

- Visual estimation (`pixel_estimated`) is always `low` and must be written as an interval
- Use `review_confidence` after a review module has run, `output_confidence` when none has; **the two are mutually exclusive**

## 7. The Discovery Phase Is **Not** Bound by This Contract

Layer 1 discovery and Layer 2 specialist intermediates use lightweight structures
(`candidate_issue` / `provisional_finding`) and **need not** satisfy the evidence requirements above.
Only final records after Layer 4 must be fully compliant.

This is the heart of this architectural revision: **discover first with high recall, formalize afterward**.
Never drop an issue during discovery just because `evidence_refs` cannot be produced at that moment.

---

Full definitions are in `00-contracts.md`; machine validation follows `schemas/*.json`.
