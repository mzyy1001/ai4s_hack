# M6 Supplement · Animal Model Ethics Enhancement

**New capability**: Recognize animal models used, cross-check 3R principle compliance, detect welfare violations against international norms.

**Integration**: Runs as `animal_model_compliance.py` after `ethics_compliance_check.py`; both produce signals for M6 routing.

---

## 1. Scope

This enhancement extends M6 to:

| Task | Offline Capable | Notes |
|------|---|---|
| **Animal model extraction** | ✅ Text-based regex | Species, strain, age, procedures, anesthesia, euthanasia |
| **3R Principle audit** | ✅ Text search | Detects missing coverage of Replacement, Reduction, Refinement |
| **Welfare red lines** | ✅ Hard-coded patterns | Inhumane euthanasia, painful procedures without anesthesia, chronic distress, excessive numbers |
| **International norms check** | ✅ Offline | AVMA 2020, EU Directive 2010/63/EU, ARRIVE 2.0 |
| **Cross-paper animal tracking** | ❌ X1 only (MGI) | Placeholder for future MGI/Jackson Lab cross-reference |

---

## 2. Animal Model Extraction (M1 Enhancement via `animal_model_compliance.py`)

Automatically extracts from paper text:

```json
{
  "species": "mouse",
  "strain": "C57BL/6J",
  "age_or_weight": "8-10 weeks old",
  "numbers_per_group": {"extracted": [4, 4], "total_approx": 8},
  "procedures_applied": ["surgery", "behavioral_testing"],
  "anesthesia_used": "isoflurane",
  "analgesia_used": null,
  "euthanasia_method": "CO2",
  "humane_endpoints": "weight loss > 20%",
  "replacements_considered": true,
  "reductions_justified": true,
  "refinements_detailed": true
}
```

### Detection Methods

**Species**: Regex match against strain names (C57BL/6, Sprague-Dawley, Lewis, etc.)  
**Procedures**: Pattern search for keywords (surgery, injection, restraint, swim test, etc.)  
**Anesthesia**: Exact keyword match (isoflurane, ketamine, propofol, pentobarbital)  
**Euthanasia**: Regex for method (CO2, cervical dislocation, pentobarbital)  
**Humane endpoints**: Phrase matching (weight loss threshold, pain score, moribund)  
**3R Compliance**: Search for replacement/reduction/refinement keywords in methods + declarations

---

## 3. Signal Types Produced

### Signal Type 1: `ethics_requirement_unmet` (ETH-ANI-002 Enhancement)

**When**: Paper does not adequately explain 3R principle compliance

```json
{
  "type": "ethics_requirement_unmet",
  "target": "ethics.ETH-ANI-002",
  "detail": "[ETH-ANI-002] 3R Principle: Replacement(not_discussed); Reduction(not_justified); Refinement(not_detailed)",
  "three_rs_assessment": {
    "replacement_considered": false,
    "reduction_justified": false,
    "refinement_detailed": false,
    "issues": [
      ["Replacement", "not_discussed"],
      ["Reduction", "not_justified"],
      ["Refinement", "not_detailed"]
    ]
  },
  "routed_to": ["M6"],
  "produced_by": "animal_model_compliance"
}
```

**Severity**: Will be determined by M6 based on study complexity
- Minor: One of three 3R principles missing discussion
- Major: Two or more principles missing
- N/A if paper explicitly discusses all three

---

### Signal Type 2: `animal_welfare_violation` (NEW)

**When**: Paper describes acts clearly against international-recognized human morality

```json
{
  "type": "animal_welfare_violation",
  "target": "ethics.animal_welfare.inhumane_euthanasia_method",
  "severity_hint": "critical",
  "detail": "Paper reports cervical dislocation for C57BL/6 mice; international standards prohibit this without prior anesthesia",
  "welfare_violation": {
    "violation_type": "inhumane_euthanasia_method",
    "severity": "critical",
    "international_standards": ["AVMA 2020 Guidelines", "EU Directive 2010/63/EU"],
    "animal_details": {
      "species": "mouse",
      "strain": "C57BL/6J",
      "euthanasia": "cervical dislocation"
    }
  },
  "routed_to": ["M6"],
  "produced_by": "animal_model_compliance"
}
```

**Five red lines** (welfare violations):

| Violation | Severity | Trigger |
|-----------|----------|---------|
| **Inhumane euthanasia method** | critical | Cervical dislocation, decapitation, exsanguination for mice/rats without anesthesia |
| **Painful procedure no anesthesia** | critical | Surgery, tissue sampling, or disease induction without anesthesia/analgesia/humane endpoints |
| **Chronic distress no humane endpoint** | major | Stress paradigm, behavioral testing without predefined early-exit criteria |
| **Large group no reduction justification** | major | >100 animals used without sample-size/power justification |
| **No replacement justification** | minor | In vivo studies without discussing why alternatives unsuitable |

---

### Signal Type 3: `external_validation_candidate` (X1 Placeholder)

**When**: Animal strain/allele is recognized and ready for external cross-check

```json
{
  "type": "external_validation_candidate",
  "target": "ethics.animal_model_identity",
  "detail": "[X1 Candidate] Ready for MGI cross-check: mouse C57BL/6J",
  "x1_candidate": {
    "check_type": "mgi_mouse_model_identity",
    "species": "mouse",
    "strain": "C57BL/6J",
    "procedures": ["surgery", "behavioral_testing"],
    "ready_for": [
      "allele_identity_verification",
      "cross_paper_treatment_pattern"
    ]
  },
  "routed_to": ["M6"],
  "produced_by": "animal_model_compliance"
}
```

**What X1 will do when network available** (see Round 21 Proposal P3):
- Look up strain in MGI database → verify it exists
- If transgenic (Cre driver), check tissue tropism against paper claims
- Cross-check same strain/allele usage in prior papers → flag inconsistent treatment
- Example: "Same mouse used for spinal surgery in Paper A but for mild restraint stress in Paper B — tissue recovery differs"

---

## 4. Integration with M6

```
M6 Workflow
├─ Input: structured_result_v2 (from M1)
├─ Step 1: ethics_compliance_check.py
│         └─ produces: ETH-ANI-001 (IACUC approval), ETH-ANI-003 (basic info), ETH-ANI-004 (anesthesia)
├─ Step 2: animal_model_compliance.py  [NEW]
│         ├─ extracts: animal model details
│         └─ produces: enhanced ETH-ANI-002, welfare_violation signals, X1 candidates
├─ Step 3: M6 decision logic
│         └─ routes both signal types to ethics_committee reviewer
└─ Output: m6_findings (combined severity, evidence, action)
```

**Key difference**: Old M6 only checked "did paper mention IACUC approval?" New M6 checks "how is the animal welfare ensured?"

---

## 5. What Happens When Signals Are Routed to M6

### For `ethics_requirement_unmet` (ETH-ANI-002)

**Example**: Paper does NOT discuss 3R Replacement principle

M6 Decision Logic:
```
IF 3R compliance signal
  AND paper describes in vivo experiments
  AND "in vitro" / "computational" NOT mentioned
THEN:
  finding.severity = major
  finding.detail = "Study uses living mice but does not discuss why 
                   in vitro alternatives were unsuitable (3R Replacement principle)"
  finding.action = "Request authors: (a) if alternatives were considered, 
                   add brief justification; (b) if not, explain why"
```

---

### For `animal_welfare_violation`

**Example**: Paper mentions "cervical dislocation" for mice euthanasia

M6 Decision Logic:
```
IF welfare_violation.severity == critical
THEN:
  finding.severity = critical
  finding.detail = "Paper describes euthanasia method prohibited 
                   under AVMA 2020 and EU Directive 2010/63/EU for rodents"
  finding.action = "Critical: Editor must contact authors to confirm 
                   whether anesthesia was used. If not, reject paper 
                   or require revision to describe anesthesia protocol."
  finding.who = editor
```

---

## 6. Limitations & Design Choices

### What This Does NOT Catch (Requires Human Judgment)

- ❌ **Appropriateness of model choice**: "Why use mice instead of rats?" (regulatory context-dependent)
- ❌ **Housing/social conditions**: Papers rarely report these
- ❌ **Cross-paper inconsistencies**: Same animal used for conflicting purposes (needs X1 MGI lookup)
- ❌ **Actual tissue tropism of Cre driver**: "Does this Cre really only target hepatocytes?" (needs X1 MGI)
- ❌ **Breeding rationale**: "Why breed this specific transgenic?" (needs expert review)

### Why Some Checks Are "Offline Only"

**Regex-based extraction** is inherently limited but:
- **Avoids false precision**: No network API means "inhumane euthanasia detected" is a fact, not speculation
- **Offline robustness**: Works without MGI/internet access
- **Low false positive**: Only flags methods explicitly described in paper

**Example**: We cannot say "this Cre driver does NOT target the claimed tissue" based on paper text alone. That requires MGI database lookup (X1). So we output `external_validation_candidate` instead of finding.

---

## 7. Testing & Calibration

Self-test covers:

| Case | Expected Result |
|------|---|
| Painful surgery + no anesthesia | ✅ critical welfare_violation |
| Cervical dislocation for mice | ✅ critical welfare_violation |
| Complete 3R discussion | ✅ No ETH-ANI-002 signal |
| 200 mice + no reduction justification | ✅ major welfare_violation |
| No replacement discussion | ✅ minor welfare_violation |

---

## 8. Future (X1 Network Layer)

When MGI connector is implemented (Round 21 P3):

```python
# Pseudo-code for X1 enhancement
if signal.x1_candidate.species == "mouse":
    mgi_record = fetch_from_mgi(strain=signal.x1_candidate.strain)
    
    # Check 1: Allele identity
    if mgi_record.allele_id != paper.claim_allele_id:
        → generate mismatch finding
    
    # Check 2: Tissue tropism (for Cre drivers)
    if "hepatocyte-specific" in paper:
        x_detected_tissues = mgi_record.cre_detected_tissues
        if "non-hepatic" in x_detected_tissues:
            → generate tissue_scope_concern finding
    
    # Check 3: Cross-paper pattern
    prior_papers = fetch_from_literature(strain=strain, allele=allele)
    for prior in prior_papers:
        if prior.procedure != current_paper.procedure:
            → generate usage_pattern_review_candidate
```

---

## 9. References

- **AVMA Guidelines for the Euthanasia of Animals: 2020 Edition** (American Veterinary Medical Association)
- **Directive 2010/63/EU** (European Union) — Protection of animals used for scientific purposes, Article 24 (anesthesia), Annex VIII (euthanasia)
- **ARRIVE 2.0 Checklist** (du Sert et al., PLOS Biology 2020) — items 4a (replacement), 5 (humane endpoints), 6 (sample size justification)
- **NIH Office of Laboratory Animal Welfare (OLAW)** — Guidelines for Institutional Animal Care and Use Committees
- **Declaration of Helsinki** (2024 revision) — Ethical Principles for Medical Research Involving Animals (Article 31)
- **3Rs Centre** (NC3Rs, UK) — https://www.nc3rs.org.uk/the-3rs

---

## 10. Change Log

- **2026-08-07** (today): Initial implementation
  - Animal model extraction from text
  - 3R principle compliance checking
  - Five welfare red lines (inhumane euthanasia, painful procedures, chronic distress, excessive numbers, no replacement justification)
  - X1 placeholder for MGI cross-check
  - All self-tests passing
  
- **Future**: X1 MGI connector integration (when network access restored)

