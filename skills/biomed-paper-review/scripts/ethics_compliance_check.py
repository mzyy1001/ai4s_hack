#!/usr/bin/env python3
"""伦理合规筛查（一期能力，只用标准库，离线运行）。

把 `skills/biomed-paper-review/resources/ethics_rules.json` 的规范库
应用到 M1 抽出的结构化事实上，产出 `extraction_signal`
（`type: ethics_requirement_unmet`），交 **M6** 判定是否构成 finding。

**本模块不产出 finding。** 与 `statistical_forensics.py → M4` 是同一个模式：
工具层给出「规范要求 X，稿件未见 X」这一机器级观察，
由模块负责人的规则库决定它是否构成稿件问题、severity 多少。

为什么能离线
------------
规范库是**结构化要求索引**，不是外部数据库查询。这正好落在一期的定义里
并构成无网络时的离线保底。批件号真伪、注册号时序等需要统一外部证据层；
该层尚未接入本组件，本模块不做，也不假装做。

三条防误报设计
--------------
1. **适用性先行**：规则只在 `applies_when` 条件成立时才评估。
   纯细胞系研究不会被要求动物伦理批件。
2. **parse_failed 不等于缺失**：字段因补充材料不可得而 `parse_failed` 时，
   产出的是 `partial_extraction` 而不是 `ethics_requirement_unmet`
   —— 我们没看过，就不能说稿件没写（`00-contracts.md §6.4`）。
3. **反向规则**：`assert_not_applicable` 类规则（如商业化细胞系豁免）
   主动压制其他规则的误报。

用法
----
    from ethics_compliance_check import screen
    signals = screen(structured_result, evaluation_matrix_facts)

命令行：
    python3 <Skill 目录>/scripts/ethics_compliance_check.py --input structured_result_v2.json
    python3 <Skill 目录>/scripts/ethics_compliance_check.py --selftest
"""

import argparse
import json
import os
import re
import sys

# 脚本位于 skills/<name>/scripts/，规范库在同级的 resources/。
# 用 __file__ 相对定位，不写死任何绝对路径（L1 明确扣硬编码路径的分）。
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


# ---------------------------------------------------------------- 事实提取

def _get(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _field_text(field_obj):
    """把 extracted_field 的 value 压成可检索文本。"""
    if not isinstance(field_obj, dict):
        return ""
    v = field_obj.get("value")
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def _named_entity_hits(text, names):
    """按独立名称命中细胞系，避免 `CHO` 误命中 `chondrocyte`。"""
    hits = []
    for name in names:
        pattern = rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])"
        if re.search(pattern, text, re.I):
            hits.append(name)
    return hits


def derive_facts(structured_result, rb):
    """从 structured_result 推出 applies_when 需要的布尔事实。

    只用**已抽取到的**内容推断，抽取不确定时事实置 None（= 不确定），
    applies_when 命中 None 时规则不评估，改出 partial_extraction。
    """
    if not isinstance(structured_result, dict):
        raise ValueError("structured_result 必须是 JSON 对象")
    if not isinstance(rb, dict):
        raise ValueError("伦理规范库必须是 JSON 对象")
    ad = structured_result.get("article_design", {})
    if not isinstance(ad, dict):
        raise ValueError("article_design 必须是 JSON 对象")
    primary = ad.get("primary_design", {}) or {}
    comps = ad.get("design_components", []) or []
    if not isinstance(primary, dict):
        raise ValueError("article_design.primary_design 必须是 JSON 对象")
    if not isinstance(comps, list) or any(not isinstance(c, dict) for c in comps):
        raise ValueError("article_design.design_components 必须是对象数组")
    types = {primary.get("type")} | {c.get("type") for c in comps}
    families = {primary.get("family")} | {c.get("family") for c in comps}
    types.discard(None)
    families.discard(None)

    subjects_txt = _field_text(_get(structured_result, "population.subjects")) or ""
    subj_lower = subjects_txt.lower()

    exempt = rb.get("exempt_cell_lines", {}).get("lines", [])
    exempt_hit = _named_entity_hits(subjects_txt, exempt)

    # 是否只用了已建立的商业化细胞系
    human_primary_markers = ["human primary", "primary human", "human tissue",
                             "human organoid", "patient-derived", "patient derived",
                             "patient", "患者", "donor", "供者", "人源", "人体",
                             "biopsy", "活检", "surgical specimen", "手术标本",
                             "peripheral blood", "外周血", "pbmc", "huvec",
                             "human umbilical vein endothelial"]
    has_primary_human = any(m in subj_lower for m in human_primary_markers)

    # `virus`/`viral` 本身可指灭活样本、载体或假病毒。只有文本明确指向具感染性
    # 菌（毒）种/活体病原体时才置 True；仅有泛称时保留 None，禁止自动立缺失信号。
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

    # 弱势群体
    markers = rb.get("vulnerable_population_markers", {})
    all_markers = [m.lower() for m in markers.get("en", [])] + markers.get("zh", [])
    facts["vulnerable_population"] = any(m in subj_lower or m in subjects_txt
                                         for m in all_markers)
    facts["includes_minors"] = bool(
        re.search(r"child|pediatric|infant|neonat|minor|adolescen|儿童|婴|新生儿|未成年|青少年",
                  subjects_txt, re.I))
    return facts


# ---------------------------------------------------------------- 规则求值

def _applies(rule, facts):
    """返回 True / False / None（None = 事实不确定，不评估）。"""
    cond = rule.get("applies_when", {})
    if not cond:
        return True
    for key, want in cond.items():
        if key in ("jurisdiction_hint", "involves_pain_or_distress",
                   "animals_euthanized", "uses_identifiable_data",
                   "consent_waived", "gain_of_function",
                   "uses_chinese_human_genetic_resources",
                   "uses_foreign_genetic_resources"):
            # 这些事实一期无法从结构化结果可靠推出 —— 不自动评估
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
    """主入口。返回 extraction_signal 列表。

    合规（要求已满足）的规则**不产出信号** —— 沉默即通过。
    """
    if not isinstance(structured_result, dict):
        raise ValueError("structured_result 必须是 JSON 对象")
    if not isinstance(signal_start, int) or isinstance(signal_start, bool) or signal_start < 0:
        raise ValueError("signal_start 必须是非负整数")
    rb = load_rulebase() if rulebase is None else rulebase
    if not isinstance(rb, dict) or not isinstance(rb.get("rules"), list):
        raise ValueError("伦理规范库缺少 rules 数组")
    if any(not isinstance(rule, dict) for rule in rb["rules"]):
        raise ValueError("伦理规范库 rules 的每一项必须是 JSON 对象")
    facts = derive_facts(structured_result, rb)
    version = rb.get("rulebase_version")
    signals = []
    n = 0

    # 反向规则：先算出被豁免的规则集合
    suppressed = set()
    if facts.get("uses_established_cell_line_only"):
        suppressed |= {"ETH-CELL-001", "ETH-HUM-001", "ETH-HUM-002"}

    for rule in rb["rules"]:
        if rule["check"] == "assert_not_applicable":
            continue  # 反向规则不单独出信号
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
                f"[{rule['rule_id']}] {rule['title_zh']}：本条按规范库设定"
                f"**一律交人工判定**；自动化未判定要求未满足"
                f"（{rule.get('false_positive_guard','')}）。"))
            continue

        if applicable is None:
            signals.append(_sig(
                sid, "partial_extraction", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}：适用性所需事实"
                f"（{list(rule.get('applies_when', {}).keys())}）无法从结构化结果可靠推出，本条未评估。"))
            continue

        # 取字段
        fpath = rule.get("check_args", {}).get("field")
        if not fpath:
            continue
        field = _get(structured_result, fpath)
        status = (field or {}).get("status")

        # parse_failed / unresolved 不得判缺失
        if status in ("parse_failed", "unresolved", "ambiguous"):
            signals.append(_sig(
                sid, "partial_extraction", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}：字段 `{fpath}` 状态为 "
                f"{status}，我们没能读到，**不得据此判定稿件缺失**（00-contracts §6.4）。"))
            continue

        if status == "not_applicable":
            continue  # 设计上不适用，合规

        text = _field_text(field)

        # 子串型检查
        want_any = rule.get("check_args", {}).get("expect_substring_any")
        if want_any:
            if status == "reported" and any(w.lower() in text.lower() for w in want_any):
                continue  # 满足
            signals.append(_sig(
                sid, "ethics_requirement_unmet", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}：规范要求稿件报告 "
                f"{rule['manuscript_must_report']}，但 `{fpath}` 中未见相关表述"
                f"（检索词 {want_any}）。",
                {"rulebase_version": version}))
            continue

        want_contains = rule.get("check_args", {}).get("any")
        if rule["check"] == "field_contains_any" and want_contains:
            if status == "reported" and any(w.lower() in text.lower() for w in want_contains):
                continue
            signals.append(_sig(
                sid, "ethics_requirement_unmet", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}：`{fpath}` 中未见 {want_contains}。",
                {"rulebase_version": version}))
            continue

        # 存在性检查
        if status == "reported":
            continue
        if status == "not_reported":
            signals.append(_sig(
                sid, "ethics_requirement_unmet", rule,
                f"[{rule['rule_id']}] {rule['title_zh']}：规范要求稿件报告 "
                f"{rule['manuscript_must_report']}，已完整检索确认 `{fpath}` 未报告。",
                {"rulebase_version": version}))
    return signals


# ---------------------------------------------------------------- 自检
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

    # --- 案例 1：动物实验缺伦理批件 → 应报 ---
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
    expect("动物缺批件 → ETH-ANI-001", "ETH-ANI-001" in ids, True)
    expect("不误报人体伦理 ETH-HUM-001", "ETH-HUM-001" in ids, False)

    # --- 案例 2：纯商业细胞系 → 不应报人体/组织伦理 ---
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
    expect("商业细胞系不报 ETH-CELL-001", "ETH-CELL-001" in ids2, False)
    expect("商业细胞系不报 ETH-HUM-002", "ETH-HUM-002" in ids2, False)

    # --- 案例 2b：HUVEC 是原代人源材料，不得按既有细胞系豁免 ---
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
    expect("HUVEC 不走商业细胞系豁免", "ETH-CELL-001" in ids2b, True)

    # --- 案例 2c：短名称按实体边界匹配，CHO 不得命中 chondrocytes ---
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
    expect("CHO 不误命中 chondrocytes", facts2c["_exempt_cell_lines_hit"], [])

    # --- 案例 2d：既有细胞系 + 患者材料不能整篇豁免 ---
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
    expect("混合患者材料禁止整篇豁免",
           facts2d["uses_established_cell_line_only"], False)

    # --- 案例 3：补充材料不可得 → partial_extraction 而非缺失 ---
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
    expect("parse_failed → partial_extraction", ani[0]["type"] if ani else None,
           "partial_extraction")

    # --- 案例 4：RCT 缺注册号 → 应报 ---
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
    expect("RCT 缺注册 → ETH-HUM-005", "ETH-HUM-005" in ids4, True)
    expect("RCT 有批件不报 ETH-HUM-001", "ETH-HUM-001" in ids4, False)

    # --- 案例 5：假病毒只形成适用性不确定，不得报 BSL 缺失 ---
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
    expect("假病毒不报 BSL 缺失",
           all(s["type"] != "ethics_requirement_unmet" for s in bio5), True)

    # --- 案例 6：manual_only 只是人工候选，不得谎称 requirement_unmet ---
    sr6 = {
        "article_design": {"primary_design": {"family": "experimental",
                                                "type": "in_vitro"},
                           "design_components": []},
        "population": {"subjects": _mk_field("reported", "H9 hESC cell culture")},
        "declarations": {"ethics_statement": _mk_field("reported", "institutional review")},
    }
    sigs6 = screen(sr6, rb)
    cell6 = [s for s in sigs6 if s["target"] == "ethics.ETH-CELL-003"]
    expect("manual_only 不冒充要求未满足",
           cell6[0]["type"] if cell6 else None, "partial_extraction")

    # --- 契约：信号无 severity，路由到 M6 ---
    expect("信号 id 符合 schema",
           all(re.match(r"^SIG-[0-9]{3,}$", s["id"]) for s in sigs), True)
    expect("伦理命中带规则轨迹",
           all("ethics" in s for s in sigs if s["type"] == "ethics_requirement_unmet"), True)
    expect("伦理 signal 不携带 severity hint",
           all("severity_hint" not in s.get("ethics", {}) for s in sigs), True)
    expect("信号无 severity", all("severity" not in s for s in sigs), True)
    expect("路由到 M6", all(s["routed_to"] == ["M6"] for s in sigs), True)

    # --- 规范库自身完整性 ---
    bad = [r["rule_id"] for r in rb["rules"]
           if not r.get("citations") and r["check"] != "assert_not_applicable"]
    expect("每条规则都有出处引用", bad, [])
    bad2 = [r["rule_id"] for r in rb["rules"] if not r.get("false_positive_guard")]
    expect("每条规则都有防误报说明", bad2, [])

    try:
        screen([])
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    expect("非对象 structured_result 给出受控错误", invalid_rejected, True)

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


def _read_json(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _main(argv=None):
    parser = _JsonArgumentParser(description="伦理规范库筛查（只产 signal）")
    parser.add_argument("--input", metavar="JSON",
                        help="structured_result JSON 文件；- 表示 stdin")
    parser.add_argument("--rulebase", metavar="JSON", default=RULEBASE,
                        help="规范库路径；默认按脚本位置解析 Skill 内 resources")
    parser.add_argument("--signal-start", type=int, default=600)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.input:
        parser.error("必须提供 --input JSON（或 --selftest）")
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
