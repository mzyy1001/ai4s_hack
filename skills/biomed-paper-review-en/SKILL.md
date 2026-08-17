---
name: biomed-paper-review-en
description: Structured extraction and review assistance for biomedical papers (PDF / JATS XML / plain text). Extracts a reusable structured fact table - design, subjects, interventions, endpoints, key values, claims, declarations - each field with status and source quote; parses figures, reading values from original images with figure/panel/page locators. Reviews six dimensions - macro logic, methods, statistics, figure/table standards, ethics and animal welfare, conclusion-evidence match - recomputing manuscript numbers deterministically and validating references, registrations, cell lines, and identifiers against authoritative databases; tool failures become system_limitation, not manuscript faults. Outputs graded findings traceable to source, coverage and confidence scores, prioritized review advice. Modes: full review / structured extraction / figure analysis / targeted check. Use to pre-screen manuscripts, extract structured data, validate identifiers, check statistics or ethics, or judge conclusion overreach.
---

# Biomedical Paper Review Assistance Skill

## 0. You are the orchestrator, not the reviewer

**You do not do the item-by-item review yourself.** Your job is to split the review
**into multiple independent subsessions**, each of which reads the same paper with
**its own review objective and its own single rulebook**, and finally you consolidate
everything into a contract-conformant report.

### 0.0 The one and only architectural axiom

> **What the layers isolate is the "review objective and reasoning context", not the "paper body".**

The bare model is already a strong reviewer on its own. Cramming five thousand lines of
rules into a single context crowds out attention (in real runs, only one of eight rulebooks
was actually read), so **the objectives must be separated**: one subsession, one role,
one rulebook, one clean reasoning context.

But **the body text must not be sliced along with them**. A three-condition test on the
same real paper, same model, same full text: bare model (full text + open-ended prompt)
**63 findings including 2 critical**; the old architecture (finding layer compressed into
candidates → specialists got only evidence packs) 43 findings, **0 critical**, and missed
one of the bare model's two strongest findings; this architecture (every layer gets the
full text) **96 findings including 6 critical**, recovering 6 of those 7 deep issues.

The failure mechanism is **double compression, with the second pass determined by the first**:
the finding layer compresses the paper into a candidate list, and the evidence packs then
pull body-text snippets according to that list — passages nobody flagged (construct
schematics, cloning descriptions, strain provenance) are read by no layer at all, and once
missed they are structurally unrecoverable. Moreover, the "isolation" was fake to begin
with: the statistics pack already covered 71% of the full text, the claims pack 52% —
the recall price was paid without any real isolation gained.

**Therefore: the full text is open to every layer that needs it; the only things isolated
are the objective, the rulebook, and the reasoning context.**

### 0.1 Create subsessions with the `task` tool (this is the core mechanism of this Skill)

Every stage must genuinely create an **independent subsession** via the `task` tool:

```
task(
  subagent_type = "general",        ← use the built-in general; no custom agent file needed
  description   = "<stage name>",
  prompt        = "<the stage's complete self-contained instructions + all materials it needs>"
)
```

**Empirically confirmed — do not doubt this again**: `subagent_type: general` creates a
subsession that returns an independent `sessionId`; multiple task calls issued in one
reply execute concurrently; the same `task_id` can be continued and the subsession
remembers the previous round; without a model override the subsession inherits the main
session's model; a subsession cannot see anything not explicitly passed in; a subsession
can run bash and read files.

**Three hard rules**:

1. **Do not specify a model override.** Subsessions must inherit the main session's model,
   otherwise evaluation comparisons are invalidated.
2. **The subsession's prompt must be self-contained.** It cannot see your context; anything
   you do not write into the prompt does not exist for it.
3. **Give the full text to every layer that needs it.** The body text is not the scarce
   resource — attention is. Isolation comes from "one subsession has one objective and one
   rulebook", not from rationing the body text.

### 0.2 Execution graph

```
Main session (you)
│
├── L0  task(general) → Global review    **full text + minimal prompt; no rulebase, no schema, no checklist**
│                                      ← must run first; nothing may touch the paper until it finishes
│                                      produces G-01…G-nn, entered directly into the ledger
│
├── L0b task(general) → Mapping & routing  full text + mapping instructions (**does NOT hunt for problems**)
│                                      produces paper_map / claim_map / experiment_map
│                                      + figure inventory + identifier harvest + which modules to open
│
├── L1  task(general) → M2 macro logic     **full text** + 02-macro-logic.md      + the G items routed to it
│      task(general) → M3 experimental methods  **full text** + 03-experimental-methods.md + …
│      task(general) → M4 statistics       **full text** + 04-statistics.md      + …
│      task(general) → M5 figures          **full text** + 05-figures-and-charts.md + …
│      task(general) → M6 ethics           **full text** + 06-ethics-compliance.md + …
│      task(general) → M7 conclusions      **full text** + 07-conclusions-discussion.md + …
│
├── L2  deterministic tools + X1 external validation   run by the main session itself; never delegated
│
├── L3  continue each specialist on the same task_id   feed the deterministic evidence, have them re-deliberate
│
├── L4  task(general) → reconciliation subsession   **full text** + all specialist outputs + G items + tool signals
│                                      one extra duty: audit whether any G item vanished without explanation
│
└── L5  main session does contract normalization and report rendering
```

The L0 prompt must contain no rulebase, no contract, no schema, no checklist of any kind —
it IS the bare-model condition itself. **This guarantees that this Skill's floor is the
bare model**: all later layers may only add on top of it, or refute a specific item with
stated reasons — they can never silently shrink it.

### 0.3 Parallel execution (subsessions are mutually isolated; whatever can run in parallel must)

Subsessions **cannot see each other**, so "L0 stays clean" is achieved by **keeping its own
prompt clean**, not by making the others wait for it. There are only three real dependencies:

```
L0 ∥ L0b                       parallel: invisible to each other, no contamination
   ↓ (after both return)
M2 ∥ M3 ∥ M4 ∥ M5 ∥ M6         parallel: the five modules have no inter-dependencies
   ↓
M7                              serial: it consumes the other modules' conclusions
   ↓
L2 tools (main session, multiple commands concurrently)
   ↓
Continuation re-deliberation of M2…M6   parallel: same task_id, mutually independent
   ↓
L4 reconciliation → L5 rendering        serial
```

**How to actually parallelize**: issue **multiple `task` calls at once in the same reply**;
the runtime executes them concurrently. Sending one, waiting for it, then sending the next
degrades into serial execution. Empirically: launching the five specialists serially takes
several times as long as in parallel, and there are no dependencies between them.

Critical path ≈ `max(L0, L0b)` + `max(M2…M6)` + `M7` + tools + `max(continuations)` + `L4` + `L5`.

---

## 1. L0 · Global review (the whole paper, minimal constraints)

```
task(subagent_type="general", description="L0 Global Review",
     prompt = minimal prompt + full paper text)
```

**This layer must be the cleanest**: cleanliness comes from its own prompt containing no
rules and no checklists, not from making other layers wait for it. **It may be launched in
parallel with L0b** (subsessions cannot see each other, so no contamination).

Put in the prompt **only**: the full paper text, the figure inventory, and the passage below.
**Strictly forbidden**: rulebase, contract, schema, candidate-type enumerations, any form of
checklist — **any checklist becomes a ceiling**. Empirically: when the finding layer carried
a checklist, its 39 candidates mapped almost one-to-one onto checklist items, while the bare
model's two strongest findings on the same paper never entered the pool. The checklist was
meant as a floor and became a ceiling in practice.

The full instruction text (do not add anything):

> You are a senior peer reviewer in this field. Read the paper in full and **list every
> issue** you would raise in a review report.
>
> Scientific logic, experimental design, statistical methods, figure and data presentation,
> ethics compliance, the match between conclusions and evidence, reporting completeness —
> any aspect. **Exhaust every problem you can find.**
>
> Every item must be pinned to a specific location and specific content (section / figure /
> exact wording); no vague generalities. Give each item a severity:
> `critical` / `major` / `minor` / `info`.
> Raise uncertain items too, marked `confidence: low`.
>
> Output a JSON array, each item of the form:
> `{"id":"G-01","statement":"…","locations":["Methods sec006","Fig 3A"],
>   "severity":"major","confidence":"high"}`

**This IS the bare-model condition itself**, so this Skill's floor is nailed to the bare
model. G items go into the `candidate_resolution_log` **immediately**; from then on they
may only be explicitly dispositioned, never evaporate (see §6).

### 1.1 Why there is no longer a "finding layer"

The old finding layer did **substantive review** and **mapping & routing** at the same time,
and the structuring that mapping requires crowds out the openness that review requires.
They are now split: substantive review moved up to L0 (unconstrained, therefore stronger),
mapping & routing moved down to L0b (purely mechanical, therefore cheaper).

**Compliance checklists need no separate channel either** — the M2/M4/M6 rulebases ARE those
checklists. Empirically: the checklist channel of the dual-channel design actually bundled
up and lost "no exact P values / test statistics / CIs / effect sizes anywhere in the text",
whereas the M4 rulebase covers it natively. **Checklists belong to the rulebase, not to the
finding layer.**

## 1b. L0b · Mapping & routing (does not hunt for problems)

```
task(subagent_type="general", description="L0b Map & Route",
     prompt = mapping instructions + full paper text)
```

> You are **not a reviewer**. In this round do not raise any review comments and do not
> evaluate the paper's quality. You do exactly three things:
>
> 1. **Mapping**: `paper_map` (sections and their roles), `experiment_map` (per experiment:
>    model / groups / intervention / endpoints / timepoints / n), `claim_map` (each claim's
>    exact wording, location, and the Results/figures supporting it), and the figure and
>    table inventory.
> 2. **Identifier harvest** (for the deterministic tools): reference DOIs/PMIDs,
>    registration numbers, cell line names, antibody catalog numbers and RRIDs,
>    gene/protein symbols, accession numbers, species and strains, dose-unit pairs.
> 3. **Routing recommendation**: per the trigger table in §2, state which modules to open
>    and the reason for each, and which not to open and why.
>
> Output JSON: `paper_map`, `experiment_map`, `claim_map`, `figure_inventory`,
> `identifier_harvest`, `routing_plan[]`.

L0b's output is **a map for the tools and the router**, not a candidate list. It produces
no findings and no severities.

## 2. Routing: deciding which subsessions to open

**Do not run all six modules by default.** Take the union per the table below; both running
and not running a module must have its reason stated in the report.

| Trigger source | Rule |
| --- | --- |
| Study design | RCT / cohort → M4, M6, M7; animal → M3, M6; in-vitro cell → M3; meta-analysis → M2, M4, M7 |
| Candidate routing | open whichever module `suggested_route` points to |
| Tool signals | table/p-value/CI inconsistency → M4, M2; missing ethics items → M6; identifier anomalies → M3 |

| Module | Rulebase | Materials it receives |
| --- | --- | --- |
| M2 macro logic | `references/02-macro-logic.md` | **full text** + maps + index |
| M3 experimental methods | `references/03-experimental-methods.md` | **full text** + maps + index |
| M4 statistics | `references/04-statistics.md` | **full text** + maps + index |
| M5 figures | `references/05-figures-and-charts.md` | **full text** + figure inventory + image files (if readable) |
| M6 ethics | `references/06-ethics-compliance.md` + `06b-animal-model-ethics-enhancement.md` | **full text** + maps + index |
| M7 conclusions | `references/07-conclusions-discussion.md` | **full text** + maps + the other modules' conclusions |

The "index" in the third column is only a starting-point hint; **it is not a boundary** (see §3.1).

The complete routing table is in `references/00-routing.md`.

**The metric is not "read all eight rulebooks"** — it is routing recall: for the modules
this run does execute, not a single corresponding rulebook may be missed. Not reading the
ethics rulebase for a pure bioinformatics paper is correct, not a defect.

## 3. L1 · Specialist subsessions (full text + their one rulebook)

One `task(general)` per module. The prompt must be self-contained and include five things:

```
① Role and boundary instructions (see below)
② **The full paper text** — no longer an evidence pack
③ Index: the module's list of relevant locations (a starting point, not a boundary)
④ L0b's maps (paper_map / experiment_map / claim_map)
⑤ The G items routed to it + any existing tool signals
```

**③ has been demoted from "substitute" to "index"**: the old evidence pack was a substitute
for the full text; now it is merely "these locations are known to be relevant, start there".
**The specialist is obligated to read the full text** and must not treat anything as
nonexistent merely because it is not in the index.

Role instructions (written into every specialist prompt):

> You are the review specialist for **<module>**.
> **Read the rulebase first**: `<skill dir>/references/<corresponding file>`
> (use the read tool; path in the table above).
>
> **The rulebase is your lens; the full text is your object.** You have the entire paper:
> if you need to compare across sections, revisit the construct descriptions in Methods,
> or check figure captions against the body text, go read them directly.
> Do **not** give all your attention to the rulebase without reading the paper, and do
> **not** read the paper without applying the rulebase — your value is precisely "viewing
> the whole paper through this rulebook", which the global-review layer cannot do.
>
> You are also given **the items the global review (L0) has already raised that fall within
> your domain**. For each one you must give an explicit verdict: `confirm` (and complete
> the evidence and grading) / `refine` (correct the wording or grading, with reasons) /
> `refute` (reject it — you **must** provide counter-evidence) / `out_of_scope` (not your
> domain). **You may not silently skip any item.** You may refute one, but you may not
> make it disappear.
>
> Beyond that, **proactively add** problems in your domain that L0 did not raise — that is
> the reason you exist.
>
> Tool signals are deterministic facts but **carry no severity**: whether they constitute a
> problem, and how serious, is your judgment in light of the impact.
> You do **not** do deduplication, clustering, final grading, or report rendering.
> Output JSON: `provisional_findings[]` (with category / severity / statement /
> evidence_locations / source: `specialist_rule` | `confirms_global`),
> `global_verdicts[]` (verdict and reasoning for every G item), `requested_tool_checks[]`.

### 3.1 How the index is cut (a starting point, not a boundary)

| Module | Index points to |
| --- | --- |
| M4 statistics | statistical-methods paragraphs, related Results, tables, caption statistics, sample sizes, tests, p values, CIs |
| M3 experimental methods | the entire Methods section, reagents and equipment, sample provenance, construct and cloning descriptions, strain provenance |
| M5 figures | figure captions, first in-text citation of each figure, related Results |
| M6 ethics | study-design summary, subject/animal descriptions, ethics statements, informed consent, registration information |
| M7 conclusions | exact claim wording, the Results supporting it, associated tables/figures, follow-up duration, study population, limitations |
| M2 macro logic | `paper_map` + `claim_map` + reference list and in-text citation locations |

### 3.2 "Could not obtain" and "the manuscript did not report" are still two different things

Specialists now have the full text, so **the excuse "the material wasn't in my pack" is gone**.
But the other class of limitation still exists and must be logged truthfully: images
unavailable or unreadable, supplementary materials not provided, external endpoints
unreachable. All of these produce a `system_limitation` and must **not** be treated as
"the manuscript did not report it", nor as "the manuscript has no problem".

## 4. L2 · Deterministic validation and X1 external validation (you run these yourself; never hand them to a subsession)

**Proactive scanning is not optional.** The real uplift usually comes from checks the bare
model would never think to perform — run them as soon as a structured object is parsed,
**without waiting for any candidate**:

| Parsed | What to run |
| --- | --- |
| A table of mutually exclusive, exhaustive category counts | `statistical_forensics`'s `table_total` |
| "count + percentage" | `count_percentage` |
| "mean + integer scale + n" | `grim` |
| test statistic + df + p | `test_statistic_p` |
| point estimate + CI | `ci_estimate` |
| cell line name / NCT registration number / reference DOI / human gene symbol | `external_figure_validation` |
| image files | `figure_integrity_audit` |
| dose-unit pairs | `normalize_biomed_units` |
| animal experiments (species/anesthesia/euthanasia/3R) | `animal_model_compliance` (rules in `references/06b-animal-model-ethics-enhancement.md`; output goes to M6) |

Every invocation must land on exactly one terminal state: `executed` / `not_applicable` /
`failed` / `skipped`; the last two require a reason. **No tool that should run may vanish
silently.** A non-zero exit code counts as not completed — log a `system_limitation`;
**interpreting empty stdout as "no problem found" is forbidden**.

**Write intermediate files to the current working directory; writing to `/tmp` is forbidden** —
in real runs this was rejected by the runtime with
`permission requested: external_directory (/tmp/*); auto-rejecting`,
severing the entire forensic chain. Use stdin whenever possible.

```bash
if [ -z "${BIOMED_REVIEW_SKILL_DIR:-}" ]; then
  BIOMED_REVIEW_SKILL_DIR="$(git rev-parse --show-toplevel)/skills/biomed-paper-review-en"
fi
export BIOMED_REVIEW_SKILL_DIR

printf '%s' '[{"check":"table_total","counts":[12,18],"declared_total":28,"categories_exhaustive":true,"target":"Table 1"}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/statistical_forensics.py" --input -

printf '%s' '[{"check":"cell_line","cell_line":"MDA-MB-435","evidence_refs":["EV-001"]}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/external_figure_validation.py" --input -

python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/ethics_compliance_check.py" --input structured_result_v2.json
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/animal_model_compliance.py" --input structured_result_v2.json  # animal-study papers only
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/figure_integrity_audit.py" --input figures
python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/normalize_biomed_units.py" --compare 'mg/mL' 'g/L'
printf '%s' '[{"check":"accession","accession":"NCT123","database":"clinicaltrials"}]' |
  python3 "${BIOMED_REVIEW_SKILL_DIR}/scripts/sequence_identifier_audit.py" --input -
```

### 4.1 L3 · After tool results arrive, **continue the same specialist subsession**

This is the most valuable link in the architecture: let the specialist **re-deliberate its
own verdicts after seeing the deterministic evidence**.

```
task(task_id = <that specialist subsession's id>,
     prompt  = "Deterministic validation results follow: <tool output>.
                Re-deliberate your previous round's verdicts accordingly: which do you
                confirm, which do you withdraw, and should any severity be adjusted?")
```

Continue with the **same task_id**; the subsession remembers the previous round, so
**there is no need to resend the full text** (which is also why continuation is far cheaper
than opening a new session).

## 5. L4 · Reconciliation subsession (full text + all outputs)

```
task(subagent_type="general", description="Reconciliation", prompt = …)
```

Put in the prompt: **the full paper text**, `paper_map`, `experiment_map`, `claim_map`,
all of L0's G items, each specialist's `provisional_findings` and `global_verdicts`,
the tool signals, and `system_limitations`. **Do not include the full rulebase texts**
(they would crowd out the paper body).

### 5.0 High-output layers must write to disk and return only a pointer (lesson from real runs)

L4 simultaneously holds the full text, dozens of G items, and six specialists' outputs —
**its return payload will exceed the limit**: real runs produced `truncated: true`
(cut off after returning 42,049 characters). That time the orchestrator recovered from the
on-disk file with no data lost, but you cannot count on being that lucky every time.

**Therefore, any subsession whose output may exceed roughly 30,000 characters (L4 always;
L0 and the specialists often) must be instructed:**

```
Write the complete JSON to <working dir>/<stage name>.json.
In your reply give ONLY: the file path + a count summary (items per category)
+ a summary of the 3–5 most important items.
Do not inline the complete JSON in your reply.
```

The main session then reads that file with the read tool. **A truncated return = that layer
failed**; it must be rerun or recovered from the on-disk file — you must **not** carry a
truncated, incomplete output forward as if it were complete.

Instruction highlights:

> You have the entire paper and all specialist outputs. You have three tasks:
>
> **One: cross-section contradictions.** Check item by item:
> Abstract↔Results, Methods↔Results, Methods↔baseline table, Results↔Tables,
> Results↔Figures, Tables↔Discussion, Discussion↔Conclusion,
> **construct design↔attribution claims**, follow-up duration↔safety claims,
> study population↔extrapolation claims, registration record↔manuscript,
> references↔citation-validation results.
>
> Typical cases (all really happened): Methods says ASA I–III were enrolled while the
> baseline table shows only II/III; one p value in a table and a different one in the
> Discussion; 48-hour follow-up yet a claim of "no serious complications observed";
> the Discussion claims two genetic systems agree, but once aligned by age the adult-mouse
> results are exactly the opposite.
>
> **Two: merging and deduplication.** Merge duplicate items from different specialists
> about the same issue, keeping the more specific wording and localization.
>
> **Three: the G-item audit (not optional).** Check every one of L0's G items:
> does it have an explicit destination in the final results? If an item was ignored by all
> specialists (no `global_verdicts` entry covers it), **you must issue a verdict yourself**
> with clear reasoning; if it was `refute`d, check whether the counter-evidence holds.
> **No G item may disappear without explanation** — this is this layer's hard deliverable.
>
> Output `reconciled_findings[]`, `cross_section_findings[]`,
> `candidate_resolution_log[]`, `global_audit[]` (each G item's final destination and reason).

## 6. Candidate lifecycle and the **additivity guarantee** (hard requirements)

### 6.1 Every item must have a destination

L0's G items, specialists' new items, and tool/external-validation signals **all go into
the same single ledger**:

```
promoted_to_finding | merged | rejected | unresolved | blocked_by_system_limitation
```

- `rejected` **must** carry a `rejection_reason`
- `promoted_to_finding` must point to a `final_finding_id`; `merged` must point to `merged_into`
- **If the evidence cannot be located, record `unresolved`, never `rejected`** — that means
  we failed to locate it, not that the problem does not exist

Earlier implementations silently dropped valid issues between discovery and rendering;
this ledger exists to make any loss visible.

### 6.2 The additivity guarantee (this architecture's core promise)

> **Final results ⊇ the L0 global review's conclusions, minus exactly and only those
> explicitly refuted with stated reasons.**

Relative to the bare model, the Skill may only add, or subtract **with argumentation** —
it may never shrink out of thin air. As concrete checks, before rendering the report you
must self-verify:

1. Every G item has a terminal state in `global_audit[]`;
2. Every `rejected` item has a `rejection_reason`, and the reason is **counter-evidence**,
   not "no specialist mentioned it" or "outside my module's scope";
3. Any G item whose `severity` was downgraded must have the downgrade reason recorded;
4. If the final finding count is **lower than** the G-item count, the report must
   explicitly explain where the difference went.

**If any of the above cannot be satisfied, do not render the report** — write the gap
straight into `system_limitations` instead.

## 7. L5 · Contract normalization and report rendering (you do this yourself; never hand it to a subsession)

**Only at this step is the full contract applied**; before this, findings must not be
constrained by any schema:

```
evidence-register normalization → finding-schema normalization → deduplication → clustering
→ severity harmonization → confidence → coverage → report rendering
```

The complete contract is in `references/00-contracts.md`; machine validation is governed by
`schemas/*.json`; subsessions need only the minimal set in `references/00-runtime-contract.md`.

**Every finding is labeled with its origin**: `global_review` / `specialist_rule` /
`deterministic_tool` / `external_validation` / `cross_section_reconciliation` / `multiple`.

This distribution is **the sole basis for judging whether this architecture is worth it**:
findings that come only from `global_review` are what the bare model already had — **not
uplift**; only findings unique to the other four origins are **true uplift**.
If the uplift is small, the conclusion is to **trim the rulebase**, not to add more rules.

**`evidence_refs[]` must be item-specific** (contract §1.4.1): real runs produced 60
findings of which 57 shared the same set of 24 references — formally compliant, but with
auditability reduced to zero. Self-check before rendering:
**more than half the findings sharing an identical reference list = shotgun citation, and
must be narrowed.**

### 7.1 Runtime telemetry is mandatory

**Copy the field names from the table below verbatim; do not invent synonyms.** Lesson from
real runs: an old name like `candidate_count_discovery` was output while
`additive_guarantee_held` was omitted — the result was that **the additivity guarantee
actually held but was never machine-readably asserted**, which is as good as no proof.
Self-check before rendering: is every key below present? If one is missing, add it —
do not rename it.

Required keys: `child_sessions` `task_calls` `continuations` `modules_run`
`modules_skipped` `references_required` `references_read` `routing_recall`
`tool_execution_recall` `global_findings_count` `global_findings_confirmed`
`global_findings_refuted` `global_findings_unresolved`
`additive_guarantee_held` `findings_added_beyond_global`
`finding_origin_breakdown`

```json
{"runtime_utilization":{
  "child_sessions": 5, "task_calls": 6, "continuations": 1,
  "modules_run": ["M4","M6","M7"], "modules_skipped": {"M3":"no in-vitro/animal component"},
  "references_required": ["04-statistics","06-ethics-compliance","07-conclusions-discussion"],
  "references_read": ["04-statistics","06-ethics-compliance","07-conclusions-discussion"],
  "routing_recall": 1.0, "tool_execution_recall": 1.0,
  "global_findings_count": 63, "global_findings_confirmed": 58,
  "global_findings_refuted": 3, "global_findings_unresolved": 2,
  "additive_guarantee_held": true,
  "findings_added_beyond_global": 21,
  "finding_origin_breakdown": {"global_review":58,"specialist_rule":9,
    "deterministic_tool":3,"external_validation":6,"cross_section_reconciliation":3}}}
```

**If `child_sessions` is 0, the layering never actually happened** — that is an execution
failure, not "the architecture is ineffective", and it must be stated truthfully in the report.

**If `additive_guarantee_held` is false**, some G items evaporated inside the pipeline —
equally an execution failure; the report must state which items and at which layer they
got stuck.

---

## 8. Execution modes

Default is `full_review`. When the user only wants one figure or one number, you must
**not** auto-run the full review.

| Mode | Subsessions opened | risk_score | Confidence field |
| --- | --- | --- | --- |
| `full_review` | L0 + L0b + routed modules + reconciliation | full | `review_confidence` |
| `structured_extraction` | L0b mapping + extraction only (**L0 is NOT run**) | **not output** | `output_confidence` |
| `figure_analysis / interpretation_only` | figure parsing only | **not output** | `output_confidence` |
| `figure_analysis / figure_review` | L0b + M5 | partial | `review_confidence` |
| `targeted_check` | L0b + selected modules | partial | `review_confidence` |

**Only `full_review` runs L0.** Extraction and targeted checks do not need a global review —
running it would be a waste; but precisely for that reason, these modes **do not enjoy the
additivity guarantee of §6.2**, and the report must state this.

`review_confidence` and `output_confidence` are **mutually exclusive**. Partial scores must
never be compared side by side with `full_review` scores. Every mode must output
`execution_scope`, `coverage_breakdown`, `all_system_limitations[]`, and `runtime_utilization`.

## 9. Boundary statement (must be written into the report verbatim)

> This Skill automates and assists the foundational stages of paper review, including
> structured evidence extraction, figure interpretation, reporting-standard checks, and
> prioritization for human review. **It does not replace the scientific, statistical,
> clinical, or ethical judgment of qualified reviewers.** Any score produced by this Skill
> is a screening signal and does not constitute a decision to accept, reject, or publish.

**Evidence must be auditable**: every final finding must carry evidence of one of three
types — `present` (with a locator) / `absence` (search scope + search terms + result) /
`external` (endpoint, query, time, response hash).
**Never fabricate citations for content that does not exist.** But do not get the direction
backwards — the evidence requirement exists to **verify** findings, not to **reduce** them.

The M1 upstream extraction layer uses `references/01-structured-extraction.md`; it
**produces no findings** — its duty is to extract fields and verifiable identifiers for the
specialists and external validation to use.
