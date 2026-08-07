#!/usr/bin/env python3
"""Score a review_report.json: contract health, uplift attribution, ground-truth hits."""
import json, os, re, sys

BASE = "/Users/henrychen/ai4s_hack_runs"

# The 7 findings the OLD architecture missed on PMC11856280 (bare model found them).
TARGETS_11856280 = {
    "1 knockin is also RAGE-null (confounded genetic validation)":
        r"RAGE.?null|full.length|exons? 10|敲入.*(敲除|缺失)|构件.*混杂",
    "2 single 7-dpi timepoint cannot support 'accelerates'":
        r"单一时间点|single time.?point|时间序列|时程|无法区分.*更快|accelerat.*(unsupport|无支撑|缺乏)",
    "3 fiber-level pseudoreplication":
        r"伪重复|pseudorep|nested|嵌套|单根纤维|分析单元|实验单元",
    "4 db/db BKS vs C57BL/6J control mismatch":
        r"BKS|B6\.BKS|背景.{0,12}(不同|错配|不匹配|混杂|可比)|strain background.{0,20}(mismatch|control)|品系.{0,10}(错配|不匹配|不可比)",
    "5 allogeneic mdx transplant, no immunosuppression":
        r"免疫抑制|immunosuppress|排斥|allogeneic|同种异体|免疫功能完整",
    "6 bGHpA qPCR vs construct contradiction":
        r"bGHpA|bGH.{0,25}(引物|primer|矛盾|contradict|探针|probe)|滴度.{0,20}(矛盾|不一致|contradict)",
    "7 glucose reduction as confounder":
        r"血糖.*(混杂|confound|解释)|glucose.*confound|代谢.*(混杂|替代解释)",
}

# Papers with KNOWN external-verification answers — the real uplift tests.
GROUND_TRUTH = {
    "p1-cellline-PMC11985696": {
        "what": "cell line CCL4 = CVCL_M024, MISCLASSIFIED (not chordoma)",
        "pat": r"CCL4|CVCL_M024|误认|misidentif|misclassif|contaminat|污染",
    },
    "p2-retracted-PMC7439339": {
        "what": "this paper was RETRACTED (notice PMC12888758)",
        "pat": r"撤稿|retract|RETRACTION|PMC12888758",
    },
    "p3-rct-PMC12193851": {
        "what": "clinical RCT: registration / outcome switching / CONSORT",
        "pat": r"注册|registration|NCT|ChiCTR|CONSORT|outcome.switch|结局切换",
    },
}


def score(run_dir):
    p = os.path.join(BASE, run_dir, "review_report.json")
    if not os.path.exists(p):
        return f"{run_dir}: no review_report.json yet"
    r = json.load(open(p))
    fs = r.get("all_findings", [])
    out = [f"\n{'='*72}\n{run_dir}  —  {len(fs)} findings"]

    sev = {}
    for f in fs:
        sev[f.get("severity", "?")] = sev.get(f.get("severity", "?"), 0) + 1
    out.append(f"  severity: {sev}")

    origin = {}
    for f in fs:
        o = f.get("origin") or f.get("source") or "?"
        origin[str(o)] = origin.get(str(o), 0) + 1
    out.append(f"  origin:   {origin}")

    ru = r.get("runtime_utilization", {}) or {}
    for k in ("child_sessions", "task_calls", "continuations", "routing_recall",
              "tool_execution_recall", "global_findings_count",
              "global_findings_confirmed", "global_findings_refuted",
              "additive_guarantee_held", "findings_added_beyond_global"):
        if k in ru:
            out.append(f"  {k}: {ru[k]}")
    if "modules_run" in ru:
        out.append(f"  modules_run: {ru['modules_run']}  skipped: {ru.get('modules_skipped')}")

    sl = r.get("all_system_limitations", []) or []
    out.append(f"  system_limitations: {len(sl)}")

    # IMPORTANT: match only against FINDING text. The evidence registry quotes the
    # paper verbatim, so scanning the whole report scores the manuscript, not the review.
    parts = []
    for f in fs:
        for k in ("title", "statement", "detail", "description", "category"):
            v = f.get(k)
            if isinstance(v, str):
                parts.append(v)
    for k in ("issue_clusters", "cross_section_findings", "manual_review_plan"):
        v = r.get(k)
        if v:
            parts.append(json.dumps(v, ensure_ascii=False))
    blob = "\n".join(parts)

    # uplift attribution: what did NOT come from the bare-model layer?
    beyond = [f for f in fs if "global_review" not in str(f.get("origin", ""))]
    out.append(f"  findings NOT solely from global review (candidate uplift): {len(beyond)}")

    if "11856280" in run_dir:
        hit = 0
        out.append("  --- 7 previously-missed findings:")
        for name, pat in TARGETS_11856280.items():
            ok = re.search(pat, blob, re.I) is not None
            hit += ok
            out.append(f"      {'HIT ' if ok else 'MISS'} {name}")
        out.append(f"  RECOVERY: {hit}/7")

    for key, gt in GROUND_TRUTH.items():
        if key in run_dir:
            ok = re.search(gt["pat"], blob, re.I) is not None
            out.append(f"  --- GROUND TRUTH: {gt['what']}")
            out.append(f"      {'HIT — external verification paid off' if ok else 'MISS'}")

    return "\n".join(out)


if __name__ == "__main__":
    dirs = sys.argv[1:] or ["e2e-v2-pmc11856280", "p1-cellline-PMC11985696",
                            "p2-retracted-PMC7439339", "p3-rct-PMC12193851"]
    for d in dirs:
        print(score(d))
