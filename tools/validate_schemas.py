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
               "partial_extraction", "ambiguous_extraction",
               # 一期统计取证（Skill 内 statistical_forensics.py），不需要原始数据
               "test_statistic_p_mismatch", "ci_estimate_mismatch",
               "count_percentage_mismatch", "grim_incompatible_mean",
               "table_total_mismatch",
               # 一期伦理规范库筛查（Skill 内 scripts/ethics_compliance_check.py）
               "ethics_requirement_unmet",
               # 一期序列与标识符确定性审计
               "sequence_identifier_inconsistent",
               # 一期论文内图像完整性审计
               "figure_integrity_candidate",
               # 一期可选外部验证层 X1
               "external_validation_candidate"}
SYSLIM_CATEGORY = {"parse_failed", "figure_unreadable", "table_unparseable",
                   "supplement_inaccessible", "section_missing_from_input",
                   "ocr_low_quality", "encoding_error", "input_truncated",
                   "external_source_unavailable", "external_access_denied",
                   "external_rate_limited", "external_response_unparseable"}
KEY_DATA_STATUS = {"reported", "compatible_multiple_sources", "conflicting",
                   "ambiguous", "pending_visual_resolution", "parse_failed"}
NUMERIC_TYPE = {"point", "interval", "lower_bound", "upper_bound", "categorical"}
REVIEW_MODULES = {"M2", "M3", "M4", "M5", "M6", "M7"}
CONFIDENCE = {"high", "medium", "low"}

STAGE_DEPS = {"stage_2": "stage_1", "stage_3": "stage_1", "stage_3b": "stage_2",
              "stage_3c_external_validation": "stage_3b",
              "stage_4": "stage_3b", "stage_5": "stage_4"}
SEVERITY_WEIGHT = {"critical": 25, "major": 10, "minor": 3, "info": 0}
SEVERITY_RANK = {"critical": 3, "major": 2, "minor": 1, "info": 0}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}
STAT_FORENSICS_CHECKS = {"test_statistic_p_mismatch", "ci_estimate_mismatch",
                         "count_percentage_mismatch", "grim_incompatible_mean",
                         "table_total_mismatch"}


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
    fig_items = (figrec.get("properties", {}).get("observations", {}).get("items", {}))
    fig_refs = {x.get("$ref") for x in fig_items.get("allOf", []) if isinstance(x, dict)}
    key_defs = schemas.get("key_data.schema.json", {}).get("$defs", {})
    rep.check("key_data.schema.json#/$defs/observation_core" in fig_refs and
              fig_items.get("unevaluatedProperties") is False and
              "observation_core" in key_defs and
              key_defs.get("observation", {}).get("unevaluatedProperties") is False,
              "figure observation 可追加路由字段且两种落盘形状均封闭")
    axis_def = figrec.get("$defs", {}).get("axis", {})
    rep.check("scale" in axis_def.get("required", []),
              "figure axis 显式要求 scale，禁止空轴对象")

    syslim = schemas.get("system_limitation.schema.json", {})
    rep.check("severity" in json.dumps(syslim.get("not", {})),
              "system_limitation 禁止 severity")

    sig = schemas.get("extraction_signal.schema.json", {})
    rep.check("severity" in json.dumps(sig.get("not", {})),
              "extraction_signal 禁止 severity")
    sig_enum = set(sig.get("properties", {}).get("type", {}).get("enum", []))
    rep.check(sig_enum == SIGNAL_TYPE, "signal type 十五值且无 parse_failure",
              f"schema={sorted(sig_enum)}")
    forensics_enum = set(sig.get("properties", {}).get("forensics", {})
                         .get("properties", {}).get("check", {}).get("enum", []))
    rep.check(forensics_enum == STAT_FORENSICS_CHECKS,
              "forensics.check 覆盖五种已实现统计取证",
              f"schema={sorted(forensics_enum)}")

    ev = schemas.get("evidence.schema.json", {})
    ev_defs = ev.get("$defs", {})
    external = ev_defs.get("external_evidence", {})
    external_required = set(external.get("required", []))
    expected_external = {"id", "type", "database", "endpoint", "query", "record_id",
                         "retrieved_at", "database_version", "http_status",
                         "retrieval_status", "response_sha256", "parser_version",
                         "assertions", "created_by"}
    rep.check(expected_external <= external_required and
              external.get("properties", {}).get("created_by", {}).get("const") ==
              "stage_3c_external_validation",
              "external evidence 可追溯且只能由 X1 创建")
    sig_blob = json.dumps(sig.get("allOf", []), ensure_ascii=False)
    rep.check("external_validation_candidate" in sig_blob and
              "stage_3c_external_validation" in sig_blob and
              "external_check" in sig_blob,
              "external signal 强制 X1 产出并携带比较轨迹")

    try:
        with open(REPORT_TEMPLATE, encoding="utf-8") as fh:
            template = fh.read()
        stale = [token for token in ("confidence_score", "extraction_gap_penalty", "min_group_n",
                                     "methods.groups", "evidence.locator", "七维审核")
                 if token in template]
        headings = ["## 一、执行摘要", "## 二、结构化结果表", "## 三、图表解读与原图定位",
                    "## 四、审核发现", "## 五、抽取信号", "## 六、系统限制",
                    "## 七、覆盖率明细", "## 八、人工复核建议"]
        usability_tokens = ["render_evidence_refs", "comparable_to_full_review=false",
                            "未执行模块没有被判定为“无问题”", "P0 > P1 > P2",
                            "不得与任何其他报告的风险分横向比较或排序", "不是稿件问题",
                            "collect_review_fields", "format_rate", "render_cluster_findings",
                            "render_plan_finding_packages", "逐 finding 核对包",
                            "契约哨兵 rate=1.0"]
        blocks_balanced = (template.count("{{#if") == template.count("{{/if}}") and
                           template.count("{{#each") == template.count("{{/each}}") and
                           template.count("{{#with") == template.count("{{/with}}"))
        rep.check(not stale and all(template.count(h) == 1 for h in headings) and
                  all(token in template for token in usability_tokens) and blocks_balanced,
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
        elif e.get("type") == "external":
            required = {"database", "endpoint", "query", "record_id", "retrieved_at",
                        "database_version", "http_status", "retrieval_status",
                        "response_sha256", "parser_version", "assertions", "created_by"}
            if not required.issubset(e):
                ev_bad.append(f"{eid}: external 型缺 {sorted(required - set(e))}")
            if e.get("created_by") != "stage_3c_external_validation":
                ev_bad.append(f"{eid}: external 型非 X1 创建")
            if "locator" in e or "quote" in e:
                ev_bad.append(f"{eid}: external 型含稿件 locator/quote")
            public_request = (str(e.get("endpoint", "")) + " " +
                              json.dumps(e.get("query", {}), ensure_ascii=False)).lower()
            if re.search(r"(api[_-]?key|authorization|cookie|access_token|secret)=", public_request):
                ev_bad.append(f"{eid}: external 型请求元数据疑似含凭证")
            if not re.match(r"^[a-f0-9]{64}$", str(e.get("response_sha256", ""))):
                ev_bad.append(f"{eid}: external 型 response_sha256 非法")
            status = e.get("retrieval_status")
            if status == "resolved" and (not e.get("record_id") or not e.get("assertions")):
                ev_bad.append(f"{eid}: resolved external 缺 record/assertions")
            if status in {"not_found", "not_addressed"} and (e.get("record_id") is not None or
                                                               e.get("assertions")):
                ev_bad.append(f"{eid}: 未解析 external 不得带 record/assertions")
        else:
            ev_bad.append(f"{eid}: type 非法")
    rep.check(not ev_bad, "证据登记表三型合法（absence 无引文、external 可追溯）",
              "; ".join(ev_bad[:5]))

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
            elif val.get("type") == "interval":
                low, high = val.get("low"), val.get("high")
                if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low >= high:
                    pixel_bad.append(f"{path}: pixel interval 必须非零宽（low < high）")
            if node.get("extraction_confidence") != "low":
                pixel_bad.append(f"{path}: pixel 置信度非 low")
            if node.get("manual_review_needed") is not True:
                pixel_bad.append(f"{path}: pixel 未置 manual_review_needed")
    rep.check(not prov_bad, "provenance 带 derivation 且组合合法", "; ".join(prov_bad[:5]))
    rep.check(not pixel_bad, "pixel_estimated 满足数值与人工复核强制约束", "; ".join(pixel_bad[:5]))

    # --- Figure Parser → Stage 3b 路由包络 ---
    fig_bad = []
    route_keys = {"experiment_id", "group", "comparison", "timepoint", "endpoint"}
    figure_observations = {}
    for fig in inst.get("figure_records", []):
        fobs = fig.get("observations", [])
        for axis_name, axis in (fig.get("axes") or {}).items():
            axis_range = axis.get("range")
            if isinstance(axis_range, list) and len(axis_range) == 2:
                if not all(isinstance(value, (int, float)) for value in axis_range):
                    fig_bad.append(f"{fig.get('figure_id')}/{axis_name}: axis range 端点必须为数值")
                elif axis_range[0] >= axis_range[1]:
                    fig_bad.append(f"{fig.get('figure_id')}/{axis_name}: axis range 必须严格递增")
                elif axis.get("scale") in {"log10", "log2", "ln"} and axis_range[0] <= 0:
                    fig_bad.append(f"{fig.get('figure_id')}/{axis_name}: 对数轴 range 必须全为正值")
        if any((o.get("provenance") or {}).get("source_type") == "pixel_estimated"
               for o in fobs):
            if fig.get("extraction_confidence") != "low":
                fig_bad.append(f"{fig.get('figure_id')}: 含 pixel observation 但整条记录非 low")
            if fig.get("manual_review_needed") is not True:
                fig_bad.append(f"{fig.get('figure_id')}: 含 pixel observation 但未强制人工复核")
        for obs in fobs:
            obs_id = obs.get("observation_id")
            if obs_id in figure_observations and figure_observations[obs_id] != obs:
                fig_bad.append(f"{fig.get('figure_id')}/{obs_id}: Stage 3 重复 id 的完整内容不一致")
            else:
                figure_observations[obs_id] = obs
            route = obs.get("target_grouping_key")
            if not isinstance(route, dict) or set(route) != route_keys:
                fig_bad.append(f"{fig.get('figure_id')}/{obs.get('observation_id')}: 五键路由不完整")
            if not isinstance(obs.get("metric_name"), str) or not obs.get("metric_name"):
                fig_bad.append(f"{fig.get('figure_id')}/{obs.get('observation_id')}: 缺规范 metric_name")
            if obs.get("metric_family") not in {
                    "continuous_summary", "effect_estimate", "count", "proportion", "p_value",
                    "correlation", "time_to_event", "dose_response", "classification_metric",
                    "diagnostic_accuracy"}:
                fig_bad.append(f"{fig.get('figure_id')}/{obs.get('observation_id')}: metric_family 非法")
            if (obs.get("provenance") or {}).get("source_type") == "axis_readable" and \
                    not fig.get("axes"):
                fig_bad.append(f"{fig.get('figure_id')}/{obs_id}: axis_readable 但未登记坐标轴")
        curve = fig.get("curve_fit")
        if isinstance(curve, dict) and "reported_in_manuscript" not in curve:
            fig_bad.append(f"{fig.get('figure_id')}: curve_fit 未声明 reported_in_manuscript")
        for marker in fig.get("significance_markers", []):
            required = {"marker", "comparison", "p_value", "defined_in_caption"}
            if not required.issubset(marker):
                fig_bad.append(f"{fig.get('figure_id')}: significance_marker 字段不完整")
    rep.check(not fig_bad, "figure observation 路由与 panel 级像素降级成立",
              "; ".join(fig_bad[:5]))

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

        temporal_bad = []
        for path, node in walk(sr):
            if not isinstance(node, dict):
                continue
            refs = list(node.get("evidence_refs", []) or [])
            pr = node.get("provenance")
            if isinstance(pr, dict) and pr.get("evidence_ref"):
                refs.append(pr["evidence_ref"])
            for ref in refs:
                creator = (registry.get(ref) or {}).get("created_by")
                if creator not in {"stage_1", "stage_2", "stage_3", "stage_3b"}:
                    temporal_bad.append(f"{path}: {ref} 由未来审核模块 {creator} 创建")
        rep.check(not temporal_bad, "structured_result 不消费 Stage 4 才创建的证据",
                  "; ".join(temporal_bad[:5]))

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
        merged_figure_ids = set()
        core_keys = {"observation_id", "value", "unit", "unit_normalized", "uncertainty",
                     "n", "replicate_type", "provenance", "extraction_confidence",
                     "manual_review_needed", "quote"}
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
            for obs in obs_list:
                obs_id = obs.get("observation_id")
                source = figure_observations.get(obs_id)
                if source is None:
                    continue
                if obs_id in merged_figure_ids:
                    kd_bad.append(f"{obs_id}: 同一 Figure observation 落入多个 key_data 组")
                merged_figure_ids.add(obs_id)
                source_core = {key: source[key] for key in core_keys if key in source}
                if source_core != obs:
                    kd_bad.append(f"{obs_id}: Stage 3b 未原样保留全部 observation_core 字段")
                if source.get("metric_name") != k.get("metric_name") or \
                        source.get("metric_family") != k.get("metric_family") or \
                        source.get("target_grouping_key") != k.get("grouping_key"):
                    kd_bad.append(f"{obs_id}: Stage 3 路由身份与 v2 目标组不一致")
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
        if version == "v2" and figure_observations:
            rejected_figure_ids = {
                target
                for limitation in inst.get("all_system_limitations", [])
                if limitation.get("category") == "parse_failed" and
                limitation.get("produced_by") == "stage_3b"
                for target in limitation.get("affected_targets", [])
                if target in figure_observations
            }
            multiply_accounted = merged_figure_ids & rejected_figure_ids
            if multiply_accounted:
                kd_bad.append("Figure observations 同时落盘和拒收: " +
                              ", ".join(sorted(multiply_accounted)))
            missing_figure_ids = (set(figure_observations) - merged_figure_ids -
                                  rejected_figure_ids)
            if missing_figure_ids:
                kd_bad.append("Figure observations 未全部回流 v2: " +
                              ", ".join(sorted(missing_figure_ids)))
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
        ref_types = [(registry.get(ref) or {}).get("type") for ref in f.get("evidence_refs", [])]
        if "external" in ref_types:
            if not ref_types or ref_types[0] != "present" or "present" not in ref_types:
                f_bad.append(f"{f.get('id')}: external finding 缺稿件 present 首锚点")
            ext_entries = [registry.get(ref, {}) for ref in f.get("evidence_refs", [])
                           if (registry.get(ref) or {}).get("type") == "external"]
            if any(e.get("retrieval_status") != "resolved" for e in ext_entries):
                f_bad.append(f"{f.get('id')}: external finding 引用了未 resolved 的外部记录")
            derived = set(f.get("derived_from_signals", []))
            ext_signals = [s for s in inst.get("all_extraction_signals", [])
                           if s.get("id") in derived and
                           s.get("type") == "external_validation_candidate"]
            finding_refs = set(f.get("evidence_refs", []))
            if not any((s.get("external_check") or {}).get("comparison_result") == "mismatch" and
                       (s.get("external_check") or {}).get("comparability") == "complete" and
                       set(s.get("evidence_refs", [])) <= finding_refs
                       for s in ext_signals):
                f_bad.append(f"{f.get('id')}: external finding 缺同证据、完全可比的 mismatch signal 血缘")
        for ref in f.get("evidence_refs", []):
            creator = (registry.get(ref) or {}).get("created_by")
            if creator not in {"stage_1", "stage_2", "stage_3", "stage_3b",
                               "stage_3c_external_validation", f.get("module")}:
                f_bad.append(f"{f.get('id')}: 消费了并行模块 {creator} 创建的 {ref}")
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
        if s.get("type") == "source_value_conflict" and sr:
            source_by_observation = {
                obs.get("observation_id"): (obs.get("provenance") or {}).get("source_type")
                for group in sr.get("key_data", []) for obs in group.get("observations", [])
            }
            if any(source_by_observation.get(ref) in VISUALLY_DERIVED
                   for ref in s.get("observation_refs", [])) and \
                    "M5" not in s.get("routed_to", []):
                s_bad.append(f"{s.get('id')}: 含视觉来源的冲突未路由 M5")
        if s.get("type") == "external_validation_candidate":
            if s.get("produced_by") != "stage_3c_external_validation":
                s_bad.append(f"{s.get('id')}: external signal 非 X1 产出")
            if not s.get("external_check"):
                s_bad.append(f"{s.get('id')}: external signal 缺 external_check")
            ref_types = [(registry.get(ref) or {}).get("type")
                         for ref in s.get("evidence_refs", [])]
            if "present" not in ref_types or "external" not in ref_types:
                s_bad.append(f"{s.get('id')}: external signal 未同时引用 present/external")
            if not set(s.get("routed_to", [])) <= {"M2", "M4", "M6", "M7"}:
                s_bad.append(f"{s.get('id')}: external signal 路由越界")
            check = s.get("external_check") or {}
            manuscript_refs = check.get("manuscript_evidence_refs", [])
            external_refs = check.get("external_evidence_refs", [])
            if any((registry.get(ref) or {}).get("type") != "present"
                   for ref in manuscript_refs):
                s_bad.append(f"{s.get('id')}: manuscript_evidence_refs 含非 present")
            if any((registry.get(ref) or {}).get("type") != "external"
                   for ref in external_refs):
                s_bad.append(f"{s.get('id')}: external_evidence_refs 含非 external")
            if any((registry.get(ref) or {}).get("retrieval_status") != "resolved"
                   for ref in external_refs):
                s_bad.append(f"{s.get('id')}: external_evidence_refs 含未 resolved 记录")
            if set(s.get("evidence_refs", [])) != set(manuscript_refs) | set(external_refs):
                s_bad.append(f"{s.get('id')}: external_check 双 refs 与顶层 evidence_refs 不一致")
            result = check.get("comparison_result")
            comparability = check.get("comparability")
            if result in {"match", "mismatch"} and comparability != "complete":
                s_bad.append(f"{s.get('id')}: match/mismatch 但非 complete")
            if result == "not_comparable" and (comparability != "none" or
                                                not check.get("noncomparability_reasons")):
                s_bad.append(f"{s.get('id')}: not_comparable 缺 none/reasons")
    rep.check(not s_bad, "extraction_signal 契约成立", "; ".join(s_bad[:5]))

    l_bad = []
    for l in inst.get("all_system_limitations", []):
        if l.get("category") not in SYSLIM_CATEGORY:
            l_bad.append(f"{l.get('id')}: category={l.get('category')}")
        if "severity" in l:
            l_bad.append(f"{l.get('id')}: 携带 severity")
        if str(l.get("category", "")).startswith("external_") and \
                l.get("produced_by") != "stage_3c_external_validation":
            l_bad.append(f"{l.get('id')}: external limitation 非 X1 产出")
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
                      "partial 分数标记为不可比")
        else:
            rep.check(risk.get("comparable_to_full_review") is True,
                      "完整分数标记为可与 full_review 比较")

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
        expected_band = ("partial_not_classified" if risk.get("partial") else
                         "routine_review" if expected_risk <= 19 else
                         "clarification_needed" if expected_risk <= 49 else
                         "major_revision_suggested")
        if risk.get("band") != expected_band:
            score_bad.append(f"band={risk.get('band')} expected={expected_band}")
        if risk.get("priority_manual_review") is not critical_seen:
            score_bad.append("priority_manual_review 与 critical 簇不一致")
        rep.check(not score_bad, "issue_clusters 与 manuscript_risk_score 可复算",
                  "; ".join(score_bad[:8]))

        plan_bad = []
        required_plan_ids = {
            f["id"] for f in findings
            if f.get("severity") in {"critical", "major"}
            or f.get("manual_review", {}).get("priority") == "P2"
        }
        planned_ids = []
        for item in inst.get("manual_review_plan", []):
            item_priorities = []
            for fid in item.get("finding_ids", []):
                if fid not in finding_by_id:
                    plan_bad.append(f"复核计划引用不存在 finding: {fid}")
                else:
                    priority = finding_by_id[fid].get("manual_review", {}).get("priority")
                    if priority:
                        item_priorities.append(priority)
                planned_ids.append(fid)
            if item_priorities:
                expected_priority = min(item_priorities, key=lambda p: PRIORITY_RANK[p])
                if item.get("priority") != expected_priority:
                    plan_bad.append(
                        f"复核计划 priority={item.get('priority')} expected={expected_priority}"
                    )
        duplicate_ids = sorted({fid for fid in planned_ids if planned_ids.count(fid) > 1})
        if duplicate_ids:
            plan_bad.append(f"finding 在复核计划中重复: {duplicate_ids}")
        missing_ids = required_plan_ids - set(planned_ids)
        if missing_ids:
            plan_bad.append(f"应复核 finding 未全部进入计划: {sorted(missing_ids)}")
        for finding in findings:
            severity = finding.get("severity")
            priority = finding.get("manual_review", {}).get("priority")
            if severity == "critical" and priority != "P0":
                plan_bad.append(f"{finding.get('id')}: critical 必须为 P0")
            elif severity == "major" and priority not in {"P0", "P1"}:
                plan_bad.append(f"{finding.get('id')}: major 只能为 P0/P1")
            elif severity in {"minor", "info"} and priority is not None and priority != "P2":
                plan_bad.append(f"{finding.get('id')}: minor/info 若设置 priority 必须为 P2")
        rep.check(not plan_bad, "报告级复核计划覆盖完整且优先级可解释",
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



# ---------------------------------------------------- 工具产出 signal 的契约符合性

SCRIPTS_DIR = os.path.join(ROOT, "skills", "biomed-paper-review", "scripts")


def _collect_tool_signals():
    """实际调用各工具，收集它们吐出的 signal。返回 (signals, skipped)。"""
    import sys as _sys
    if SCRIPTS_DIR not in _sys.path:
        _sys.path.insert(0, SCRIPTS_DIR)

    sigs, skipped = [], []

    # --- 统计取证：五种检查各造一个必然触发的输入 ---
    try:
        import statistical_forensics as sf
        sigs += sf.check_all([
            {"check": "test_statistic_p", "test_family": "t", "statistic": 2.228,
             "df": 10, "tail": "two", "reported_p": "0.001"},
            {"check": "ci_estimate", "estimate": 20.0, "ci_low": 9.8, "ci_high": 15.7},
            {"check": "count_percentage", "count": 42, "n": 84,
             "reported_percent": 60.0, "reported_percent_text": "60.0"},
            {"check": "grim", "scale_is_integer": True, "n": 10, "mean_text": "3.14"},
            {"check": "table_total", "counts": [12, 18], "declared_total": 28,
             "categories_exhaustive": True},
            {"check": "grim", "scale_is_integer": False},          # -> partial_extraction
        ])
    except Exception as exc:
        skipped.append(f"statistical_forensics: {exc}")

    # --- 伦理筛查 ---
    try:
        import ethics_compliance_check as ec
        f = lambda st, v=None: {"applicability": "applicable", "requiredness": "required",
                                "status": st, "value": v, "evidence_refs": ["EV-001"],
                                "extraction_confidence": "high"}
        sigs += ec.screen({
            "article_design": {"primary_design": {"family": "experimental",
                                                  "type": "in_vivo_animal"},
                               "design_components": []},
            "population": {"subjects": f("reported", "C57BL/6 小鼠")},
            "declarations": {"ethics_statement": f("not_reported")},
            "measurement": {"sample_size_justification": f("not_reported")},
            "design": {"interventions": f("reported", "腹腔注射")},
        })
    except Exception as exc:
        skipped.append(f"ethics_compliance_check: {exc}")

    # --- 序列与标识符 ---
    try:
        import sequence_identifier_audit as sa
        sigs += sa.audit([
            {"check": "hgvs", "hgvs": "R273H"},
            {"check": "hgvs", "hgvs": "p.Arg273His",
             "sequence": "MEEPQSDPSV", "sequence_type": "protein"},
            {"check": "gene_symbol", "symbol": "TP53", "species": "mouse"},
            {"check": "accession", "accession": "NCT123", "database": "clinicaltrials"},
            {"check": "primer", "sequence": "ATATATATATATATATAT"},
        ])
    except Exception as exc:
        skipped.append(f"sequence_identifier_audit: {exc}")

    # --- 图像完整性（依赖 numpy/PIL，缺失则跳过而非失败）---
    try:
        import figure_integrity_audit as fi
        if not fi.DEPS_OK:
            skipped.append(f"figure_integrity_audit: {fi.DEPS_ERR}")
        else:
            import numpy as _np
            rng = _np.random.default_rng(7)
            base = rng.integers(0, 255, size=(256, 256)).astype(float)
            base[128:192, 128:192] = base[0:64, 0:64]      # 植入网格对齐的重复
            sigs += fi.find_duplicate_regions({"synthetic.png": base})
            spliced = rng.normal(120, 6, size=(128, 256))
            spliced[:, 128:] += 60
            sigs += fi.find_splice_discontinuity("blot.png", spliced)
    except Exception as exc:
        skipped.append(f"figure_integrity_audit: {exc}")

    # --- 外部数据核验 X1（需联网；离线时跳过而非失败）---
    # 这一层的产出同时含 external evidence，由 check_external_evidence 单独校验。
    try:
        import external_figure_validation as x1
        R = ["EV-001"]
        out = x1.validate([
            {"check": "cell_line", "cell_line": "MDA-MB-435", "evidence_refs": R},
            {"check": "variant", "uniprot": "P04637", "position": 999,
             "evidence_refs": R},
            {"check": "blot_band", "uniprot": "P04637", "reported_kda": 120,
             "evidence_refs": R},
            {"check": "trial_registration", "nct": "NCT99999999", "evidence_refs": R},
            {"check": "cited_retracted", "doi": "10.1016/S0140-6736(20)31180-6",
             "evidence_refs": R},
            {"check": "gene_symbol", "symbol": "MARCH1", "evidence_refs": R},
            {"check": "gene_symbol", "symbol": "2-Sep", "evidence_refs": R},
            {"check": "reference_exists", "doi": "10.1234/fake.doi.99999",
             "evidence_refs": R},
            {"check": "species", "species": "Mus fakius", "evidence_refs": R},
            {"check": "rrid", "rrid": "AB_9999999", "evidence_refs": R},
            {"check": "compound", "compound": "imatinib", "reported_mw": 250.0,
             "evidence_refs": R},
            {"check": "pdb", "pdb_id": "9ZZZ", "evidence_refs": R},
        ])
        if not out["signals"]:
            skipped.append("external_figure_validation: 外部源不可达（离线？），本层未校验")
        else:
            sigs += out["signals"]
            _EXTERNAL_SIGNALS.extend(out["signals"])
            _EXTERNAL_EVIDENCE.update(out["evidence_registry"])
    except Exception as exc:
        skipped.append(f"external_figure_validation: {exc}")

    return sigs, skipped


# X1 产出的 external evidence，由 _collect_tool_signals 填充
_EXTERNAL_EVIDENCE = {}


def check_external_evidence(rep, schemas):
    """校验 X1 产出的 external evidence 是否合契约。

    signal 层查不到这个 —— evidence 走的是另一份 schema，
    而外部证据是 X1 唯一能被复查的凭据，写错就等于不可复查。
    """
    rep.section("X1 外部证据的契约符合性")
    if not _EXTERNAL_EVIDENCE:
        print("  (跳过) 未收集到 external evidence（外部源不可达）")
        return

    ev_schema = schemas.get("evidence.schema.json", {})
    ext = ev_schema.get("$defs", {}).get("external_evidence", {})
    required = set(ext.get("required", []))
    allowed = set(ext.get("properties", {}))

    entries = list(_EXTERNAL_EVIDENCE.values())
    bad_req = [f"{e.get('id')}: 缺 {sorted(required - set(e))}"
               for e in entries if not required.issubset(set(e))]
    rep.check(not bad_req, "external evidence 必填字段齐全", "; ".join(bad_req[:3]))

    bad_extra = [f"{e.get('id')}: 多 {sorted(set(e) - allowed)}"
                 for e in entries if set(e) - allowed]
    rep.check(not bad_extra, "external evidence 无越界字段", "; ".join(bad_extra[:3]))

    bad_id = [str(e.get("id")) for e in entries
              if not re.match(r"^EV-[0-9]{3,}$", str(e.get("id", "")))]
    rep.check(not bad_id, "external evidence id 合契约 pattern", "; ".join(bad_id[:3]))

    bad_key = [k for k, e in _EXTERNAL_EVIDENCE.items() if e.get("id") != k]
    rep.check(not bad_key, "登记表键与条目 id 相等", "; ".join(bad_key[:3]))

    bad_sha = [e["id"] for e in entries
               if not re.match(r"^[a-f0-9]{64}$", str(e.get("response_sha256", "")))]
    rep.check(not bad_sha, "external evidence 带合法响应 sha256", "; ".join(bad_sha[:3]))

    # 契约的条件约束：resolved 必须有 record_id 且 assertions 非空；
    # not_found / not_addressed 必须 record_id 为 null 且 assertions 为空
    bad_res = [e["id"] for e in entries if e.get("retrieval_status") == "resolved"
               and (not e.get("record_id") or not e.get("assertions"))]
    rep.check(not bad_res, "resolved 条目有 record_id 且 assertions 非空",
              "; ".join(bad_res[:3]))
    bad_unres = [e["id"] for e in entries
                 if e.get("retrieval_status") in ("not_found", "not_addressed")
                 and (e.get("record_id") is not None or e.get("assertions"))]
    rep.check(not bad_unres, "未解析条目 record_id 为 null 且 assertions 为空",
              "; ".join(bad_unres[:3]))

    bad_ep = [e["id"] for e in entries
              if not str(e.get("endpoint", "")).startswith("https://")
              or re.search(r"(api[_-]?key|authorization|cookie|access_token|secret)=",
                           str(e.get("endpoint", "")), re.I)]
    rep.check(not bad_ep, "endpoint 为 https 且不含凭证", "; ".join(bad_ep[:3]))

    bad_asrt = []
    asrt_req = {"predicate", "subject", "external_value", "unit", "source_path"}
    for e in entries:
        for a in e.get("assertions", []):
            if not asrt_req.issubset(set(a)):
                bad_asrt.append(f"{e['id']}: 缺 {sorted(asrt_req - set(a))}")
    rep.check(not bad_asrt, "assertion 必填字段齐全", "; ".join(bad_asrt[:3]))

    # signal 里引用的外部证据必须都能解析到登记表
    dangling = []
    for s in _EXTERNAL_SIGNALS:
        for ref in s.get("external_check", {}).get("external_evidence_refs", []):
            if ref not in _EXTERNAL_EVIDENCE:
                dangling.append(f"{s['id']} -> {ref}")
    rep.check(not dangling, "signal 的 external_evidence_refs 全部可解析",
              "; ".join(dangling[:3]))

    resolved = [e for e in entries if e.get("retrieval_status") == "resolved"]
    print(f"  （共 {len(entries)} 条外部证据，{len(resolved)} 条已解析，"
          f"覆盖 {len({e['database'] for e in entries})} 个数据库）")


_EXTERNAL_SIGNALS = []


# type -> 该类型必须携带的判据块（schema 的条件约束）
SIGNAL_EVIDENCE_BLOCK = {
    "test_statistic_p_mismatch": "forensics",
    "ci_estimate_mismatch": "forensics",
    "count_percentage_mismatch": "forensics",
    "grim_incompatible_mean": "forensics",
    "table_total_mismatch": "forensics",
    "sequence_identifier_inconsistent": "sequence_audit",
    "figure_integrity_candidate": "image_audit",
    "ethics_requirement_unmet": "ethics",
    "external_validation_candidate": "external_check",
}


def check_tool_signals(rep, schemas):
    """把五个工具真正吐出的 signal 拿去比对 extraction_signal.schema.json。

    这一层补的是一个真实漏洞：工具自检只测工具自身逻辑，
    fixture 校验只测手写实例，二者之间没有连接 ——
    工具产出不合契约的 signal 时无人发现。
    """
    rep.section("工具产出 signal 的契约符合性")

    sig_schema = schemas.get("extraction_signal.schema.json", {})
    if not sig_schema:
        rep.check(False, "extraction_signal.schema.json 可读")
        return

    type_enum = set(sig_schema.get("properties", {}).get("type", {}).get("enum", []))
    produced_enum = set(sig_schema.get("properties", {}).get("produced_by", {}).get("enum", []))
    required = set(sig_schema.get("required", []))

    sigs, skipped = _collect_tool_signals()
    for s in skipped:
        print(f"  (跳过) {s}")

    rep.check(len(sigs) > 0, "至少收集到一条工具产出的 signal",
              f"skipped={skipped}")
    if not sigs:
        return

    bad_type = sorted({x.get("type") for x in sigs} - type_enum)
    rep.check(not bad_type, "工具产出的 type 全部在契约枚举内", f"越界: {bad_type}")

    bad_req = [f"{x.get('id')}: 缺 {sorted(required - set(x))}"
               for x in sigs if not required.issubset(set(x))]
    rep.check(not bad_req, "工具产出的 signal 必填字段齐全", "; ".join(bad_req[:4]))

    bad_ids = [str(x.get("id")) for x in sigs
               if not re.match(r"^SIG-[0-9]{3,}$", str(x.get("id", "")))]
    rep.check(not bad_ids, "工具产出的 signal id 符合契约 pattern",
              "; ".join(bad_ids[:4]))

    bad_prod = sorted({x.get("produced_by") for x in sigs} - produced_enum)
    rep.check(not bad_prod, "工具产出的 produced_by 合法", f"越界: {bad_prod}")

    # schema 用 allOf 条件约束 routed_to 白名单，而上面几项只查了顶层字段 ——
    # 实测漏过一次：schema 只允许 X1 路由 M2/M4/M6/M7，工具却发往 M3/M5，
    # 164 项检查全绿却根本没查这一条。条件约束必须单独展开验证。
    cond = {}
    for a in sig_schema.get("allOf", []):
        t = ((a.get("if") or {}).get("properties") or {}).get("type", {}).get("const")
        wl = (((a.get("then") or {}).get("properties") or {})
              .get("routed_to", {}).get("items", {}).get("enum"))
        if t and wl:
            cond[t] = set(wl)
    bad_route = []
    for x in sigs:
        wl = cond.get(x.get("type"))
        if wl and not set(x.get("routed_to") or []).issubset(wl):
            bad_route.append(f"{x.get('id')}({x.get('type')}): "
                             f"{sorted(set(x.get('routed_to') or []) - wl)} 不在白名单")
    rep.check(not bad_route, "工具产出的 routed_to 满足 schema 的条件白名单",
              "; ".join(bad_route[:4]))

    bad_route = [x.get("id") for x in sigs
                 if not set(x.get("routed_to") or []) <= REVIEW_MODULES]
    rep.check(not bad_route, "工具产出的 routed_to 全在 M2–M7", "; ".join(bad_route[:4]))

    has_sev = [x.get("id") for x in sigs if "severity" in x]
    rep.check(not has_sev, "工具产出的 signal 一律无 severity", "; ".join(has_sev[:4]))

    bad_block = []
    for x in sigs:
        need = SIGNAL_EVIDENCE_BLOCK.get(x.get("type"))
        if need and need not in x:
            bad_block.append(f"{x.get('id')}({x.get('type')}) 缺 {need}")
    rep.check(not bad_block, "各类 signal 携带其判据块", "; ".join(bad_block[:4]))

    bad_forensics = [f"{x.get('id')}:{x.get('forensics', {}).get('check')}"
                      for x in sigs if "forensics" in x and
                      x.get("forensics", {}).get("check") not in STAT_FORENSICS_CHECKS]
    rep.check(not bad_forensics, "统计工具产出的 forensics.check 在 schema 枚举内",
              "; ".join(bad_forensics[:4]))

    # 图像审计的定性禁令：schema 层已强制，这里再验实际产出
    img = [x for x in sigs if x.get("type") == "figure_integrity_candidate"]
    if img:
        bad_img = [x.get("id") for x in img
                   if x["image_audit"].get("severity_hint") is not None
                   or x["image_audit"].get("candidate") is not True
                   or x["image_audit"].get("manual_review_required") is not True]
        rep.check(not bad_img,
                  "图像审计信号恒为候选、无 severity_hint、强制人工复核",
                  "; ".join(bad_img[:4]))

    print(f"  （共校验 {len(sigs)} 条工具产出的 signal）")

def main():
    args = set(sys.argv[1:])
    rep = Report(quiet="--quiet" in args)
    schemas = check_schemas(rep)
    if "--no-tools" not in args:
        check_tool_signals(rep, schemas)
        check_external_evidence(rep, schemas)

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
