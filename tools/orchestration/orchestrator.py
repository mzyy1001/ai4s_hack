#!/usr/bin/env python3
"""编排器：把分层协议**编译成真实的多次独立模型调用**。

与上一版的根本区别
------------------
上一版是在**同一个上下文**里写「现在做发现」「现在扮演 M4」——
那仍然是一次单体执行：前面阶段的全部内容还在上下文里占着注意力。

本模块让每个阶段成为一次 `ModelClient.complete()`，**互不继承上下文**：

    发现调用  ≠  M4 调用  ≠  M7 调用  ≠  校正调用  ≠  核查调用

阶段之间只通过**显式结构化产物**传递（paper_map / candidates / packets /
provisional findings / signals），因此接口可见、可校验、可度量。

`telemetry.assert_decomposed()` 是硬性不变量：
分解没真的发生时，整轮结果作废，而不是当作「架构无效」。

用法
----
    python3 -m runtime.orchestrator --paper fulltext.txt --out review.json
    python3 skills/biomed-paper-review/runtime/orchestrator.py --paper x.txt --dry-run
"""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# 编排器已移出 skill 目录：它依赖私有模型凭据，在评测沙箱里跑不了。
# 留在仓库里作为**本地研究工具**，用于验证分层是否真的带来增益。
_SKILL = os.path.join(os.path.dirname(os.path.dirname(_HERE)),
                      "skills", "biomed-paper-review")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import packet_builder                                            # noqa: E402
import router                                                    # noqa: E402
from model_client import ModelClient, ModelUnavailable           # noqa: E402
from telemetry import Telemetry                                  # noqa: E402
from tool_dispatcher import ToolDispatcher                       # noqa: E402

PROMPTS = os.path.join(_HERE, "prompts")
REFS = os.path.join(_SKILL, "references")

DISCOVERY_SCHEMA = {
    "type": "object",
    "required": ["paper_map", "candidate_issues"],
    "properties": {
        "paper_map": {"type": "object"},
        "study_design": {"type": "string"},
        "followup_duration": {"type": ["string", "null"]},
        "n_total": {"type": ["integer", "null"]},
        "experiment_map": {"type": "array"},
        "claim_map": {"type": "array"},
        "cross_section_links": {"type": "array"},
        "candidate_issues": {"type": "array"},
    },
}
SPECIALIST_SCHEMA = {
    "type": "object",
    "required": ["provisional_findings", "candidate_verdicts"],
    "properties": {
        "provisional_findings": {"type": "array"},
        "candidate_verdicts": {"type": "array"},
        "requested_tool_checks": {"type": "array"},
    },
}
RECONCILE_SCHEMA = {
    "type": "object",
    "required": ["reconciled_findings", "candidate_resolution_log"],
    "properties": {
        "reconciled_findings": {"type": "array"},
        "cross_section_findings": {"type": "array"},
        "candidate_resolution_log": {"type": "array"},
    },
}
VERIFY_SCHEMA = {
    "type": "object",
    "required": ["verdict"],
    "properties": {
        "verdict": {"enum": ["confirmed", "downgraded", "rejected",
                             "needs_manual_review"]},
        "adjusted_severity": {"type": ["string", "null"]},
        "reason": {"type": "string"},
    },
}


def _read(path, limit=None):
    try:
        with open(path, encoding="utf-8") as fh:
            t = fh.read()
        return t[:limit] if limit else t
    except OSError:
        return ""


class Orchestrator:
    def __init__(self, client=None, telemetry=None, workdir=".", verify_threshold=("critical", "major")):
        self.tel = telemetry or Telemetry()
        self.client = client or ModelClient(telemetry=self.tel)
        self.tools = ToolDispatcher(telemetry=self.tel, workdir=workdir)
        self.verify_threshold = verify_threshold
        self.limitations = []

    def _limit(self, stage, detail):
        """阶段失败 → system_limitation。**绝不当作「审完了，没问题」。**"""
        self.limitations.append({
            "id": f"SYS-{len(self.limitations) + 1:03d}",
            "category": "stage_execution_failed",
            "impact": f"{stage} 未完成：{detail}",
            "recommended_action": "修复后重跑该阶段；在此之前不得就其覆盖范围下结论",
            "produced_by": stage,
        })

    # ---------------------------------------------------------- Layer 1
    def discovery(self, paper_text):
        """**独立调用 #1**：只带发现提示与稿件，不带任何规则库与完整契约。"""
        sys_p = _read(os.path.join(PROMPTS, "discovery.md"))
        try:
            r = self.client.complete(
                system_prompt=sys_p,
                user_content={"manuscript": paper_text},
                response_schema=DISCOVERY_SCHEMA,
                stage="discovery",
                metadata={"rulebooks": [], "packets": []})
        except ModelUnavailable as e:
            self._limit("discovery", str(e))
            return None
        d = r.parsed or {}
        self.tel.candidates["discovered"] = len(d.get("candidate_issues") or [])
        return d

    # ---------------------------------------------------------- Layer 2
    def specialist(self, module, packet, candidates, rulebook_file):
        """**每个专家一次独立调用**：只给它那一包证据 + 那一本规则。"""
        sys_p = _read(os.path.join(PROMPTS, "specialist.md"))
        rule = _read(os.path.join(REFS, rulebook_file), limit=60000)
        if rule:
            self.tel.read_references([rulebook_file.replace(".md", "")])
        contract = _read(os.path.join(REFS, "00-runtime-contract.md"))
        try:
            r = self.client.complete(
                system_prompt=sys_p + f"\n\n你这次的领域是 **{module}**。",
                user_content={
                    "runtime_contract": contract,
                    "rulebook": rule,
                    "review_packet": packet,
                    "candidate_issues": candidates,
                },
                response_schema=SPECIALIST_SCHEMA,
                stage="specialist", module=module,
                metadata={"rulebooks": [rulebook_file],
                          "packets": [packet.get("packet_id")],
                          "candidates": [c.get("candidate_id") for c in candidates]})
        except ModelUnavailable as e:
            self._limit(f"specialist:{module}", str(e))
            return None
        return r.parsed or {}

    # ---------------------------------------------------------- Layer 4
    def reconcile(self, discovery, provisionals, signals):
        """**独立调用**：只给紧凑结构化输入，不给规则库全文、不给全文。"""
        sys_p = _read(os.path.join(PROMPTS, "reconciliation.md"))
        try:
            r = self.client.complete(
                system_prompt=sys_p,
                user_content={
                    "paper_map": (discovery or {}).get("paper_map"),
                    "experiment_map": (discovery or {}).get("experiment_map"),
                    "claim_map": (discovery or {}).get("claim_map"),
                    "cross_section_links": (discovery or {}).get("cross_section_links"),
                    "candidate_issues": (discovery or {}).get("candidate_issues"),
                    "provisional_findings": provisionals,
                    "tool_signals": signals,
                    "system_limitations": self.limitations,
                },
                response_schema=RECONCILE_SCHEMA,
                stage="reconciliation",
                metadata={"rulebooks": [], "packets": []})
        except ModelUnavailable as e:
            self._limit("reconciliation", str(e))
            return None
        return r.parsed or {}

    # ---------------------------------------------------------- Layer 4b
    def verify(self, finding):
        """**每条重要发现一次独立核查调用**，不给它任何历史上下文。"""
        sys_p = _read(os.path.join(PROMPTS, "verification.md"))
        try:
            r = self.client.complete(
                system_prompt=sys_p,
                user_content={"finding": finding},
                response_schema=VERIFY_SCHEMA,
                stage="verification",
                metadata={"rulebooks": [], "packets": []})
        except ModelUnavailable as e:
            self._limit("verification", str(e))
            return {"verdict": "needs_manual_review", "reason": f"核查未执行：{e}"}
        return r.parsed or {"verdict": "needs_manual_review",
                            "reason": "核查未返回结构化结果"}

    # ---------------------------------------------------------- 全流程
    def run(self, paper_text, tables=None):
        # Layer 1
        disc = self.discovery(paper_text) or {}
        cands = disc.get("candidate_issues") or []

        # Layer 3a：主动扫描（**不等候选**，这一路是裸模型不会自己发起的）
        self.tools.proactive_scan(paper_text, tables)
        signals = self.tools.signals

        # 路由：纯代码决定跑哪些模块，不消耗模型注意力
        planned = router.plan(disc.get("study_design"), cands, signals, self.tel)

        # 建索引与证据包，各一次，全程复用
        index = packet_builder.EvidenceIndex(paper_text)

        # Layer 2：每个模块一次独立调用（M7 留到最后）
        provisionals, per_module = [], {}
        order = [m for m in planned["modules"] if m != "M7"] + \
                (["M7"] if "M7" in planned["modules"] else [])
        for m in order:
            info = planned["modules"][m]
            pk = packet_builder.build(planned["packet_of"][m], index, disc,
                                      [c for c in cands
                                       if c.get("candidate_id") in info["candidates"]],
                                      [s for s in signals
                                        if s.get("id") in info["signals"]])
            out = self.specialist(m, pk, pk["candidate_issues"],
                                  planned["rulebook_of"][m])
            if out:
                pf = out.get("provisional_findings") or []
                for f in pf:
                    f["module"] = m
                    f.setdefault("origin", "specialist_rule")
                provisionals += pf
                per_module[m] = out

        # Layer 4
        rec = self.reconcile(disc, provisionals, signals) or {}
        findings = rec.get("reconciled_findings") or provisionals

        # Layer 4b：只核查高影响的
        verified = []
        for f in findings:
            sev = (f.get("severity") or "").lower()
            if sev in self.verify_threshold:
                v = self.verify(f)
                f["verification"] = v
                if v.get("verdict") == "rejected":
                    continue
                if v.get("verdict") == "downgraded" and v.get("adjusted_severity"):
                    f["severity"] = v["adjusted_severity"]
            verified.append(f)
            self.tel.record_finding_origin(f.get("origin", "specialist_rule"))

        for f in rec.get("cross_section_findings") or []:
            self.tel.record_finding_origin("cross_section_reconciliation")

        log = rec.get("candidate_resolution_log") or []
        for e in log:
            st = e.get("status", "")
            key = {"promoted_to_finding": "promoted", "merged": "merged",
                   "rejected": "rejected", "unresolved": "unresolved",
                   "blocked_by_system_limitation": "blocked"}.get(st)
            if key:
                self.tel.candidates[key] += 1

        ok, note = self.tel.assert_decomposed()
        return {
            "discovery": disc,
            "routing_plan": {k: v for k, v in planned.items() if k != "modules"},
            "modules_run": sorted(planned["modules"]),
            "modules_skipped": planned["skipped"],
            "tool_report": self.tools.report(),
            "findings": verified,
            "cross_section_findings": rec.get("cross_section_findings") or [],
            "candidate_resolution_log": log,
            "system_limitations": self.limitations,
            "runtime_utilization": self.tel.summary(),
            "decomposition_verified": ok,
            "decomposition_note": note,
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True)
    ap.add_argument("--out", default="review_result.json")
    ap.add_argument("--telemetry-out", default=None)
    ap.add_argument("--provider")
    ap.add_argument("--model")
    ap.add_argument("--dry-run", action="store_true",
                    help="不调用模型，只跑路由/索引/证据包/主动扫描，验证管线连通")
    a = ap.parse_args()

    text = _read(a.paper)
    if not text:
        print(f"读不到论文：{a.paper}", file=sys.stderr)
        return 2

    tel = Telemetry()
    if a.dry_run:
        # 干跑：只验确定性部分。**明确标注未做模型调用**，
        # 否则会被误读成「跑完了没发现问题」
        td = ToolDispatcher(telemetry=tel)
        td.proactive_scan(text, None)
        idx = packet_builder.EvidenceIndex(text)
        pl = router.plan("randomised controlled trial", [], td.signals, tel)
        out = {"dry_run": True,
               "_note": "未进行任何模型调用；本结果只验证确定性管线连通性",
               "index_stats": idx.stats(),
               "routing_plan": {k: v for k, v in pl.items() if k != "modules"},
               "modules_run": sorted(pl["modules"]),
               "modules_skipped": pl["skipped"],
               "tool_report": td.report(),
               "runtime_utilization": tel.summary()}
    else:
        client = ModelClient(provider=a.provider, model=a.model, telemetry=tel)
        out = Orchestrator(client, tel).run(text)

    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    if a.telemetry_out:
        tel.dump(a.telemetry_out)

    u = out.get("runtime_utilization", {})
    print(f"模型调用 {u.get('model_calls_total', 0)} 次  {u.get('calls_by_stage', {})}")
    print(f"跑了模块 {out.get('modules_run')}  跳过 {list(out.get('modules_skipped', {}))}")
    print(f"路由召回率 {u.get('routing_recall')}  工具执行召回率 "
          f"{u.get('tool_execution_recall')}")
    print(f"工具任务 {out.get('tool_report', {}).get('status_counts')}")
    if not a.dry_run:
        print(f"分解校验：{'通过' if out.get('decomposition_verified') else '**未通过**'} "
              f"—— {out.get('decomposition_note')}")
    print(f"结果写入 {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
