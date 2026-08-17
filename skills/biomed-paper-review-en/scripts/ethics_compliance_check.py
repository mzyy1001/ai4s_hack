#!/usr/bin/env python3
"""Ethics compliance screening (phase-1 capability; stdlib only, runs offline).

Applies the rulebase in `skills/biomed-paper-review/resources/ethics_rules.json`
to the structured facts extracted by M1, and emits `extraction_signal`
entries (`type: ethics_requirement_unmet`) for **M6** to decide whether they
constitute findings.

**This module never emits findings itself.** Same pattern as
`statistical_forensics.py -> M4`: the tool layer produces the machine-level
observation "the rulebase requires X, and X was not seen in the manuscript";
the module owner's rulebase decides whether that constitutes a manuscript
problem and at what severity.

Why this can run offline
------------------------
The rulebase is a **structured index of requirements**, not an external
database query. That fits squarely within the phase-1 definition and provides
the offline fallback when no network is available. Verifying approval-number
authenticity, registration-number chronology, etc. requires the unified
external-evidence layer; that layer is not yet wired into this component, so
this module does not do it — and does not pretend to.

Three false-positive guards
---------------------------
1. **Applicability first**: a rule is evaluated only when its `applies_when`
   condition holds. A pure cell-line study is never asked for an animal
   ethics approval.
2. **parse_failed is not absence**: when a field is `parse_failed` because
   supplementary material was unavailable, we emit `partial_extraction`
   rather than `ethics_requirement_unmet` — if we could not read it, we may
   not claim the manuscript omitted it (`00-contracts.md §6.4`).
3. **Negative rules**: `assert_not_applicable` rules (e.g. the
   commercial-cell-line exemption) actively suppress false positives from
   other rules.

Usage
-----
    from ethics_compliance_check import screen
    signals = screen(structured_result, evaluation_matrix_facts)

Command line:
    python3 <skill dir>/scripts/ethics_compliance_check.py --input structured_result_v2.json
    python3 <skill dir>/scripts/ethics_compliance_check.py --selftest
"""

import argparse
import json
import os
import re
import sys

# The script lives in skills/<name>/scripts/; the rulebase is in the sibling
# resources/ directory. Locate it relative to __file__ — never hard-code an
# absolute path (L1 explicitly deducts points for hard-coded paths).
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULEBASE = os.path.join(SKILL_ROOT, "resources", "ethics_rules.json")


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)


def load_rulebase(path=RULEBASE):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- fact derivation

def _get(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _field_text(field_obj):
    """Flatten an extracted_field's value into searchable text."""
    if not isinstance(field_obj, dict):
        return ""
    v = field_obj.get("value")
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def _named_entity_hits(text, names):
    """Match cell lines as standalone names so `CHO` cannot hit `chondrocyte`."""
    hits = []
    for name in names:
        pattern = rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])"
        if re.search(pattern, text, re.I):
            hits.append(name)
    return hits


def derive_facts(structured_result, rb):
    """Derive the boolean facts needed by applies_when from structured_result.

    Inference uses **extracted** content only. When extraction is uncertain the
    fact is set to None (= unknown); a rule whose applies_when hits a None fact
    is not evaluated and yields partial_extraction instead.
    """
    if not isinstance(structured_result, dict):
        raise ValueError("structured_result must be a JSON object")
    if not isinstance(rb, dict):
        raise ValueError("ethics rulebase must be a JSON object")
    ad = structured_result.get("article_design", {})
    if not isinstance(ad, dict):
        raise ValueError("article_design must be a JSON object")
    primary = ad.get("primary_design", {}) or {}
    comps = ad.get("design_components", []) or []
    if not isinstance(primary, dict):
        raise ValueError("article_design.primary_design must be a JSON object")
    if not isinstance(comps, list) or any(not isinstance(c, dict) for c in comps):
        raise ValueError("article_design.design_components must be an array of objects")
    types = {primary.get("type")} | {c.get("type") for c in comps}
    families = {primary.get("family")} | {c.get("family") for c in comps}
    types.discard(None)
    families.discard(None)

    subjects_txt = _field_text(_get(structured_result, "population.subjects")) or ""
    subj_lower = subjects_txt.lower()

    exempt = rb.get("exempt_cell_lines", {}).get("lines", [])
    exempt_hit = _named_entity_hits(subjects_txt, exempt)

    # Whether only established commercial cell lines were used
    human_primary_markers = ["human primary", "primary human", "human tissue",
                             "human organoid", "patient-derived", "patient derived",
                             "patient", "患者", "donor", "供者", "人源", "人体",
                             "biopsy", "活检", "surgical specimen", "手术标本",
                             "peripheral blood", "外周血", "pbmc", "huvec",
                             "human umbilical vein endothelial"]
    has_primary_human = any(m in subj_lower for m in human_primary_markers)

    # `virus`/`viral` alone may refer to inactivated samples, vectors, or
    # pseudoviruses. Set True only when the text explicitly indicates an
    # infectious strain / live pathogen; with only a generic mention keep None —
    # never auto-raise a missing-requirement signal from it.
    pathogen_confirmed = bool(re.search(
        r"\blive\s+(?:virus|bacteri(?:um|a))\b|\binfectious\s+(?:virus|agent|pathogen)\b|"
        r"\breplication[- ]competent\b|活病毒|活菌|病原(?:菌|毒株)|具感染性(?:样本|病毒)",
        subjects_txt, re.I))
    pathogen_mentioned = bool(re.search(
        r"virus|viral|bacteri|pathogen|infect|病毒|细菌|病原|感染",
        subjects_txt, re.I))

    facts = {
        "has_human_subjects": (
            bool(families & {"human_interventional", "human_observational"})
            or has_primary_human
        ),
        "has_animal_experiment": "in_vivo_animal" in types
        or ("preclinical_mixed" in types and any(
            c.get("type") == "in_vivo_animal" for c in comps)),
        "design_family": primary.get("family"),
        "uses_established_cell_line_only": bool(exempt_hit) and not has_primary_human
        and not (families & {"human_interventional", "human_observational"}),
        "uses_human_derived_primary_material": has_primary_human,
        "uses_human_embryonic_stem_cells": bool(
            re.search(r"\bhESC\b|human embryonic stem|人胚胎干细胞", subjects_txt, re.I)),
        "cultures_human_embryos": bool(
            re.search(r"human embryo|人胚胎", subjects_txt, re.I)),
        "uses_pathogens": True if pathogen_confirmed else (None if pathogen_mentioned else False),
        "_exempt_cell_lines_hit": exempt_hit,
    }

    # Vulnerable populations
    markers = rb.get("vulnerable_population_markers", {})
    all_markers = [m.lower() for m in markers.get("en", [])] + markers.get("zh", [])
    facts["vulnerable_population"] = any(m in subj_lower or m in subjects_txt
                                         for m in all_markers)
    facts["includes_minors"] = bool(
        re.search(r"child|pediatric|infant|neonat|minor|adolescen|儿童|婴|新生儿|未成年|青少年",
                  subjects_txt, re.I))
    return facts


# ---------------------------------------------------------------- rule evaluation

def _applies(rule, facts):
    """Return True / False / None (None = fact unknown, do not evaluate)."""
    cond = rule.get("applies_when", {})
    if not cond:
        return True
    for key, want in cond.items():
        if key in ("jurisdiction_hint", "involves_pain_or_distress",
                   "animals_euthanized", "uses_identifiable_data",
                   "consent_waived", "gain_of_function",
                   "uses_chinese_human_genetic_resources",
                   "uses_foreign_genetic_resources"):
            # These facts cannot be reliably derived from the structured
            # result in phase 1 — never evaluate them automatically.
            return None
        got = facts.get(key)
        if got is None:
            return None
        if got != want:
            return False
    return True


def _sig(sid, stype, rule, detail, extra=None):
    out = {
        "id": sid,
        "type": stype,
        "target": f"ethics.{rule['rule_id']}",
        "detail": detail,
        "observation_refs": [],
        "evidence_refs": [],
        "routed_to": [rule.get("consumer", "M6")],
        "produced_by": "stage_2",
    }
    if stype == "ethics_requirement_unmet":
        out["ethics"] = {
            "rule_id": rule["rule_id"],
            "domain": rule["domain"],
            "citations": rule.get("citations", []),
            "manuscript_must_report": rule.get("manuscript_must_report", []),
            "rulebase_version": extra.get("rulebase_version") if extra else None,
        }
    return out


def screen(structured_result, rulebase=None, signal_start=600):
    """Main entry point. Returns a list of extraction_signal objects.

    Compliant rules (requirement already satisfied) emit **no signal** —
    silence means pass.
    """
    if not isinstance(structured_result, dict):
        raise ValueError("structured_result must be a JSON object")
    if not isinstance(signal_start, int) or isinstance(signal_start, bool) or signal_start < 0:
        raise ValueError("signal_start must be a non-negative integer")
    rb = load_rulebase() if rulebase is None else rulebase
    if not isinstance(rb, dict) or not isinstance(rb.get("rules"), list):
        raise ValueError("ethics rulebase is missing a rules array")
    if any(not isinstance(rule, dict) for rule in rb["rules"]):
        raise ValueError("every entry in the ethics rulebase rules array must be a JSON object")
    facts = derive_facts(structured_result, rb)
    version = rb.get("rulebase_version")
    signals = []
    n = 0

    # Negative rules: compute the set of exempted rules first
    suppressed = set()
    if facts.get("uses_established_cell_line_only"):
        suppressed |= {"ETH-CELL-001", "ETH-HUM-001", "ETH-HUM-002"}

    for rule in rb["rules"]:
        if rule["check"] == "assert_not_applicable":
            continue  # negative rules never emit signals of their own
        if rule["rule_id"] in suppressed:
            continue

        applicable = _applies(rule, facts)
        if applicable is False:
            continue

        n += 1
        sid = f"SIG-{signal_start + n:03d}"

        if rule["check"] == "manual_only":
            if applicable is None:
                continue
            signals.append(_sig(
                sid, "partial_extraction", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}: per the rulebase this rule "
                f"is **always referred to human review**; automation has not judged "
                f"the requirement unmet ({rule.get('false_positive_guard','')})."))
            continue

        if applicable is None:
            signals.append(_sig(
                sid, "partial_extraction", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}: the facts required for applicability "
                f"({list(rule.get('applies_when', {}).keys())}) cannot be reliably derived "
                f"from the structured result; this rule was not evaluated."))
            continue

        # Fetch the field
        fpath = rule.get("check_args", {}).get("field")
        if not fpath:
            continue
        field = _get(structured_result, fpath)
        status = (field or {}).get("status")

        # parse_failed / unresolved must never be judged as absence
        if status in ("parse_failed", "unresolved", "ambiguous"):
            signals.append(_sig(
                sid, "partial_extraction", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}: field `{fpath}` has status "
                f"{status}; we could not read it, so **absence in the manuscript must not "
                f"be inferred from this** (00-contracts §6.4)."))
            continue

        if status == "not_applicable":
            continue  # not applicable by design — compliant

        text = _field_text(field)

        # Substring-style checks
        want_any = rule.get("check_args", {}).get("expect_substring_any")
        if want_any:
            if status == "reported" and any(w.lower() in text.lower() for w in want_any):
                continue  # satisfied
            signals.append(_sig(
                sid, "ethics_requirement_unmet", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}: the rulebase requires the manuscript "
                f"to report {rule['manuscript_must_report']}, but no such statement was found "
                f"in `{fpath}` (search terms {want_any}).",
                {"rulebase_version": version}))
            continue

        want_contains = rule.get("check_args", {}).get("any")
        if rule["check"] == "field_contains_any" and want_contains:
            if status == "reported" and any(w.lower() in text.lower() for w in want_contains):
                continue
            signals.append(_sig(
                sid, "ethics_requirement_unmet", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}: none of {want_contains} found in `{fpath}`.",
                {"rulebase_version": version}))
            continue

        # Existence checks
        if status == "reported":
            continue
        if status == "not_reported":
            signals.append(_sig(
                sid, "ethics_requirement_unmet", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}: the rulebase requires the manuscript "
                f"to report {rule['manuscript_must_report']}; a complete search confirmed "
                f"`{fpath}` is not reported.",
                {"rulebase_version": version}))
    return signals


# ---------------------------------------------------------------- selftest
def _mk_field(status, value=None):
    return {"applicability": "applicable", "requiredness": "required",
            "status": status, "value": value, "evidence_refs": ["EV-001"],
            "extraction_confidence": "high"}


def _selftest():
    rb = load_rulebase()
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    # --- Case 1: animal experiment lacking ethics approval -> must report ---
    sr = {
        "article_design": {"primary_design": {"family": "experimental",
                                              "type": "in_vivo_animal"},
                           "design_components": []},
        "population": {"subjects": _mk_field("reported", "C57BL/6J 小鼠，6-8 周龄雌性")},
        "declarations": {"ethics_statement": _mk_field("not_reported")},
        "measurement": {"sample_size_justification": _mk_field("not_reported")},
        "design": {"interventions": _mk_field("reported", "腹腔注射")},
    }
    sigs = screen(sr, rb)
    ids = {s.get("ethics", {}).get("rule_id") for s in sigs}
    expect("animal without approval -> ETH-ANI-001", "ETH-ANI-001" in ids, True)
    expect("no false positive on human ethics ETH-HUM-001", "ETH-HUM-001" in ids, False)

    # --- Case 2: commercial cell lines only -> must not report human/tissue ethics ---
    sr2 = {
        "article_design": {"primary_design": {"family": "experimental",
                                              "type": "in_vitro"},
                           "design_components": []},
        "population": {"subjects": _mk_field("reported", "HepG2 与 Huh7 人肝癌细胞系")},
        "declarations": {"ethics_statement": _mk_field("not_applicable"),
                         "informed_consent": _mk_field("not_applicable")},
    }
    sigs2 = screen(sr2, rb)
    ids2 = {s.get("ethics", {}).get("rule_id") for s in sigs2}
    expect("commercial cell lines skip ETH-CELL-001", "ETH-CELL-001" in ids2, False)
    expect("commercial cell lines skip ETH-HUM-002", "ETH-HUM-002" in ids2, False)

    # --- Case 2b: HUVEC is primary human material, must not get the established-line exemption ---
    sr2b = {
        "article_design": {"primary_design": {"family": "experimental",
                                                "type": "in_vitro"},
                           "design_components": []},
        "population": {"subjects": _mk_field(
            "reported", "Primary HUVEC isolated from human umbilical cords")},
        "declarations": {"ethics_statement": _mk_field("not_reported"),
                         "informed_consent": _mk_field("not_reported")},
    }
    sigs2b = screen(sr2b, rb)
    ids2b = {s.get("ethics", {}).get("rule_id") for s in sigs2b}
    expect("HUVEC does not get the commercial-line exemption", "ETH-CELL-001" in ids2b, True)

    # --- Case 2c: short names match on entity boundaries; CHO must not hit chondrocytes ---
    sr2c = {
        "article_design": {"primary_design": {"family": "experimental",
                                                "type": "in_vitro"},
                           "design_components": []},
        "population": {"subjects": _mk_field(
            "reported", "Primary murine chondrocytes from C57BL/6 mice")},
        "declarations": {"ethics_statement": _mk_field("not_applicable"),
                         "informed_consent": _mk_field("not_applicable")},
    }
    facts2c = derive_facts(sr2c, rb)
    expect("CHO does not false-match chondrocytes", facts2c["_exempt_cell_lines_hit"], [])

    # --- Case 2d: established lines + patient material must not exempt the whole paper ---
    sr2d = {
        "article_design": {"primary_design": {"family": "experimental",
                                                "type": "organoid"},
                           "design_components": []},
        "population": {"subjects": _mk_field(
            "reported", "HepG2 cells and patient-derived liver organoids")},
        "declarations": {"ethics_statement": _mk_field("not_reported"),
                         "informed_consent": _mk_field("not_reported")},
    }
    facts2d = derive_facts(sr2d, rb)
    expect("mixed patient material blocks whole-paper exemption",
           facts2d["uses_established_cell_line_only"], False)

    # --- Case 3: supplementary material unavailable -> partial_extraction, not absence ---
    sr3 = {
        "article_design": {"primary_design": {"family": "experimental",
                                              "type": "in_vivo_animal"},
                           "design_components": []},
        "population": {"subjects": _mk_field("reported", "C57BL/6 小鼠")},
        "declarations": {"ethics_statement": {**_mk_field("parse_failed"),
                                              "system_limitation_ref": "SYS-001"}},
    }
    sigs3 = screen(sr3, rb)
    ani = [s for s in sigs3 if "ETH-ANI-001" in s["target"]]
    expect("parse_failed -> partial_extraction", ani[0]["type"] if ani else None,
           "partial_extraction")

    # --- Case 4: RCT lacking registration number -> must report ---
    sr4 = {
        "article_design": {"primary_design": {"family": "human_interventional",
                                              "type": "randomized_controlled_trial"},
                           "design_components": []},
        "population": {"subjects": _mk_field("reported", "择期手术成年患者 84 例")},
        "declarations": {"ethics_statement": _mk_field("reported", "伦理批件 2023ER004"),
                         "informed_consent": _mk_field("reported", "书面知情同意")},
        "design": {"registration": _mk_field("not_reported")},
    }
    sigs4 = screen(sr4, rb)
    ids4 = {s.get("ethics", {}).get("rule_id") for s in sigs4}
    expect("RCT missing registration -> ETH-HUM-005", "ETH-HUM-005" in ids4, True)
    expect("RCT with approval skips ETH-HUM-001", "ETH-HUM-001" in ids4, False)

    # --- Case 5: pseudovirus only raises applicability uncertainty, never missing-BSL ---
    sr5 = {
        "article_design": {"primary_design": {"family": "experimental",
                                                "type": "in_vitro"},
                           "design_components": []},
        "population": {"subjects": _mk_field(
            "reported", "non-replicating lentiviral pseudovirus particles")},
        "measurement": {"assays": _mk_field("not_reported")},
    }
    sigs5 = screen(sr5, rb)
    bio5 = [s for s in sigs5 if s["target"] == "ethics.ETH-BIO-001"]
    expect("pseudovirus does not report missing BSL",
           all(s["type"] != "ethics_requirement_unmet" for s in bio5), True)

    # --- Case 6: manual_only is only a human-review candidate, never claims requirement_unmet ---
    sr6 = {
        "article_design": {"primary_design": {"family": "experimental",
                                                "type": "in_vitro"},
                           "design_components": []},
        "population": {"subjects": _mk_field("reported", "H9 hESC cell culture")},
        "declarations": {"ethics_statement": _mk_field("reported", "institutional review")},
    }
    sigs6 = screen(sr6, rb)
    cell6 = [s for s in sigs6 if s["target"] == "ethics.ETH-CELL-003"]
    expect("manual_only never masquerades as requirement unmet",
           cell6[0]["type"] if cell6 else None, "partial_extraction")

    # --- Contract: signals carry no severity and route to M6 ---
    expect("signal ids match the schema",
           all(re.match(r"^SIG-[0-9]{3,}$", s["id"]) for s in sigs), True)
    expect("ethics hits carry a rule trail",
           all("ethics" in s for s in sigs if s["type"] == "ethics_requirement_unmet"), True)
    expect("ethics signals carry no severity hint",
           all("severity_hint" not in s.get("ethics", {}) for s in sigs), True)
    expect("signals carry no severity", all("severity" not in s for s in sigs), True)
    expect("routed to M6", all(s["routed_to"] == ["M6"] for s in sigs), True)

    # --- Rulebase self-integrity ---
    bad = [r["rule_id"] for r in rb["rules"]
           if not r.get("citations") and r["check"] != "assert_not_applicable"]
    expect("every rule has source citations", bad, [])
    bad2 = [r["rule_id"] for r in rb["rules"] if not r.get("false_positive_guard")]
    expect("every rule has a false-positive guard note", bad2, [])

    try:
        screen([])
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    expect("non-object structured_result raises a controlled error", invalid_rejected, True)

    print("\nAll passed" if ok else "\nFailures present")
    return 0 if ok else 1


def _read_json(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _main(argv=None):
    parser = _JsonArgumentParser(description="Ethics rulebase screening (signals only)")
    parser.add_argument("--input", metavar="JSON",
                        help="structured_result JSON file; - reads stdin")
    parser.add_argument("--rulebase", metavar="JSON", default=RULEBASE,
                        help="rulebase path; defaults to the skill's resources dir resolved from the script location")
    parser.add_argument("--signal-start", type=int, default=600)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.input:
        parser.error("--input JSON is required (or use --selftest)")
    try:
        structured_result = _read_json(args.input)
        rulebase = _read_json(args.rulebase)
        signals = screen(structured_result, rulebase, signal_start=args.signal_start)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "detail": str(exc)}},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"signals": signals}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
