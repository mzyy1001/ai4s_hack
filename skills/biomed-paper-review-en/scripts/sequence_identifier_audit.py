#!/usr/bin/env python3
"""Deterministic sequence and identifier audit (phase-1 capability; stdlib only, offline).

This is the class of capability with **the largest uplift potential** in this
project: every error below can be judged deterministically by rules, while a
general-purpose LLM can neither check them reliably nor provide auditable
criteria.

Seven check classes
-------------------
1. `hgvs_syntax_invalid` / `hgvs_syntax_unresolved` — explicit syntax violation / beyond the subset this tool supports
2. `variant_position_out_of_range` — variant position exceeds the given sequence length
3. `variant_reference_mismatch` — HGVS reference amino acid disagrees with the actual residue in the sequence
4. `gene_symbol_species_mismatch` — gene-symbol casing convention disagrees with the stated species
5. `accession_format_invalid`  — accession does not match that database's format
6. `primer_qc_out_of_range`    — primer length/GC%/Tm outside conventional ranges
7. `sequence_alphabet_invalid` — sequence contains illegal characters

Design principle: report only "deterministic violations" and "candidates"
--------------------------------------------------------------------------
- **Range, reference residue, accession format, and alphabet** (2/3/5/7) are
  deterministic checks when the reference version is explicit.
- The local HGVS parser covers only common substitutions, del/dup/ins/delins
  and some protein expressions; expressions beyond that subset are tagged
  `hgvs_syntax_unresolved + candidate: true` — "the parser does not support
  it" must never be reported as a manuscript syntax error.
- **Convention checks** (4/6) emit **candidates only**: gene-symbol casing
  conventions have exceptions and primer parameters vary by assay system, so
  they always carry `candidate: true` and downstream modules refer them to
  human review — automation must **never** declare the manuscript wrong.
- Never guess on insufficient input: without a sequence, no position check is
  run; with a sequence but missing completeness, accession, or version, only
  `partial_extraction` is emitted — a fragment must not be treated as a
  complete reference sequence to declare an out-of-range position.

**This module emits `extraction_signal` only — never findings.**
Routed to M2 (statement consistency) and M3 (methods and reagents).

Command line:
    python3 <skill dir>/scripts/sequence_identifier_audit.py --input sequence_items.json
    python3 <skill dir>/scripts/sequence_identifier_audit.py --selftest
"""

import argparse
import json
import re
import sys

RULE_VERSION = "2026-08-07"


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)

# ---------------------------------------------------------------- amino acid tables
AA3_TO_1 = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
    "Gln": "Q", "Glu": "E", "Gly": "G", "His": "H", "Ile": "I",
    "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
    "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
    "Sec": "U", "Pyl": "O", "Ter": "*",
}
AA1 = set(AA3_TO_1.values())

DNA_ALPHABET = set("ACGTUNRYKMSWBDHV")          # includes IUPAC degenerate bases
PROTEIN_ALPHABET = set("ACDEFGHIKLMNPQRSTVWYUOXBZ*")

# ---------------------------------------------------------------- accession formats
ACCESSION_PATTERNS = {
    "refseq_rna":    (r"^N[MR]_\d{6,9}(\.\d+)?$", "RefSeq transcript"),
    "refseq_protein": (r"^N[PR]_\d{6,9}(\.\d+)?$", "RefSeq protein"),
    "refseq_predicted": (r"^X[MRP]_\d{6,9}(\.\d+)?$", "RefSeq predicted"),
    "ensembl_gene":  (r"^ENS[A-Z]{0,4}G\d{11}(\.\d+)?$", "Ensembl gene"),
    "ensembl_transcript": (r"^ENS[A-Z]{0,4}T\d{11}(\.\d+)?$", "Ensembl transcript"),
    "ensembl_protein": (r"^ENS[A-Z]{0,4}P\d{11}(\.\d+)?$", "Ensembl protein"),
    # Official UniProtKB regex
    "uniprot": (r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})(-\d+)?$",
                "UniProt accession"),
    "dbsnp":    (r"^rs\d+$", "dbSNP"),
    "pdb":      (r"^[0-9][A-Za-z0-9]{3}$", "PDB structure"),
    "geo_series": (r"^GSE\d+$", "GEO series"),
    "geo_sample": (r"^GSM\d+$", "GEO sample"),
    "sra_run":  (r"^[SED]RR\d+$", "SRA run"),
    "sra_study": (r"^[SED]RP\d+$", "SRA study"),
    "bioproject": (r"^PRJ[DEN][A-Z]\d+$", "BioProject"),
    "pride":    (r"^PXD\d{6,}$", "PRIDE proteomics"),
    "clinicaltrials": (r"^NCT\d{8}$", "ClinicalTrials.gov"),
    "chictr":   (r"^ChiCTR[0-9A-Za-z-]+$", "ChiCTR"),
    "hgnc":     (r"^HGNC:\d+$", "HGNC ID"),
    "rrid":     (r"^RRID:[A-Za-z]+_[A-Za-z0-9_.-]+$", "RRID"),
    "cellosaurus": (r"^CVCL_[A-Z0-9]{4}$", "Cellosaurus"),
}

# ---------------------------------------------------------------- species naming conventions
# Official nomenclature-committee casing conventions: ALL CAPS for human
# (HGNC), Title case for mouse/rat (MGI/RGD), all lowercase for zebrafish
# (ZFIN). These are **conventions**, not hard rules, so only candidates are
# reported.
SPECIES_CONVENTION = {
    "human":     ("upper", "HGNC: human gene symbols are all uppercase, e.g. TP53"),
    "mouse":     ("title", "MGI: mouse gene symbols are capitalized with the rest lowercase, e.g. Trp53"),
    "rat":       ("title", "RGD: rat gene symbols are capitalized with the rest lowercase, e.g. Tp53"),
    "zebrafish": ("lower", "ZFIN: zebrafish gene symbols are all lowercase, e.g. tp53"),
}
SPECIES_ALIASES = {
    "human": ["human", "homo sapiens", "patient", "人类", "人体"],
    "mouse": ["mouse", "mice", "mus musculus", "murine", "小鼠", "鼠"],
    "rat": ["rat", "rats", "rattus", "大鼠"],
    "zebrafish": ["zebrafish", "danio rerio", "斑马鱼"],
}


def detect_species(text):
    """Detect the species from free text; return None when undecidable (then the symbol-convention check is skipped)."""
    if not text:
        return None
    low = str(text).lower()
    hits = [sp for sp, al in SPECIES_ALIASES.items() if any(a in low for a in al)]
    return hits[0] if len(hits) == 1 else None


def _sig(sid, stype, target, detail, extra):
    extra = dict(extra)
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
    """Normalize a 3-letter or 1-letter residue to 1-letter; return None if unrecognized."""
    if tok in AA3_TO_1:
        return AA3_TO_1[tok]
    if tok in AA1:
        return tok
    if len(tok) == 3 and tok.capitalize() in AA3_TO_1:
        return AA3_TO_1[tok.capitalize()]
    return None


def _text(value):
    """Safely convert an optional scalar to stripped text; tolerate JSON numbers, reject containers."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        raise ValueError("sequence/identifier fields must be scalars, not objects or arrays")
    return str(value).strip()


def check_hgvs(item, sid="SIG-001"):
    """Combined HGVS check: syntax + position range + reference residue.

    item: {hgvs, sequence(optional), sequence_type(protein/dna), reference_id,
           reference_version, sequence_complete, target(optional)}
    """
    h = _text(item.get("hgvs"))
    target = item.get("target", "variant")
    if not h:
        return None

    if h.startswith("p."):
        m = HGVS_PROTEIN.match(h)
        if not m:
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"HGVS protein expression {h!r} is beyond the common subset supported "
                        f"by the local parser; this must not be judged a syntax error — use a "
                        f"full HGVS parser or human review.",
                        {"check": "hgvs_syntax_unresolved", "candidate": True, "hgvs": h})
        ref = _norm_aa(m.group("ref"))
        pos = int(m.group("pos"))
        alt_raw = m.group("alt")
        if pos < 1:
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"Protein residue positions in HGVS {h!r} must start at 1.",
                        {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})
        if ref is None:
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"Reference residue {m.group('ref')!r} in HGVS {h!r} is not a valid amino acid.",
                        {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})
        if alt_raw not in ("=", "del", "dup") and not alt_raw.startswith(("fs", "ext")):
            if _norm_aa(alt_raw) is None:
                return _sig(sid, "sequence_identifier_inconsistent", target,
                            f"Substituted residue {alt_raw!r} in HGVS {h!r} is not a valid amino acid.",
                            {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})

        seq = _text(item.get("sequence")).upper()
        if seq and item.get("sequence_type", "protein") == "protein":
            missing_context = [name for name in
                               ("reference_id", "reference_version", "sequence_complete")
                               if item.get(name) in (None, "")]
            if item.get("sequence_complete") is not True and "sequence_complete" not in missing_context:
                missing_context.append("sequence_complete=true")
            if missing_context:
                return _sig(
                    sid, "partial_extraction", target,
                    f"A sequence was provided, but the reference context needed to fix "
                    f"coordinates is missing: {', '.join(missing_context)}. A fragment or "
                    f"unversioned sequence must not be treated as a complete reference, so the "
                    f"out-of-range and reference-residue checks were not run.",
                    {"check": "reference_context_incomplete", "candidate": True,
                     "hgvs": h, "missing_context": missing_context,
                     "routed_to": ["M3"]})
            if pos > len(seq):
                return _sig(sid, "sequence_identifier_inconsistent", target,
                            f"Variant {h} position {pos} exceeds the given protein sequence "
                            f"length {len(seq)}. An out-of-range position is a deterministic error.",
                            {"check": "variant_position_out_of_range", "candidate": False,
                             "hgvs": h, "position": pos, "sequence_length": len(seq)})
            actual = seq[pos - 1]
            if actual != ref:
                return _sig(sid, "sequence_identifier_inconsistent", target,
                            f"Variant {h} claims the reference residue at position {pos} is {ref}, "
                            f"but the given sequence actually has {actual} there.",
                            {"check": "variant_reference_mismatch", "candidate": False,
                             "hgvs": h, "position": pos,
                             "claimed_ref": ref, "actual_ref": actual})
        return None

    if h.startswith("c."):
        if not HGVS_CODING.match(h):
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"HGVS coding expression {h!r} is beyond the common subset supported "
                        f"by the local parser; this must not be judged a syntax error — use a "
                        f"full HGVS parser or human review.",
                        {"check": "hgvs_syntax_unresolved", "candidate": True, "hgvs": h})
        return None

    if h.startswith("g."):
        if not HGVS_GENOMIC.match(h):
            return _sig(sid, "sequence_identifier_inconsistent", target,
                        f"HGVS genomic expression {h!r} is beyond the common subset supported "
                        f"by the local parser; this must not be judged a syntax error — use a "
                        f"full HGVS parser or human review.",
                        {"check": "hgvs_syntax_unresolved", "candidate": True, "hgvs": h})
        return None

    if re.match(r"^(n|m|r|o)\.", h):
        return _sig(sid, "sequence_identifier_inconsistent", target,
                    f"HGVS expression {h!r} uses a prefix not yet covered by the local parser; "
                    f"this must not be judged a syntax error — use a full HGVS parser or human review.",
                    {"check": "hgvs_syntax_unresolved", "candidate": True, "hgvs": h})

    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"Variant name {h!r} lacks an HGVS prefix (expected one of c. / g. / p. / n. / m.).",
                {"check": "hgvs_syntax_invalid", "candidate": False, "hgvs": h})


# ================================================================ 4 gene symbols
def check_gene_symbol(item, sid="SIG-002"):
    """Whether gene-symbol casing matches the stated species' convention. **Candidates only.**"""
    sym = _text(item.get("symbol"))
    species = item.get("species") or detect_species(item.get("context"))
    target = item.get("target", "gene_symbol")
    if not sym or not species or species not in SPECIES_CONVENTION:
        return None
    if not re.match(r"^[A-Za-z][A-Za-z0-9_.-]*$", sym):
        return None  # does not look like a gene symbol; leave to other checks

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
                f"Gene symbol {sym!r} is written contrary to the naming convention for the "
                f"stated species '{species}' ({note}). This may be a species mix-up, or the "
                f"authors may deliberately be citing an ortholog — **candidate, refer to "
                f"human review**.",
                {"check": "gene_symbol_species_mismatch", "candidate": True,
                 "symbol": sym, "species": species, "expected_convention": want,
                 "routed_to": ["M2", "M3"]})


# ================================================================ 5 accessions
def check_accession(item, sid="SIG-003"):
    """Whether an accession matches the declared database's format. **Deterministic.**"""
    acc = _text(item.get("accession"))
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
                f"Accession {acc!r} does not match the {label} format specification. "
                f"A format violation is a deterministic error (authenticity verification "
                f"needs external data sources and belongs to layer X1).",
                {"check": "accession_format_invalid", "candidate": False,
                 "accession": acc, "database": db})


# ================================================================ 6 primer QC
def _gc_fraction(seq):
    s = seq.upper()
    return (s.count("G") + s.count("C")) / len(s) if s else 0.0


def _tm_wallace(seq):
    """Wallace rule, for short primers (<14 nt)."""
    s = seq.upper()
    return 2 * (s.count("A") + s.count("T")) + 4 * (s.count("G") + s.count("C"))


def _tm_gc_formula(seq):
    """Basic GC formula, for 14-70 nt. Tm = 64.9 + 41*(GC-16.4)/N"""
    s = seq.upper()
    n = len(s)
    gc = s.count("G") + s.count("C")
    return 64.9 + 41.0 * (gc - 16.4) / n


def check_primer(item, sid="SIG-004"):
    """Basic primer QC. **Candidates only** — parameter ranges vary by system and application."""
    seq = _text(item.get("sequence")).upper()
    target = item.get("target", "primer")
    if not seq:
        return None

    bad = set(seq) - DNA_ALPHABET
    if bad:
        return _sig(sid, "sequence_identifier_inconsistent", target,
                    f"Primer sequence contains illegal base characters {sorted(bad)}.",
                    {"check": "sequence_alphabet_invalid", "candidate": False,
                     "invalid_chars": sorted(bad)})

    issues = []
    n = len(seq)
    if not (15 <= n <= 35):
        issues.append(f"length {n} nt outside the usual 15-35 nt")
    gc = _gc_fraction(seq) * 100
    if not (40.0 <= gc <= 60.0):
        issues.append(f"GC content {gc:.1f}% outside the usual 40-60%")
    tm = _tm_wallace(seq) if n < 14 else _tm_gc_formula(seq)
    if not (50.0 <= tm <= 68.0):
        issues.append(f"estimated Tm {tm:.1f}°C outside the usual 50-68°C")
    # Simple self-dimer check: does the 3' terminal 6 nt match the sequence's
    # own reverse complement
    comp = str.maketrans("ACGT", "TGCA")
    rc = seq.translate(comp)[::-1]
    if seq[-6:] in rc[:-6] if n > 12 else False:
        issues.append("3' terminal 6 nt matches the sequence's own reverse complement; possible self-dimer")

    if not issues:
        return None
    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"Primer {seq} deviates from conventional parameters: {'; '.join(issues)}. "
                f"Primer parameters vary by amplification system — **candidate, refer to "
                f"human review**.",
                {"check": "primer_qc_out_of_range", "candidate": True,
                 "sequence": seq, "length": n, "gc_percent": round(gc, 1),
                 "tm_estimate": round(tm, 1), "issues": issues,
                 "routed_to": ["M3"]})


# ================================================================ 7 sequence alphabet
def check_sequence_alphabet(item, sid="SIG-005"):
    seq = _text(item.get("sequence")).upper()
    kind = item.get("sequence_type", "dna")
    target = item.get("target", "sequence")
    if not seq:
        return None
    allowed = DNA_ALPHABET if kind == "dna" else PROTEIN_ALPHABET
    bad = set(seq) - allowed
    if not bad:
        return None
    return _sig(sid, "sequence_identifier_inconsistent", target,
                f"{kind} sequence contains illegal characters {sorted(bad)}.",
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
    """items: [{check: <name>, ...}] -> list of extraction_signals. Compliant items emit no signal."""
    if not isinstance(items, list):
        raise ValueError("sequence audit input must be a JSON array")
    out = []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"sequence audit item {i} must be a JSON object")
        fn = CHECKS.get(item.get("check"))
        if fn is None:
            raise ValueError(f"sequence audit item {i} has an unsupported check: {item.get('check')!r}")
        try:
            sig = fn(item, sid=f"SIG-{i:03d}")
        except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
            raise ValueError(f"sequence audit item {i} has invalid parameters: {exc}") from exc
        if sig is not None:
            out.append(sig)
    return out


# ================================================================ selftest
def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    P53 = "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP"

    # --- HGVS syntax ---
    expect("valid p.Arg273His -> no signal", check_hgvs({"hgvs": "p.Arg273His"}), None)
    expect("valid p.R273H -> no signal", check_hgvs({"hgvs": "p.R273H"}), None)
    expect("valid c.76A>T -> no signal", check_hgvs({"hgvs": "c.76A>T"}), None)
    s = check_hgvs({"hgvs": "p.Xyz273His"})
    expect("invalid residue -> flagged", s["sequence_audit"]["check"] if s else None,
           "hgvs_syntax_invalid")
    s = check_hgvs({"hgvs": "p.Arg0His"})
    expect("protein position 0 -> syntax violation",
           s["sequence_audit"]["check"] if s else None, "hgvs_syntax_invalid")
    s = check_hgvs({"hgvs": "R273H"})
    expect("missing HGVS prefix -> flagged", s["sequence_audit"]["check"] if s else None,
           "hgvs_syntax_invalid")
    s = check_hgvs({"hgvs": "p.Arg273HisfsTer5"})
    expect("valid HGVS beyond the subset -> human-review candidate",
           s["sequence_audit"]["check"] if s else None, "hgvs_syntax_unresolved")
    expect("beyond the subset must not be judged deterministic",
           s["sequence_audit"]["candidate"] if s else None, True)
    s = check_hgvs({"hgvs": "n.76A>T"})
    expect("valid prefix beyond the subset must not be flagged as missing prefix",
           s["sequence_audit"]["check"] if s else None, "hgvs_syntax_unresolved")

    # --- position out of range (deterministic) ---
    s = check_hgvs({"hgvs": "p.Arg273His", "sequence": P53, "sequence_type": "protein",
                    "reference_id": "TEST-P53", "reference_version": "1",
                    "sequence_complete": True})
    expect("position 273 beyond 60aa -> flagged", s["sequence_audit"]["check"] if s else None,
           "variant_position_out_of_range")
    expect("out of range is deterministic, not candidate", s["sequence_audit"]["candidate"] if s else None, False)

    # --- reference residue mismatch (deterministic) ---
    # P53[1] = 'E' (position 2). Claiming p.Ala2Val must be flagged.
    s = check_hgvs({"hgvs": "p.Ala2Val", "sequence": P53, "sequence_type": "protein",
                    "reference_id": "TEST-P53", "reference_version": "1",
                    "sequence_complete": True})
    expect("reference residue mismatch -> flagged", s["sequence_audit"]["check"] if s else None,
           "variant_reference_mismatch")
    # Correct case: position 2 really is E (Glu)
    s = check_hgvs({"hgvs": "p.Glu2Val", "sequence": P53, "sequence_type": "protein",
                    "reference_id": "TEST-P53", "reference_version": "1",
                    "sequence_complete": True})
    expect("reference residue matches -> no signal", s, None)
    s = check_hgvs({"hgvs": "p.Arg273His", "sequence": P53,
                    "sequence_type": "protein"})
    expect("unversioned fragment must not be judged deterministically out of range", s["type"] if s else None,
           "partial_extraction")
    expect("missing reference context carries an explicit criterion",
           s["sequence_audit"]["check"] if s else None,
           "reference_context_incomplete")

    # --- gene-symbol species convention (candidate) ---
    s = check_gene_symbol({"symbol": "TP53", "species": "mouse"})
    expect("mouse written as TP53 -> candidate flag",
           s["sequence_audit"]["check"] if s else None, "gene_symbol_species_mismatch")
    expect("symbol convention is a candidate", s["sequence_audit"]["candidate"] if s else None, True)
    expect("mouse Trp53 -> no signal",
           check_gene_symbol({"symbol": "Trp53", "species": "mouse"}), None)
    expect("human TP53 -> no signal",
           check_gene_symbol({"symbol": "TP53", "species": "human"}), None)
    expect("species undecidable -> no check",
           check_gene_symbol({"symbol": "TP53"}), None)
    s = check_gene_symbol({"symbol": "Tp53", "context": "C57BL/6 小鼠肝组织"})
    expect("species detected from context, symbol compliant -> no signal", s, None)

    # --- accession formats ---
    expect("valid UniProt P04637 -> no signal",
           check_accession({"accession": "P04637", "database": "uniprot"}), None)
    s = check_accession({"accession": "P0463", "database": "uniprot"})
    expect("truncated UniProt -> flagged", s["sequence_audit"]["check"] if s else None,
           "accession_format_invalid")
    expect("valid NM_000546.6 -> no signal",
           check_accession({"accession": "NM_000546.6", "database": "refseq_rna"}), None)
    expect("valid rs1042522 -> no signal",
           check_accession({"accession": "rs1042522", "database": "dbsnp"}), None)
    s = check_accession({"accession": "NCT123", "database": "clinicaltrials"})
    expect("NCT with wrong digit count -> flagged", s["sequence_audit"]["check"] if s else None,
           "accession_format_invalid")
    expect("valid GSE12345 -> no signal",
           check_accession({"accession": "GSE12345", "database": "geo_series"}), None)

    # --- primer QC ---
    good = "ACGTGCTAGCTAGCTAGGCA"          # 20nt, GC 55%
    expect("conventional primer -> no signal", check_primer({"sequence": good}), None)
    s = check_primer({"sequence": "ATATATATATATATATAT"})   # GC 0%
    expect("GC 0% -> candidate flag", s["sequence_audit"]["check"] if s else None,
           "primer_qc_out_of_range")
    expect("primer QC is a candidate", s["sequence_audit"]["candidate"] if s else None, True)
    s = check_primer({"sequence": "ACGTXYZ"})
    expect("illegal bases -> deterministic flag", s["sequence_audit"]["check"] if s else None,
           "sequence_alphabet_invalid")

    # --- contract ---
    sigs = audit([{"check": "hgvs", "hgvs": "R273H"},
                  {"check": "gene_symbol", "symbol": "TP53", "species": "mouse"}])
    expect("signals carry no severity", all("severity" not in x for x in sigs), True)
    expect("uniform type", {x["type"] for x in sigs}, {"sequence_identifier_inconsistent"})
    expect("all carry rule_version",
           all(x["sequence_audit"].get("rule_version") for x in sigs), True)
    expect("signal ids match the schema",
           all(re.match(r"^SIG-[0-9]{3,}$", x["id"]) for x in sigs), True)

    try:
        audit([None])
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    expect("non-object input raises a controlled error", invalid_rejected, True)

    print("\nAll passed" if ok else "\nFailures present")
    return 0 if ok else 1


def _read_json(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _main(argv=None):
    parser = _JsonArgumentParser(description="Deterministic sequence and identifier audit")
    parser.add_argument("--input", metavar="JSON", help="JSON file with the check array; - reads stdin")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.input:
        parser.error("--input JSON is required (or use --selftest)")
    try:
        items = _read_json(args.input)
        signals = audit(items)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "detail": str(exc)}},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"signals": signals}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
