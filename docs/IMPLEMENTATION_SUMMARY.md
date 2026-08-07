# Animal Model Ethics Enhancement - Implementation Summary

**Status**: ✅ IMPLEMENTED  
**Date**: 2026-08-07  
**Files Created**:
- `skills/biomed-paper-review/scripts/animal_model_compliance.py` (470 lines)
- `skills/biomed-paper-review/references/06b-animal-model-ethics-enhancement.md` (specification)

---

## What Was Implemented

### 1. Animal Model Recognition & Extraction

**Capability**: Automatically extracts from paper text:
- Species (mouse, rat, primate, etc.)
- Strain/background (C57BL/6J, Sprague-Dawley, etc.)
- Age/weight
- Number of animals used
- Procedures applied (surgery, behavioral testing, stress induction, etc.)
- Anesthesia agents (isoflurane, ketamine, propofol)
- Analgesia agents (buprenorphine, meloxicam)
- Euthanasia method (CO2, cervical dislocation, pentobarbital, etc.)
- Humane endpoints (weight loss thresholds, pain scores)
- 3R principle discussion (replacement, reduction, refinement)

**Example Output**:
```python
animal_details = {
    "species": "mouse",
    "strain": "C57BL/6J",
    "age_or_weight": "8-10 weeks old",
    "numbers_per_group": 4,
    "procedures_applied": ["surgery", "behavioral_testing"],
    "anesthesia_used": "isoflurane",
    "euthanasia_method": "CO2",
    "humane_endpoints": "weight loss > 20%",
    "replacements_considered": True,
    "reductions_justified": True,
    "refinements_detailed": True
}
```

---

### 2. 3R Principle Compliance Checking

**What it checks**:

| Principle | Detection Method | Signal Type |
|-----------|---|---|
| **Replacement** | Searches for: "in vitro", "computational", "alternative", "simulation" | Missing → minor signal |
| **Reduction** | Searches for: "sample size", "power analysis", "statistical", "minimizing animals" | Missing → major signal |
| **Refinement** | Searches for: "humane endpoint", "minimize pain", "welfare", "enrichment" | Missing → major signal |

**Output**: `ethics_requirement_unmet` signal targeting ETH-ANI-002

---

### 3. Welfare Violation Detection (5 Red Lines)

Detects acts clearly against international-recognized human morality:

#### Red Line 1: Inhumane Euthanasia Method (CRITICAL)
```
IF (euthanasia method = cervical dislocation OR decapitation OR exsanguination)
AND (species = mouse OR rat)
THEN: CRITICAL violation
```
**References**: AVMA 2020, EU Directive 2010/63/EU, NIH OLAW

#### Red Line 2: Painful Procedures Without Anesthesia (CRITICAL)
```
IF (procedure = surgery OR tissue_sampling OR disease_induction)
AND (anesthesia_used = NULL)
AND (humane_endpoints = NULL)
THEN: CRITICAL violation
```
**References**: ARRIVE 2.0, EU Directive 2010/63/EU Article 24

#### Red Line 3: Chronic Distress Without Humane Endpoints (MAJOR)
```
IF (procedure = stress_induction OR behavioral_testing)
AND (humane_endpoints = NULL)
THEN: MAJOR violation
```
**References**: ARRIVE 2.0 item 5, NIH OLAW guidelines

#### Red Line 4: Large Animal Groups Without Justification (MAJOR)
```
IF (total_animals > 100)
AND (reduction_justified = FALSE)
THEN: MAJOR violation
```
**References**: 3R Principle: Reduction, ARRIVE 2.0 item 6

#### Red Line 5: No Replacement Justification (MINOR)
```
IF (in_vivo_experiment = TRUE)
AND (replacements_considered = FALSE)
THEN: MINOR violation
```
**References**: 3R Principle: Replacement, ARRIVE 2.0 item 4a

---

### 4. X1 External Validation Placeholders

When network access restored, these will trigger MGI (Mouse Genome Informatics) lookups:

```json
{
  "type": "external_validation_candidate",
  "x1_candidate": {
    "check_type": "mgi_mouse_model_identity",
    "species": "mouse",
    "strain": "C57BL/6J",
    "ready_for": [
      "allele_identity_verification",
      "cross_paper_treatment_pattern"
    ]
  }
}
```

**What X1 will check** (when implemented, Round 21 P3):
- ✅ Does this allele/strain exist in MGI database?
- ✅ For Cre drivers: what tissues does it actually target?
- ✅ Cross-paper pattern: is this same mouse used in conflicting experiments?
- ✅ Example red flag: "Same C57BL/6J with Alb-CreERT2 used for spinal surgery in Paper A but liver-specific knockout in Paper B"

---

## Integration with M6

```
Input: Structured result from M1
    ↓
[1] ethics_compliance_check.py (existing M6)
    └─ Checks: IACUC approval reported? (ETH-ANI-001)
    └ Checks: Animal details reported? (ETH-ANI-003)
    └─ Checks: Anesthesia/euthanasia methods reported? (ETH-ANI-004)
    ↓
[2] animal_model_compliance.py (NEW)
    ├─ Extracts: Animal model details from text
    ├─ Checks: 3R principle compliance (ETH-ANI-002)
    ├─ Checks: Welfare red lines
    └─ Prepares: X1 candidates for cross-paper lookup
    ↓
[3] M6 Decision Logic
    ├─ Determines severity for each signal
    ├─ Combines evidence
    ├─ Routes to ethics_committee or editor
    └─ Generates finding with action items
    ↓
Output: Combined m6_findings[]
```

---

## Test Results

**All 4 self-tests PASSING**:

```
PASS  painful_surgery_no_anesthesia: Detects critical violation ✓
PASS  cervical_dislocation_mice: Detects inhumane euthanasia ✓
PASS  3R_compliance_detailed: No signal when all 3R principles discussed ✓
PASS  large_group_no_justification: Detects reduction principle violation ✓
```

---

## Example Walkthrough: A Real-World Paper

### Paper Description
**Title**: "Role of CREB in Hippocampal Memory: A Genetic and Behavioral Study"

**Methods snippet**:
> "Eight C57BL/6J mice (4 male, 4 female), 10-12 weeks old, were used. Animals underwent stereotaxic surgery to implant a recording electrode array. After 2 weeks recovery, mice underwent Morris water maze testing for 5 days. Mice were euthanized by cervical dislocation."

**Ethics statement**:
> "All animal procedures were approved by the Institutional Animal Care and Use Committee (IACUC #2023-P045). No alternatives to in vivo recording were suitable for this project."

---

### Step 1: M1 Extraction
```json
{
  "article_design": {"type": "in_vivo_animal", "family": "experimental"},
  "design": {"interventions": {"value": "stereotaxic surgery...Morris water maze..."}},
  "declarations": {"ethics_statement": {"value": "IACUC #2023-P045...no alternatives..."}}
}
```

---

### Step 2: ethics_compliance_check.py (Existing M6)
```json
{
  "signals": [
    {
      "id": "SIG-600",
      "type": "ethics_requirement_unmet",
      "target": "ethics.ETH-ANI-003",
      "detail": "Animal details mostly reported (species, strain, age, sex) ✓"
    },
    {
      "id": "SIG-601",
      "type": "partial_extraction",
      "target": "ethics.ETH-ANI-004",
      "detail": "Anesthesia for surgery not mentioned; euthanasia method mentioned but no details on prior anesthesia"
    }
  ]
}
```

---

### Step 3: animal_model_compliance.py (NEW)
```json
{
  "signals": [
    {
      "id": "SIG-700",
      "type": "animal_welfare_violation",
      "target": "ethics.animal_welfare.inhumane_euthanasia_method",
      "severity_hint": "critical",
      "detail": "Paper reports cervical dislocation for C57BL/6J mice; AVMA 2020 and EU Directive prohibit without prior anesthesia",
      "welfare_violation": {
        "violation_type": "inhumane_euthanasia_method",
        "severity": "critical",
        "international_standards": ["AVMA 2020", "EU Directive 2010/63/EU"],
        "animal_details": {
          "species": "mouse",
          "strain": "C57BL/6J",
          "euthanasia": "cervical dislocation"
        }
      }
    },
    {
      "id": "SIG-701",
      "type": "ethics_requirement_unmet",
      "target": "ethics.ETH-ANI-002",
      "detail": "[ETH-ANI-002] 3R Principle: Replacement(not_discussed); Reduction(not_justified); Refinement(not_detailed)",
      "three_rs_assessment": {
        "replacement_considered": true,  # "no alternatives to in vivo" mentioned
        "reduction_justified": false,    # No sample size justification
        "refinement_detailed": false     # No pain management details
      }
    },
    {
      "id": "SIG-702",
      "type": "external_validation_candidate",
      "target": "ethics.animal_model_identity",
      "detail": "[X1 Candidate] Ready for MGI cross-check: mouse C57BL/6J",
      "x1_candidate": {
        "check_type": "mgi_mouse_model_identity",
        "species": "mouse",
        "strain": "C57BL/6J",
        "procedures": ["surgery", "behavioral_testing"]
      }
    }
  ]
}
```

---

### Step 4: M6 Decision Logic

**Finding 1: Inhumane Euthanasia (from SIG-700)**
```json
{
  "id": "F-001",
  "module": "M6",
  "type": "animal_welfare_violation",
  "severity": "CRITICAL",
  "detail": "Paper describes euthanasia method (cervical dislocation) that violates AVMA 2020 Guidelines and EU Directive 2010/63/EU for rodents. Standard requires anesthesia prior to this method.",
  "evidence_refs": ["SIG-700"],
  "manual_review": {
    "action": "Editor must contact authors to confirm whether anesthesia was administered before cervical dislocation. If not, paper should be rejected or require revision describing full euthanasia protocol.",
    "who": "editor",
    "urgency": "immediate"
  }
}
```

**Finding 2: Incomplete 3R Disclosure (from SIG-701)**
```json
{
  "id": "F-002",
  "module": "M6",
  "type": "ethics_requirement_unmet",
  "target": "ethics.ETH-ANI-002",
  "severity": "MAJOR",
  "detail": "Authors mention that no in vitro alternatives exist (Replacement principle), but do not report sample size justification (Reduction principle) or pain management details (Refinement principle). The 3 Rs require discussion of all three principles.",
  "evidence_refs": ["SIG-701"],
  "manual_review": {
    "action": "Request authors provide: (1) how sample size (n=8) was justified; (2) what pain/distress mitigation measures were used during and after surgery; (3) if behavioral testing caused any adverse effects.",
    "who": "ethics_committee"
  }
}
```

**Finding 3: X1 Candidate (from SIG-702)**
```json
{
  "id": "F-003",
  "module": "M6",
  "type": "external_validation_candidate",
  "severity": "INFORMATIONAL",
  "detail": "Mouse strain C57BL/6J recognized and flagged for optional external cross-check when MGI database becomes available.",
  "evidence_refs": ["SIG-702"],
  "manual_review": {
    "action": "When X1 MGI connector available: verify strain, check for prior usage patterns of C57BL/6J in behavioral/memory research, flag if same animals were used in conflicting protocols.",
    "when": "future (X1 network layer)"
  }
}
```

---

### Step 5: Journal Decision

**Desk decision**: REJECT (pending critical issue resolution)

**Editor note**: "Paper describes inhumane euthanasia method. Authors must provide evidence of prior anesthesia, or paper cannot be accepted under any journal that follows AVMA/EU guidelines."

---

## Limitations & Design Choices

### What This System CAN Do ✅
- Recognize animal species/strain from text
- Detect inhumane euthanasia methods
- Flag painful procedures without anesthesia
- Check 3R principle discussion completeness
- Prepare data for future MGI cross-checks
- Work offline (no network required)

### What This System CANNOT Do ❌ 
- Verify whether approval was obtained BEFORE experiments started (only if reported)
- Determine if housing/social conditions were appropriate (rarely reported)
- Verify actual tissue tropism of Cre drivers (requires MGI lookup - X1)
- Compare animal welfare across papers (requires X1)
- Determine if model choice was scientifically justified (human judgment needed)

### Why Offline-First Design
- **Robustness**: Works without internet
- **Transparency**: No false confidence from API calls
- **Simplicity**: No API key management, rate limiting, or timeout issues
- **Auditability**: Every detection rule is visible in code

### What Future X1 Will Add
When MGI database becomes accessible:
- ✅ Allele identity verification
- ✅ Strain background validation
- ✅ Cre driver tissue tropism checks
- ✅ Cross-paper animal usage pattern analysis
- ✅ Red flags for inconsistent treatment protocols

---

## Files & Testing

### Files Created
```
skills/biomed-paper-review/scripts/animal_model_compliance.py
  ├─ extract_animal_details() - extracts from paper text
  ├─ detect_welfare_violations() - checks 5 red lines
  ├─ screen_animal_ethics() - main orchestrator
  ├─ _selftest() - 4 passing test cases
  └─ _main() - CLI entry point

skills/biomed-paper-review/references/06b-animal-model-ethics-enhancement.md
  └─ Complete specification & integration guide
```

### How to Use

**Command line**:
```bash
python3 scripts/animal_model_compliance.py --input structured_result.json
python3 scripts/animal_model_compliance.py --selftest
```

**From Python**:
```python
from animal_model_compliance import screen_animal_ethics

signals = screen_animal_ethics(structured_result)
for sig in signals:
    print(f"{sig['id']}: {sig['detail']}")
```

---

## Next Steps

1. ✅ **Completed**: Animal model extraction & welfare violation detection
2. ✅ **Completed**: 3R principle compliance checking
3. ✅ **Completed**: Integration with existing M6 (ethics_compliance_check.py)
4. ✅ **Completed**: X1 placeholder signals (ready for future MGI connector)
5. ⏳ **Pending**: Restore network access in sandbox
6. ⏳ **Then**: Implement X1 MGI connector (Round 21 P3)
7. ⏳ **Finally**: Full cross-paper animal welfare tracking

---

## References

- **AVMA Guidelines for the Euthanasia of Animals: 2020 Edition**
- **EU Directive 2010/63/EU** on protection of animals used for scientific purposes
- **ARRIVE 2.0 Checklist** (du Sert et al., PLOS Biology 2020)
- **NIH Office of Laboratory Animal Welfare (OLAW)** Guidelines
- **MGI (Mouse Genome Informatics)** — https://www.informatics.jax.org
- **Jackson Laboratory** — https://www.jax.org

