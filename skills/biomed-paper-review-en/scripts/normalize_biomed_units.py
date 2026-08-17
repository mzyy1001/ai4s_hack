#!/usr/bin/env python3
"""Biomedical unit normalizer (phase-1 capability; stdlib only).

Implements step 1 "unit normalization" of `references/00-contracts.md §5.4` —
that step previously only said "cannot normalize -> ambiguous" with no
executable normalization, so the comparability verdict could never land.
This module fills that gap.

Design principle: fail closed
-----------------------------
**Better to return "cannot normalize" than to perform an uncertain
conversion.** A normalization error either manufactures a fake conflict
(judging mg/mL vs g/L contradictory) or masks a real one (merging mg/kg with
mg/kg/day). Therefore:

- only deterministic conversions **within one dimension** are performed;
- mass concentration <-> molar concentration **requires** both the analyte
  and an explicit molecular weight, otherwise
  `conversion_requires_molecular_weight` is returned — **an approximate
  molecular weight is never substituted**;
- body-weight/body-surface normalized doses (mg/kg, mg/m2) and absolute
  amounts (mg) have **different dimensions** and are never merged;
- time-bearing rates (mg/kg/day) and time-free doses (mg/kg) have
  **different dimensions** and are never merged;
- unknown aliases always yield `unknown_unit`, and the caller judges
  `ambiguous`.

Usage
-----
    from normalize_biomed_units import normalize, compare_units

    normalize("µM")
    # {'status': 'ok', 'ucum_code': 'uM', 'dimension': 'substance_concentration',
    #  'factor_to_base': 1e-06, 'base_unit': 'mol/L', 'rule_id': 'conc.molar', ...}

    compare_units("mg/mL", "g/L")   # -> ('comparable', 1.0)
    compare_units("mg/kg", "mg/kg/day")  # -> ('incomparable_dimension', None)

Command line:
    python3 <skill dir>/scripts/normalize_biomed_units.py --normalize 'µM'
    python3 <skill dir>/scripts/normalize_biomed_units.py --compare 'mg/mL' 'g/L'
    python3 <skill dir>/scripts/normalize_biomed_units.py --selftest
"""

import argparse
import json
import math
import re
import sys
import unicodedata

RULE_VERSION = "2026-08-07"


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)

# ---------------------------------------------------------------- dimension definitions
# One base unit per dimension; conversion is allowed only within a dimension.

DIMENSIONS = {
    "substance_concentration": "mol/L",
    "mass_concentration": "g/L",
    "mass": "g",
    "mass_per_body_weight": "g/kg",
    "mass_per_body_surface": "g/m2",
    "mass_per_body_weight_per_time": "g/kg/s",
    "time": "s",
    "length": "m",
    "volume": "L",
    "count": "1",
    "count_concentration": "1/L",
    "dimensionless": "1",
    "temperature_celsius": "Cel",
    "catalytic_activity": "U",
    "pressure": "Pa",
}

# ---------------------------------------------------------------- prefixes
SI_PREFIX = {
    "Y": 1e24, "Z": 1e21, "E": 1e18, "P": 1e15, "T": 1e12, "G": 1e9, "M": 1e6,
    "k": 1e3, "h": 1e2, "da": 1e1, "": 1.0,
    "d": 1e-1, "c": 1e-2, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12,
    "f": 1e-15, "a": 1e-18, "z": 1e-21, "y": 1e-24,
}

# ---------------------------------------------------------------- alias normalization
# Keys must already be in post-§1 text-normalized form (micro sign,
# superscripts, whitespace).
ALIAS = {
    # molar concentration
    "M": ("substance_concentration", 1.0, "conc.molar"),
    "mol/L": ("substance_concentration", 1.0, "conc.molar"),
    "mol/l": ("substance_concentration", 1.0, "conc.molar"),
    "molar": ("substance_concentration", 1.0, "conc.molar"),
    "mol/dm3": ("substance_concentration", 1.0, "conc.molar"),
    # mass concentration
    "g/L": ("mass_concentration", 1.0, "conc.mass"),
    "g/l": ("mass_concentration", 1.0, "conc.mass"),
    "g/dL": ("mass_concentration", 10.0, "conc.mass"),
    "g/mL": ("mass_concentration", 1000.0, "conc.mass"),
    "%(w/v)": ("mass_concentration", 10.0, "conc.mass.percent_wv"),
    # mass
    "g": ("mass", 1.0, "mass.base"),
    "Da": ("mass", 1.0, "mass.dalton"),
    # dose
    "g/kg": ("mass_per_body_weight", 1.0, "dose.per_bw"),
    "g/m2": ("mass_per_body_surface", 1.0, "dose.per_bsa"),
    # time
    "s": ("time", 1.0, "time.base"),
    "sec": ("time", 1.0, "time.base"),
    "min": ("time", 60.0, "time.base"),
    "h": ("time", 3600.0, "time.base"),
    "hr": ("time", 3600.0, "time.base"),
    "d": ("time", 86400.0, "time.base"),
    "day": ("time", 86400.0, "time.base"),
    "wk": ("time", 604800.0, "time.base"),
    "week": ("time", 604800.0, "time.base"),
    # length
    "m": ("length", 1.0, "length.base"),
    # volume
    "L": ("volume", 1.0, "volume.base"),
    "l": ("volume", 1.0, "volume.base"),
    # counts
    "cells": ("count", 1.0, "count.base"),
    "copies": ("count", 1.0, "count.base"),
    "cells/L": ("count_concentration", 1.0, "count.conc"),
    "cells/mL": ("count_concentration", 1000.0, "count.conc"),
    # dimensionless
    "1": ("dimensionless", 1.0, "dimensionless.base"),
    "%": ("dimensionless", 0.01, "dimensionless.percent"),
    "ratio": ("dimensionless", 1.0, "dimensionless.base"),
    "fold": ("dimensionless", 1.0, "dimensionless.base"),
    "AU": ("dimensionless", 1.0, "dimensionless.arbitrary"),
    # others
    "Cel": ("temperature_celsius", 1.0, "temp.celsius"),
    "U": ("catalytic_activity", 1.0, "activity.unit"),
    "Pa": ("pressure", 1.0, "pressure.base"),
    "mmHg": ("pressure", 133.322, "pressure.mmhg"),
}

# Base symbols that accept SI prefixes (prefix + symbol is looked up in ALIAS)
PREFIXABLE = {"M", "mol/L", "g/L", "g", "L", "m", "s", "U", "Da", "g/kg", "g/m2",
              "cells/L", "Pa"}


def _normalize_text(raw):
    """§1 text normalization: Unicode micro signs, superscripts, full-width forms, whitespace, per, exponents."""
    if raw is None:
        return ""
    s = unicodedata.normalize("NFKC", str(raw)).strip()
    # Unify the various "micro" signs to ASCII u
    s = s.replace("µ", "u").replace("μ", "u").replace("μ", "u")
    # Superscript digits
    for sup, plain in {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                       "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
                       "⁻": "-"}.items():
        s = s.replace(sup, plain)
    # Unify non-ASCII minus signs to the ASCII hyphen (U+2212 minus, hyphen, en dash)
    s = s.replace("−", "-").replace("‐", "-").replace("–", "-")
    # Middle-dot multiplication signs
    s = s.replace("·", ".").replace("×", "*").replace("⁄", "/")
    # per -> /
    s = re.sub(r"\s+per\s+", "/", s, flags=re.IGNORECASE)
    # Negative-exponent notation mg.kg-1 -> mg/kg
    s = re.sub(r"\.?([A-Za-z]+)\s*-1\b", r"/\1", s)
    # Strip whitespace
    s = re.sub(r"\s+", "", s)
    return s


def _split_prefix(token):
    """Split a token into (prefix_factor, base_symbol); return None when not found."""
    if token in ALIAS:
        return 1.0, token
    for plen in (2, 1):
        if len(token) > plen:
            pre, rest = token[:plen], token[plen:]
            if pre in SI_PREFIX and rest in PREFIXABLE and rest in ALIAS:
                return SI_PREFIX[pre], rest
    return None


def normalize(raw_unit):
    """Normalize a manuscript's original unit notation to a UCUM-style code + dimension + factor to the base unit.

    Returns a dict whose `status` is one of:
        ok                                normalization succeeded
        unknown_unit                      unrecognized; caller should judge ambiguous
        conversion_requires_molecular_weight   recognized, but cross-dimension conversion needs a molecular weight
        dimensionless_input               input was empty / null
    """
    out = {
        "input": raw_unit,
        "rule_version": RULE_VERSION,
        "status": "unknown_unit",
        "ucum_code": None,
        "dimension": None,
        "base_unit": None,
        "factor_to_base": None,
        "rule_id": None,
        "note": None,
    }

    if raw_unit is None or str(raw_unit).strip() == "":
        out.update(status="dimensionless_input", ucum_code=None,
                   dimension="dimensionless", base_unit="1", factor_to_base=1.0,
                   rule_id="dimensionless.null",
                   note="dimensionless metric; the caller must not judge the report incomplete for lacking a unit")
        return out

    s = _normalize_text(raw_unit)

    # Rates: X/time — must be kept distinct from the same unit without time
    rate = re.match(r"^(.+?)/(s|sec|min|h|hr|d|day|wk|week)$", s)
    if rate:
        head, tspec = rate.group(1), rate.group(2)
        head_res = normalize(head)
        t_res = normalize(tspec)
        if head_res["status"] == "ok" and t_res["status"] == "ok":
            if head_res["dimension"] == "mass_per_body_weight":
                out.update(
                    status="ok",
                    ucum_code=f"{head_res['ucum_code']}/{t_res['ucum_code']}",
                    dimension="mass_per_body_weight_per_time",
                    base_unit=DIMENSIONS["mass_per_body_weight_per_time"],
                    factor_to_base=head_res["factor_to_base"] / t_res["factor_to_base"],
                    rule_id="dose.per_bw_per_time",
                    note="rate dimension; not comparable with a time-free dose",
                )
                return out
            out.update(status="unknown_unit",
                       note=f"unregistered rate dimension: {head_res['dimension']}/time")
            return out

    hit = _split_prefix(s)
    if hit is None:
        # Common compound concentration notations mg/mL, ug/L ...
        m = re.match(r"^([A-Za-z]+)/([A-Za-z]+)$", s)
        if m:
            num, den = m.group(1), m.group(2)
            num_hit = _split_prefix(num)
            den_hit = _split_prefix(den)
            if num_hit and den_hit:
                nf, nb = num_hit
                df, db = den_hit
                ndim = ALIAS[nb][0]
                ddim = ALIAS[db][0]
                if ndim == "mass" and ddim == "volume":
                    factor = (nf * ALIAS[nb][1]) / (df * ALIAS[db][1])
                    out.update(status="ok", ucum_code=f"{num}/{den}",
                               dimension="mass_concentration",
                               base_unit=DIMENSIONS["mass_concentration"],
                               factor_to_base=factor, rule_id="conc.mass.compound")
                    return out
                if ndim == "substance_concentration" and ddim == "volume":
                    pass  # falls through to unknown below
                if ndim == "mass" and ddim == "mass":
                    factor = (nf * ALIAS[nb][1]) / (df * ALIAS[db][1])
                    out.update(status="ok", ucum_code=f"{num}/{den}",
                               dimension="mass_per_body_weight",
                               base_unit=DIMENSIONS["mass_per_body_weight"],
                               factor_to_base=factor, rule_id="dose.per_bw.compound")
                    return out
                if ndim == "count" and ddim == "volume":
                    factor = (nf * ALIAS[nb][1]) / (df * ALIAS[db][1])
                    out.update(status="ok", ucum_code=f"{num}/{den}",
                               dimension="count_concentration",
                               base_unit=DIMENSIONS["count_concentration"],
                               factor_to_base=factor, rule_id="count.conc.compound")
                    return out
        out["note"] = f"unregistered unit notation: {s} (after normalization)"
        return out

    pfactor, base = hit
    dim, bfactor, rule_id = ALIAS[base]
    out.update(status="ok", ucum_code=s, dimension=dim,
               base_unit=DIMENSIONS[dim],
               factor_to_base=pfactor * bfactor, rule_id=rule_id)
    return out


# Mass concentration <-> molar concentration: needs a molecular weight; phase 1
# never looks one up automatically
CONVERTIBLE_WITH_MW = {
    frozenset({"mass_concentration", "substance_concentration"}),
}


def compare_units(unit_a, unit_b, molecular_weight=None, analyte=None):
    """Decide whether two units are comparable.

    Returns (verdict, factor_a_to_b):
        ('comparable', f)                     b_value = a_value * f
        ('incomparable_dimension', None)      different dimensions — different things, not a conflict
        ('conversion_requires_molecular_weight', None)
        ('unknown_unit', None)                at least one side unrecognized -> caller judges ambiguous
    """
    ra, rb = normalize(unit_a), normalize(unit_b)

    if ra["status"] == "unknown_unit" or rb["status"] == "unknown_unit":
        return "unknown_unit", None

    da, db = ra["dimension"], rb["dimension"]

    if da == db:
        return "comparable", ra["factor_to_base"] / rb["factor_to_base"]

    if frozenset({da, db}) in CONVERTIBLE_WITH_MW:
        try:
            mw = float(molecular_weight)
        except (TypeError, ValueError, OverflowError):
            mw = None
        if (mw is None or not math.isfinite(mw) or mw <= 0
                or analyte is None or not str(analyte).strip()):
            return "conversion_requires_molecular_weight", None
        # g/L -> mol/L requires dividing by MW (g/mol)
        a_base = ra["factor_to_base"]
        b_base = rb["factor_to_base"]
        if da == "mass_concentration":
            return "comparable", (a_base / mw) / b_base
        return "comparable", (a_base * mw) / b_base

    return "incomparable_dimension", None


# ---------------------------------------------------------------- selftest
SELFTEST = [
    # (a, b, expected verdict, expected factor or None)
    ("uM", "umol/L", "comparable", 1.0),
    ("µM", "uM", "comparable", 1.0),
    ("μmol·L−1", "uM", "comparable", 1.0),
    ("mg/mL", "g/L", "comparable", 1.0),
    ("mM", "uM", "comparable", 1000.0),
    ("mg/kg", "mg/kg/day", "incomparable_dimension", None),
    ("mg/kg", "mg/m2", "incomparable_dimension", None),
    ("mg", "mg/kg", "incomparable_dimension", None),
    ("mg/L", "uM", "conversion_requires_molecular_weight", None),
    ("banana", "uM", "unknown_unit", None),
    ("h", "min", "comparable", 60.0),
    ("%", "1", "comparable", 0.01),
]


def _selftest():
    ok = True
    for raw, want_code in (("μM", "uM"), ("μmol·L−1", "umol/L")):
        got = normalize(raw)
        good = got["status"] == "ok" and got["ucum_code"] == want_code
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {raw!r} -> ucum_code={got['ucum_code']!r} "
              f"(want {want_code!r})")

    for a, b, want_v, want_f in SELFTEST:
        v, f = compare_units(a, b)
        good = v == want_v and (want_f is None or (f is not None and abs(f - want_f) < 1e-9))
        ok &= good
        mark = "PASS" if good else "FAIL"
        print(f"  {mark}  {a!r} vs {b!r} -> {v} factor={f} (want {want_v} {want_f})")

    # Cross-dimension conversion with molecular weight: glucose 180.16 g/mol, 1 g/L = 5.551 mmol/L
    v, f = compare_units("g/L", "mmol/L", molecular_weight=180.16, analyte="glucose")
    expect = (1.0 / 180.16) / 1e-3
    good = v == "comparable" and abs(f - expect) < 1e-6
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  g/L vs mmol/L (glucose MW=180.16) -> {v} factor={f}")

    for bad_mw in (0, -1, "unknown", float("inf")):
        v, f = compare_units("g/L", "mmol/L", molecular_weight=bad_mw, analyte="glucose")
        good = v == "conversion_requires_molecular_weight" and f is None
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  invalid molecular weight {bad_mw!r} safely rejected -> {v}")

    print("\nAll passed" if ok else "\nFailures present")
    return 0 if ok else 1


def _main(argv=None):
    parser = _JsonArgumentParser(description="Biomedical unit normalization and comparability verdicts")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--normalize", metavar="UNIT", help="normalize one unit")
    mode.add_argument("--compare", nargs=2, metavar=("UNIT_A", "UNIT_B"),
                      help="decide whether two units are comparable")
    mode.add_argument("--selftest", action="store_true", help="run the built-in selftest")
    parser.add_argument("--molecular-weight", type=float,
                        help="positive molecular weight in g/mol, required for mass/molar concentration conversion")
    parser.add_argument("--analyte", help="analyte name, required for mass/molar concentration conversion")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.normalize is not None:
        result = normalize(args.normalize)
    else:
        verdict, factor = compare_units(
            args.compare[0], args.compare[1],
            molecular_weight=args.molecular_weight, analyte=args.analyte)
        result = {
            "unit_a": args.compare[0], "unit_b": args.compare[1],
            "verdict": verdict, "factor_a_to_b": factor,
            "rule_version": RULE_VERSION,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
