#!/usr/bin/env python3
"""Statistical forensics (phase-1 capability, standard library only).

Deterministic consistency checks that require **no raw data**. This is the
phase-1 capability where this project most clearly outperforms "have a general
LLM read the paper and comment": the errors below are nearly invisible to the
human eye and undetectable by an LLM, yet they can be judged deterministically
from the numbers the paper itself reports.

Five checks
-----------
1. `test_statistic_p_mismatch`  -- recompute p from the test statistic + df, compare with the reported value
2. `ci_estimate_mismatch`       -- does the point estimate fall inside its own reported 95% CI
3. `count_percentage_mismatch`  -- are counts and percentages mutually consistent
4. `grim_incompatible_mean`     -- is an integer-scale mean possible for the given n
5. `table_total_mismatch`       -- does the sum of category counts equal the declared denominator

Design principle: do not run when preconditions are incomplete
--------------------------------------------------------------
Every check has explicit **applicability preconditions**; when they are not
met, the check is **never run** and a `partial_extraction` is produced instead
of a guess. All comparisons use the **rounding interval implied by the
reported precision**, never point equality -- a paper writing `p = 0.03` means
the true value lies in [0.025, 0.035), and testing it for "equality" against a
recomputed 0.0312 would be wrong.

**This module only produces `extraction_signal`s (no severity), never
findings.** Whether something constitutes a manuscript problem is decided by
M4 (`references/04-statistics.md`). This matches the contract that M1 and the
tool layer never draw conclusions about the manuscript.

Usage
-----
    from statistical_forensics import check_all
    signals = check_all(claims)

Command line:
    python3 <skill dir>/scripts/statistical_forensics.py --input checks.json
    printf '%s' '[{"check":"count_percentage","count":3,"n":10,"reported_percent":30,"reported_percent_text":"30"}]' |
      python3 <skill dir>/scripts/statistical_forensics.py --input -
    python3 <skill dir>/scripts/statistical_forensics.py --selftest
"""

import argparse
import json
import math
import re
import sys

RULE_VERSION = "2026-08-07"


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)


# ================================================================ Distribution functions
# No scipy in the standard library; pure-Python implementations below
# (regularized incomplete beta / gamma via continued-fraction expansion).

def _log_beta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _betacf(a, b, x, itmax=300, eps=3e-16):
    """Continued-fraction expansion, Numerical Recipes §6.4."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta function I_x(a,b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(a * math.log(x) + b * math.log(1.0 - x) - _log_beta(a, b))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(b * math.log(1.0 - x) + a * math.log(x) - _log_beta(b, a)) \
        * _betacf(b, a, 1.0 - x) / b


def gammainc_lower(s, x, itmax=300, eps=3e-16):
    """Regularized lower incomplete gamma P(s,x)."""
    if x <= 0.0:
        return 0.0
    if x < s + 1.0:
        ap, total, delta = s, 1.0 / s, 1.0 / s
        for _ in range(itmax):
            ap += 1.0
            delta *= x / ap
            total += delta
            if abs(delta) < abs(total) * eps:
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    # Continued fraction (upper incomplete)
    b = x + 1.0 - s
    c = 1e300
    d = 1.0 / b
    h = d
    for i in range(1, itmax + 1):
        an = -i * (i - s)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    q = math.exp(-x + s * math.log(x) - math.lgamma(s)) * h
    return 1.0 - q


def norm_sf(z):
    """Standard normal upper tail."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def t_sf(t, df):
    """Student's t upper tail P(T > t)."""
    if df <= 0:
        return float("nan")
    x = df / (df + t * t)
    p = 0.5 * betainc(df / 2.0, 0.5, x)
    return p if t > 0 else 1.0 - p


def chi2_sf(stat, df):
    """Chi-square upper tail."""
    if df <= 0 or stat < 0:
        return float("nan")
    return 1.0 - gammainc_lower(df / 2.0, stat / 2.0)


def f_sf(stat, df1, df2):
    """F-distribution upper tail."""
    if stat <= 0 or df1 <= 0 or df2 <= 0:
        return float("nan")
    x = df2 / (df2 + df1 * stat)
    return betainc(df2 / 2.0, df1 / 2.0, x)


# ================================================================ Rounding intervals

def rounding_interval(text):
    """Derive from the reported text the rounding interval containing the true value.

    '0.03'    -> (0.025, 0.035)
    '0.0312'  -> (0.03115, 0.03125)
    '12.4'    -> (12.35, 12.45)
    Inequality forms ('<0.001') return None -- those are not rounded values
    and are handled separately.
    """
    s = str(text).strip()
    if s.startswith("<") or s.startswith(">") or s.startswith("≤") or s.startswith("≥"):
        return None
    m = re.match(r"^-?\d+(?:\.(\d+))?$", s)
    if not m:
        return None
    decimals = len(m.group(1)) if m.group(1) else 0
    half = 0.5 * (10 ** -decimals)
    val = float(s)
    return (val - half, val + half)


def _sig(signal_id, stype, target, detail, extra):
    """Build an object conforming to the extraction_signal contract (no severity)."""
    base = {
        "id": signal_id,
        "type": stype,
        "target": target,
        "detail": detail,
        "observation_refs": [],
        "evidence_refs": [],
        # The contract (00-contracts.md routing table) routes count-type issues
        # to both M4 and M2: the numbers themselves belong to M4, while
        # "table vs. body-text inconsistency" falls under M2's completeness
        # scope. Routing to M4 only (as done previously) meant M2 never
        # received these two signal types.
        "routed_to": (["M4", "M2"]
                      if stype in ("count_percentage_mismatch", "table_total_mismatch")
                      else ["M4"]),
        "produced_by": "stage_2",
        "forensics": dict(extra, rule_version=RULE_VERSION),
    }
    return base


# ================================================================ Check 1

def check_test_statistic_p(item, signal_id="SIG-101"):
    """Recompute the p-value and compare with the reported one.

    Preconditions (all required, otherwise the check does not run):
    test_family in {t,F,chi2,z}, statistic, df (except for z),
    tail in {one,two}, and reported_p parseable as a rounded value.
    """
    fam = item.get("test_family")
    stat = item.get("statistic")
    tail = item.get("tail")
    rep = item.get("reported_p")

    if fam not in {"t", "F", "chi2", "z"} or stat is None or tail not in {"one", "two"}:
        return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                    "Statistical forensics preconditions incomplete (missing test_family / statistic / tail); this check was not run.",
                    {"check": "test_statistic_p_mismatch", "ran": False})

    if fam in {"F", "chi2"} and tail != "one":
        return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                    f"The {fam} statistic uses an upper-tail probability; tail must be 'one'. This check was not run.",
                    {"check": "test_statistic_p_mismatch", "ran": False})

    if fam == "t":
        df = item.get("df")
        if df is None:
            return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                        "t-test is missing degrees of freedom; p was not recomputed.",
                        {"check": "test_statistic_p_mismatch", "ran": False})
        p = t_sf(abs(stat), df)
    elif fam == "z":
        p = norm_sf(abs(stat))
    elif fam == "chi2":
        df = item.get("df")
        if df is None:
            return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                        "Chi-square test is missing degrees of freedom; p was not recomputed.",
                        {"check": "test_statistic_p_mismatch", "ran": False})
        p = chi2_sf(stat, df)
    else:  # F
        df1, df2 = item.get("df1"), item.get("df2")
        if df1 is None or df2 is None:
            return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                        "F-test is missing numerator or denominator degrees of freedom; p was not recomputed.",
                        {"check": "test_statistic_p_mismatch", "ran": False})
        p = f_sf(stat, df1, df2)

    # F and chi2 are inherently one-tailed; t/z are doubled according to tail
    if fam in {"t", "z"} and tail == "two":
        p *= 2.0

    interval = rounding_interval(rep)
    if interval is None:
        # '<0.001' form: only check the direction
        s = str(rep).strip()
        m = re.match(r"^(<|≤)\s*([\d.]+)$", s)
        if m:
            operator = m.group(1)
            bound = float(m.group(2))
            violates = p >= bound if operator == "<" else p > bound
            if violates:
                return _sig(signal_id, "test_statistic_p_mismatch",
                            item.get("target", "statistics"),
                            f"Reported p {rep}, but recomputing from the {fam} statistic {stat} (df={item.get('df', (item.get('df1'), item.get('df2')))}) "
                            f"gives p={p:.4g}, which does not satisfy the claimed upper bound.",
                            {"check": "test_statistic_p_mismatch", "ran": True,
                             "test_family": fam, "statistic": stat,
                             "df": item.get("df"), "df1": item.get("df1"),
                             "df2": item.get("df2"), "tail": tail,
                             "recomputed_p": p, "reported_p": rep,
                             "reported_bound": bound, "reported_operator": operator})
            return None
        return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                    f"Reported p-value form {rep!r} cannot be parsed as a rounding interval; no comparison was made.",
                    {"check": "test_statistic_p_mismatch", "ran": False})

    lo, hi = interval
    if lo <= p <= hi:
        return None  # consistent, no signal
    return _sig(signal_id, "test_statistic_p_mismatch", item.get("target", "statistics"),
                f"Reported p = {rep} (rounding interval [{lo:.6g}, {hi:.6g}]), "
                f"but recomputing from the {fam} statistic {stat} gives p = {p:.6g}, outside that interval.",
                {"check": "test_statistic_p_mismatch", "ran": True,
                 "test_family": fam, "statistic": stat,
                 "df": item.get("df"), "df1": item.get("df1"),
                 "df2": item.get("df2"), "tail": tail,
                 "recomputed_p": p, "reported_p": rep,
                 "expected_interval": [lo, hi]})


# ================================================================ Check 2

def check_ci_estimate(item, signal_id="SIG-102"):
    """Does the point estimate fall inside its own reported CI.

    Preconditions: estimate, ci_low, ci_high all present and ci_low < ci_high.
    For ratio measures (OR/RR/HR), if scale='log' is given, compare on the
    log scale.
    """
    est, lo, hi = item.get("estimate"), item.get("ci_low"), item.get("ci_high")
    if est is None or lo is None or hi is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "effect_estimate"),
                    "CI consistency preconditions incomplete (missing point estimate or interval endpoints); this check was not run.",
                    {"check": "ci_estimate_mismatch", "ran": False})
    if lo >= hi:
        return _sig(signal_id, "ci_estimate_mismatch", item.get("target", "effect_estimate"),
                    f"Confidence interval lower bound {lo} is not below upper bound {hi}; the interval itself is invalid.",
                    {"check": "ci_estimate_mismatch", "ran": True,
                     "estimate": est, "ci": [lo, hi]})

    # Use a rounding tolerance at the reported precision so mere rounding is not flagged as an error
    tol = 0.0
    for key in ("estimate_text", "ci_low_text", "ci_high_text"):
        iv = rounding_interval(item.get(key, ""))
        if iv:
            tol = max(tol, (iv[1] - iv[0]) / 2.0)

    if lo - tol <= est <= hi + tol:
        return None
    return _sig(signal_id, "ci_estimate_mismatch", item.get("target", "effect_estimate"),
                f"Point estimate {est} falls outside its own reported 95% CI [{lo}, {hi}] "
                f"(rounding tolerance {tol:g} already accounted for).",
                {"check": "ci_estimate_mismatch", "ran": True,
                 "estimate": est, "ci": [lo, hi], "tolerance": tol})


# ================================================================ Check 3

def check_count_percentage(item, signal_id="SIG-103"):
    """Count vs. percentage consistency. Preconditions: count, n, reported_percent all present and n > 0."""
    count, n, pct = item.get("count"), item.get("n"), item.get("reported_percent")
    if count is None or n is None or pct is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "proportion"),
                    "Count-percentage consistency preconditions incomplete; this check was not run.",
                    {"check": "count_percentage_mismatch", "ran": False})
    if n <= 0:
        return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                    f"Denominator n = {n} is invalid.",
                    {"check": "count_percentage_mismatch", "ran": True})
    if count < 0:
        return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                    f"Count {count} must not be negative.",
                    {"check": "count_percentage_mismatch", "ran": True,
                     "count": count, "n": n})
    if count > n:
        return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                    f"Count {count} exceeds denominator {n}.",
                    {"check": "count_percentage_mismatch", "ran": True,
                     "count": count, "n": n})

    actual = 100.0 * count / n
    iv = rounding_interval(item.get("reported_percent_text", str(pct)))
    if iv is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "proportion"),
                    f"Percentage {pct!r} cannot be parsed as a rounding interval; no comparison was made.",
                    {"check": "count_percentage_mismatch", "ran": False})
    lo, hi = iv
    if lo <= actual <= hi:
        return None
    return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                f"Reported {count}/{n} = {pct}%, but the recomputed value is {actual:.4g}%, "
                f"outside the reported-precision rounding interval [{lo:g}, {hi:g}].",
                {"check": "count_percentage_mismatch", "ran": True,
                 "count": count, "n": n, "recomputed_percent": actual,
                 "expected_interval": [lo, hi]})


# ================================================================ Check 4

def check_grim(item, signal_id="SIG-104"):
    """GRIM: is an equally weighted arithmetic mean on an integer scale possible for the given n.

    **Strict preconditions** (the check does not run if any is unmet):
      - `scale_is_integer = True` (each subject's value is an integer)
      - `items_per_subject` (item count when summing multi-item Likert scales), default 1
      - `n` is explicit and n <= 200 (GRIM loses resolution as n grows; above 200 it is essentially useless)
      - the mean is given as text so decimal places can be parsed
      - **not applicable**: adjusted means, least-squares means, weighted means,
        n unclear after missing data, continuous scales
    """
    if not item.get("scale_is_integer"):
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    "GRIM preconditions unmet (not confirmed to be a raw arithmetic mean on an integer scale); this check was not run.",
                    {"check": "grim_incompatible_mean", "ran": False})
    if item.get("is_adjusted_mean"):
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    "An adjusted mean / LS mean was reported; GRIM does not apply, so this check was not run.",
                    {"check": "grim_incompatible_mean", "ran": False})

    n = item.get("n")
    mean_text = item.get("mean_text")
    if n is None or mean_text is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    "GRIM is missing n or the mean text; this check was not run.",
                    {"check": "grim_incompatible_mean", "ran": False})
    if n <= 0 or n > 200:
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    f"n = {n} is outside GRIM's effective range (1-200); this check was not run.",
                    {"check": "grim_incompatible_mean", "ran": False})

    m = re.match(r"^-?\d+(?:\.(\d+))?$", str(mean_text).strip())
    if not m:
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    f"Mean {mean_text!r} cannot be parsed for decimal places; this check was not run.",
                    {"check": "grim_incompatible_mean", "ran": False})
    decimals = len(m.group(1)) if m.group(1) else 0
    mean = float(mean_text)
    k = item.get("items_per_subject", 1)
    total_units = n * k

    half = 0.5 * (10 ** -decimals)
    mean_lo, mean_hi = mean - half, mean + half

    # Possible totals are integers; the corresponding set of means
    lo_sum = math.floor(mean * total_units) - 2
    hi_sum = math.ceil(mean * total_units) + 2
    for s in range(lo_sum, hi_sum + 1):
        cand = s / total_units
        # Treat rounding endpoints as a closed interval: when the paper does not
        # state half-even vs. half-up, boundary candidates count as feasible,
        # avoiding false positives from Python's binary floats and banker's rounding.
        if mean_lo <= cand <= mean_hi:
            return None  # a feasible integer total exists -> consistent
    return _sig(signal_id, "grim_incompatible_mean", item.get("target", "mean"),
                f"Reported mean {mean_text} (n = {n}"
                + (f", {k} items per subject" if k != 1 else "")
                + f") is impossible on an integer scale: no integer total rounds to this value at {decimals} decimal places.",
                {"check": "grim_incompatible_mean", "ran": True,
                 "n": n, "items_per_subject": k, "reported_mean": mean_text})


# ================================================================ Check 5

def check_table_total(item, signal_id="SIG-105"):
    """Does the sum of category counts equal the declared denominator.

    Preconditions: `counts` (counts of mutually exclusive and exhaustive
    categories) and `declared_total` both present. **Only applicable when the
    categories are mutually exclusive and exhaustive** -- the caller must
    confirm this; otherwise "the total does not equal n" is normal (e.g.
    multi-select comorbidities).

    Typical error: a Table 1 characteristic with two categories, 12 + 18 = 30,
    while the header declares n = 28 for that group.
    """
    counts = item.get("counts")
    total = item.get("declared_total")
    target = item.get("target", "table")

    if not counts or total is None:
        return _sig(signal_id, "partial_extraction", target,
                    "Table-total consistency preconditions incomplete (missing category counts or declared denominator); this check was not run.",
                    {"check": "table_total_mismatch", "ran": False})

    if not item.get("categories_exhaustive", False):
        return _sig(signal_id, "partial_extraction", target,
                    "Categories not confirmed as mutually exclusive and exhaustive "
                    "(e.g. multi-select comorbidities); a total differing from the denominator is normal there, so this check was not run.",
                    {"check": "table_total_mismatch", "ran": False})

    try:
        s_counts = sum(int(c) for c in counts)
        total_i = int(total)
    except (TypeError, ValueError):
        return _sig(signal_id, "partial_extraction", target,
                    "Counts or denominator cannot be parsed as integers; this check was not run.",
                    {"check": "table_total_mismatch", "ran": False})

    missing = item.get("missing_count")
    if missing is not None:
        try:
            s_counts += int(missing)
        except (TypeError, ValueError):
            pass

    if s_counts == total_i:
        return None

    return _sig(signal_id, "table_total_mismatch", target,
                f"Category counts sum to {s_counts} ({' + '.join(str(c) for c in counts)}"
                + (f" + missing {missing}" if missing is not None else "")
                + f"), but the declared denominator is {total_i}, a difference of {s_counts - total_i}. "
                f"Given mutually exclusive and exhaustive categories, this is a deterministic counting error.",
                {"check": "table_total_mismatch", "ran": True,
                 "counts": list(counts), "declared_total": total_i,
                 "observed_sum": s_counts, "difference": s_counts - total_i})


# ================================================================ Aggregation

CHECKS = {
    "test_statistic_p": check_test_statistic_p,
    "ci_estimate": check_ci_estimate,
    "count_percentage": check_count_percentage,
    "grim": check_grim,
    "table_total": check_table_total,
}


def check_all(items, signal_start=100):
    """items is [{check: <name>, ...params}]; returns a list of extraction_signals.

    Consistent items **produce no signal** (silence means pass); only
    inconsistencies or incomplete preconditions produce output.
    """
    if not isinstance(items, list):
        raise ValueError("Statistical forensics input must be a JSON array")
    if not isinstance(signal_start, int) or isinstance(signal_start, bool) or signal_start < 0:
        raise ValueError("signal_start must be a non-negative integer")

    out = []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"Statistical forensics item {i} must be a JSON object")
        fn = CHECKS.get(item.get("check"))
        if fn is None:
            raise ValueError(f"Statistical forensics item {i} has an unsupported check: {item.get('check')!r}")
        try:
            sig = fn(item, signal_id=f"SIG-{signal_start + i:03d}")
        except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
            raise ValueError(f"Statistical forensics item {i} has invalid parameters: {exc}") from exc
        if sig is not None:
            # If the caller has already bound observation and manuscript
            # evidence, keep those refs; the tool never fabricates locations.
            # When absent, keep empty arrays for the Stage 2 aggregator to
            # fill in before handing off to M4.
            for ref_key in ("observation_refs", "evidence_refs"):
                refs = item.get(ref_key)
                if refs is not None:
                    if not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
                        raise ValueError(f"Statistical forensics item {i}: {ref_key} must be an array of strings")
                    sig[ref_key] = list(refs)
            out.append(sig)
    return out


# ================================================================ Self-test
def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    # --- Distribution functions vs. known values ---
    expect("norm_sf(1.96)≈0.025", round(norm_sf(1.96), 4), 0.025)
    expect("t_sf(2.228,10)*2≈0.05", round(t_sf(2.228, 10) * 2, 3), 0.05)
    expect("chi2_sf(3.841,1)≈0.05", round(chi2_sf(3.841, 1), 3), 0.05)
    expect("f_sf(4.965,2,10)≈0.032", round(f_sf(4.965, 2, 10), 3), 0.032)

    # --- Check 1: a consistent t-test must not be flagged ---
    s = check_test_statistic_p({"check": "test_statistic_p", "test_family": "t",
                                "statistic": 2.228, "df": 10, "tail": "two",
                                "reported_p": "0.05"})
    expect("consistent t -> no signal", s, None)

    # Misreported p (reported 0.001, actual 0.05)
    s = check_test_statistic_p({"test_family": "t", "statistic": 2.228, "df": 10,
                                "tail": "two", "reported_p": "0.001"})
    expect("inconsistent t -> flagged", s["type"] if s else None, "test_statistic_p_mismatch")
    expect("recomputed-p signal keeps test family", s["forensics"].get("test_family"), "t")
    expect("recomputed-p signal keeps df", s["forensics"].get("df"), 10)

    s = check_test_statistic_p({"test_family": "t", "statistic": 4.0, "df": 30,
                                "tail": "two", "reported_p": "<0.001"})
    expect("p upper bound satisfied -> no signal", s, None)

    s = check_test_statistic_p({"test_family": "z", "statistic": 0.0,
                                "tail": "one", "reported_p": "≤0.5"})
    expect("equal to non-strict p bound -> no signal", s, None)

    s = check_test_statistic_p({"test_family": "chi2", "statistic": 3.841, "df": 1,
                                "tail": "two", "reported_p": "0.05"})
    expect("chi2 declared two-tailed -> not run", s["forensics"]["ran"], False)

    # Missing df -> does not run
    s = check_test_statistic_p({"test_family": "t", "statistic": 2.2, "tail": "two",
                                "reported_p": "0.05"})
    expect("missing df -> partial_extraction", s["type"], "partial_extraction")

    # --- Check 2 ---
    s = check_ci_estimate({"estimate": 12.4, "ci_low": 9.8, "ci_high": 15.7})
    expect("estimate inside CI -> no signal", s, None)
    s = check_ci_estimate({"estimate": 20.0, "ci_low": 9.8, "ci_high": 15.7})
    expect("estimate outside CI -> flagged", s["type"], "ci_estimate_mismatch")

    # --- Check 3 ---
    s = check_count_percentage({"count": 42, "n": 84, "reported_percent": 50.0,
                                "reported_percent_text": "50.0"})
    expect("42/84=50.0% -> no signal", s, None)
    s = check_count_percentage({"count": 42, "n": 84, "reported_percent": 60.0,
                                "reported_percent_text": "60.0"})
    expect("42/84 != 60.0% -> flagged", s["type"], "count_percentage_mismatch")
    s = check_count_percentage({"count": -1, "n": 10, "reported_percent": -10.0,
                                "reported_percent_text": "-10.0"})
    expect("negative count -> flagged", s["type"], "count_percentage_mismatch")

    # --- Check 4: GRIM ---
    # n=10, mean=3.10 feasible (total 31)
    s = check_grim({"scale_is_integer": True, "n": 10, "mean_text": "3.10"})
    expect("GRIM feasible -> no signal", s, None)
    # n=10, mean=3.14 infeasible (total would need to be 31.4)
    s = check_grim({"scale_is_integer": True, "n": 10, "mean_text": "3.14"})
    expect("GRIM infeasible -> flagged", s["type"], "grim_incompatible_mean")
    # Adjusted mean -> does not run
    s = check_grim({"scale_is_integer": True, "n": 10, "mean_text": "3.14",
                    "is_adjusted_mean": True})
    expect("adjusted mean -> partial_extraction", s["type"], "partial_extraction")
    # n too large -> does not run
    s = check_grim({"scale_is_integer": True, "n": 500, "mean_text": "3.14"})
    expect("n>200 -> partial_extraction", s["type"], "partial_extraction")

    # --- Check 5: table totals (a gap found in real A/B testing) ---
    # rct_clinical Table 1: menopausal status 12 + 18 = 30, but the header declares n = 28
    s = check_table_total({"counts": [12, 18], "declared_total": 28,
                           "categories_exhaustive": True})
    expect("12+18 != 28 -> flagged", s["type"] if s else None, "table_total_mismatch")
    expect("difference is correct", s["forensics"]["difference"] if s else None, 2)
    s = check_table_total({"counts": [13, 15], "declared_total": 28,
                           "categories_exhaustive": True})
    expect("13+15 = 28 -> no signal", s, None)
    s = check_table_total({"counts": [12, 14], "declared_total": 28,
                           "missing_count": 2, "categories_exhaustive": True})
    expect("equal after counting missing -> no signal", s, None)
    s = check_table_total({"counts": [12, 18], "declared_total": 28})
    expect("exclusive/exhaustive unconfirmed -> not run",
           s["forensics"]["ran"] if s else None, False)

    # --- Signal contract: must not carry severity ---
    sigs = check_all([{"check": "grim", "scale_is_integer": True, "n": 10,
                       "mean_text": "3.14", "evidence_refs": ["EV-001"]}])
    expect("signal id matches schema", bool(re.match(r"^SIG-[0-9]{3,}$", sigs[0]["id"])), True)
    expect("signal has no severity", all("severity" not in x for x in sigs), True)
    expect("signal routed to M4", sigs[0]["routed_to"], ["M4"])
    expect("input evidence refs preserved", sigs[0]["evidence_refs"], ["EV-001"])

    try:
        check_all([None])
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    expect("non-object input yields controlled error", invalid_rejected, True)

    print("\nAll passed" if ok else "\nFailures present")
    return 0 if ok else 1


def _read_json(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _main(argv=None):
    parser = _JsonArgumentParser(description="Statistical consistency forensics requiring no raw data")
    parser.add_argument("--input", metavar="JSON", help="JSON file with the array of checks; - reads stdin")
    parser.add_argument("--signal-start", type=int, default=100)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.input:
        parser.error("either --input JSON or --selftest is required")
    try:
        items = _read_json(args.input)
        signals = check_all(items, signal_start=args.signal_start)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "detail": str(exc)}},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"signals": signals}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
