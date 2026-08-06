#!/usr/bin/env python3
"""契约校验器 —— 只用 Python 标准库，沙箱可运行。

两层校验：

  1. schema 层：全部 *.schema.json 可解析、跨文件 $ref 目标存在、
     枚举定义唯一（同名枚举在不同文件中取值必须一致）。
  2. 实例层：对 tools/fixtures/*.json 执行 references/00-contracts.md §11
     的契约 lint 检查表。

用法：
    python3 tools/validate_schemas.py           # schema 层 + 实例层
    python3 tools/validate_schemas.py --schema  # 只跑 schema 层
    python3 tools/validate_schemas.py --quiet   # 只输出失败项与总结

退出码：0 = 全部通过；1 = 存在失败项。
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(ROOT, "skills", "biomed-paper-review", "schemas")
FIXTURE_DIR = os.path.join(ROOT, "tools", "fixtures")
REPORT_TEMPLATE = os.path.join(ROOT, "skills", "biomed-paper-review", "templates",
                               "review_report.md")

# ---------------------------------------------------------------- 契约枚举
# 与 references/00-contracts.md 保持同步；任一处改动必须同步另一处。

SOURCE_TYPE = {"explicit_main_text", "explicit_table", "explicit_figure_caption",
               "axis_readable", "pixel_estimated"}
EXPLICIT_REPORTED = {"explicit_main_text", "explicit_table", "explicit_figure_caption"}
VISUALLY_DERIVED = {"axis_readable", "pixel_estimated"}
EXTRACTION_METHOD = {"text_parse", "table_parse", "caption_parse", "axis_read",
                     "visual_estimation", "ocr_text"}
METHOD_BY_SOURCE = {
    "explicit_main_text": {"text_parse", "ocr_text"},
    "explicit_table": {"table_parse", "ocr_text"},
    "explicit_figure_caption": {"caption_parse", "ocr_text"},
    "axis_readable": {"axis_read"},
    "pixel_estimated": {"visual_estimation"},
}
FIELD_STATUS = {"reported", "not_reported", "not_applicable", "ambiguous",
                "conflicting", "parse_failed", "unresolved"}
APPLICABILITY = {"applicable", "not_applicable", "applicability_uncertain"}
REQUIREDNESS = {"required", "recommended", "optional"}
SEVERITY = {"critical", "major", "minor", "info"}
SIGNAL_TYPE = {"source_value_conflict", "claim_without_resolved_evidence_link",
               "ambiguous_study_design", "unresolved_cross_reference",
               "partial_extraction", "ambiguous_extraction"}
SYSLIM_CATEGORY = {"parse_failed", "figure_unreadable", "table_unparseable",
                   "supplement_inaccessible", "section_missing_from_input",
                   "ocr_low_quality", "encoding_error", "input_truncated"}
KEY_DATA_STATUS = {"reported", "compatible_multiple_sources", "conflicting",
                   "ambiguous", "pending_visual_resolution", "parse_failed"}
NUMERIC_TYPE = {"point", "interval", "lower_bound", "upper_bound", "categorical"}
REVIEW_MODULES = {"M2", "M3", "M4", "M5", "M6", "M7"}
CONFIDENCE = {"high", "medium", "low"}

STAGE_DEPS = {"stage_2": "stage_1", "stage_3": "stage_1", "stage_3b": "stage_2",
              "stage_4": "stage_3b", "stage_5": "stage_4"}
SEVERITY_WEIGHT = {"critical": 25, "major": 10, "minor": 3, "info": 0}
SEVERITY_RANK = {"critical": 3, "major": 2, "minor": 1, "info": 0}


class Report:
    def __init__(self, quiet=False):
        self.failures = []
        self.passes = 0
        self.quiet = quiet

    def check(self, cond, label, detail=""):
        if cond:
            self.passes += 1
            if not self.quiet:
                print(f"  \033[32mPASS\033[0m {label}")
        else:
            self.failures.append((label, detail))
            print(f"  \033[31mFAIL\033[0m {label}" + (f" — {detail}" if detail else ""))

    def section(self, name):
        if not self.quiet:
            print(f"\n=== {name} ===")


# ---------------------------------------------------------------- schema 层

def check_schemas(rep):
    rep.section("Schema 层")
    if not os.path.isdir(SCHEMA_DIR):
        rep.check(False, "schemas/ 目录存在", SCHEMA_DIR)
        return {}

    schemas, ids = {}, {}
    for fn in sorted(os.listdir(SCHEMA_DIR)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(SCHEMA_DIR, fn)
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            schemas[fn] = doc
            ids[doc.get("$id", fn)] = fn
            rep.check(True, f"{fn} 可解析")
        except Exception as exc:
            rep.check(False, f"{fn} 可解析", str(exc))

    # 跨文件 $ref 目标存在
    missing = []
    for fn, doc in schemas.items():
        for ref in set(re.findall(r'"\$ref":\s*"([^"#]+)#?', json.dumps(doc))):
            if ref and ref not in ids:
                missing.append(f"{fn} -> {ref}")
    rep.check(not missing, "全部跨文件 $ref 目标存在", "; ".join(missing))

    # 枚举一致性：source_type 必须处处一致
    blob = json.dumps(schemas, ensure_ascii=False)
    deprecated = ['"figure_axis"', '"figure_pixel"', '"figure_caption"',
                  '"min_group_n"', '"extraction_quality_findings"',
                  '"source_conflict_signals"', '"unresolved_evidence_links"']
    hits = [d for d in deprecated if d in blob]
    rep.check(not hits, "schema 中无已废弃标识符", ", ".join(hits))

    common = schemas.get("common.schema.json", {})
    st = set(common.get("$defs", {}).get("source_type", {}).get("enum", []))
    rep.check(st == SOURCE_TYPE, "common.source_type 枚举与契约一致",
              f"schema={sorted(st)}")

    fs = set(common.get("$defs", {}).get("field_status", {}).get("enum", []))
    rep.check(fs == FIELD_STATUS, "common.field_status 枚举与契约一致",
              f"schema={sorted(fs)}")

    fm = schemas.get("finding.schema.json", {})
    mod_ref = json.dumps(fm.get("properties", {}).get("module", {}))
    rep.check("module_id_review" in mod_ref,
              "finding.module 指向 M2–M7（M1 非法）", mod_ref[:80])
    rep.check(fm.get("properties", {}).get("id", {}).get("pattern") == "^M[2-7]-[0-9]{3}$",
              "finding.id pattern 排除 M1")

    figrec = schemas.get("figure_record.schema.json", {})
    neg = json.dumps(figrec.get("not", {}))
    rep.check("issues" in neg and "findings" in neg,
              "figure_record 禁止携带 finding（Figure Parser 不评判）")

    syslim = schemas.get("system_limitation.schema.json", {})
    rep.check("severity" in json.dumps(syslim.get("not", {})),
              "system_limitation 禁止 severity")

    sig = schemas.get("extraction_signal.schema.json", {})
    rep.check("severity" in json.dumps(sig.get("not", {})),
              "extraction_signal 禁止 severity")
    sig_enum = set(sig.get("properties", {}).get("type", {}).get("enum", []))
    rep.check(sig_enum == SIGNAL_TYPE, "signal type 六值且无 parse_failure",
              f"schema={sorted(sig_enum)}")

    try:
        with open(REPORT_TEMPLATE, encoding="utf-8") as fh:
            template = fh.read()
        stale = [token for token in ("confidence_score", "extraction_gap_penalty", "min_group_n",
                                     "methods.groups", "evidence.locator", "七维审核")
                 if token in template]
        headings = ["## 一、执行摘要", "## 二、结构化结果表", "## 三、图表解读与原图定位",
                    "## 四、审核发现", "## 五、抽取信号", "## 六、系统限制",
                    "## 七、覆盖率明细", "## 八、人工复核建议"]
        rep.check(not stale and all(template.count(h) == 1 for h in headings),
                  "报告模板已迁移到八节新契约且无废弃字段", ", ".join(stale))
    except OSError as exc:
        rep.check(False, "报告模板可读取", str(exc))

    return schemas


# ---------------------------------------------------------------- 实例层

def walk(node, path="$"):
    """深度遍历，产出 (path, dict) 对。"""
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")


def collect_observations(inst):
    obs = []
    for path, node in walk(inst):
        if isinstance(node, dict) and "observation_id" in node and "provenance" in node:
            obs.append((path, node))
    return obs


def close_enough(actual, expected, tolerance=0.0005):
    return isinstance(actual, (int, float)) and abs(actual - expected) <= tolerance


def check_instance(rep, name, inst):
    rep.section(f"实例层 · {name}")
    registry = inst.get("evidence_registry", {})

    # --- 证据引用可解析 ---
    bad_refs = []
    for path, node in walk(inst):
        if not isinstance(node, dict):
            continue
        for key in ("evidence_refs",):
            for ref in node.get(key, []) or []:
                if ref not in registry:
                    bad_refs.append(f"{path}.{key}:{ref}")
        pr = node.get("provenance")
        if isinstance(pr, dict):
            r = pr.get("evidence_ref")
            if r and r not in registry:
                bad_refs.append(f"{path}.provenance:{r}")
    rep.check(not bad_refs, "全部 evidence_ref 解析到登记表条目", "; ".join(bad_refs[:5]))

    # --- 登记表自身合法 ---
    ev_bad = []
    for eid, e in registry.items():
        if e.get("id") != eid:
            ev_bad.append(f"{eid}: id 与键不符")
        if e.get("type") == "absence":
            if "quote" in e:
                ev_bad.append(f"{eid}: absence 型含 quote")
            if "locator" in e:
                ev_bad.append(f"{eid}: absence 型含 locator")
            if not e.get("searched_locations") or not e.get("search_terms"):
                ev_bad.append(f"{eid}: absence 型缺检索范围或检索词")
        elif e.get("type") == "present":
            if "locator" not in e:
                ev_bad.append(f"{eid}: present 型缺 locator")
        else:
            ev_bad.append(f"{eid}: type 非法")
    rep.check(not ev_bad, "证据登记表条目合法（absence 无引文）", "; ".join(ev_bad[:5]))

    # --- provenance / derivation ---
    prov_bad, pixel_bad = [], []
    for path, node in walk(inst):
        if not isinstance(node, dict):
            continue
        pr = node.get("provenance")
        if not isinstance(pr, dict):
            continue
        st = pr.get("source_type")
        if st not in SOURCE_TYPE:
            prov_bad.append(f"{path}: source_type={st}")
            continue
        der = pr.get("derivation")
        if not isinstance(der, dict) or "extraction_method" not in der or "ocr_used" not in der:
            prov_bad.append(f"{path}: 缺 derivation")
            continue
        if der["extraction_method"] not in METHOD_BY_SOURCE[st]:
            prov_bad.append(f"{path}: {st} 不允许 {der['extraction_method']}")
        if (der["extraction_method"] == "ocr_text") != (der["ocr_used"] is True):
            prov_bad.append(f"{path}: ocr_text 与 ocr_used=true 必须同时成立")
        if st == "pixel_estimated":
            val = node.get("value", {})
            if not isinstance(val, dict) or val.get("type") not in {"interval", "lower_bound", "upper_bound"}:
                pixel_bad.append(f"{path}: pixel 值非区间")
            if node.get("extraction_confidence") != "low":
                pixel_bad.append(f"{path}: pixel 置信度非 low")
            if node.get("manual_review_needed") is not True:
                pixel_bad.append(f"{path}: pixel 未置 manual_review_needed")
    rep.check(not prov_bad, "provenance 带 derivation 且组合合法", "; ".join(prov_bad[:5]))
    rep.check(not pixel_bad, "pixel_estimated 满足四项强制约束", "; ".join(pixel_bad[:5]))

    # --- 数值形式 ---
    num_bad = []
    for path, node in walk(inst):
        if isinstance(node, dict) and "observation_id" in node:
            v = node.get("value")
            if not isinstance(v, dict) or v.get("type") not in NUMERIC_TYPE:
                num_bad.append(f"{path}: value 非 numeric 对象")
            elif v.get("type") == "interval" and v.get("low", 0) > v.get("high", 0):
                num_bad.append(f"{path}: interval.low > interval.high")
            unc = node.get("uncertainty")
            if not isinstance(unc, dict):
                num_bad.append(f"{path}: 缺 uncertainty")
            elif unc.get("type") in {"95CI", "IQR", "range"}:
                if not isinstance(unc.get("low"), (int, float)) or not isinstance(unc.get("high"), (int, float)):
                    num_bad.append(f"{path}: 区间型 uncertainty 缺数值 low/high")
                elif unc["low"] > unc["high"]:
                    num_bad.append(f"{path}: uncertainty.low > uncertainty.high")
            elif unc.get("type") in {"SD", "SEM"} and not isinstance(unc.get("value"), (int, float)):
                num_bad.append(f"{path}: SD/SEM 缺数值 value")
    rep.check(not num_bad, "全部观测数值为 numeric 变体对象", "; ".join(num_bad[:5]))

    # --- structured_result 状态机 ---
    sr = inst.get("structured_result")
    if sr:
        version = sr.get("version")
        pending, field_bad = [], []
        matrix_bad = []
        for path, node in walk(sr):
            if not isinstance(node, dict) or "status" not in node:
                continue
            if "applicability" not in node:
                continue  # 既不是 extracted_field 也不是 matrix_entry
            if "value" not in node:
                # evaluation_matrix 条目：路由索引，不承载 na_reason /
                # system_limitation_ref —— 那些是字段本身的属性，重复存储会漂移。
                if not node.get("applies_to"):
                    matrix_bad.append(f"{path}: matrix 条目缺 applies_to")
                if node.get("status") not in FIELD_STATUS:
                    matrix_bad.append(f"{path}: status={node.get('status')}")
                for forbidden in ("na_reason", "system_limitation_ref", "value"):
                    if forbidden in node:
                        matrix_bad.append(f"{path}: matrix 条目不得携带 {forbidden}")
                continue
            s = node["status"]
            if s not in FIELD_STATUS:
                field_bad.append(f"{path}: status={s}")
            if node.get("applicability") not in APPLICABILITY:
                field_bad.append(f"{path}: applicability={node.get('applicability')}")
            if node.get("requiredness") not in REQUIREDNESS:
                field_bad.append(f"{path}: requiredness={node.get('requiredness')}")
            if s != "reported" and node.get("value") is not None:
                field_bad.append(f"{path}: 非 reported 但 value 非 null")
            if s == "not_applicable" and not node.get("na_reason"):
                field_bad.append(f"{path}: not_applicable 缺 na_reason")
            if s == "parse_failed" and not node.get("system_limitation_ref"):
                field_bad.append(f"{path}: parse_failed 缺 system_limitation_ref")
            if s == "parse_failed":
                sys_ids = {x.get("id") for x in inst.get("all_system_limitations", [])}
                if node.get("system_limitation_ref") not in sys_ids:
                    field_bad.append(f"{path}: system_limitation_ref 无法解析")
            if s == "unresolved":
                pending.append(path)
                if not node.get("resolution_state"):
                    field_bad.append(f"{path}: unresolved 缺 resolution_state")
                if node.get("system_limitation_ref"):
                    field_bad.append(f"{path}: unresolved 不得填 system_limitation_ref")
            if s in {"reported", "not_reported"} and not node.get("evidence_refs"):
                field_bad.append(f"{path}: {s} 缺证据")
            if s == "reported" and node.get("evidence_refs"):
                if not any((registry.get(ref) or {}).get("type") == "present"
                           for ref in node["evidence_refs"]):
                    field_bad.append(f"{path}: reported 缺 present 证据")
            if s == "not_reported" and node.get("evidence_refs"):
                if not any((registry.get(ref) or {}).get("type") == "absence" and
                           (registry.get(ref) or {}).get("search_result") == "no_match"
                           for ref in node["evidence_refs"]):
                    field_bad.append(f"{path}: not_reported 缺 no_match absence 证据")
        rep.check(not field_bad, "extracted_field 三维度与状态机合法", "; ".join(field_bad[:5]))
        rep.check(not matrix_bad, "evaluation_matrix 条目为纯索引（不复制字段属性）",
                  "; ".join(matrix_bad[:5]))

        kd_pending = [k.get("id") for k in sr.get("key_data", [])
                      if k.get("status") == "pending_visual_resolution"]
        if version == "v2":
            rep.check(not pending, "v2 中无 status=unresolved 残留", "; ".join(pending[:5]))
            rep.check(not kd_pending, "v2 中无 key_data pending 残留", "; ".join(map(str, kd_pending)))
            rep.check(sr.get("stage_3b_executed") is True, "v2 标记 stage_3b_executed=true")
        else:
            rep.check(True, f"structured_result 版本={version}（v1 允许 pending）")

        # key_data 组约束
        kd_bad = []
        for k in sr.get("key_data", []):
            st = k.get("status")
            if st not in KEY_DATA_STATUS:
                kd_bad.append(f"{k.get('id')}: status={st}")
            if st in {"conflicting", "ambiguous", "pending_visual_resolution", "parse_failed"}:
                if k.get("canonical_observation") is not None:
                    kd_bad.append(f"{k.get('id')}: {st} 但 canonical 非 null")
                if k.get("reporting_completeness") != "not_assessed":
                    kd_bad.append(f"{k.get('id')}: canonical 为 null 但完整性已判定")
            if k.get("canonical_observation") and not k.get("canonical_rationale"):
                kd_bad.append(f"{k.get('id')}: 选出 canonical 但无理由")
            if st == "conflicting" and len(k.get("conflicting_observations", [])) < 2:
                kd_bad.append(f"{k.get('id')}: conflicting 但冲突观测不足 2")
            obs_list = k.get("observations", [])
            obs_ids = [o.get("observation_id") for o in obs_list]
            ids_in = set(obs_ids)
            if len(obs_ids) != len(ids_in):
                kd_bad.append(f"{k.get('id')}: observation_id 重复")
            canonical = k.get("canonical_observation")
            if st == "reported":
                if len(obs_list) != 1 or canonical not in ids_in:
                    kd_bad.append(f"{k.get('id')}: reported 必须恰有一个且选中 canonical")
                if k.get("compatible_observations") or k.get("conflicting_observations"):
                    kd_bad.append(f"{k.get('id')}: reported 不得登记配对关系")
            if st == "compatible_multiple_sources":
                if len(obs_list) < 2 or canonical not in ids_in:
                    kd_bad.append(f"{k.get('id')}: compatible_multiple_sources 缺合法 canonical")
                if set(k.get("compatible_observations", [])) != ids_in:
                    kd_bad.append(f"{k.get('id')}: 全兼容组必须列出全部 observation id")
                if k.get("conflicting_observations"):
                    kd_bad.append(f"{k.get('id')}: 全兼容组不得含冲突观测")
            if st in {"pending_visual_resolution", "parse_failed"} and obs_list:
                kd_bad.append(f"{k.get('id')}: {st} 时 observations 必须为空")
            if st == "parse_failed":
                ref = k.get("system_limitation_ref")
                sys_ids = {x.get("id") for x in inst.get("all_system_limitations", [])}
                if ref not in sys_ids:
                    kd_bad.append(f"{k.get('id')}: parse_failed 的 system_limitation_ref 无法解析")
            pair_refs = k.get("conflicting_observations", []) + k.get("compatible_observations", [])
            for key in ("conflicting_observations", "compatible_observations"):
                refs = k.get(key, [])
                if len(refs) != len(set(refs)):
                    kd_bad.append(f"{k.get('id')}: {key} 内部存在重复 id")
            for ref in pair_refs:
                if ref not in ids_in:
                    kd_bad.append(f"{k.get('id')}: 引用了不存在的 {ref}")
        rep.check(not kd_bad, "key_data 观测组约束成立", "; ".join(kd_bad[:5]))

        # 覆盖率原始数据自洽
        ci = sr.get("coverage_inputs", {})
        if ci:
            total = ci.get("required_applicable_total", -1)
            got = len(ci.get("resolved", [])) + len(ci.get("unresolved", []))
            rep.check(total == got, "coverage_inputs 分子分母自洽",
                      f"total={total} resolved+unresolved={got}")

    # --- finding ---
    findings = inst.get("all_findings", [])
    f_bad = []
    for f in findings:
        if f.get("module") not in REVIEW_MODULES:
            f_bad.append(f"{f.get('id')}: module={f.get('module')}")
        if f.get("severity") not in SEVERITY:
            f_bad.append(f"{f.get('id')}: severity={f.get('severity')}")
        if not f.get("evidence_refs"):
            f_bad.append(f"{f.get('id')}: evidence_refs 为空")
        if f.get("severity") in {"critical", "major"}:
            if not (f.get("manual_review") or {}).get("action"):
                f_bad.append(f"{f.get('id')}: >=major 无 action")
        if f.get("review_confidence") not in CONFIDENCE:
            f_bad.append(f"{f.get('id')}: review_confidence={f.get('review_confidence')}")
    rep.check(not f_bad, "finding 契约成立（无 M1、证据非空、major 有动作）",
              "; ".join(f_bad[:5]))

    # --- signal / system_limitation ---
    s_bad = []
    for s in inst.get("all_extraction_signals", []):
        if s.get("type") not in SIGNAL_TYPE:
            s_bad.append(f"{s.get('id')}: type={s.get('type')}")
        if "severity" in s:
            s_bad.append(f"{s.get('id')}: 携带 severity")
        if s.get("type") == "source_value_conflict" and s.get("produced_by") != "stage_3b":
            s_bad.append(f"{s.get('id')}: 冲突 signal 非 Stage 3b 产出")
    rep.check(not s_bad, "extraction_signal 契约成立", "; ".join(s_bad[:5]))

    l_bad = []
    for l in inst.get("all_system_limitations", []):
        if l.get("category") not in SYSLIM_CATEGORY:
            l_bad.append(f"{l.get('id')}: category={l.get('category')}")
        if "severity" in l:
            l_bad.append(f"{l.get('id')}: 携带 severity")
    rep.check(not l_bad, "system_limitation 契约成立（无 severity）", "; ".join(l_bad[:5]))

    # --- execution_scope 依赖图 ---
    scope = inst.get("execution_scope", {})
    stages = set(scope.get("executed_stages", []))
    dep_bad = [f"{s} 需要 {d}" for s, d in STAGE_DEPS.items()
               if s in stages and d not in stages]
    rep.check(not dep_bad, "阶段依赖图合法（无阶段消费未产出的产物）", "; ".join(dep_bad))

    mode = scope.get("mode")
    sub = scope.get("submode")
    mods = scope.get("executed_modules", [])
    scope_bad = []
    for key in ("executed_stages", "executed_modules", "skipped_modules", "fields",
                "assets", "observations", "supplements"):
        values = scope.get(key, [])
        if len(values) != len(set(values)):
            scope_bad.append(f"{key} 含重复值")
    if set(mods) & set(scope.get("skipped_modules", [])):
        scope_bad.append("executed_modules 与 skipped_modules 重叠")
    if mods and set(mods) | set(scope.get("skipped_modules", [])) != REVIEW_MODULES:
        scope_bad.append("已执行与跳过模块未完整划分 M2–M7")
    if mods and not {"stage_4", "stage_5"}.issubset(stages):
        scope_bad.append("执行审核模块但未声明 stage_4/stage_5")
    if mode == "structured_extraction" and not {"stage_1", "stage_2"}.issubset(stages):
        scope_bad.append("structured_extraction 缺 stage_1/stage_2")
    if sub == "interpretation_only" and not {"stage_1", "stage_3"}.issubset(stages):
        scope_bad.append("interpretation_only 缺 stage_1/stage_3")
    if sub == "figure_review" and "stage_3" not in stages:
        scope_bad.append("figure_review 缺 stage_3")
    if mode == "full_review" and "stage_3" not in stages:
        scope_bad.append("full_review 缺 stage_3")

    obs_by_id = {}
    for path, obs in collect_observations(inst):
        obs_by_id.setdefault(obs.get("observation_id"), []).append((path, obs))
    for oid in scope.get("observations", []):
        copies = obs_by_id.get(oid, [])
        if not copies:
            scope_bad.append(f"scope observation 无法解析: {oid}")
            continue
        signatures = {json.dumps({"value": o.get("value"), "provenance": o.get("provenance")},
                                 sort_keys=True, ensure_ascii=False) for _, o in copies}
        if len(signatures) != 1:
            scope_bad.append(f"scope observation 重复副本不一致: {oid}")
    rep.check(not scope_bad, "execution_scope 集合、模式与 observation 分母合法",
              "; ".join(scope_bad[:8]))
    if mode == "figure_analysis":
        rep.check(sub in {"interpretation_only", "figure_review"},
                  "figure_analysis 声明了 submode", str(sub))
    else:
        rep.check(sub is None, "非 figure_analysis 模式 submode 为 null", str(sub))
    if mode == "full_review":
        rep.check(set(mods) == REVIEW_MODULES, "full_review 跑满六个审核模块", str(mods))
    if sub == "figure_review":
        rep.check(mods == ["M5"], "figure_review 只跑 M5", str(mods))

    # --- 评分互斥与 partial ---
    has_rc = "review_confidence" in inst
    has_oc = "output_confidence" in inst
    has_risk = "manuscript_risk_score" in inst
    rep.check(not (has_rc and has_oc), "review_confidence 与 output_confidence 互斥")
    if mods:
        rep.check(has_rc and not has_oc, "跑过审核模块 → 用 review_confidence")
        rep.check(has_risk, "跑过审核模块 → 输出 manuscript_risk_score")
    else:
        rep.check(has_oc and not has_rc, "未跑审核模块 → 用 output_confidence")
        rep.check(not has_risk, "未跑审核模块 → 不输出 manuscript_risk_score")

    if has_risk:
        risk = inst["manuscript_risk_score"]
        partial_expected = set(risk.get("executed_modules", [])) != REVIEW_MODULES
        rep.check(risk.get("partial") == partial_expected,
                  "partial 标记与实际执行模块一致",
                  f"partial={risk.get('partial')} expected={partial_expected}")
        if risk.get("partial"):
            rep.check(risk.get("comparable_to_full_review") is False,
                      "partial 分数标记为不可与完整审核比较")

        score_bad = []
        if risk.get("executed_modules") != mods or risk.get("skipped_modules") != scope.get("skipped_modules", []):
            score_bad.append("risk_score 模块范围与 execution_scope 不一致")
        finding_by_id = {f.get("id"): f for f in findings}
        clusters = inst.get("issue_clusters", [])
        seen_members = []
        category_scores = {}
        critical_seen = False
        for c in clusters:
            member_ids = c.get("member_findings", [])
            members = [finding_by_id.get(fid) for fid in member_ids]
            if not member_ids or any(m is None for m in members):
                score_bad.append(f"{c.get('cluster_id')}: member finding 无法解析")
                continue
            seen_members.extend(member_ids)
            expected_rep = sorted(members, key=lambda f: (-SEVERITY_RANK[f["severity"]], f["id"]))[0]
            if c.get("representative_finding") != expected_rep["id"]:
                score_bad.append(f"{c.get('cluster_id')}: representative 不符合 severity/id 顺序")
            max_severity = expected_rep["severity"]
            if c.get("max_severity") != max_severity:
                score_bad.append(f"{c.get('cluster_id')}: max_severity 错误")
            if set(c.get("categories", [])) != {m["category"] for m in members}:
                score_bad.append(f"{c.get('cluster_id')}: categories 与成员不一致")
            member_evidence = {ref for m in members for ref in m.get("evidence_refs", [])}
            if set(c.get("evidence_refs", [])) != member_evidence:
                score_bad.append(f"{c.get('cluster_id')}: evidence_refs 未完整合并")
            category_scores.setdefault(expected_rep["category"], 0)
            category_scores[expected_rep["category"]] += SEVERITY_WEIGHT[max_severity]
            critical_seen = critical_seen or max_severity == "critical"
        if sorted(seen_members) != sorted(finding_by_id):
            score_bad.append("all_findings 未被 issue_clusters 恰好覆盖一次")
        expected_risk = min(100, sum(min(30, value) for value in category_scores.values()))
        if risk.get("value") != expected_risk:
            score_bad.append(f"risk value={risk.get('value')} expected={expected_risk}")
        expected_band = ("routine_review" if expected_risk <= 19 else
                         "clarification_needed" if expected_risk <= 49 else
                         "major_revision_suggested")
        if risk.get("band") != expected_band:
            score_bad.append(f"band={risk.get('band')} expected={expected_band}")
        if risk.get("priority_manual_review") is not critical_seen:
            score_bad.append("priority_manual_review 与 critical 簇不一致")
        rep.check(not score_bad, "issue_clusters 与 manuscript_risk_score 可复算",
                  "; ".join(score_bad[:8]))

        plan_bad = []
        major_ids = {f["id"] for f in findings if f.get("severity") in {"critical", "major"}}
        planned_ids = []
        for item in inst.get("manual_review_plan", []):
            for fid in item.get("finding_ids", []):
                if fid not in finding_by_id:
                    plan_bad.append(f"复核计划引用不存在 finding: {fid}")
                planned_ids.append(fid)
        if not major_ids.issubset(set(planned_ids)):
            plan_bad.append(f"major/critical 未全部进入复核计划: {sorted(major_ids - set(planned_ids))}")
        rep.check(not plan_bad, "major/critical findings 均有报告级复核动作",
                  "; ".join(plan_bad[:5]))

    # --- 覆盖率分母 ---
    cov = inst.get("extraction_coverage")
    cb = inst.get("coverage_breakdown", {})
    if cov and cb:
        den = cb.get("scope_denominators", {})
        got = len(cb.get("resolved_fields", [])) + len(cb.get("unresolved_required_fields", []))
        rep.check(den.get("required_fields_total") == got,
                  "coverage_breakdown 分子分母自洽",
                  f"total={den.get('required_fields_total')} sum={got}")
        fr = cov.get("field_resolution", {})
        rep.check(fr.get("total") == den.get("required_fields_total"),
                  "覆盖率分母取自 execution_scope",
                  f"rate.total={fr.get('total')} scope={den.get('required_fields_total')}")
        for key in ("asset_readability", "supplement_accessibility"):
            r = cov.get(key, {})
            if r.get("total") == 0:
                rep.check(r.get("rate") == 1.0, f"{key} 分母为 0 时记 1.0", str(r))

        cov_bad = []
        if den.get("assets_total") != len(scope.get("assets", [])):
            cov_bad.append("assets_total 不等于 execution_scope.assets 长度")
        if den.get("supplements_total") != len(scope.get("supplements", [])):
            cov_bad.append("supplements_total 不等于 execution_scope.supplements 长度")
        covered_fields = set(cb.get("resolved_fields", [])) | {
            x.get("field_path") for x in cb.get("unresolved_required_fields", [])
        }
        if not covered_fields.issubset(set(scope.get("fields", []))):
            cov_bad.append("coverage 字段超出 execution_scope.fields")
        parts = [
            ("field_resolution", len(cb.get("resolved_fields", [])), den.get("required_fields_total", 0)),
            ("asset_readability", den.get("assets_total", 0) - len(cb.get("unreadable_assets", [])),
             den.get("assets_total", 0)),
            ("supplement_accessibility",
             den.get("supplements_total", 0) - len(cb.get("inaccessible_supplements", [])),
             den.get("supplements_total", 0)),
        ]
        exact_rates = []
        for key, resolved, total in parts:
            item = cov.get(key, {})
            expected_rate = 1.0 if total == 0 else resolved / total
            exact_rates.append(expected_rate)
            if item.get("resolved") != resolved or item.get("total") != total:
                cov_bad.append(f"{key} 分子分母错误")
            if not close_enough(item.get("rate"), expected_rate):
                cov_bad.append(f"{key}.rate={item.get('rate')} expected={expected_rate:.3f}")
        expected_cov = round(0.60 * exact_rates[0] + 0.25 * exact_rates[1] + 0.15 * exact_rates[2], 3)
        if not close_enough(cov.get("value"), expected_cov):
            cov_bad.append(f"coverage={cov.get('value')} expected={expected_cov}")
        if not set(cb.get("unreadable_assets", [])).issubset(set(scope.get("assets", []))):
            cov_bad.append("unreadable_assets 超出 execution_scope.assets")
        if not set(cb.get("inaccessible_supplements", [])).issubset(set(scope.get("supplements", []))):
            cov_bad.append("inaccessible_supplements 超出 execution_scope.supplements")
        rep.check(not cov_bad, "extraction_coverage 由 scope 分子分母复算成立",
                  "; ".join(cov_bad[:8]))

        confidence_bad = []
        scope_obs_ids = scope.get("observations", [])
        scope_obs = [obs_by_id[oid][0][1] for oid in scope_obs_ids if oid in obs_by_id]
        obs_den = max(1, len(scope_obs_ids))
        pixel_share = sum(o.get("provenance", {}).get("source_type") == "pixel_estimated"
                          for o in scope_obs) / obs_den
        ocr_share = sum(o.get("provenance", {}).get("derivation", {}).get("ocr_used") is True
                        for o in scope_obs) / obs_den
        if has_oc:
            out = inst["output_confidence"]
            expected = round(expected_cov * max(0, 1 - 0.30 * pixel_share - 0.20 * ocr_share), 3)
            if not close_enough(out.get("pixel_share"), pixel_share):
                confidence_bad.append("output pixel_share 错误")
            if not close_enough(out.get("ocr_share"), ocr_share):
                confidence_bad.append("output ocr_share 错误")
            if not close_enough(out.get("value"), expected):
                confidence_bad.append(f"output_confidence={out.get('value')} expected={expected}")
        if has_rc:
            review = inst["review_confidence"]
            finding_den = max(1, len(findings))
            pixel_evidence = {o["provenance"]["evidence_ref"] for o in scope_obs
                              if o.get("provenance", {}).get("source_type") == "pixel_estimated"}
            ocr_evidence = {o["provenance"]["evidence_ref"] for o in scope_obs
                            if o.get("provenance", {}).get("derivation", {}).get("ocr_used") is True}
            pixel_dep = sum(bool(set(f.get("evidence_refs", [])) & pixel_evidence)
                            for f in findings) / finding_den
            ocr_dep = sum(bool(set(f.get("evidence_refs", [])) & ocr_evidence)
                          for f in findings) / finding_den
            low_rate = sum(f.get("review_confidence") == "low" for f in findings) / finding_den
            conflict_count = 0
            scope_obs_set = set(scope_obs_ids)
            if sr:
                conflict_count = sum(k.get("status") == "conflicting" and
                                     bool({o.get("observation_id") for o in k.get("observations", [])} & scope_obs_set)
                                     for k in sr.get("key_data", []))
            q = max(0, 1 - 0.30 * pixel_dep - 0.20 * ocr_dep - 0.10 * low_rate)
            c_factor = max(0, 1 - 0.10 * min(conflict_count, 5))
            expected = round(expected_cov * q * c_factor, 3)
            expected_parts = {
                "pixel_dependency_rate": pixel_dep,
                "ocr_dependency_rate": ocr_dep,
                "low_conf_finding_rate": low_rate,
            }
            for key, expected_part in expected_parts.items():
                if not close_enough(review.get(key), expected_part):
                    confidence_bad.append(f"{key} 错误")
            if review.get("unresolved_conflict_count") != conflict_count:
                confidence_bad.append("unresolved_conflict_count 错误")
            if not close_enough(review.get("value"), expected):
                confidence_bad.append(f"review_confidence={review.get('value')} expected={expected}")
            warning = review.get("weak_evidence_warning")
            if (expected < 0.5) != (warning == "本次审核证据基础较弱，结论仅供参考"):
                confidence_bad.append("weak_evidence_warning 与阈值不一致")
        rep.check(not confidence_bad, "review/output confidence 由 scope observation 复算成立",
                  "; ".join(confidence_bad[:8]))


def main():
    args = set(sys.argv[1:])
    rep = Report(quiet="--quiet" in args)
    check_schemas(rep)

    if "--schema" not in args:
        if os.path.isdir(FIXTURE_DIR):
            for fn in sorted(os.listdir(FIXTURE_DIR)):
                if not fn.endswith(".json"):
                    continue
                with open(os.path.join(FIXTURE_DIR, fn), encoding="utf-8") as fh:
                    inst = json.load(fh)
                check_instance(rep, fn, inst)
        else:
            print(f"\n(跳过实例层：{FIXTURE_DIR} 不存在)")

    print("\n" + "=" * 60)
    if rep.failures:
        print(f"\033[31m{len(rep.failures)} 项失败\033[0m / {rep.passes} 项通过")
        for label, detail in rep.failures:
            print(f"  - {label}" + (f" — {detail}" if detail else ""))
        return 1
    print(f"\033[32m全部通过\033[0m（{rep.passes} 项检查）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
