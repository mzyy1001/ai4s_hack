#!/usr/bin/env python3
"""路由器：决定这篇论文该跑哪些专家、每个专家读哪本规则、要跑哪些工具。

**这是纯代码，不是模型判断。** 上一版把「该读哪本规则」交给模型自己决定，
结果它读了最像总纲的那本（00-contracts）就没余力了，八本只读一本。
路由是确定性的调度问题，不该消耗模型注意力。

required_modules =
      design_mandatory_modules          研究设计决定的必跑模块
    ∪ candidate_triggered_modules       发现阶段候选路由到的模块
    ∪ tool_signal_triggered_modules     工具信号路由到的模块

**不默认跑满 M2–M7。** 一篇纯生信论文跑 M6 伦理只是浪费调用。
但每个模块跑与不跑都必须记录理由，否则无法区分「判断后认为不需要」与「漏了」。
"""

RULEBOOK = {
    "M2": "02-macro-logic.md",
    "M3": "03-experimental-methods.md",
    "M4": "04-statistics.md",
    "M5": "05-figures-and-charts.md",
    "M6": "06-ethics-compliance.md",
    "M7": "07-conclusions-discussion.md",
}

PACKET = {
    "M2": "cross_section", "M3": "methods", "M4": "statistics",
    "M5": "figures", "M6": "ethics", "M7": "claims",
}

# 候选类型 → 模块。与 references/00-routing.md §1 保持一致。
CANDIDATE_ROUTES = {
    "possible_internal_inconsistency": ["M2"],
    "possible_cross_section_inconsistency": ["RECONCILE"],
    "possible_reporting_omission": ["M2"],
    "possible_data_leakage": ["M2"],
    "possible_reference_problem": ["M2"],
    "possible_method_underreporting": ["M3"],
    "possible_cell_line_issue": ["M3"],
    "possible_identifier_issue": ["M3"],
    "possible_animal_necessity_issue": ["M3", "M6"],
    "possible_statistical_test_mismatch": ["M4"],
    "possible_sample_size_issue": ["M4"],
    "possible_numeric_inconsistency": ["M4", "M2"],
    "possible_multiplicity_issue": ["M4"],
    "possible_outcome_switching": ["M4"],
    "possible_figure_presentation_issue": ["M5"],
    "possible_figure_duplication": ["M5"],
    "possible_figure_text_contradiction": ["M5"],
    "possible_blot_annotation_issue": ["M5"],
    "possible_ethics_issue": ["M6"],
    "possible_registration_issue": ["M6"],
    "possible_consent_issue": ["M6"],
    "possible_unsupported_claim": ["M7"],
    "possible_overgeneralization": ["M7"],
    "possible_followup_overreach": ["M7"],
    "possible_causal_overreach": ["M7"],
    "possible_unit_dimension_issue": ["M4"],
}

# 研究设计 → 必跑模块。这些与有没有候选无关，是设计本身要求的。
DESIGN_MANDATORY = [
    (("randomi", "rct", "clinical trial", "临床试验", "随机"), ["M4", "M6", "M7"]),
    (("cohort", "case-control", "cross-sectional", "队列", "观察性"), ["M4", "M6", "M7"]),
    (("animal", "mice", "mouse", "rat", "in vivo", "动物"), ["M3", "M6"]),
    (("cell line", "in vitro", "culture", "细胞"), ["M3"]),
    (("meta-analysis", "systematic review", "荟萃"), ["M2", "M4", "M7"]),
]

# 工具信号 → 模块
SIGNAL_ROUTES = {
    "table_total_mismatch": ["M4", "M2"],
    "count_percentage_mismatch": ["M4", "M2"],
    "test_statistic_p_mismatch": ["M4"],
    "ci_estimate_mismatch": ["M4"],
    "grim_incompatible_mean": ["M4"],
    "ethics_requirement_unmet": ["M6"],
    "sequence_identifier_inconsistent": ["M3", "M2"],
    "figure_integrity_candidate": ["M5"],
    "external_validation_candidate": [],   # 按 check_type 细分，见下
}

X1_CHECK_ROUTES = {
    "cell_line_problematic": ["M3"],
    "rrid_resolves": ["M3"],
    "species_name_valid": ["M3"],
    "variant_position_range": ["M2", "M3"],
    "variant_reference_residue": ["M2", "M3"],
    "gene_symbol_excel_corruption": ["M2", "M3"],
    "gene_symbol_outdated": ["M2", "M3"],
    "gene_symbol_unrecognized": ["M2", "M3"],
    "reference_doi_resolves": ["M2"],
    "cited_work_retracted": ["M2", "M7"],
    "trial_registration_exists": ["M6"],
    "prospective_registration": ["M6"],
    "outcome_switching": ["M4", "M7"],
    "blot_band_molecular_weight": ["M5"],
    "ic50_order_of_magnitude": ["M5"],
    "compound_name_valid": ["M3", "M5"],
    "compound_molecular_weight": ["M3", "M5"],
    "pdb_entry_exists": ["M3", "M5"],
    "accession_exists": ["M7"],
}

MODULE_TOOLS = {
    "M3": ["sequence_identifier_audit", "external_figure_validation"],
    "M4": ["statistical_forensics", "normalize_biomed_units"],
    "M5": ["figure_integrity_audit"],
    "M6": ["ethics_compliance_check", "external_figure_validation"],
    "M2": ["external_figure_validation"],
}


def design_modules(study_design):
    """研究设计决定的必跑模块。"""
    d = (study_design or "").lower()
    out = {}
    for keys, mods in DESIGN_MANDATORY:
        hit = next((k for k in keys if k in d), None)
        if hit:
            for m in mods:
                out.setdefault(m, f"研究设计含「{hit}」，该设计必跑 {m}")
    return out


def candidate_modules(candidates):
    """候选触发的模块。未知类型兜底到 M2，并标记 fallback。"""
    out, reconcile, fallback = {}, [], []
    for c in candidates or []:
        if not isinstance(c, dict):
            continue
        ctype = c.get("candidate_type") or c.get("type") or ""
        cid = c.get("candidate_id", "?")
        mods = CANDIDATE_ROUTES.get(ctype)
        if mods is None:
            # 兜底而不是丢弃 —— 丢弃等于让这个候选永远无人处理。
            # **但必须校验模块名**：发现阶段的模型会自造名字（实测见过
            # "CHECKLIST"），直接透传会让下游按不存在的模块去找规则库而崩溃。
            suggested = [m for m in (c.get("suggested_modules") or [])
                         if m in RULEBOOK or m == "RECONCILE"]
            mods = suggested or ["M2"]
            fallback.append(cid)
        else:
            mods = [m for m in mods if m in RULEBOOK or m == "RECONCILE"]
        for m in mods:
            if m == "RECONCILE":
                reconcile.append(cid)
            else:
                out.setdefault(m, []).append(cid)
    return out, reconcile, fallback


def signal_modules(signals):
    out = {}
    for s in signals or []:
        st = s.get("type")
        mods = list(SIGNAL_ROUTES.get(st, []))
        if st == "external_validation_candidate":
            ct = (s.get("external_check") or {}).get("check_type")
            mods = list(X1_CHECK_ROUTES.get(ct, ["M2"]))
        for m in mods:
            if m not in RULEBOOK:
                continue                     # 同上：不透传未知模块名
            out.setdefault(m, []).append(s.get("id", "?"))
    return out


def plan(study_design, candidates, signals=None, telemetry=None):
    """产出完整路由计划。

    返回 dict：modules（要跑的）、skipped（不跑的及原因）、
    reconcile_candidates、required_references、required_tools。
    """
    dm = design_modules(study_design)
    cm, reconcile, fallback = candidate_modules(candidates)
    sm = signal_modules(signals)

    modules = {}
    for m, why in dm.items():
        modules.setdefault(m, {"reasons": [], "candidates": [], "signals": []})
        modules[m]["reasons"].append(why)
    for m, ids in cm.items():
        modules.setdefault(m, {"reasons": [], "candidates": [], "signals": []})
        modules[m]["reasons"].append(f"{len(ids)} 条候选路由至此")
        modules[m]["candidates"] += ids
    for m, ids in sm.items():
        modules.setdefault(m, {"reasons": [], "candidates": [], "signals": []})
        modules[m]["reasons"].append(f"{len(ids)} 条工具信号路由至此")
        modules[m]["signals"] += ids

    skipped = {m: "研究设计不要求，且无候选或信号指向该模块"
               for m in RULEBOOK if m not in modules}

    required_refs = sorted({RULEBOOK[m].replace(".md", "") for m in modules})
    required_tools = sorted({t for m in modules for t in MODULE_TOOLS.get(m, [])})

    if telemetry:
        telemetry.require_references(required_refs)
        telemetry.require_tools(required_tools)
        for m, info in modules.items():
            telemetry.module_decision(m, True, "；".join(info["reasons"]))
        for m, why in skipped.items():
            telemetry.module_decision(m, False, why)

    return {
        "modules": modules,
        "skipped": skipped,
        "reconcile_candidates": reconcile,
        "routing_fallback_candidates": fallback,
        "required_references": required_refs,
        "required_tools": required_tools,
        "rulebook_of": {m: RULEBOOK[m] for m in modules},
        "packet_of": {m: PACKET[m] for m in modules},
    }


def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    cands = [
        {"candidate_id": "CAND-001", "candidate_type": "possible_numeric_inconsistency"},
        {"candidate_id": "CAND-002", "candidate_type": "possible_cross_section_inconsistency"},
        {"candidate_id": "CAND-003", "candidate_type": "possible_weird_new_type"},
    ]
    p = plan("randomised controlled trial", cands)

    expect("RCT 必跑 M4/M6/M7", all(m in p["modules"] for m in ("M4", "M6", "M7")), True)
    expect("数值候选把 M2 拉进来", "M2" in p["modules"], True)
    expect("纯 RCT 不跑 M3", "M3" in p["skipped"], True)
    expect("跨节候选进 reconcile", p["reconcile_candidates"], ["CAND-002"])
    expect("未知类型兜底不丢弃", p["routing_fallback_candidates"], ["CAND-003"])
    expect("required_references 只含要跑的模块",
           p["required_references"],
           ["02-macro-logic", "04-statistics", "06-ethics-compliance",
            "07-conclusions-discussion"])
    expect("跳过的模块有理由", bool(p["skipped"].get("M3")), True)

    p2 = plan("in vitro cell line study", [])
    expect("体外研究跑 M3", "M3" in p2["modules"], True)
    expect("体外研究不必跑 M6", "M6" in p2["skipped"], True)

    sigs = [{"id": "SIG-901", "type": "external_validation_candidate",
             "external_check": {"check_type": "cited_work_retracted"}}]
    p3 = plan("cohort study", [], sigs)
    expect("X1 撤稿信号路由到 M2 与 M7",
           all(m in p3["modules"] for m in ("M2", "M7")), True)

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
