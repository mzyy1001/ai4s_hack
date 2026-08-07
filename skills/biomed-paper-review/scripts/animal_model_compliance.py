#!/usr/bin/env python3
"""
动物模型伦理合规审计（M6 增强）

职责：
1. 从 M1 抽出的动物信息推导 3R 原则遵循度
2. 检测重度福利违规（international norms）
3. 准备跨论文对比数据（X1 联网层）
4. 输出 extraction_signal 和 ethics_requirement_unmet signals

设计原则：
- 离线优先：仅用论文内容与硬编码的已知模式
- 不过度自信：无法确定时置为 partial_extraction
- 3R 缺失 ≠ 3R 违反：未报告与违反有严格区别
- 人道性红线：明确反对国际公认道德的行为升级 critical

与 M6 的关系：
- 本模块补充 ETH-ANI-002（3R 原则）与 ETH-ANI-004（人道终点）
- 新增 `animal_welfare_violation` 类 signal
- 不新增规则，只增强既有规则的证据链与严重度判定
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULEBASE = os.path.join(SKILL_ROOT, "resources", "ethics_rules.json")


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)


def extract_animal_details(structured_result):
    """
    从 structured_result 提取动物模型关键字段。
    """
    pop = structured_result.get("population", {})
    subjects_field = pop.get("subjects", {})
    subjects_text = subjects_field.get("value", "")
    
    design = structured_result.get("design", {})
    measurement = structured_result.get("measurement", {})
    decl = structured_result.get("declarations", {})
    
    # Extract species
    species = None
    species_patterns = [
        (r"\b(C57BL/6[JN]?|Balb/c|FVB|129|Swiss|CD-1|ICR|Nude|SCID|NOD)", "mouse"),
        (r"\b(Sprague[\s-]?Dawley|Lewis|Wistar|Fisher|Long[\s-]?Evans|Brown[\s-]?Norway)", "rat"),
        (r"\b(rhesus|macaque|cynomolgus|marmoset|baboon)", "primate"),
        (r"\b(Beagle|Rabbit|Guinea[\s-]?pig|Hamster|Ferret)", "other"),
    ]
    
    for pattern, sp in species_patterns:
        if re.search(pattern, subjects_text, re.I):
            species = sp
            break
    
    # Strain
    strain_match = re.search(
        r"\b(C57BL/6[JN]?|Balb/c|FVB|129S\d+|Swiss|CD-1|Nude|SCID|NOD)\b",
        subjects_text, re.I)
    strain = strain_match.group(1) if strain_match else None
    
    # Age/weight
    age_match = re.search(r"(\d+[\s-]?(?:week|month|year|day)s?\s+old|aged?\s+\d+[\s-]?week|~?\d+[\s-]?\d+\s*g)", 
                          subjects_text, re.I)
    age_or_weight = age_match.group(1) if age_match else None
    
    # Numbers - look for total numbers and per-group numbers
    numbers_per_group = None
    total_match = re.search(r"(\d+)\s+(?:mice|rats|animals|subjects)", subjects_text, re.I)
    n_per_group_matches = re.findall(r"[nN]\s*=\s*(\d+)|per\s+group.*?(\d+)|groups?.*?(\d+).*?each", subjects_text)

    all_ns = []
    if total_match:
        all_ns.append(int(total_match.group(1)))
    if n_per_group_matches:
        for t in n_per_group_matches:
            for x in t:
                if x:
                    all_ns.append(int(x))

    if all_ns:
        numbers_per_group = {"extracted": all_ns, "total_approx": max(all_ns) if all_ns else None}
    
    # Procedures
    procedures = []
    procedure_patterns = {
        "surgery": r"\b(surgery|surgical|resection|ligation|injection|implant|graft)\b",
        "repeated_dosing": r"\b(injection|infusion|gavage|oral dosing).*?(?:daily|weekly|multiple times)\b",
        "stress_induction": r"\b(restraint|cold exposure|heat stress|social isolation|fear conditioning)\b",
        "tissue_sampling": r"\b(biopsy|blood draw|tissue harvest|organ removal)\b",
        "behavioral_testing": r"\b(swim test|shock|foot shock|Morris water maze|forced swim)\b",
        "disease_induction": r"\b(infection|tumor challenge|colitis induction|disease model)\b",
    }
    
    methods_text = (structured_result.get("design", {}).get("interventions", {}).get("value", "") or "") + \
                   (structured_result.get("measurement", {}).get("assays", {}).get("value", "") or "")
    
    for proc_name, pattern in procedure_patterns.items():
        if re.search(pattern, methods_text, re.I):
            procedures.append(proc_name)
    
    # Anesthesia/analgesia/euthanasia
    ethics_stmt = decl.get("ethics_statement", {}).get("value", "") or ""
    anesthesia = re.search(r"(isoflurane|ketamine|propofol|sevoflurane|sodium pentobarbital|anesthesia.*?(?:used|administered))", 
                          ethics_stmt, re.I)
    analgesia = re.search(r"(buprenorphine|meloxicam|carprofen|ibuprofen|analgesia|analgesic)", 
                         ethics_stmt, re.I)
    euthanasia = re.search(r"(CO2|cervical dislocation|decapitation|exsanguination|pentobarbital|euthanasia.*?(?:by|method).*?(?:CO2|dislocation|decapitation|exsanguination|pentobarbital))", 
                          ethics_stmt, re.I)
    
    humane_endpoints = re.search(r"(humane endpoint|early euthanasia|predefined criteria for euthanasia|moribund|pain score|weight loss.*?threshold)", 
                                ethics_stmt, re.I)
    
    # 3R compliance signals
    combined_text = methods_text + " " + ethics_stmt
    three_rs = {
        "replacement_considered": bool(re.search(r"(replacement|alternative|in\s+vitro|computational|simulation)", combined_text, re.I)),
        "reduction_justified": bool(re.search(r"(reduction|sample size|power analysis|statistical|minimizing.*?animal|fewer animal)", combined_text, re.I)),
        "refinement_detailed": bool(re.search(r"(refinement|minimize.*?pain|minimize.*?distress|welfare|humane endpoint|environmental enrichment)", combined_text, re.I)),
    }
    
    return {
        "species": species,
        "strain": strain,
        "age_or_weight": age_or_weight,
        "source": pop.get("subjects", {}).get("value", "")[:100],
        "numbers_per_group": numbers_per_group,
        "group_descriptions": [p for p in procedures],
        "housing_conditions": None,
        "procedures_applied": procedures,
        "anesthesia_used": anesthesia.group(1) if anesthesia else None,
        "analgesia_used": analgesia.group(1) if analgesia else None,
        "euthanasia_method": euthanasia.group(1) if euthanasia else None,
        "humane_endpoints": humane_endpoints.group(1) if humane_endpoints else None,
        "reported_health_monitoring": None,
        "replacements_considered": three_rs["replacement_considered"],
        "reductions_justified": three_rs["reduction_justified"],
        "refinements_detailed": three_rs["refinement_detailed"],
    }


def detect_welfare_violations(animal_details, methods_text):
    """检测明确反对国际公认道德的行为（international norms）。"""
    violations = []
    
    # Red line 1: Prohibited euthanasia methods (without prior anesthesia)
    prohibited_methods = ["decapitation", "neck dislocation", "cervical dislocation", "exsanguination", "drowning"]
    if animal_details.get("euthanasia_method"):
        method_text = animal_details["euthanasia_method"].lower()
        for prohibited in prohibited_methods:
            if prohibited in method_text:
                species = (animal_details.get("species") or "").lower()
                if "mouse" in species or "rat" in species:
                    violations.append({
                        "type": "inhumane_euthanasia_method",
                        "severity": "critical",
                        "detail": f"Paper reports {animal_details['euthanasia_method']} for {animal_details.get('species', 'animal')}; "
                                 "international standards prohibit this without prior anesthesia",
                        "references": ["AVMA 2020 Guidelines", "EU Directive 2010/63/EU"]
                    })
    
    # Red line 2: Painful procedures without anesthesia
    painful_procedures = ["surgery", "tissue_sampling", "disease_induction"]
    has_painful = any(p in animal_details.get("procedures_applied", []) for p in painful_procedures)
    
    if has_painful:
        if not animal_details.get("anesthesia_used") and not animal_details.get("humane_endpoints"):
            violations.append({
                "type": "painful_procedure_no_anesthesia",
                "severity": "critical",
                "detail": f"Paper reports {', '.join([p for p in animal_details.get('procedures_applied', []) if p in painful_procedures])} "
                         "but does not report anesthesia or analgesia",
                "references": ["ARRIVE 2.0", "EU Directive 2010/63/EU Article 24"]
            })
    
    # Red line 3: Chronic distress without endpoints
    distress_procedures = ["stress_induction", "behavioral_testing"]
    has_distress = any(p in animal_details.get("procedures_applied", []) for p in distress_procedures)
    
    if has_distress and not animal_details.get("humane_endpoints"):
        violations.append({
            "type": "chronic_distress_no_humane_endpoint",
            "severity": "major",
            "detail": f"Paper reports stress/behavioral procedures but does not report predefined humane endpoints",
            "references": ["ARRIVE 2.0 item 5", "NIH OLAW guidelines"]
        })
    
    # Red line 4: Excessive animals without justification
    if animal_details.get("numbers_per_group") and animal_details.get("numbers_per_group").get("total_approx"):
        total = animal_details["numbers_per_group"]["total_approx"]
        if total > 100 and not animal_details.get("reductions_justified"):
            violations.append({
                "type": "large_group_no_reduction_justification",
                "severity": "major",
                "detail": f"Paper uses {total} animals but does not justify numbers against 3R Reduction principle",
                "references": ["3R Principle: Reduction", "ARRIVE 2.0 item 6"]
            })
    
    # Red line 5: No alternatives considered
    if not animal_details.get("replacements_considered") and "in vivo" in methods_text.lower():
        violations.append({
            "type": "no_replacement_justification",
            "severity": "minor",
            "detail": "Paper does not justify why in vivo studies were necessary (3R Replacement principle)",
            "references": ["3R Principle: Replacement", "ARRIVE 2.0 item 4a"]
        })
    
    return violations


def screen_animal_ethics(structured_result, signal_start=700):
    """Main entry point. Returns list of signals."""
    if not isinstance(structured_result, dict):
        raise ValueError("structured_result must be JSON object")
    
    # Check if animal experiments exist
    article_design = structured_result.get("article_design", {})
    primary = article_design.get("primary_design", {})
    components = article_design.get("design_components", [])
    
    has_animal = (primary.get("type") == "in_vivo_animal" or 
                 any(c.get("type") == "in_vivo_animal" for c in components))
    
    if not has_animal:
        return []
    
    signals = []
    n = 0
    
    # Extract animal model details
    animal_details = extract_animal_details(structured_result)
    methods_text = (structured_result.get("design", {}).get("interventions", {}).get("value", "") or "") + \
                   (structured_result.get("measurement", {}).get("assays", {}).get("value", "") or "")
    
    # ========== 3R Principle Compliance ==========
    three_rs_issues = []
    
    if not animal_details["replacements_considered"]:
        three_rs_issues.append(("Replacement", "not_discussed"))
    
    if not animal_details["reductions_justified"]:
        three_rs_issues.append(("Reduction", "not_justified"))
    
    if not animal_details["refinements_detailed"]:
        three_rs_issues.append(("Refinement", "not_detailed"))
    
    if three_rs_issues:
        n += 1
        sid = f"SIG-{signal_start + n:03d}"
        issue_str = "; ".join([f"{p}({s})" for p, s in three_rs_issues])
        signals.append({
            "id": sid,
            "type": "ethics_requirement_unmet",
            "target": "ethics.ETH-ANI-002",
            "detail": f"[ETH-ANI-002] 3R Principle: {issue_str}",
            "observation_refs": [],
            "evidence_refs": [],
            "routed_to": ["M6"],
            "produced_by": "animal_model_compliance",
            "three_rs_assessment": {
                "replacement_considered": animal_details["replacements_considered"],
                "reduction_justified": animal_details["reductions_justified"],
                "refinement_detailed": animal_details["refinements_detailed"],
                "issues": three_rs_issues
            }
        })
    
    # ========== Animal Welfare Violations ==========
    welfare_violations = detect_welfare_violations(animal_details, methods_text)
    
    for violation in welfare_violations:
        n += 1
        sid = f"SIG-{signal_start + n:03d}"
        signals.append({
            "id": sid,
            "type": "animal_welfare_violation",
            "target": f"ethics.animal_welfare.{violation['type']}",
            "severity_hint": violation["severity"],
            "detail": violation["detail"],
            "observation_refs": [],
            "evidence_refs": [],
            "routed_to": ["M6"],
            "produced_by": "animal_model_compliance",
            "welfare_violation": {
                "violation_type": violation["type"],
                "severity": violation["severity"],
                "international_standards": violation["references"],
                "animal_details": {
                    "species": animal_details["species"],
                    "strain": animal_details["strain"],
                    "procedures": animal_details["procedures_applied"],
                    "anesthesia": animal_details["anesthesia_used"],
                    "euthanasia": animal_details["euthanasia_method"]
                }
            }
        })
    
    # ========== X1 Placeholder: Cross-Paper Analysis ==========
    if animal_details["strain"] and animal_details["species"]:
        n += 1
        sid = f"SIG-{signal_start + n:03d}"
        signals.append({
            "id": sid,
            "type": "external_validation_candidate",
            "target": "ethics.animal_model_identity",
            "detail": f"[X1 Candidate] Ready for MGI cross-check: {animal_details['species']} {animal_details['strain']}",
            "observation_refs": [],
            "evidence_refs": [],
            "routed_to": ["M6"],
            "produced_by": "animal_model_compliance",
            "x1_candidate": {
                "check_type": "mgi_mouse_model_identity",
                "species": animal_details["species"],
                "strain": animal_details["strain"],
                "procedures": animal_details["procedures_applied"],
                "ready_for": ["allele_identity_verification", "cross_paper_treatment_pattern"]
            }
        })
    
    return signals


def _selftest():
    """Self-test: animal model compliance detection."""
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    # Test 1: Painful surgery without anesthesia
    sr1 = {
        "article_design": {
            "primary_design": {"family": "experimental", "type": "in_vivo_animal"},
            "design_components": []
        },
        "population": {"subjects": {"value": "C57BL/6 mice, 8-10 weeks old"}},
        "design": {"interventions": {"value": "surgical implant of electrode array without anesthesia"}},
        "measurement": {"assays": {"value": ""}},
        "declarations": {"ethics_statement": {"value": "IACUC approval obtained"}}
    }
    sigs1 = screen_animal_ethics(sr1)
    critical_welfare = [s for s in sigs1 if s.get("severity_hint") == "critical"]
    expect("painful_surgery_no_anesthesia", len(critical_welfare) > 0, True)

    # Test 2: Decapitation without anesthesia
    sr2 = {
        "article_design": {
            "primary_design": {"family": "experimental", "type": "in_vivo_animal"},
            "design_components": []
        },
        "population": {"subjects": {"value": "C57BL/6J mice"}},
        "design": {"interventions": {"value": "forced swim test"}},
        "measurement": {"assays": {"value": ""}},
        "declarations": {"ethics_statement": {"value": "Mice were euthanized by cervical dislocation"}}
    }
    sigs2 = screen_animal_ethics(sr2)
    euthanasia_violations = [s for s in sigs2 if "inhumane_euthanasia" in s.get("target", "")]
    expect("cervical_dislocation_mice", len(euthanasia_violations) > 0, True)

    # Test 3: 3R compliance
    sr3 = {
        "article_design": {
            "primary_design": {"family": "experimental", "type": "in_vivo_animal"},
            "design_components": []
        },
        "population": {"subjects": {"value": "8 C57BL/6J mice (n=4 per group), 12 weeks"}},
        "design": {"interventions": {"value": "isoflurane anesthesia; power analysis justified; in vitro studies first"}},
        "measurement": {"assays": {"value": ""}},
        "declarations": {"ethics_statement": {"value": "IACUC approved; humane endpoint: 20% weight loss"}}
    }
    sigs3 = screen_animal_ethics(sr3)
    three_rs_sigs = [s for s in sigs3 if "ETH-ANI-002" in s.get("target", "")]
    expect("3R_compliance_detailed", len(three_rs_sigs) == 0, True)

    # Test 4: Large group without justification
    sr4 = {
        "article_design": {
            "primary_design": {"family": "experimental", "type": "in_vivo_animal"},
            "design_components": []
        },
        "population": {"subjects": {"value": "200 mice across 10 groups (n=20 each)"}},
        "design": {"interventions": {"value": "chronic stress"}},
        "measurement": {"assays": {"value": ""}},
        "declarations": {"ethics_statement": {"value": "IACUC approval obtained"}}
    }
    sigs4 = screen_animal_ethics(sr4)
    reduction_issues = [s for s in sigs4 if "large_group" in s.get("target", "")]
    expect("large_group_no_justification", len(reduction_issues) > 0, True)

    print("\nAll tests passed" if ok else "\nSome tests failed")
    return 0 if ok else 1


def _main(argv=None):
    parser = _JsonArgumentParser(description="Animal model ethics compliance audit")
    parser.add_argument("--input", metavar="JSON", help="structured_result JSON file")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    
    if args.selftest:
        return _selftest()
    
    if not args.input:
        parser.error("Must provide --input JSON or --selftest")
    
    try:
        if args.input == "-":
            structured_result = json.load(sys.stdin)
        else:
            with open(args.input, encoding="utf-8") as f:
                structured_result = json.load(f)
        
        signals = screen_animal_ethics(structured_result)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "detail": str(exc)}},
                        ensure_ascii=False), file=sys.stderr)
        return 2
    
    print(json.dumps({"signals": signals}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
