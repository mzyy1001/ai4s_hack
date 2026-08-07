#!/usr/bin/env python3
"""工具调度：由编排器**用代码**调用确定性脚本，不依赖模型记得去跑。

上一版把工具执行交给模型自己发起 shell 命令，两个后果都出现过：
一次是模型把脚本当源码反复 grep 却从不执行；一次是它把中间文件写到 /tmp
被运行时拒绝，整条取证链断掉。**确定性执行不该是模型的职责。**

两种触发路径都必须支持：

    主动扫描    解析出结构化对象即跑，**不等任何候选**
    候选验证    发现或专家怀疑某处有问题 → 定向核算

主动扫描尤其重要：真正的增益往往来自裸模型根本不会想到去做的检查。

每个 tool_task 必须落到唯一终态：executed / not_applicable / skipped / failed，
后两者必须给理由。**工具绝不允许悄无声息地消失。**
"""

import json
import os
import re
import subprocess

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "skills", "biomed-paper-review", "scripts")

# 主动扫描的正则：从稿件里认出可以直接送去核算的结构化对象
RE_COUNT_PCT = re.compile(r"(\d+)\s*/\s*(\d+)\s*\(\s*([\d.]+)\s*%\s*\)")
RE_T_TEST = re.compile(r"t\s*\(\s*(\d+)\s*\)\s*=\s*([\d.]+).{0,40}?[pP]\s*[=<]\s*([\d.]+)")
RE_CI = re.compile(r"([\d.]+)\s*(?:\(|,)\s*95%\s*CI[:\s]*([\d.]+)\s*(?:-|–|to)\s*([\d.]+)")
RE_NCT = re.compile(r"\bNCT\d{8}\b")
RE_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")
RE_CELL = re.compile(r"\b(?:MDA-MB-\d+|HeLa|HEK\s?293|A549|MCF-?7|HepG2|U-?CH[12]|"
                     r"IPEC|CCL\d+|SK-?[A-Z]+-?\d+|HL-?60|Jurkat|K562)\b")


class ToolDispatcher:
    def __init__(self, telemetry=None, workdir="."):
        self.telemetry = telemetry
        self.workdir = os.path.abspath(workdir)
        self.tasks = []
        self.signals = []
        self._n = 0

    def _next_id(self):
        self._n += 1
        return f"TOOL-{self._n:03d}"

    def _run(self, script, payload, timeout=180):
        """跑一个脚本。中间数据走 stdin，**不写临时文件** ——
        写 /tmp 会被运行时权限拒绝（实测踩过），写工作目录则会污染两臂对比。"""
        path = os.path.join(SCRIPTS_DIR, script)
        if not os.path.isfile(path):
            return None, f"脚本不存在：{script}"
        try:
            p = subprocess.run(
                ["python3", path, "--input", "-"],
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True, text=True, timeout=timeout,
                cwd=self.workdir, start_new_session=True)
        except subprocess.TimeoutExpired:
            return None, f"超时 {timeout}s"
        except Exception as exc:                                 # noqa: BLE001
            return None, f"{type(exc).__name__}: {str(exc)[:150]}"
        if p.returncode != 0:
            return None, f"退出码 {p.returncode}: {(p.stderr or '')[:200]}"
        try:
            return json.loads(p.stdout or "[]"), None
        except ValueError:
            return None, f"输出非 JSON：{(p.stdout or '')[:150]}"

    def dispatch(self, tool, script, target, checks, payload, origin=None,
                 proactive=False):
        """执行一个工具任务并登记终态。"""
        tid = self._next_id()
        task = {"tool_task_id": tid, "tool": tool, "target": target,
                "checks": checks, "origin": origin or [], "proactive": proactive}

        if not payload:
            task["status"] = "not_applicable"
            task["skip_reason"] = "稿件中未解析到该工具可处理的对象"
            self.tasks.append(task)
            return task

        out, err = self._run(script, payload)
        if err:
            task["status"] = "failed"
            task["skip_reason"] = err
            # **失败绝不等于「没问题」** —— 登记为限制交给调用方
            if self.telemetry:
                self.telemetry.executed_tool(tool, ok=False)
            self.tasks.append(task)
            return task

        sigs = out.get("signals", out) if isinstance(out, dict) else out
        sigs = sigs if isinstance(sigs, list) else []
        for s in sigs:
            s.setdefault("_tool_task_id", tid)
        self.signals.extend(sigs)
        task["status"] = "executed"
        task["signal_ids"] = [s.get("id") for s in sigs]
        if self.telemetry:
            self.telemetry.executed_tool(tool, ok=True)
        self.tasks.append(task)
        return task

    # ------------------------------------------------------- 主动扫描
    def proactive_scan(self, text, tables=None):
        """从稿件里认出结构化对象并**自动**送检，不等候选。"""
        t = text or ""

        # 计数-百分比
        items = [{"check": "count_percentage", "count": int(a), "n": int(b),
                  "reported_percent": float(c), "reported_percent_text": c,
                  "target": f"{a}/{b} ({c}%)"}
                 for a, b, c in RE_COUNT_PCT.findall(t)[:40]]
        self.dispatch("statistical_forensics", "statistical_forensics.py",
                      "计数-百分比", ["count_percentage"], items, proactive=True)

        # t 检验的 p 反算
        items = [{"check": "test_statistic_p", "test_family": "t",
                  "statistic": float(s), "df": int(df), "tail": "two",
                  "reported_p": p, "target": f"t({df})={s}, p={p}"}
                 for df, s, p in RE_T_TEST.findall(t)[:20]]
        self.dispatch("statistical_forensics", "statistical_forensics.py",
                      "t 检验 p 值", ["test_statistic_p"], items, proactive=True)

        # 点估计与 CI 自洽
        items = [{"check": "ci_estimate", "estimate": float(e),
                  "ci_low": float(lo), "ci_high": float(hi),
                  "target": f"{e} (95% CI {lo}-{hi})"}
                 for e, lo, hi in RE_CI.findall(t)[:20]]
        self.dispatch("statistical_forensics", "statistical_forensics.py",
                      "点估计与 CI", ["ci_estimate"], items, proactive=True)

        # 表格合计（由调用方给出已解析的表）
        items = [{"check": "table_total", "counts": tb["counts"],
                  "declared_total": tb["declared_total"],
                  "categories_exhaustive": True, "target": tb.get("label", "表")}
                 for tb in (tables or [])]
        self.dispatch("statistical_forensics", "statistical_forensics.py",
                      "表格合计", ["table_total"], items, proactive=True)

        # 外部核验：细胞系 / 注册号 / DOI。**这一类裸模型结构上做不到**
        ext = []
        for c in sorted(set(RE_CELL.findall(t)))[:5]:
            ext.append({"check": "cell_line", "cell_line": c, "evidence_refs": ["EV-001"]})
        for n in sorted(set(RE_NCT.findall(t)))[:3]:
            ext.append({"check": "trial_registration", "nct": n, "evidence_refs": ["EV-001"]})
        for d in sorted(set(RE_DOI.findall(t)))[:25]:
            ext.append({"check": "cited_retracted", "doi": d.rstrip(".,;"),
                        "evidence_refs": ["EV-001"]})
        self.dispatch("external_figure_validation", "external_figure_validation.py",
                      "外部标识符", ["cell_line", "trial_registration", "cited_retracted"],
                      ext, proactive=True)

        return self.tasks, self.signals

    # ------------------------------------------------------- 候选验证
    def verify_candidate(self, candidate, payload, tool, script, checks):
        return self.dispatch(tool, script, candidate.get("candidate_id", "?"),
                             checks, payload,
                             origin=[candidate.get("candidate_id")], proactive=False)

    def report(self):
        by = {}
        for t in self.tasks:
            by[t["status"]] = by.get(t["status"], 0) + 1
        return {"tool_tasks": self.tasks, "signals": self.signals,
                "status_counts": by,
                "signals_from_proactive": sum(
                    1 for t in self.tasks if t.get("proactive")
                    and t["status"] == "executed" for _ in (t.get("signal_ids") or []))}


def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    d = ToolDispatcher()
    text = ("Tumour volume differed (t(10) = 2.228, P = 0.001). "
            "Response was seen in 42/84 (60.0%) of patients. "
            "IC50 was 20.0 (95% CI 9.8-15.7) uM. "
            "Cells: MDA-MB-435 were cultured. Registered NCT01304069. "
            "See 10.1016/S0140-6736(20)31180-6 for details.")
    tables = [{"label": "Table 1", "counts": [12, 18], "declared_total": 28}]
    tasks, sigs = d.proactive_scan(text, tables)

    expect("所有任务都有终态",
           all(t.get("status") in ("executed", "not_applicable", "skipped", "failed")
               for t in tasks), True)
    expect("失败/跳过必须有理由",
           all(t.get("skip_reason") for t in tasks
               if t["status"] in ("failed", "skipped")), True)

    types = {s.get("type") for s in sigs}
    expect("表格合计不符被主动查出", "table_total_mismatch" in types, True)
    expect("t 检验 p 值不符被主动查出", "test_statistic_p_mismatch" in types, True)
    expect("CI 自洽问题被主动查出", "ci_estimate_mismatch" in types, True)
    expect("主动扫描全程无候选驱动",
           all(t["proactive"] for t in tasks), True)

    rep = d.report()
    expect("状态计数含 executed", "executed" in rep["status_counts"], True)
    print(f"       （共 {len(tasks)} 个任务，{len(sigs)} 条信号，"
          f"状态分布 {rep['status_counts']}）")

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
