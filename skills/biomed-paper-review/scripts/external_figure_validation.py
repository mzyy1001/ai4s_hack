#!/usr/bin/env python3
"""外部数据核验层 X1：拿稿件里的可核验主张去比对权威公开数据库。

**这是全套里唯一能查出「论文与真实世界不符」的工具。**
其余检查只能查论文内部是否自洽 —— 而内部自洽是裸模型本来就会做的事，
所以那部分的 uplift 结构上只能是零或负。实测的负 uplift 正源于此。

模型结构上做不到的，正是这里做的：

| 稿件里的主张 | 拿什么核 | 为什么模型做不到 |
| --- | --- | --- |
| 「用 MDA-MB-435 研究乳腺癌」 | Cellosaurus | 该系实为 M14 黑色素瘤衍生系；约六百条问题细胞系，长尾不可能知道 |
| 「本试验注册号 NCTxxxx」 | ClinicalTrials.gov | 注册日期只在注册库里，正文从不写 —— 回顾性注册纯读正文查不出 |
| 论文报告的主要结局 | ClinicalTrials.gov | 结局切换必须比对注册记录 |
| 参考文献 | Europe PMC | 撤稿常发生在模型训练截止之后 |
| WB 条带标为 100 kDa | UniProt | 需要精确分子量 |
| 「数据见 GSExxxxx」 | GEO / SRA / PRIDE | 登录号是否真的存在 |
| 报告 IC50 | ChEMBL | 已知活性数量级 |

按需查询，不预置数据集
----------------------
只在稿件里真的出现某个标识符时才发起那一次查询。不打包任何参考库：
提交包体积受限、数据库天天更新（撤稿状态尤其如此）、绝大多数论文只碰到极少数条目。

四条纪律
--------
1. **查不到 ≠ 论文错。** 接口失败一律产 `system_limitation`，**绝不**变成 finding。
   与契约 `parse_failed != not_reported` 同一条原则。
   `retrieval_status` 严格区分：`not_found` 仅限格式合法的精确标识符拿到权威 404
   或明确零记录；语义查询零命中记 `not_addressed`，绝不当作「不存在」。
2. **只产 signal，不产 finding。** 严重度由 M2–M7 结合稿件证据判定。
3. **数量级类判据恒为 `needs_manual_review`。** 不同细胞系、不同终点差一两个
   数量级是常态，不能自动判错。
4. **每条外部事实登记为 external evidence**，带端点、查询、取回时刻、响应 sha256、
   数据库版本，供复查还原。

输入
----
JSON 数组，每项须带 `check` 与 `evidence_refs`（指向稿件内 present evidence，
契约要求至少一条 —— 外部事实必须与稿件事实成对才有意义）。

    python3 external_figure_validation.py --selftest
    python3 external_figure_validation.py --input -
    python3 external_figure_validation.py --uniprot P04637
"""

import argparse
import hashlib
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PARSER_VERSION = "x1-2026-08-07"
RULE_VERSION = "2026-08-07"
UA = {"User-Agent": "ai4s-hack-biomed-review/1.0"}
# HGNC 与 SciCrunch 默认返回 XML/HTML，必须显式要 JSON
JSON_ACCEPT = {"Accept": "application/json"}

UNIPROT = "https://rest.uniprot.org/uniprotkb"
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PRIDE = "https://www.ebi.ac.uk/pride/ws/archive/v2"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
CELLO = "https://api.cellosaurus.org"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"
HGNC = "https://rest.genenames.org"
CROSSREF = "https://api.crossref.org/works"
SCICRUNCH = "https://scicrunch.org/resolver"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"
RCSB = "https://data.rcsb.org/rest/v1/core/entry"


class Ledger:
    """收集 signal / external evidence / system_limitation，统一编号。

    id 必须满足契约 pattern `^SIG-[0-9]{3,}$` / `^EV-[0-9]{3,}$`。
    X1 用 9xx 段，与 Stage 1–3 的编号错开。
    """

    def __init__(self):
        self.signals, self.evidence, self.limits = [], {}, []
        self._sig, self._ev, self._lim = 900, 900, 0

    def next_sig(self):
        self._sig += 1
        return f"SIG-{self._sig}"

    def add_evidence(self, entry):
        self._ev += 1
        entry["id"] = f"EV-{self._ev}"
        self.evidence[entry["id"]] = entry
        return entry["id"]

    def add_limit(self, detail, target, modules, err):
        self._lim += 1
        self.limits.append({
            "id": f"SYS-9{self._lim:02d}",
            "category": "external_source_unavailable",
            "impact": detail,
            "affected_modules": modules,
            "affected_targets": [target],
            "affected_fields": [],
            "evidence_refs": [],
            "recommended_action": "网络或白名单恢复后重跑 X1；在此之前不得就该主张下结论",
            "produced_by": "stage_3c_external_validation",
            "_error": err,
        })
        return None


# ---------------------------------------------------------------- 传输层
def fetch(url, timeout=40, retries=2, headers=None):
    """返回 (text, http_status, error)。

    **任何失败都返回 error，绝不静默当成「查无此项」** —— 这正是本项目
    反复踩过的坑：把「我们没查到」当成「论文有问题」。
    """
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace"), r.status, None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, 404, {"kind": "not_found", "http": 404}
            last = {"kind": "http_error", "http": e.code}
            if e.code not in (429, 500, 502, 503, 504):
                return None, e.code, last
        except Exception as exc:                                 # noqa: BLE001
            last = {"kind": "transport_error", "detail": str(exc)[:140]}
        if i < retries:
            time.sleep(2 * (i + 1))
    return None, None, last


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def make_external_evidence(db, endpoint, query_kind, normalized_input,
                           record_id, raw, http_status, status,
                           db_version=None, assertions=None):
    """构造 external evidence 条目。

    契约硬性约束：`resolved` 必须有 record_id 且 assertions 非空；
    `not_found` / `not_addressed` 必须 record_id 为 null 且 assertions 为空。
    """
    resolved = status == "resolved"
    return {
        "type": "external",
        "database": db,
        "endpoint": endpoint,
        "query": {"query_kind": query_kind, "normalized_input": normalized_input},
        "record_id": record_id if resolved else None,
        "retrieved_at": _now(),
        "database_version": db_version,
        "http_status": http_status if http_status is not None else 200,
        "retrieval_status": status,
        "response_sha256": hashlib.sha256((raw or "").encode("utf-8")).hexdigest(),
        "parser_version": PARSER_VERSION,
        "assertions": (assertions or []) if resolved else [],
        "created_by": "stage_3c_external_validation",
    }


def make_signal(sid, target, detail, routed_to, connector, query_kind, check_type,
                manuscript_value, external_value, comparison_result, comparability,
                man_refs, ext_refs, noncomparability_reasons=None):
    sig = {
        "id": sid,
        "type": "external_validation_candidate",
        "target": target,
        "detail": detail,
        "observation_refs": [],
        "evidence_refs": list(man_refs) + list(ext_refs),
        "routed_to": routed_to,
        "produced_by": "stage_3c_external_validation",
        "external_check": {
            "connector": connector,
            "query_kind": query_kind,
            "check_type": check_type,
            "manuscript_value": manuscript_value,
            "external_value": external_value,
            "comparison_result": comparison_result,
            "comparability": comparability,
            "manuscript_evidence_refs": list(man_refs),
            "external_evidence_refs": list(ext_refs),
            "rule_version": RULE_VERSION,
        },
    }
    if noncomparability_reasons:
        sig["external_check"]["noncomparability_reasons"] = noncomparability_reasons
    return sig


# ---------------------------------------------------------------- UniProt
def _uniprot(acc, led, target, modules):
    url = f"{UNIPROT}/{urllib.parse.quote(acc)}.json"
    raw, http, err = fetch(url)
    if err and err.get("kind") == "not_found":
        led.add_evidence(make_external_evidence(
            "UniProt", url, "accession_lookup", acc, None, raw, 404, "not_found"))
        return None, None
    if err:
        led.add_limit(f"无法取回 UniProt {acc}，相关核验未完成", target, modules, err)
        return None, None
    d = json.loads(raw)
    seq = d.get("sequence", {})
    p = {
        "accession": d.get("primaryAccession", acc),
        "organism": (d.get("organism") or {}).get("scientificName"),
        "length": seq.get("length"),
        "kda": (seq.get("molWeight") or 0) / 1000.0,
        "sequence": seq.get("value", ""),
    }
    ev = led.add_evidence(make_external_evidence(
        "UniProt", url, "accession_lookup", acc, p["accession"], raw, http, "resolved",
        db_version=str((d.get("entryAudit") or {}).get("entryVersion") or "") or None,
        assertions=[
            {"predicate": "sequence_length", "subject": p["accession"],
             "external_value": p["length"], "unit": "aa",
             "source_path": "sequence.length"},
            {"predicate": "molecular_weight", "subject": p["accession"],
             "external_value": round(p["kda"], 1), "unit": "kDa",
             "source_path": "sequence.molWeight"},
        ]))
    return p, ev


def check_blot_band(item, led, sid):
    """WB 条带标注的分子量与蛋白真实分子量是否相容。

    恒为 `needs_manual_review`：翻译后修饰、糖基化、二聚体、切割片段
    都会改变迁移位置，不能自动判错。
    """
    acc, kda = item.get("uniprot"), item.get("reported_kda")
    target = item.get("target", "figure.blot")
    if not acc or kda is None:
        return None
    p, ev = _uniprot(acc, led, target, ["M5"])
    if not p or not p["kda"]:
        return None
    lo, hi = p["kda"] * 0.6, p["kda"] * 1.8
    if lo <= kda <= hi:
        return None
    return make_signal(
        sid, target,
        f"图中条带标注为 {kda} kDa，UniProt {p['accession']}（{p['organism']}，"
        f"{p['length']} aa）理论分子量 {p['kda']:.1f} kDa，超出常规迁移偏差范围"
        f"（{lo:.1f}–{hi:.1f} kDa）。翻译后修饰、糖基化、二聚体、切割片段均可解释此差异，"
        f"须人工核对后再定性。",
        ["M5"], "uniprot", "accession_lookup", "blot_band_molecular_weight",
        {"reported_kda": kda}, {"theoretical_kda": round(p["kda"], 1)},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


def check_variant(item, led, sid):
    """变异位点是否落在真实蛋白序列内、参考残基是否相符。

    这把 `sequence_identifier_audit.py` 从「只能对着论文自己给的序列查」
    升级为「对着真实蛋白查」—— 论文不给序列时也能查。
    """
    acc, pos = item.get("uniprot"), item.get("position")
    ref = item.get("ref_aa")
    target = item.get("target", "variant")
    if not acc or pos is None:
        return None
    p, ev = _uniprot(acc, led, target, ["M2", "M3"])
    if not p:
        return None
    if pos > (p["length"] or 0):
        return make_signal(
            sid, target,
            f"变异位点 {pos} 超出 {p['accession']}（{p['organism']}）序列长度 "
            f"{p['length']} aa —— 位置越界。",
            ["M2", "M3"], "uniprot", "accession_lookup", "variant_position_range",
            {"position": pos}, {"sequence_length": p["length"]},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if ref:
        actual = p["sequence"][pos - 1:pos]
        if actual and actual != ref:
            return make_signal(
                sid, target,
                f"变异声称第 {pos} 位参考残基为 {ref}，"
                f"但 {p['accession']} 该位实际为 {actual}。",
                ["M2", "M3"], "uniprot", "accession_lookup",
                "variant_reference_residue",
                {"position": pos, "ref_aa": ref}, {"actual_aa": actual},
                "mismatch", "complete", item["evidence_refs"], [ev])
    return None


# ---------------------------------------------------------------- Cellosaurus
def check_cell_line(item, led, sid):
    """细胞系是否被 Cellosaurus 认定为污染 / 错误鉴定。

    **全套价值最高的一条。** MDA-MB-435 被大量论文当作乳腺癌细胞系，
    Cellosaurus 标注为 M14 黑色素瘤衍生系 —— 用它得出的「乳腺癌」结论，
    研究对象本身就不对，这推翻的是全文而非某个次要瑕疵。
    """
    name = (item.get("cell_line") or "").strip()
    target = item.get("target", "methods.cell_line")
    if not name:
        return None
    url = f"{CELLO}/search/cell-line?q={urllib.parse.quote(name)}&format=json&rows=1"
    raw, http, err = fetch(url)
    if err:
        return led.add_limit(f"无法查询 Cellosaurus 中的 {name}", target, ["M3"], err)
    try:
        lst = json.loads(raw)["Cellosaurus"]["cell-line-list"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("Cellosaurus 返回无法解析", target, ["M3"],
                             {"kind": "unparseable"})
    if not lst:
        # 名称检索零命中属**语义查询**未命中，不是「该细胞系不存在」
        led.add_evidence(make_external_evidence(
            "Cellosaurus", url, "cell_line_name_search", name, None, raw, http,
            "not_addressed"))
        return None

    cl = lst[0]
    acc = next((x.get("value") for x in cl.get("accession-list", [])), None)
    problems = [c["value"] for c in cl.get("comment-list", [])
                if "Problematic" in (c.get("category") or "")]
    ev = led.add_evidence(make_external_evidence(
        "Cellosaurus", f"{CELLO}/cell-line/{acc}", "cell_line_name_search", name,
        acc, raw, http, "resolved",
        db_version=str(cl.get("entry-version") or "") or None,
        assertions=[{"predicate": "problematic_flag", "subject": acc,
                     "external_value": problems[0][:300] if problems else None,
                     "unit": None,
                     "source_path": "comment-list[category=Problematic]"}]))
    if not problems:
        return None
    return make_signal(
        sid, target,
        f"Cellosaurus 将 {name}（{acc}）标注为有问题：{problems[0][:220]}。"
        f"若稿件把它当作某组织来源的模型，该前提可能不成立，"
        f"进而影响全部基于该细胞系的结论。",
        ["M3"], "cellosaurus", "cell_line_name_search", "cell_line_problematic",
        {"cell_line": name}, {"problematic": problems[0][:300]},
        "mismatch", "complete", item["evidence_refs"], [ev])


# ---------------------------------------------------------------- 登录号
def check_accession(item, led, sid):
    """论文声称「数据已上传」的登录号是否真实存在。

    恒为 `needs_manual_review`：可能处于 embargo 或刚提交未索引。
    """
    acc = (item.get("accession") or "").strip()
    target = item.get("target", "declarations.data_availability")
    if not acc:
        return None
    if acc.startswith(("GSE", "GSM", "GDS", "GPL")):
        db = "GEO"
        url = f"{EUTILS}/esearch.fcgi?db=gds&term={urllib.parse.quote(acc)}&retmode=json"
    elif acc.startswith(("SRR", "SRX", "SRP", "ERR", "ERP", "DRR")):
        db = "SRA"
        url = f"{EUTILS}/esearch.fcgi?db=sra&term={urllib.parse.quote(acc)}&retmode=json"
    elif acc.startswith("PXD"):
        db = "PRIDE"
        url = f"{PRIDE}/projects/{urllib.parse.quote(acc)}"
    else:
        return None

    raw, http, err = fetch(url)
    missing = bool(err) and err.get("kind") == "not_found"
    if err and not missing:
        return led.add_limit(f"无法查询 {db} 登录号 {acc}", target, ["M7"], err)
    if not missing and db in ("GEO", "SRA"):
        try:
            missing = int(json.loads(raw)["esearchresult"]["count"]) == 0
        except Exception:                                        # noqa: BLE001
            return led.add_limit(f"{db} 返回无法解析", target, ["M7"],
                                 {"kind": "unparseable"})
    status = "not_found" if missing else "resolved"
    ev = led.add_evidence(make_external_evidence(
        db, url, "accession_lookup", acc, acc, raw, http, status,
        assertions=[] if missing else [
            {"predicate": "record_exists", "subject": acc, "external_value": True,
             "unit": None, "source_path": "esearchresult.count"}]))
    if not missing:
        return None
    return make_signal(
        sid, target,
        f"稿件声称的 {db} 登录号 {acc} 检索不到记录。也可能处于 embargo "
        f"或刚提交尚未索引，须人工确认后再定性。",
        ["M7"], db.lower(), "accession_lookup", "accession_exists",
        {"accession": acc}, {"found": False},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------------------------- ChEMBL
def check_ic50(item, led, sid):
    """报告的 IC50 与 ChEMBL 已知活性是否差三个数量级以上。恒为候选。"""
    cid, val = item.get("chembl_id"), item.get("reported_nm")
    target = item.get("target", "figure.dose_response")
    if not cid or not val:
        return None
    url = (f"{CHEMBL}/activity.json?molecule_chembl_id={urllib.parse.quote(cid)}"
           f"&standard_type=IC50&limit=100")
    raw, http, err = fetch(url, timeout=60)
    if err:
        return led.add_limit(f"无法取回 ChEMBL {cid} 的活性数据", target, ["M5"], err)
    try:
        acts = json.loads(raw).get("activities", [])
    except Exception:                                            # noqa: BLE001
        return led.add_limit("ChEMBL 返回无法解析", target, ["M5"],
                             {"kind": "unparseable"})
    vals = sorted(float(a["standard_value"]) for a in acts
                  if a.get("standard_value") and a.get("standard_units") == "nM")
    if len(vals) < 5:
        return led.add_limit(
            f"ChEMBL 中 {cid} 的 IC50 记录仅 {len(vals)} 条，不足以判断数量级",
            target, ["M5"], {"kind": "insufficient_records"})
    med = vals[len(vals) // 2]
    ratio = max(val / med, med / val) if med > 0 else 0
    ev = led.add_evidence(make_external_evidence(
        "ChEMBL", url, "activity_lookup", cid, cid, raw, http, "resolved",
        assertions=[{"predicate": "median_ic50", "subject": cid,
                     "external_value": med, "unit": "nM",
                     "source_path": "activities[].standard_value"}]))
    if ratio < 1000:
        return None
    return make_signal(
        sid, target,
        f"报告 IC50 = {val:g} nM，ChEMBL 中 {cid} 的 {len(vals)} 条 IC50 记录"
        f"中位数为 {med:g} nM，相差约 {ratio:.0f} 倍。不同细胞系与终点的活性差异是常态，"
        f"须人工核对实验体系是否可比。",
        ["M5"], "chembl", "activity_lookup", "ic50_order_of_magnitude",
        {"reported_nm": val}, {"median_nm": med, "n_records": len(vals)},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- ClinicalTrials.gov
def _ctgov(nct, led, target, modules):
    url = (f"{CTGOV}/{urllib.parse.quote(nct)}?fields=protocolSection.statusModule,"
           f"protocolSection.outcomesModule,protocolSection.designModule")
    raw, http, err = fetch(url, timeout=60)
    if err and err.get("kind") == "not_found":
        return None, url, raw, http, "not_found"
    if err:
        led.add_limit(f"无法查询注册号 {nct}", target, modules, err)
        return None, url, raw, http, None
    try:
        return json.loads(raw)["protocolSection"], url, raw, http, "resolved"
    except Exception:                                            # noqa: BLE001
        led.add_limit(f"{nct} 注册记录无法解析", target, modules,
                      {"kind": "unparseable"})
        return None, url, raw, http, None


def registered_late(reg, start):
    """注册是否**确定**晚于研究开始。

    ClinicalTrials.gov 的 startDate 常常只有 YYYY-MM 精度，而注册日期是
    YYYY-MM-DD。直接字符串比较会把「同月注册」误判为回顾性注册 ——
    start=2011-02、reg=2011-02-24 时，研究完全可能是 24 号之后才开始的，
    我们无从判断。**取两者中较粗的精度比较，并要求严格大于**，
    宁可漏报也不能凭猜测给稿件扣帽子。
    """
    if not (reg and start):
        return False
    n = min(len(reg), len(start))
    return reg[:n] > start[:n]


def check_trial_registration(item, led, sid):
    """注册号是否存在、是否**回顾性注册**（注册晚于研究开始）。

    ICMJE 要求前瞻性注册。注册日期与开始日期都只在注册库里，
    正文几乎从不写 —— 纯读正文绝无可能发现回顾性注册。
    """
    nct = (item.get("nct") or "").strip()
    target = item.get("target", "declarations.trial_registration")
    if not nct.upper().startswith("NCT"):
        return None
    ps, url, raw, http, status = _ctgov(nct, led, target, ["M6"])
    if status == "not_found":
        ev = led.add_evidence(make_external_evidence(
            "ClinicalTrials.gov", url, "nct_lookup", nct, None, raw, http,
            "not_found"))
        return make_signal(
            sid, target, f"稿件声称的注册号 {nct} 在 ClinicalTrials.gov 查不到记录。",
            ["M6"], "clinicaltrials_gov", "nct_lookup", "trial_registration_exists",
            {"nct": nct}, {"found": False},
            "needs_manual_review", "partial", item["evidence_refs"], [ev])
    if not ps:
        return None

    sm = ps.get("statusModule", {})
    reg = sm.get("studyFirstSubmitDate")
    start = (sm.get("startDateStruct") or {}).get("date")
    ev = led.add_evidence(make_external_evidence(
        "ClinicalTrials.gov", url, "nct_lookup", nct, nct, raw, http, "resolved",
        db_version=sm.get("lastUpdateSubmitDate"),
        assertions=[
            {"predicate": "study_first_submit_date", "subject": nct,
             "external_value": reg, "unit": None,
             "source_path": "protocolSection.statusModule.studyFirstSubmitDate"},
            {"predicate": "start_date", "subject": nct, "external_value": start,
             "unit": None,
             "source_path": "protocolSection.statusModule.startDateStruct.date"},
        ]))
    if not registered_late(reg, start):
        return None
    return make_signal(
        sid, target,
        f"{nct} 注册日期 {reg} 晚于研究开始日期 {start} —— 属回顾性注册，"
        f"不符合 ICMJE 前瞻性注册要求。注册日期仅存于注册库，正文通常不写。",
        ["M6"], "clinicaltrials_gov", "nct_lookup", "prospective_registration",
        {"claimed_registration": nct}, {"registered": reg, "started": start},
        "mismatch", "complete", item["evidence_refs"], [ev])


def check_outcome_switching(item, led, sid):
    """报告的主要结局与注册的主要结局是否一致（结局切换）。

    结局切换是临床试验最隐蔽的偏倚之一，**必须比对注册记录**。
    这里只做关键词粗筛，恒为 `needs_manual_review` —— 措辞差异也会造成不匹配。
    """
    nct = (item.get("nct") or "").strip()
    reported = (item.get("reported_primary") or "").strip()
    target = item.get("target", "outcomes.primary")
    if not nct.upper().startswith("NCT") or not reported:
        return None
    ps, url, raw, http, _ = _ctgov(nct, led, target, ["M4", "M7"])
    if not ps:
        return None
    regd = [o.get("measure") for o in
            (ps.get("outcomesModule") or {}).get("primaryOutcomes", [])
            if o.get("measure")]
    if not regd:
        return led.add_limit(f"{nct} 未登记主要结局，无法比对结局切换",
                             target, ["M4", "M7"], {"kind": "no_data"})

    stop = {"of", "the", "in", "to", "and", "at", "from", "with", "for", "rate",
            "change", "score", "time", "number", "percentage", "mean",
            "participants"}

    def words(t):
        return {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in stop}

    rw = words(reported)
    if any(words(r) & rw for r in regd):
        return None
    ev = led.add_evidence(make_external_evidence(
        "ClinicalTrials.gov", url, "nct_lookup", nct, nct, raw, http, "resolved",
        db_version=(ps.get("statusModule") or {}).get("lastUpdateSubmitDate"),
        assertions=[{"predicate": "registered_primary_outcome", "subject": nct,
                     "external_value": regd, "unit": None,
                     "source_path":
                     "protocolSection.outcomesModule.primaryOutcomes[].measure"}]))
    return make_signal(
        sid, target,
        f"稿件报告的主要结局为「{reported[:90]}」，{nct} 登记的主要结局为"
        f"「{'；'.join(regd)[:160]}」，两者无共同关键词，疑似结局切换。"
        f"措辞差异也可能造成不匹配，须人工比对。",
        ["M4", "M7"], "clinicaltrials_gov", "nct_lookup", "outcome_switching",
        {"reported_primary": reported}, {"registered_primary": regd},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- 引用已撤稿文献
def check_cited_retracted(item, led, sid):
    """引用的参考文献是否**已被撤稿**。

    模型结构上做不到：撤稿常发生在训练截止之后，长尾撤稿更不在任何模型知识里。
    走 Europe PMC 的 pubType —— 实测 Crossref 的 update-by 对已撤稿论文常为空
    （例如 Surgisphere 那篇 Lancet），不可靠。
    """
    doi = (item.get("doi") or "").strip()
    target = item.get("target", "references")
    if not doi:
        return None
    query = f'DOI:"{doi}"'
    url = f"{EPMC}/search?query={urllib.parse.quote(query)}&format=json&resultType=core"
    raw, http, err = fetch(url, timeout=60)
    if err:
        return led.add_limit(f"无法查询参考文献 {doi} 的撤稿状态", target,
                             ["M2", "M7"], err)
    try:
        res = json.loads(raw)["resultList"]["result"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("Europe PMC 返回无法解析", target, ["M2", "M7"],
                             {"kind": "unparseable"})
    if not res:
        led.add_evidence(make_external_evidence(
            "Europe PMC", url, "doi_lookup", doi, None, raw, http, "not_addressed"))
        return None
    a = res[0]
    types = (a.get("pubTypeList") or {}).get("pubType") or []
    retracted = "Retracted Publication" in types
    ev = led.add_evidence(make_external_evidence(
        "Europe PMC", url, "doi_lookup", doi, a.get("id"), raw, http, "resolved",
        assertions=[{"predicate": "is_retracted", "subject": doi,
                     "external_value": retracted, "unit": None,
                     "source_path": "resultList.result[0].pubTypeList.pubType"}]))
    if not retracted:
        return None
    return make_signal(
        sid, target,
        f"参考文献 {doi}（{(a.get('title') or '')[:70]}）已被撤稿。"
        f"若该文献是本文立论依据，相关推理需重新评估。",
        ["M2", "M7"], "europe_pmc", "doi_lookup", "cited_work_retracted",
        {"doi": doi}, {"retracted": True},
        "mismatch", "complete", item["evidence_refs"], [ev])


# ---------------------------------------------- HGNC 基因符号
# Excel 会把这些基因符号自动转成日期，是基因列表里最常见的静默污染。
# 2020 年 HGNC 为此把整个 SEPT/MARCH/DEC 家族改名（SEPT2 -> SEPTIN2）。
_EXCEL_DATE = re.compile(r"^(\d{1,2}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                         r"|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{1,2})$",
                         re.I)


def check_gene_symbol(item, led, sid):
    """人类基因符号是否为 HGNC 已批准符号；是否为已改名的旧符号；
    是否是**被 Excel 转成日期**的基因名。

    HGNC 只管人类命名；给了非人类物种就不查（小鼠走 MGI，斑马鱼走 ZFIN），
    否则会把正常的小鼠符号误报成「未批准」。
    """
    sym = (item.get("symbol") or "").strip()
    species = (item.get("species") or "").strip().lower()
    target = item.get("target", "methods.genes")
    if not sym:
        return None
    if species and species not in ("human", "homo sapiens", "hsa"):
        return None

    # Excel 日期化不需要联网就能判定，但仍登记外部证据以便复查改名后的正确符号
    if _EXCEL_DATE.match(sym):
        url = f"{HGNC}/search/prev_symbol/{urllib.parse.quote(sym)}"
        return make_signal(
            sid, target,
            f"基因符号「{sym}」是日期格式 —— Excel 会把 SEPT/MARCH/DEC 家族的符号"
            f"自动转成日期，这是基因列表里最常见的静默污染。HGNC 已于 2020 年"
            f"将该家族改名（SEPT2→SEPTIN2、MARCH1→MARCHF1）以规避此问题。"
            f"须回到原始数据核对该列究竟是哪个基因。",
            ["M2", "M3"], "hgnc", "symbol_lookup", "gene_symbol_excel_corruption",
            {"symbol": sym}, {"looks_like_date": True},
            "mismatch", "complete", item["evidence_refs"],
            [led.add_evidence(make_external_evidence(
                "HGNC", url, "symbol_lookup", sym, None, "", 200, "not_addressed"))])

    url = f"{HGNC}/fetch/symbol/{urllib.parse.quote(sym)}"
    raw, http, err = fetch(url, headers=JSON_ACCEPT)
    if err:
        return led.add_limit(f"无法查询 HGNC 中的基因符号 {sym}", target,
                             ["M2", "M3"], err)
    try:
        resp = json.loads(raw)["response"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("HGNC 返回无法解析", target, ["M2", "M3"],
                             {"kind": "unparseable"})
    if resp.get("numFound"):
        d = resp["docs"][0]
        led.add_evidence(make_external_evidence(
            "HGNC", url, "symbol_lookup", sym, d.get("hgnc_id"), raw, http, "resolved",
            assertions=[{"predicate": "symbol_status", "subject": d.get("hgnc_id"),
                         "external_value": d.get("status"), "unit": None,
                         "source_path": "response.docs[0].status"}]))
        return None

    # 未命中已批准符号 —— 可能是旧符号（已改名）、别名，或根本不存在
    purl = f"{HGNC}/search/prev_symbol/{urllib.parse.quote(sym)}"
    praw, phttp, perr = fetch(purl, headers=JSON_ACCEPT)
    if perr:
        return led.add_limit(f"无法查询 {sym} 是否为旧符号", target, ["M2", "M3"], perr)
    try:
        presp = json.loads(praw)["response"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("HGNC 返回无法解析", target, ["M2", "M3"],
                             {"kind": "unparseable"})
    if presp.get("numFound"):
        cur = presp["docs"][0].get("symbol")
        ev = led.add_evidence(make_external_evidence(
            "HGNC", purl, "prev_symbol_search", sym, presp["docs"][0].get("hgnc_id"),
            praw, phttp, "resolved",
            assertions=[{"predicate": "current_symbol", "subject": sym,
                         "external_value": cur, "unit": None,
                         "source_path": "response.docs[0].symbol"}]))
        return make_signal(
            sid, target,
            f"基因符号「{sym}」已非 HGNC 现行符号，现行符号为「{cur}」。"
            f"旧符号本身不算错误，但与现行文献比对时容易张冠李戴。",
            ["M2", "M3"], "hgnc", "prev_symbol_search", "gene_symbol_outdated",
            {"symbol": sym}, {"current_symbol": cur},
            "mismatch", "complete", item["evidence_refs"], [ev])

    ev = led.add_evidence(make_external_evidence(
        "HGNC", url, "symbol_lookup", sym, None, raw, http, "not_addressed"))
    return make_signal(
        sid, target,
        f"基因符号「{sym}」既非 HGNC 已批准符号，也不是已登记的旧符号。"
        f"可能是拼写错误、非人类物种的符号，或非标准的内部命名，须人工确认。",
        ["M2", "M3"], "hgnc", "symbol_lookup", "gene_symbol_unrecognized",
        {"symbol": sym}, {"found": False},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- Crossref 参考文献存在性
def check_reference_exists(item, led, sid):
    """参考文献的 DOI 是否真实存在。

    查的是**幻觉引文与纸厂引文** —— 生成式工具写出的参考文献常常格式完美
    但 DOI 根本不存在。模型自己核不了：它没法解析 DOI。
    """
    doi = (item.get("doi") or "").strip()
    target = item.get("target", "references")
    if not doi:
        return None
    url = f"{CROSSREF}/{urllib.parse.quote(doi, safe='')}"
    raw, http, err = fetch(url)
    if err and err.get("kind") == "not_found":
        ev = led.add_evidence(make_external_evidence(
            "Crossref", url, "doi_resolve", doi, None, raw, 404, "not_found"))
        return make_signal(
            sid, target,
            f"参考文献 DOI {doi} 在 Crossref 无法解析。格式完美但不存在的 DOI "
            f"是幻觉引文与纸厂引文的典型特征，须核对该条文献是否真实。",
            ["M2"], "crossref", "doi_resolve", "reference_doi_resolves",
            {"doi": doi}, {"resolves": False},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"无法解析 DOI {doi}", target, ["M2"], err)
    try:
        msg = json.loads(raw)["message"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("Crossref 返回无法解析", target, ["M2"],
                             {"kind": "unparseable"})
    led.add_evidence(make_external_evidence(
        "Crossref", url, "doi_resolve", doi, msg.get("DOI"), raw, http, "resolved",
        assertions=[{"predicate": "title", "subject": msg.get("DOI"),
                     "external_value": (msg.get("title") or [None])[0], "unit": None,
                     "source_path": "message.title[0]"}]))
    return None


# ---------------------------------------------- NCBI Taxonomy 物种
def check_species(item, led, sid):
    """物种学名是否为 NCBI Taxonomy 中的有效名称。"""
    name = (item.get("species") or "").strip()
    target = item.get("target", "methods.species")
    if not name:
        return None
    url = (f"{EUTILS}/esearch.fcgi?db=taxonomy&term="
           f"{urllib.parse.quote(name)}&retmode=json")
    raw, http, err = fetch(url)
    if err:
        return led.add_limit(f"无法查询物种名 {name}", target, ["M3"], err)
    try:
        r = json.loads(raw)["esearchresult"]
        cnt, ids = int(r["count"]), r.get("idlist", [])
    except Exception:                                            # noqa: BLE001
        return led.add_limit("NCBI Taxonomy 返回无法解析", target, ["M3"],
                             {"kind": "unparseable"})
    if cnt:
        led.add_evidence(make_external_evidence(
            "NCBI Taxonomy", url, "scientific_name_search", name,
            ids[0] if ids else name, raw, http, "resolved",
            assertions=[{"predicate": "taxid", "subject": name,
                         "external_value": ids[0] if ids else None, "unit": None,
                         "source_path": "esearchresult.idlist[0]"}]))
        return None
    ev = led.add_evidence(make_external_evidence(
        "NCBI Taxonomy", url, "scientific_name_search", name, None, raw, http,
        "not_addressed"))
    return make_signal(
        sid, target,
        f"物种名「{name}」在 NCBI Taxonomy 检索不到。可能是拼写错误、"
        f"过时的分类名，或俗名被当作学名使用，须人工确认。",
        ["M3"], "ncbi_taxonomy", "scientific_name_search", "species_name_valid",
        {"species": name}, {"found": False},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- RRID 试剂标识符
def check_rrid(item, led, sid):
    """抗体 / 试剂 / 质粒的 RRID 是否可解析。

    抗体是生物医学复现危机的重灾区。RRID 是目前唯一能把「哪一支抗体」
    唯一确定下来的标识符 —— 而它能不能解析，只有查 SciCrunch 才知道。
    """
    rrid = (item.get("rrid") or "").strip().replace("RRID:", "")
    target = item.get("target", "methods.reagents")
    if not rrid:
        return None
    url = f"{SCICRUNCH}/RRID:{urllib.parse.quote(rrid)}.json"
    raw, http, err = fetch(url, headers=JSON_ACCEPT)
    if err and err.get("kind") == "not_found":
        ev = led.add_evidence(make_external_evidence(
            "SciCrunch RRID", url, "rrid_resolve", rrid, None, raw, 404, "not_found"))
        return make_signal(
            sid, target,
            f"RRID:{rrid} 无法解析。RRID 是唯一能把具体某支抗体/试剂确定下来的"
            f"标识符，解析不了意味着该试剂无法被他人复现使用。",
            ["M3"], "scicrunch", "rrid_resolve", "rrid_resolves",
            {"rrid": rrid}, {"resolves": False},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"无法解析 RRID:{rrid}", target, ["M3"], err)
    try:
        hits = json.loads(raw).get("hits", {}).get("hits", [])
    except Exception:                                            # noqa: BLE001
        return led.add_limit("SciCrunch 返回无法解析", target, ["M3"],
                             {"kind": "unparseable"})
    if not hits:
        ev = led.add_evidence(make_external_evidence(
            "SciCrunch RRID", url, "rrid_resolve", rrid, None, raw, http, "not_found"))
        return make_signal(
            sid, target, f"RRID:{rrid} 解析到零条记录。",
            ["M3"], "scicrunch", "rrid_resolve", "rrid_resolves",
            {"rrid": rrid}, {"resolves": False},
            "mismatch", "complete", item["evidence_refs"], [ev])
    nm = (hits[0].get("_source", {}).get("item", {}) or {}).get("name")
    led.add_evidence(make_external_evidence(
        "SciCrunch RRID", url, "rrid_resolve", rrid, rrid, raw, http, "resolved",
        assertions=[{"predicate": "reagent_name", "subject": rrid,
                     "external_value": nm, "unit": None,
                     "source_path": "hits.hits[0]._source.item.name"}]))
    return None


# ---------------------------------------------- PubChem 化合物
def check_compound(item, led, sid):
    """化合物名是否存在；若稿件报告了分子量，与 PubChem 是否相符。"""
    name = (item.get("compound") or "").strip()
    reported_mw = item.get("reported_mw")
    target = item.get("target", "methods.compounds")
    if not name:
        return None
    url = (f"{PUBCHEM}/name/{urllib.parse.quote(name)}/property/"
           f"MolecularFormula,MolecularWeight/JSON")
    raw, http, err = fetch(url)
    if err and err.get("kind") == "not_found":
        ev = led.add_evidence(make_external_evidence(
            "PubChem", url, "compound_name_lookup", name, None, raw, 404,
            "not_addressed"))
        return make_signal(
            sid, target,
            f"化合物名「{name}」在 PubChem 检索不到。可能是内部代号、"
            f"拼写错误或未收录的新化合物，须人工确认。",
            ["M3", "M5"], "pubchem", "compound_name_lookup", "compound_name_valid",
            {"compound": name}, {"found": False},
            "needs_manual_review", "partial", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"无法查询化合物 {name}", target, ["M3", "M5"], err)
    try:
        p = json.loads(raw)["PropertyTable"]["Properties"][0]
        mw, formula = float(p["MolecularWeight"]), p["MolecularFormula"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("PubChem 返回无法解析", target, ["M3", "M5"],
                             {"kind": "unparseable"})
    ev = led.add_evidence(make_external_evidence(
        "PubChem", url, "compound_name_lookup", name, str(p.get("CID") or name),
        raw, http, "resolved",
        assertions=[
            {"predicate": "molecular_weight", "subject": name, "external_value": mw,
             "unit": "g/mol", "source_path": "PropertyTable.Properties[0].MolecularWeight"},
            {"predicate": "molecular_formula", "subject": name,
             "external_value": formula, "unit": None,
             "source_path": "PropertyTable.Properties[0].MolecularFormula"},
        ]))
    if reported_mw is None or abs(reported_mw - mw) / mw <= 0.02:
        return None
    return make_signal(
        sid, target,
        f"稿件报告 {name} 的分子量为 {reported_mw}，PubChem 记录为 {mw}"
        f"（{formula}）。分子量直接影响摩尔浓度换算，偏差会传导到全部剂量计算。"
        f"盐型、水合物、同位素标记均可解释此差异，须人工核对。",
        ["M3", "M5"], "pubchem", "compound_name_lookup", "compound_molecular_weight",
        {"reported_mw": reported_mw}, {"pubchem_mw": mw, "formula": formula},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- PDB 结构
def check_pdb(item, led, sid):
    """稿件引用的 PDB 结构编号是否存在。"""
    pdb = (item.get("pdb_id") or "").strip().upper()
    target = item.get("target", "methods.structures")
    if not pdb:
        return None
    url = f"{RCSB}/{urllib.parse.quote(pdb)}"
    raw, http, err = fetch(url)
    if err and err.get("kind") == "not_found":
        ev = led.add_evidence(make_external_evidence(
            "RCSB PDB", url, "entry_lookup", pdb, None, raw, 404, "not_found"))
        return make_signal(
            sid, target, f"稿件引用的 PDB 编号 {pdb} 在 RCSB 查不到条目。",
            ["M3", "M5"], "rcsb_pdb", "entry_lookup", "pdb_entry_exists",
            {"pdb_id": pdb}, {"found": False},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"无法查询 PDB {pdb}", target, ["M3", "M5"], err)
    try:
        d = json.loads(raw)
        title = (d.get("struct") or {}).get("title")
    except Exception:                                            # noqa: BLE001
        return led.add_limit("RCSB 返回无法解析", target, ["M3", "M5"],
                             {"kind": "unparseable"})
    led.add_evidence(make_external_evidence(
        "RCSB PDB", url, "entry_lookup", pdb, pdb, raw, http, "resolved",
        assertions=[{"predicate": "structure_title", "subject": pdb,
                     "external_value": title, "unit": None,
                     "source_path": "struct.title"}]))
    return None


CHECKS = {
    "cell_line": check_cell_line,
    "gene_symbol": check_gene_symbol,
    "reference_exists": check_reference_exists,
    "species": check_species,
    "rrid": check_rrid,
    "compound": check_compound,
    "pdb": check_pdb,
    "variant": check_variant,
    "blot_band": check_blot_band,
    "accession": check_accession,
    "ic50": check_ic50,
    "trial_registration": check_trial_registration,
    "outcome_switching": check_outcome_switching,
    "cited_retracted": check_cited_retracted,
}


def validate(items):
    """返回 {evidence_registry, signals, system_limitations}。"""
    led = Ledger()
    for item in items:
        fn = CHECKS.get(item.get("check"))
        if not fn:
            continue
        # 契约要求 manuscript_evidence_refs 至少一条 —— 外部事实必须与稿件事实
        # 成对才有意义。缺失时登记为限制，不产出不合契约的 signal。
        if not item.get("evidence_refs"):
            led.add_limit(
                f"条目 {item.get('check')} 未提供稿件 evidence_refs，"
                f"无法构成可复算的外部比较",
                item.get("target", "unknown"),
                ["M2", "M3", "M4", "M5", "M6", "M7"],
                {"kind": "missing_manuscript_evidence"})
            continue
        sig = fn(item, led, led.next_sig())
        if sig:
            led.signals.append(sig)
    return {"evidence_registry": led.evidence, "signals": led.signals,
            "system_limitations": led.limits}


# ---------------------------------------------------------------- 自检
def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    R = ["EV-001"]

    def one(item):
        return validate([dict(item, evidence_refs=R)])

    probe = one({"check": "variant", "uniprot": "P04637",
                 "position": 273, "ref_aa": "R"})
    if not probe["evidence_registry"] and probe["system_limitations"]:
        print("  SKIP  外部源不可达 —— 离线环境下降级为 system_limitation 是预期行为")
        print("\n全部通过（降级路径）")
        return 0

    expect("真实 p53 上 273 位合法", len(probe["signals"]), 0)
    ev = next(iter(probe["evidence_registry"].values()))
    expect("evidence 为 external 型", ev["type"], "external")
    expect("evidence 带响应 sha256", len(ev["response_sha256"]), 64)
    expect("resolved 必须有 assertions", len(ev["assertions"]) > 0, True)

    r = one({"check": "variant", "uniprot": "P04637", "position": 999})
    s = r["signals"][0]
    expect("位点越界 -> 报警", s["type"], "external_validation_candidate")
    expect("id 合契约 pattern", bool(re.match(r"^SIG-[0-9]{3,}$", s["id"])), True)
    expect("越界为确定性 mismatch",
           s["external_check"]["comparison_result"], "mismatch")
    expect("mismatch 时 comparability 必须 complete",
           s["external_check"]["comparability"], "complete")
    expect("signal 无 severity", "severity" not in s, True)
    expect("稿件证据被带入", s["external_check"]["manuscript_evidence_refs"], R)
    expect("外部证据可解析到登记表",
           s["external_check"]["external_evidence_refs"][0] in r["evidence_registry"],
           True)
    expect("参考残基不符 -> 报警",
           len(one({"check": "variant", "uniprot": "P04637",
                    "position": 273, "ref_aa": "A"})["signals"]), 1)

    # Cellosaurus —— 价值最高的一条
    r = one({"check": "cell_line", "cell_line": "MDA-MB-435"})
    expect("MDA-MB-435 被标为有问题", "M14" in r["signals"][0]["detail"], True)
    expect("污染细胞系为确定性 mismatch",
           r["signals"][0]["external_check"]["comparison_result"], "mismatch")
    expect("正常细胞系不报警",
           len(one({"check": "cell_line", "cell_line": "HEK293"})["signals"]), 0)

    # WB 条带
    expect("p53 标在 50 kDa 合理",
           len(one({"check": "blot_band", "uniprot": "P04637",
                    "reported_kda": 50})["signals"]), 0)
    r = one({"check": "blot_band", "uniprot": "P04637", "reported_kda": 120})
    expect("p53 标在 120 kDa -> 需人工复核",
           r["signals"][0]["external_check"]["comparison_result"],
           "needs_manual_review")

    # ClinicalTrials.gov
    r = one({"check": "outcome_switching", "nct": "NCT04368728",
             "reported_primary": "overall survival at 5 years"})
    expect("结局无重叠 -> 需人工复核",
           r["signals"][0]["external_check"]["comparison_result"],
           "needs_manual_review")
    expect("结局一致 -> 不报警",
           len(one({"check": "outcome_switching", "nct": "NCT04368728",
                    "reported_primary": "local reactions after dose 1"})["signals"]), 0)
    expect("同月注册不误报（start 只有 YYYY-MM 精度时无从判断）",
           registered_late("2011-02-24", "2011-02"), False)
    expect("确实晚一个月 -> 判为回顾性", registered_late("2011-02-24", "2011-01"), True)
    expect("注册早于开始 -> 前瞻性", registered_late("2020-04-27", "2020-04-29"), False)
    expect("前瞻性注册不报警",
           len(one({"check": "trial_registration", "nct": "NCT04368728"})["signals"]), 0)
    r = one({"check": "trial_registration", "nct": "NCT99999999"})
    expect("注册号不存在 -> 报警", len(r["signals"]), 1)
    nf = [e for e in r["evidence_registry"].values()
          if e["retrieval_status"] == "not_found"]
    expect("not_found 时 record_id 必须为 null",
           nf[0]["record_id"] if nf else "缺", None)
    expect("not_found 时 assertions 必须为空", len(nf[0]["assertions"]) if nf else -1, 0)

    # 撤稿文献
    expect("引用已撤稿文献 -> 报警",
           len(one({"check": "cited_retracted",
                    "doi": "10.1016/S0140-6736(20)31180-6"})["signals"]), 1)
    expect("未撤稿文献不报警",
           len(one({"check": "cited_retracted",
                    "doi": "10.1038/nature12373"})["signals"]), 0)

    # HGNC 基因符号
    # 只断言「不报警」不够：调用失败也不报警。必须同时断言外部证据被登记，
    # 证明这次查询真的成功了 —— 否则就是把「我们没查到」当成「论文没问题」
    r = one({"check": "gene_symbol", "symbol": "TP53"})
    expect("TP53 为现行符号，不报警",
           (len(r["signals"]), len(r["evidence_registry"])), (0, 1))
    r = one({"check": "gene_symbol", "symbol": "MARCH1"})
    expect("MARCH1 已改名 -> 报警并给出现行符号",
           r["signals"][0]["external_check"]["external_value"]["current_symbol"],
           "MARCHF1")
    r = one({"check": "gene_symbol", "symbol": "2-Sep"})
    expect("Excel 日期化基因名 -> 确定性报警",
           r["signals"][0]["external_check"]["check_type"],
           "gene_symbol_excel_corruption")
    r = one({"check": "gene_symbol", "symbol": "FAKE9999"})
    expect("无法识别的符号 -> 需人工复核",
           r["signals"][0]["external_check"]["comparison_result"],
           "needs_manual_review")
    expect("非人类物种不走 HGNC",
           len(one({"check": "gene_symbol", "symbol": "Trp53",
                    "species": "mouse"})["signals"]), 0)

    # Crossref 参考文献
    expect("真实 DOI 不报警",
           len(one({"check": "reference_exists",
                    "doi": "10.1038/nature12373"})["signals"]), 0)
    expect("不存在的 DOI -> 确定性报警",
           one({"check": "reference_exists",
                "doi": "10.1234/fake.doi.99999"})["signals"][0][
                    "external_check"]["comparison_result"], "mismatch")

    # NCBI Taxonomy
    expect("有效物种名不报警",
           len(one({"check": "species", "species": "Mus musculus"})["signals"]), 0)
    expect("无效物种名 -> 需人工复核",
           one({"check": "species", "species": "Mus fakius"})["signals"][0][
               "external_check"]["comparison_result"], "needs_manual_review")

    # RRID
    expect("有效 RRID 不报警",
           len(one({"check": "rrid", "rrid": "AB_2298772"})["signals"]), 0)
    expect("无效 RRID -> 确定性报警",
           len(one({"check": "rrid", "rrid": "AB_9999999"})["signals"]), 1)

    # PubChem
    expect("已知化合物且分子量相符 -> 不报警",
           len(one({"check": "compound", "compound": "imatinib",
                    "reported_mw": 493.6})["signals"]), 0)
    expect("分子量不符 -> 需人工复核",
           one({"check": "compound", "compound": "imatinib",
                "reported_mw": 250.0})["signals"][0][
                    "external_check"]["comparison_result"], "needs_manual_review")

    # PDB
    expect("真实 PDB 编号不报警",
           len(one({"check": "pdb", "pdb_id": "1TUP"})["signals"]), 0)
    expect("不存在的 PDB 编号 -> 确定性报警",
           one({"check": "pdb", "pdb_id": "9ZZZ"})["signals"][0][
               "external_check"]["comparison_result"], "mismatch")

    # 缺稿件证据时不得产出不合契约的 signal
    r = validate([{"check": "cell_line", "cell_line": "MDA-MB-435"}])
    expect("缺稿件 evidence_refs -> 记限制而非 signal",
           (len(r["signals"]), len(r["system_limitations"])), (0, 1))

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--input", help="待核验条目的 JSON 数组；给 - 表示从 stdin 读")
    ap.add_argument("--uniprot")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if a.input:
        try:
            raw = sys.stdin.read() if a.input == "-" else io.open(
                a.input, encoding="utf-8").read()
            items = json.loads(raw)
            if not isinstance(items, list):
                raise ValueError("顶层必须是数组")
        except Exception as exc:                                 # noqa: BLE001
            # 业务模式 stdout 只写 JSON；输入错误走 stderr + 退出码 2，不打 traceback
            print(f"error.code=invalid_input detail={str(exc)[:150]}", file=sys.stderr)
            return 2
        json.dump(validate(items), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    if a.uniprot:
        led = Ledger()
        p, _ = _uniprot(a.uniprot, led, "cli", ["M5"])
        json.dump(p or {"system_limitations": led.limits}, sys.stdout,
                  ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
