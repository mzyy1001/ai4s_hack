#!/usr/bin/env python3
"""运行时遥测：记录每一次模型调用，并**校验分层是否真的发生了**。

为什么这个模块是必需的
----------------------
上一版的失败方式很隐蔽：规范里写了五层，提示词里也写了「现在做发现」
「现在扮演 M4」，看上去像分层了 —— 但全部发生在同一个上下文里，
本质仍是一次单体执行。**从最终输出完全看不出这一点。**

所以必须有一个不依赖模型自述的、机械的判据：

    如果 hierarchical 条件下只发生了一次模型调用，架构就是失败的。

`assert_decomposed()` 就是这条不变量。它宁可让整轮实验作废，
也不让一次伪分层的结果被当成架构有效的证据。
"""

import json
import os
import time


class Telemetry:
    """收集调用记录与利用率指标。

    **不记录 token 数**：各供应商返回字段不一，拿不到就是拿不到，
    留 null 而不是估一个 —— 估出来的数字会被当真。
    """

    def __init__(self, run_id=None):
        self.run_id = run_id or f"RUN-{int(time.time())}"
        self.calls = []
        self.references_required = set()
        self.references_read = set()
        self.tools_required = set()
        self.tools_executed = set()
        self.tools_failed = set()
        self.module_decisions = []      # 为什么跑 / 为什么跳过
        self.candidates = {"discovered": 0, "promoted": 0, "merged": 0,
                           "rejected": 0, "unresolved": 0, "blocked": 0}
        self.finding_origins = {}

    # ------------------------------------------------------------ 调用记录
    def record_call(self, stage, module=None, model=None, status="ok",
                    elapsed=0.0, metadata=None, output_chars=None, error=None):
        self.calls.append({
            "call_id": f"CALL-{(module or stage or 'X').upper()}-{len(self.calls) + 1:03d}",
            "stage": stage,
            "module": module,
            "model": model,
            "status": status,
            "elapsed_s": round(elapsed, 2),
            "input_tokens": None,        # 供应商不稳定返回；宁可 null 也不估
            "output_tokens": None,
            "output_chars": output_chars,
            "rulebooks_loaded": sorted((metadata or {}).get("rulebooks", [])),
            "paper_packets_loaded": sorted((metadata or {}).get("packets", [])),
            "candidates_received": sorted((metadata or {}).get("candidates", [])),
            "tools_requested": sorted((metadata or {}).get("tools", [])),
            "error": error,
        })

    def require_references(self, refs):
        self.references_required.update(refs)

    def read_references(self, refs):
        self.references_read.update(refs)

    def require_tools(self, tools):
        self.tools_required.update(tools)

    def executed_tool(self, tool, ok=True):
        (self.tools_executed if ok else self.tools_failed).add(tool)

    def module_decision(self, module, ran, reason):
        """必须同时记录**为什么跑**与**为什么不跑**。

        只记跑了哪些，就无法区分「判断后认为不需要」与「漏了」。
        """
        self.module_decisions.append(
            {"module": module, "ran": ran,
             "why_run" if ran else "why_skipped": reason})

    def record_finding_origin(self, origin):
        self.finding_origins[origin] = self.finding_origins.get(origin, 0) + 1

    # ------------------------------------------------------------ 不变量
    def assert_decomposed(self, condition="hierarchical_skill", min_calls=3):
        """**核心不变量**：分层条件下必须真的发生了多次独立调用。

        返回 (ok, 说明)。ok=False 时该轮结果**不得**用于评价架构或规则库 ——
        那不是「架构没效果」，而是「架构根本没跑起来」，两者不能混为一谈。
        """
        n = len([c for c in self.calls if c["status"] != "failed"])
        stages = {c["stage"] for c in self.calls if c["status"] != "failed"}
        if n <= 1:
            return False, (f"{condition} 只发生了 {n} 次模型调用 —— "
                           f"分层没有真的发生，本轮结果作废。"
                           f"这不是「架构无效」，是「架构没跑起来」。")
        if n < min_calls:
            return False, (f"{condition} 只有 {n} 次调用（要求至少 {min_calls}），"
                           f"阶段覆盖 {sorted(stages)}；分解不充分，结果不可用。")
        if "discovery" not in stages:
            return False, "缺少 discovery 阶段调用 —— 发现层没有独立执行。"
        return True, f"{n} 次独立调用，阶段：{sorted(stages)}"

    # ------------------------------------------------------------ 指标
    def _ratio(self, num, den):
        return None if not den else round(len(num) / len(den), 3)

    def summary(self):
        req_r, read_r = self.references_required, self.references_read
        req_t, exe_t = self.tools_required, self.tools_executed
        c = self.candidates
        total_findings = sum(self.finding_origins.values())

        def share(k):
            return None if not total_findings else round(
                self.finding_origins.get(k, 0) / total_findings, 3)

        by_stage = {}
        for call in self.calls:
            by_stage[call["stage"]] = by_stage.get(call["stage"], 0) + 1

        return {
            "run_id": self.run_id,
            "model_calls_total": len(self.calls),
            "calls_by_stage": by_stage,
            "discovery_calls": by_stage.get("discovery", 0),
            "specialist_calls": by_stage.get("specialist", 0),
            "reconciliation_calls": by_stage.get("reconciliation", 0),
            "verification_calls": by_stage.get("verification", 0),

            "references_required": sorted(req_r),
            "references_read": sorted(read_r),
            # **不是 read/8。** 目标是「本次路由要求的一个不漏」
            "routing_recall": self._ratio(read_r & req_r, req_r),
            # 读了但不要求的属于浪费注意力，precision 就是在盯这个
            "routing_precision": self._ratio(read_r & req_r, read_r),

            "tools_required": sorted(req_t),
            "tools_executed": sorted(exe_t),
            "tools_failed": sorted(self.tools_failed),
            "tool_execution_recall": self._ratio(exe_t & req_t, req_t),

            "module_decisions": self.module_decisions,

            "candidate_count_discovery": c["discovered"],
            "candidate_count_promoted": c["promoted"],
            "candidate_count_rejected": c["rejected"],
            "candidate_count_unresolved": c["unresolved"],
            "candidate_survival_rate": (None if not c["discovered"]
                                        else round(c["promoted"] / c["discovered"], 3)),

            "finding_origin_breakdown": self.finding_origins,
            "rulebook_contribution_rate": share("specialist_rule"),
            "tool_contribution_rate": share("deterministic_tool"),
            "cross_section_contribution_rate": share("cross_section_reconciliation"),
        }

    def dump(self, path):
        ok, msg = self.assert_decomposed()
        blob = {"summary": self.summary(),
                "decomposition_verified": ok,
                "decomposition_note": msg,
                "calls": self.calls}
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(blob, fh, ensure_ascii=False, indent=2)
        return blob


def _selftest():
    ok_all = True

    def expect(label, got, want):
        nonlocal ok_all
        good = got == want
        ok_all &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    t = Telemetry("RUN-TEST")
    # 单次调用 = 伪分层，必须判失败
    t.record_call(stage="discovery")
    expect("只有 1 次调用 -> 判定分解失败", t.assert_decomposed()[0], False)

    t.record_call(stage="specialist", module="M4")
    t.record_call(stage="reconciliation")
    expect("3 次调用且含 discovery -> 通过", t.assert_decomposed()[0], True)

    t2 = Telemetry()
    for s in ("specialist", "specialist", "reconciliation"):
        t2.record_call(stage=s)
    expect("缺 discovery -> 判定失败", t2.assert_decomposed()[0], False)

    t.require_references(["04-statistics", "06-ethics-compliance"])
    t.read_references(["04-statistics", "06-ethics-compliance"])
    s = t.summary()
    expect("路由召回率", s["routing_recall"], 1.0)
    expect("路由精确率", s["routing_precision"], 1.0)

    t.read_references(["05-figures-and-charts"])       # 读了不要求的
    expect("多读无关规则 -> precision 下降",
           t.summary()["routing_precision"], 0.667)
    expect("多读无关规则不影响 recall", t.summary()["routing_recall"], 1.0)

    t.require_tools(["statistical_forensics"])
    t.executed_tool("statistical_forensics")
    expect("工具执行召回率", t.summary()["tool_execution_recall"], 1.0)

    t.module_decision("M3", False, "本文无体外/动物实验成分")
    expect("跳过原因被记录",
           t.summary()["module_decisions"][0].get("why_skipped") is not None, True)

    print("\n全部通过" if ok_all else "\n存在失败项")
    return 0 if ok_all else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
