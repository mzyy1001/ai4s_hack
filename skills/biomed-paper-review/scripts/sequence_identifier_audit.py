#!/usr/bin/env python3
"""序列与标识符确定性审计（一期能力，只用标准库，离线运行）。

这是本项目**最能拉开 uplift 的一类能力**：下列错误全部可由规则确定性判定，
而通用大模型既查不准、也给不出可审计的判据。

七类检查
--------
1. `hgvs_syntax_invalid`        —— HGVS 变异命名法语法违规
2. `variant_position_out_of_range` —— 变异位点超出所给序列长度
3. `variant_reference_mismatch` —— HGVS 参考氨基酸与序列实际残基不符
4. `gene_symbol_species_mismatch` —— 基因符号书写惯例与所述物种不符
5. `accession_format_invalid`  —— 登录号格式不符合该数据库规范
6. `primer_qc_out_of_range`    —— 引物长度/GC%/Tm 超出常规区间
7. `sequence_alphabet_invalid` —— 序列含非法字符

设计原则 · 只报「确定性违规」与「候选」
--------------------------------------
- **语法与范围类**（1/2/3/5/7）是**确定性**的：违反即为错误，无需领域判断。
- **惯例类**（4/6）只产出**候选**：基因符号大小写惯例有例外，引物参数因体系而异，
  一律标 `candidate: true`，由下游模块交人工，**不得**自动判定稿件有错。
- 输入不足时不猜：缺序列就不做位置检查，缺物种就不做符号惯例检查。

**本模块只产出 `extraction_signal`，不产出 finding。**
路由到 M2（表述一致性）与 M3（方法与试剂）。

命令行自检：
    python3 sequence_identifier_audit.py --selftest
"""

import re
import sys

RULE_VERSION = "2026-08-07"

# ---------------------------------------------------------------- 氨基酸表
AA3_TO_1 = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
    "Gln": "Q", "Glu": "E", "Gly": "G", "His": "H", "Ile": "I",
    "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
    "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
    "Sec": "U", "Pyl": "O", "Ter": "*",
}
AA1 = set(AA3_TO_1.values())

DNA_ALPHABET = set("ACGTUNRYKMSWBDHV")          # 含 IUPAC 简并碱基
PROTEIN_ALPHABET = set("ACDEFGHIKLMNPQRSTVWYUOXBZ*")

# ---------------------------------------------------------------- 登录号格式
ACCESSION_PATTERNS = {
    "refseq_rna":    (r"^N[MR]_\d{6,9}(\.\d+)?$", "RefSeq 转录本"),
    "refseq_protein": (r"^N[PR]_\d{6,9}(\.\d+)?$", "RefSeq 蛋白"),
    "refseq_predicted": (r"^X[MRP]_\d{6,9}(\.\d+)?$", "RefSeq 预测"),
    "ensembl_gene":  (r"^ENS[A-Z]{0,4}G\d{11}(\.\d+)?$", "Ensembl 基因"),
    "ensembl_transcript": (r"^ENS[A-Z]{0,4}T\d{11}(\.\d+)?$", "Ensembl 转录本"),
    "ensembl_protein": (r"^ENS[A-Z]{0,4}P\d{11}(\.\d+)?$", "Ensembl 蛋白"),
    # UniProtKB 官方正则
    "uniprot": (r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})(-\d+)?$",
                "UniProt 登录号"),
    "dbsnp":    (r"^rs\d+$", "dbSNP"),
    "pdb":      (r"^[0-9][A-Za-z0-9]{3}$", "PDB 结构"),
    "geo_series": (r"^GSE\d+$", "GEO 数据集"),
    "geo_sample": (r"^GSM\d+$", "GEO 样本"),
    "sra_run":  (r"^[SED]RR\d+$", "SRA run"),
    "sra_study": (r"^[SED]RP\d+$", "SRA study"),
    "bioproject": (r"^PRJ[DEN][A-Z]\d+$", "BioProject"),
    "pride":    (r"^PXD\d{6,}$", "PRIDE 蛋白组"),
    "clinicaltrials": (r"^NCT\d{8}$", "ClinicalTrials.gov"),
    "chictr":   (r"^ChiCTR[0-9A-Za-z-]+$", "ChiCTR"),
    "hgnc":     (r"^HGNC:\d+$", "HGNC ID"),
    "rrid":     (r"^RRID:[A-Za-z]+_[A-Za-z0-9_.-]+$", "RRID"),
    "cellosaurus": (r"^CVCL_[A-Z0-9]{4}$", "Cellosaurus"),
}

# ---------------------------------------------------------------- 物种命名惯例
# 官方命名委员会的书写惯例。ALL CAPS 是人类（HGNC），首字母大写是小鼠/大鼠
# （MGI/RGD），全小写是斑马鱼（ZFIN）。这是**惯例**不是硬规则，因此只报候选。
SPECIES_CONVENTION = {
    "human":     ("upper", "HGNC：人类基因符号全大写，如 TP53"),
    "mouse":     ("title", "MGI：小鼠基因符号首字母大写、其余小写，如 Trp53"),
    "rat":       ("title", "RGD：大鼠基因符号首字母大写、其余小写，如 Tp53"),
    "zebrafish": ("lower", "ZFIN：斑马鱼基因符号全小写，如 tp53"),
}
SPECIES_ALIASES = {
    "human": ["human", "homo sapiens", "patient", "人类", "人体"],
    "mouse": ["mouse", "mice", "mus musculus", "murine", "小鼠", "鼠"],
    "rat": ["rat", "rats", "rattus", "大鼠"],
    "zebrafish": ["zebrafish", "danio rerio", "斑马鱼"],
}


def detect_species(text):
    """从自由文本判定物种；判不出返回 None（则不做符号惯例检查）。"""
    if not text:
        return None
    low = str(text).lower()
    hits = [sp for sp, al in SPECIES_ALIASES.items() if any(a in low for a in al)]
    return hits[0] if len(hits) == 1 else None


def _sig(sid, stype, target, detail, extra):
    return {
        "id": sid,
        "type": stype,
        "target": target,
        "detail": detail,
        "observation_refs": [],
        "evidence_refs": [],
        "routed_to": extra.pop("routed_to", ["M2", "M3"]),
        "produced_by": "stage_2",
        "sequence_audit": dict(extra, rule_version=RULE_VERSION),
    }


# ================================================================ 1-3 HGVS
HGVS_PROTEIN = re.compile(
    r"^p\.\(?"
    r"(?P<ref>[A-Z][a-z]{2}|[A-Z*])"
    r"(?P<pos>\d+)"
    r"(?P<alt>[A-Z][a-z]{2}|[A-Z*]|=|del|dup|fs(\*\d+)?|ext\*?\d*)"
    r"\)?$"
)
HGVS_CODING = re.compile(
    r"^c\.(?P<pos>[\d+\-*_]+)"
    r"(?P<change>[ACGT]>[ACGT]|del[ACGT]*|dup[ACGT]*|ins[ACGT]+|delins[ACGT]+|=)$"
)
HGVS_GENOMIC = re.compile(
    r"^g\.(?P<pos>[\d_]+)"
    r"(?P<change>[ACGT]>[ACGT]|del[ACGT]*|dup[ACGT]*|ins[ACGT]+|delins[ACGT]+|=)$"
)


def _norm_aa(tok):
    """把 3 字母或 1 字母残基统一为 1 字母；不认识返回 None。"""
    if tok in AA3_TO_1:
        return AA3_TO_1[tok]
    if tok in AA1:
        return tok
    if len(tok) == 3 and tok.capitalize() in AA3_TO_1:
        return AA3_TO_1[tok.capitalize()]
    return None


def check_hgvs(item, sid="SIG-S01"):
    """HGVS 语法 + 位置范围 + 参考残基三合一检查。

    item: {hgvs, sequence(可选), sequence_type(protein/dna), target(可选)}
    """
    h = (item.get("hgvs") or "").strip()
    target = item.get("target", "variant")
    if not h:
        return None

    if h.startswith("p."):
        m = HGVS_PROTEIN.match(h)
        if not m:
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"HGVS 蛋白命名 {h!r} 不符合语法（期望形如 p.Arg273His 或 p.R273H）。",
                        {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})
        ref = _norm_aa(m.group("ref"))
        pos = int(m.group("pos"))
        alt_raw = m.group("alt")
        if ref is None:
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"HGVS {h!r} 的参考残基 {m.group('ref')!r} 不是合法氨基酸。",
                        {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})
        if alt_raw not in ("=", "del", "dup") and not alt_raw.startswith(("fs", "ext")):
            if _norm_aa(alt_raw) is None:
                return _sig(sid, "sequence_identifier_inconsistent", target,
                            f"HGVS {h!r} 的替换残基 {alt_raw!r} 不是合法氨基酸。",
                            {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})

        seq = (item.get("sequence") or "").strip().upper()
        if seq and item.get("sequence_type", "protein") == "protein":
            if pos > len(seq):
                return _sig(sid, "sequence_identifier_inconsistent", target,
                            f"变异位点 {h} 的位置 {pos} 超出所给蛋白序列长度 {len(seq)}。"
                            f"位置越界是确定性错误。",
                            {"check": "variant_position_out_of_range", "candidate": False,
                             "hgvs": h, "position": pos, "sequence_length": len(seq)})
            actual = seq[pos - 1]
            if actual != ref:
                return _sig(sid, "sequence_identifier_inconsistent", target,
                            f"变异 {h} 声称第 {pos} 位参考残基为 {ref}，"
                            f"但所给序列该位实际为 {actual}。",
                            {"check": "variant_reference_mismatch", "candidate": False,
                             "hgvs": h, "position": pos,
                             "claimed_ref": ref, "actual_ref": actual})
        return None

    if h.startswith("c."):
        if not HGVS_CODING.match(h):
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"HGVS 编码区命名 {h!r} 不符合语法（期望形如 c.76A>T / c.76_78del）。",
                        {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})
        return None

    if h.startswith("g."):
        if not HGVS_GENOMIC.match(h):
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"HGVS 基因组命名 {h!r} 不符合语法。",
                        {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})
        return None

    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"变异命名 {h!r} 缺少 HGVS 前缀（应为 c. / g. / p. / n. / m. 之一）。",
                {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})


# ================================================================ 4 基因符号
def check_gene_symbol(item, sid="SIG-S02"):
    """基因符号书写惯例与所述物种是否相符。**只报候选。**"""
    sym = (item.get("symbol") or "").strip()
    species = item.get("species") or detect_species(item.get("context"))
    target = item.get("target", "gene_symbol")
    if not sym or not species or species not in SPECIES_CONVENTION:
        return None
    if not re.match(r"^[A-Za-z][A-Za-z0-9_.-]*$", sym):
        return None  # 不像基因符号，交给别的检查

    want, note = SPECIES_CONVENTION[species]
    letters = [c for c in sym if c.isalpha()]
    if not letters:
        return None

    if want == "upper":
        ok = all(c.isupper() for c in letters)
    elif want == "lower":
        ok = all(c.islower() for c in letters)
    else:  # title
        ok = letters[0].isupper() and all(c.islower() for c in letters[1:])

    if ok:
        return None
    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"基因符号 {sym!r} 的书写与所述物种「{species}」的命名惯例不符（{note}）。"
                f"这可能是物种张冠李戴，也可能是作者有意引用直系同源基因 —— "
                f"**候选，交人工确认**。",
                {"check": "gene_symbol_species_mismatch", "candidate": True,
                 "symbol": sym, "species": species, "expected_convention": want,
                 "routed_to": ["M2", "M3"]})


# ================================================================ 5 登录号
def check_accession(item, sid="SIG-S03"):
    """登录号格式是否符合所声明数据库的规范。**确定性。**"""
    acc = (item.get("accession") or "").strip()
    db = item.get("database")
    target = item.get("target", "accession")
    if not acc or not db:
        return None
    if db not in ACCESSION_PATTERNS:
        return None
    pattern, label = ACCESSION_PATTERNS[db]
    if re.match(pattern, acc):
        return None
    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"登录号 {acc!r} 不符合 {label} 的格式规范。"
                f"格式违规是确定性错误（真伪核验需外部数据源，属 X1 层）。",
                {"check": "accession_format_invalid", "candidate": False,
                 "accession": acc, "database": db})


# ================================================================ 6 引物 QC
def _gc_fraction(seq):
    s = seq.upper()
    return (s.count("G") + s.count("C")) / len(s) if s else 0.0


def _tm_wallace(seq):
    """Wallace 规则，适用于短引物（<14 nt）。"""
    s = seq.upper()
    return 2 * (s.count("A") + s.count("T")) + 4 * (s.count("G") + s.count("C"))


def _tm_gc_formula(seq):
    """基础 GC 公式，适用于 14-70 nt。Tm = 64.9 + 41*(GC-16.4)/N"""
    s = seq.upper()
    n = len(s)
    gc = s.count("G") + s.count("C")
    return 64.9 + 41.0 * (gc - 16.4) / n


def check_primer(item, sid="SIG-S04"):
    """引物基本 QC。**只报候选** —— 参数区间因体系与应用而异。"""
    seq = (item.get("sequence") or "").strip().upper()
    target = item.get("target", "primer")
    if not seq:
        return None

    bad = set(seq) - DNA_ALPHABET
    if bad:
        return _sig(sid, "sequence_identifier_inconsistent", target,
                    f"引物序列含非法碱基字符 {sorted(bad)}。",
                    {"check": "sequence_alphabet_invalid", "candidate": False,
                     "invalid_chars": sorted(bad)})

    issues = []
    n = len(seq)
    if not (15 <= n <= 35):
        issues.append(f"长度 {n} nt 超出常规 15–35 nt")
    gc = _gc_fraction(seq) * 100
    if not (40.0 <= gc <= 60.0):
        issues.append(f"GC 含量 {gc:.1f}% 超出常规 40–60%")
    tm = _tm_wallace(seq) if n < 14 else _tm_gc_formula(seq)
    if not (50.0 <= tm <= 68.0):
        issues.append(f"估算 Tm {tm:.1f}°C 超出常规 50–68°C")
    # 简单自二聚：3' 末端 6 nt 与自身反向互补序列是否匹配
    comp = str.maketrans("ACGT", "TGCA")
    rc = seq.translate(comp)[::-1]
    if seq[-6:] in rc[:-6] if n > 12 else False:
        issues.append("3' 末端 6 nt 与自身反向互补序列匹配，可能形成自二聚")

    if not issues:
        return None
    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"引物 {seq} 的常规参数存在偏离：{'；'.join(issues)}。"
                f"引物参数因扩增体系而异，**候选，交人工确认**。",
                {"check": "primer_qc_out_of_range", "candidate": True,
                 "sequence": seq, "length": n, "gc_percent": round(gc, 1),
                 "tm_estimate": round(tm, 1), "issues": issues,
                 "routed_to": ["M3"]})


# ================================================================ 7 序列字母表
def check_sequence_alphabet(item, sid="SIG-S05"):
    seq = (item.get("sequence") or "").strip().upper()
    kind = item.get("sequence_type", "dna")
    target = item.get("target", "sequence")
    if not seq:
        return None
    allowed = DNA_ALPHABET if kind == "dna" else PROTEIN_ALPHABET
    bad = set(seq) - allowed
    if not bad:
        return None
    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"{kind} 序列含非法字符 {sorted(bad)}。",
                {"check": "sequence_alphabet_invalid", "candidate": False,
                 "invalid_chars": sorted(bad)})


CHECKS = {
    "hgvs": check_hgvs,
    "gene_symbol": check_gene_symbol,
    "accession": check_accession,
    "primer": check_primer,
    "sequence_alphabet": check_sequence_alphabet,
}


def audit(items):
    """items: [{check: <名>, ...}] -> extraction_signal 列表。合规项不产出信号。"""
    out = []
    for i, item in enumerate(items, 1):
        fn = CHECKS.get(item.get("check"))
        if fn is None:
            continue
        sig = fn(item, sid=f"SIG-S{i:02d}")
        if sig is not None:
            out.append(sig)
    return out


# ================================================================ 自检
def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    P53 = "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP"

    # --- HGVS 语法 ---
    expect("合法 p.Arg273His 无信号", check_hgvs({"hgvs": "p.Arg273His"}), None)
    expect("合法 p.R273H 无信号", check_hgvs({"hgvs": "p.R273H"}), None)
    expect("合法 c.76A>T 无信号", check_hgvs({"hgvs": "c.76A>T"}), None)
    s = check_hgvs({"hgvs": "p.Xyz273His"})
    expect("非法残基 -> 报警", s["sequence_audit"]["check"] if s else None,
           "hgvs_syntax_invalid")
    s = check_hgvs({"hgvs": "R273H"})
    expect("缺 HGVS 前缀 -> 报警", s["sequence_audit"]["check"] if s else None,
           "hgvs_syntax_invalid")

    # --- 位置越界（确定性）---
    s = check_hgvs({"hgvs": "p.Arg273His", "sequence": P53, "sequence_type": "protein"})
    expect("位置 273 超出 60aa -> 报警", s["sequence_audit"]["check"] if s else None,
           "variant_position_out_of_range")
    expect("越界属确定性非候选", s["sequence_audit"]["candidate"] if s else None, False)

    # --- 参考残基不符（确定性）---
    # P53[1] = 'E'（第 2 位）。声称 p.Ala2Val 应报错。
    s = check_hgvs({"hgvs": "p.Ala2Val", "sequence": P53, "sequence_type": "protein"})
    expect("参考残基不符 -> 报警", s["sequence_audit"]["check"] if s else None,
           "variant_reference_mismatch")
    # 正确的：第 2 位确实是 E (Glu)
    s = check_hgvs({"hgvs": "p.Glu2Val", "sequence": P53, "sequence_type": "protein"})
    expect("参考残基相符 -> 无信号", s, None)

    # --- 基因符号物种惯例（候选）---
    s = check_gene_symbol({"symbol": "TP53", "species": "mouse"})
    expect("小鼠写成 TP53 -> 候选报警",
           s["sequence_audit"]["check"] if s else None, "gene_symbol_species_mismatch")
    expect("符号惯例属候选", s["sequence_audit"]["candidate"] if s else None, True)
    expect("小鼠 Trp53 -> 无信号",
           check_gene_symbol({"symbol": "Trp53", "species": "mouse"}), None)
    expect("人类 TP53 -> 无信号",
           check_gene_symbol({"symbol": "TP53", "species": "human"}), None)
    expect("物种判不出 -> 不检查",
           check_gene_symbol({"symbol": "TP53"}), None)
    s = check_gene_symbol({"symbol": "Tp53", "context": "C57BL/6 小鼠肝组织"})
    expect("从上下文识别小鼠且符号合规 -> 无信号", s, None)

    # --- 登录号格式 ---
    expect("合法 UniProt P04637 -> 无信号",
           check_accession({"accession": "P04637", "database": "uniprot"}), None)
    s = check_accession({"accession": "P0463", "database": "uniprot"})
    expect("残缺 UniProt -> 报警", s["sequence_audit"]["check"] if s else None,
           "accession_format_invalid")
    expect("合法 NM_000546.6 -> 无信号",
           check_accession({"accession": "NM_000546.6", "database": "refseq_rna"}), None)
    expect("合法 rs1042522 -> 无信号",
           check_accession({"accession": "rs1042522", "database": "dbsnp"}), None)
    s = check_accession({"accession": "NCT123", "database": "clinicaltrials"})
    expect("NCT 位数不对 -> 报警", s["sequence_audit"]["check"] if s else None,
           "accession_format_invalid")
    expect("合法 GSE12345 -> 无信号",
           check_accession({"accession": "GSE12345", "database": "geo_series"}), None)

    # --- 引物 QC ---
    good = "ACGTGCTAGCTAGCTAGGCA"          # 20nt, GC 55%
    expect("常规引物 -> 无信号", check_primer({"sequence": good}), None)
    s = check_primer({"sequence": "ATATATATATATATATAT"})   # GC 0%
    expect("GC 0% -> 候选报警", s["sequence_audit"]["check"] if s else None,
           "primer_qc_out_of_range")
    expect("引物 QC 属候选", s["sequence_audit"]["candidate"] if s else None, True)
    s = check_primer({"sequence": "ACGTXYZ"})
    expect("非法碱基 -> 确定性报警", s["sequence_audit"]["check"] if s else None,
           "sequence_alphabet_invalid")

    # --- 契约 ---
    sigs = audit([{"check": "hgvs", "hgvs": "R273H"},
                  {"check": "gene_symbol", "symbol": "TP53", "species": "mouse"}])
    expect("信号无 severity", all("severity" not in x for x in sigs), True)
    expect("type 统一", {x["type"] for x in sigs}, {"sequence_identifier_inconsistent"})
    expect("均有 rule_version",
           all(x["sequence_audit"].get("rule_version") for x in sigs), True)

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(__doc__)
