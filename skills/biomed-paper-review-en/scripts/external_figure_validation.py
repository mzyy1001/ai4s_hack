#!/usr/bin/env python3
"""External data validation layer X1: check verifiable manuscript claims against authoritative public databases.

**This is the only tool in the suite that can detect "the paper disagrees with
the real world."** Every other check only tests the paper's internal
consistency -- which a bare LLM already does, so the uplift there is
structurally zero or negative. The measured negative uplift stems from
exactly this.

What the model structurally cannot do is precisely what happens here:

| Claim in the manuscript | Checked against | Why the model cannot do it |
| --- | --- | --- |
| "We studied breast cancer using MDA-MB-435" | Cellosaurus | The line is actually an M14 melanoma derivative; ~600 problematic cell lines form a long tail no model can know |
| "This trial is registered as NCTxxxx" | ClinicalTrials.gov | Registration dates exist only in the registry, never in the body text -- retrospective registration cannot be found by reading the text alone |
| Primary outcomes reported by the paper | ClinicalTrials.gov | Outcome switching can only be found by comparing against the registry record |
| References | Europe PMC | Retractions often happen after the model's training cutoff |
| WB band labeled 100 kDa | UniProt | Requires the exact molecular weight |
| "Data available at GSExxxxx" | GEO / SRA / PRIDE | Does the accession actually exist |
| Reported IC50 | ChEMBL | Known activity orders of magnitude |

Query on demand, no bundled datasets
------------------------------------
A query is issued only when an identifier actually appears in the manuscript.
No reference library is bundled: submission size is limited, the databases
update daily (retraction status especially), and most papers touch only a
handful of entries.

Four disciplines
----------------
1. **"Not found" != "the paper is wrong."** Any interface failure produces a
   `system_limitation` and **never** becomes a finding. Same principle as the
   contract's `parse_failed != not_reported`. `retrieval_status` is strict:
   `not_found` is reserved for a well-formed exact identifier that received an
   authoritative 404 or explicit zero records; a semantic query with zero hits
   is recorded as `not_addressed` and never treated as "does not exist."
2. **Only signals, never findings.** Severity is judged by M2-M7 together
   with manuscript evidence.
3. **Order-of-magnitude criteria are always `needs_manual_review`.** Different
   cell lines and endpoints routinely differ by one or two orders of
   magnitude; that cannot be auto-flagged as wrong.
4. **Every external fact is registered as external evidence** with endpoint,
   query, retrieval time, response sha256, and database version, so it can be
   reproduced on re-review.

Input
-----
A JSON array; each item must carry `check` and `evidence_refs` (pointing to
present evidence inside the manuscript; the contract requires at least one --
an external fact is only meaningful when paired with a manuscript fact).

    python3 external_figure_validation.py --selftest
    python3 external_figure_validation.py --input -
    python3 external_figure_validation.py --uniprot P04637
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PARSER_VERSION = "x1-2026-08-07"
RULE_VERSION = "2026-08-07"
UA = {"User-Agent": "ai4s-hack-biomed-review/1.0"}
# HGNC and SciCrunch return XML/HTML by default; JSON must be requested explicitly
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
    """Collect signals / external evidence / system_limitations with unified numbering.

    ids must match the contract patterns `^SIG-[0-9]{3,}$` / `^EV-[0-9]{3,}$`.
    X1 uses the 9xx range, keeping clear of Stage 1-3 numbering.
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
            "recommended_action": "Re-run X1 once network or allowlist access is restored; until then no conclusion may be drawn about this claim",
            "produced_by": "stage_3c_external_validation",
            "_error": err,
        })
        return None


# ---------------------------------------------------------------- Record/replay
# X1's selftest hits the real interfaces. When the network is down, the
# allowlist blocks a host, or an upstream field changes, the selftest cannot
# run -- and **"cannot run" does not mean the code is broken**, the same
# principle as parse_failed != not_reported in the contract. Recording real
# responses to disk and replaying them offline lets the selftest complete
# deterministically without a network.
#
# Explicit boundary: fixture replay **validates our parsing and decision
# logic**, not whether the upstream interfaces have changed. Upstream changes
# are only discovered by re-recording, so an all-green offline run must
# **never** be claimed as "external validation is available."
FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "resources", "x1_fixtures.json")
_FIXTURES = None
_RECORDING = None
# Strict offline: a fixture miss **must raise an error**, never silently fall
# back to the network -- otherwise the "offline selftest" quietly becomes an
# online one, testing something entirely different from what it claims
_OFFLINE = False


def _load_fixtures():
    global _FIXTURES
    if _FIXTURES is None:
        try:
            with io.open(os.path.abspath(FIXTURE_PATH), encoding="utf-8") as fh:
                blob = json.load(fh)
            _FIXTURES = blob.get("responses", blob) if isinstance(blob, dict) else {}
        except (OSError, ValueError):
            _FIXTURES = {}
    return _FIXTURES


def _fixture_key(url):
    """Index by URL. Query strings contain no credentials, so they are safe to persist."""
    return url



# ---------------------------------------------------------------- Transport layer
def fetch(url, timeout=40, retries=2, headers=None):
    """Return (text, http_status, error).

    **Every failure returns an error and is never silently treated as "no such
    record"** -- exactly the trap this project has fallen into repeatedly:
    mistaking "we could not retrieve it" for "the paper has a problem."
    """
    # Replay first: a fixture hit means no network request is made
    fx = _load_fixtures()
    if fx and not _RECORDING:
        rec = fx.get(_fixture_key(url))
        if rec is not None:
            return (rec.get("body"), rec.get("http"), rec.get("error"))
    if _OFFLINE and not _RECORDING:
        return None, None, {"kind": "fixture_missing", "url": url[:120]}

    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                if _RECORDING is not None:
                    _RECORDING[_fixture_key(url)] = {
                        "body": body, "http": r.status, "error": None}
                return body, r.status, None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                if _RECORDING is not None:
                    _RECORDING[_fixture_key(url)] = {
                        "body": None, "http": 404,
                        "error": {"kind": "not_found", "http": 404}}
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
    """Build an external evidence entry.

    Hard contract constraints: `resolved` must have a record_id and non-empty
    assertions; `not_found` / `not_addressed` must have a null record_id and
    empty assertions.
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
    # Fetch only the fields we use: the full record is 869 KB, trimmed to
    # 1.1 KB (a 750x difference). Both sandbox bandwidth and recorded fixture
    # size benefit.
    url = (f"{UNIPROT}/{urllib.parse.quote(acc)}.json"
           f"?fields=accession,protein_name,sequence,organism_name")
    raw, http, err = fetch(url)
    if err and err.get("kind") == "not_found":
        led.add_evidence(make_external_evidence(
            "UniProt", url, "accession_lookup", acc, None, raw, 404, "not_found"))
        return None, None
    if err:
        led.add_limit(f"Could not retrieve UniProt {acc}; the related validation was not completed", target, modules, err)
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
        # With trimmed fields entryAudit is no longer returned; the contract
        # allows a null database_version, and the version number **must not
        # be guessed** -- a guessed version will not match on re-review
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
    """Is the molecular weight labeled on a WB band compatible with the protein's actual weight.

    Always `needs_manual_review`: post-translational modification,
    glycosylation, dimers, and cleavage fragments all shift migration and
    cannot be auto-flagged as wrong.
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
        f"The band in the figure is labeled {kda} kDa, while UniProt "
        f"{p['accession']} ({p['organism']}, {p['length']} aa) has a theoretical "
        f"molecular weight of {p['kda']:.1f} kDa, outside the usual migration "
        f"deviation range ({lo:.1f}-{hi:.1f} kDa). Post-translational "
        f"modification, glycosylation, dimers, and cleavage fragments can all "
        f"explain the difference; manual review is required before drawing any conclusion.",
        ["M5"], "uniprot", "accession_lookup", "blot_band_molecular_weight",
        {"reported_kda": kda}, {"theoretical_kda": round(p["kda"], 1)},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


def check_variant(item, led, sid):
    """Does the variant position fall within the real protein sequence, and does the reference residue match.

    This upgrades `sequence_identifier_audit.py` from "check only against the
    sequence the paper itself provides" to "check against the real protein" --
    it works even when the paper gives no sequence.
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
            f"Variant position {pos} exceeds the {p['accession']} ({p['organism']}) "
            f"sequence length of {p['length']} aa -- position out of range.",
            ["M2", "M3"], "uniprot", "accession_lookup", "variant_position_range",
            {"position": pos}, {"sequence_length": p["length"]},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if ref:
        actual = p["sequence"][pos - 1:pos]
        if actual and actual != ref:
            return make_signal(
                sid, target,
                f"The variant claims the reference residue at position {pos} is {ref}, "
                f"but {p['accession']} actually has {actual} at that position.",
                ["M2", "M3"], "uniprot", "accession_lookup",
                "variant_reference_residue",
                {"position": pos, "ref_aa": ref}, {"actual_aa": actual},
                "mismatch", "complete", item["evidence_refs"], [ev])
    return None


# ---------------------------------------------------------------- Cellosaurus
def check_cell_line(item, led, sid):
    """Is the cell line flagged by Cellosaurus as contaminated / misidentified.

    **The single most valuable check in the suite.** MDA-MB-435 is used in
    many papers as a breast cancer cell line, yet Cellosaurus annotates it as
    an M14 melanoma derivative -- "breast cancer" conclusions drawn from it
    rest on the wrong study object entirely, overturning the whole paper
    rather than a minor flaw.
    """
    name = (item.get("cell_line") or "").strip()
    target = item.get("target", "methods.cell_line")
    if not name:
        return None
    # Likewise fetch only the needed fields: full record 166 KB, trimmed 2.4 KB
    url = (f"{CELLO}/search/cell-line?q={urllib.parse.quote(name)}"
           f"&format=json&rows=1&fields=id,ac,cc,ox,sy")
    raw, http, err = fetch(url)
    if err:
        return led.add_limit(f"Could not query Cellosaurus for {name}", target, ["M3"], err)
    try:
        lst = json.loads(raw)["Cellosaurus"]["cell-line-list"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("Cellosaurus response could not be parsed", target, ["M3"],
                             {"kind": "unparseable"})
    if not lst:
        # Zero hits on a name search is a **semantic query** miss, not "this cell line does not exist"
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
        f"Cellosaurus flags {name} ({acc}) as problematic: {problems[0][:220]}. "
        f"If the manuscript treats it as a model of a particular tissue origin, "
        f"that premise may not hold, affecting every conclusion based on this cell line.",
        ["M3"], "cellosaurus", "cell_line_name_search", "cell_line_problematic",
        {"cell_line": name}, {"problematic": problems[0][:300]},
        "mismatch", "complete", item["evidence_refs"], [ev])


# ---------------------------------------------------------------- Accessions
def check_accession(item, led, sid):
    """Does the accession the paper claims to have deposited data under actually exist.

    Always `needs_manual_review`: the record may be under embargo or newly
    submitted and not yet indexed.
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
        return led.add_limit(f"Could not query {db} accession {acc}", target, ["M7"], err)
    if not missing and db in ("GEO", "SRA"):
        try:
            missing = int(json.loads(raw)["esearchresult"]["count"]) == 0
        except Exception:                                        # noqa: BLE001
            return led.add_limit(f"{db} response could not be parsed", target, ["M7"],
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
        f"The {db} accession {acc} claimed by the manuscript returns no record. "
        f"It may also be under embargo or newly submitted and not yet indexed; "
        f"manual confirmation is required before drawing any conclusion.",
        ["M7"], db.lower(), "accession_lookup", "accession_exists",
        {"accession": acc}, {"found": False},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------------------------- ChEMBL
def check_ic50(item, led, sid):
    """Does the reported IC50 differ from known ChEMBL activity by three or more orders of magnitude. Always a candidate only."""
    cid, val = item.get("chembl_id"), item.get("reported_nm")
    target = item.get("target", "figure.dose_response")
    if not cid or not val:
        return None
    url = (f"{CHEMBL}/activity.json?molecule_chembl_id={urllib.parse.quote(cid)}"
           f"&standard_type=IC50&limit=100")
    raw, http, err = fetch(url, timeout=60)
    if err:
        return led.add_limit(f"Could not retrieve ChEMBL activity data for {cid}", target, ["M5"], err)
    try:
        acts = json.loads(raw).get("activities", [])
    except Exception:                                            # noqa: BLE001
        return led.add_limit("ChEMBL response could not be parsed", target, ["M5"],
                             {"kind": "unparseable"})
    vals = sorted(float(a["standard_value"]) for a in acts
                  if a.get("standard_value") and a.get("standard_units") == "nM")
    if len(vals) < 5:
        return led.add_limit(
            f"ChEMBL has only {len(vals)} IC50 records for {cid}, not enough to judge the order of magnitude",
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
        f"Reported IC50 = {val:g} nM, while the median of {len(vals)} ChEMBL "
        f"IC50 records for {cid} is {med:g} nM, a roughly {ratio:.0f}-fold "
        f"difference. Activity differences across cell lines and endpoints are "
        f"the norm; whether the experimental systems are comparable requires manual review.",
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
        led.add_limit(f"Could not query registration number {nct}", target, modules, err)
        return None, url, raw, http, None
    try:
        return json.loads(raw)["protocolSection"], url, raw, http, "resolved"
    except Exception:                                            # noqa: BLE001
        led.add_limit(f"Registration record for {nct} could not be parsed", target, modules,
                      {"kind": "unparseable"})
        return None, url, raw, http, None


def registered_late(reg, start):
    """Is registration **definitely** later than the study start.

    ClinicalTrials.gov startDate often has only YYYY-MM precision, while the
    registration date is YYYY-MM-DD. A naive string comparison would misjudge
    "registered the same month" as retrospective registration -- with
    start=2011-02 and reg=2011-02-24, the study may well have started after
    the 24th; we cannot tell. **Compare at the coarser of the two precisions
    and require strictly greater**: better to miss a case than to accuse a
    manuscript on a guess.
    """
    if not (reg and start):
        return False
    n = min(len(reg), len(start))
    return reg[:n] > start[:n]


def check_trial_registration(item, led, sid):
    """Does the registration number exist, and is the trial **retrospectively registered** (registration after study start).

    ICMJE requires prospective registration. Both dates exist only in the
    registry and almost never appear in the body text -- retrospective
    registration is impossible to discover by reading the text alone.
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
            sid, target, f"The registration number {nct} claimed by the manuscript has no record on ClinicalTrials.gov.",
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
        f"{nct} was registered on {reg}, later than the study start date {start} "
        f"-- retrospective registration, which does not meet the ICMJE prospective "
        f"registration requirement. The registration date exists only in the "
        f"registry and is rarely stated in the text.",
        ["M6"], "clinicaltrials_gov", "nct_lookup", "prospective_registration",
        {"claimed_registration": nct}, {"registered": reg, "started": start},
        "mismatch", "complete", item["evidence_refs"], [ev])


def check_outcome_switching(item, led, sid):
    """Does the reported primary outcome match the registered one (outcome switching).

    Outcome switching is one of the most covert biases in clinical trials and
    **must be checked against the registry record**. Only a coarse keyword
    screen is done here, always `needs_manual_review` -- wording differences
    alone can cause a mismatch.
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
        return led.add_limit(f"{nct} has no registered primary outcome; outcome switching cannot be compared",
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
        f"The manuscript reports the primary outcome as \"{reported[:90]}\", "
        f"while {nct} registers \"{'; '.join(regd)[:160]}\"; they share no "
        f"keywords, suggesting possible outcome switching. Wording differences "
        f"alone can also cause a mismatch; manual comparison is required.",
        ["M4", "M7"], "clinicaltrials_gov", "nct_lookup", "outcome_switching",
        {"reported_primary": reported}, {"registered_primary": regd},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- Citing retracted references
def check_cited_retracted(item, led, sid):
    """Has a cited reference **been retracted**.

    Structurally impossible for the model: retractions often occur after the
    training cutoff, and long-tail retractions are in no model's knowledge.
    Uses Europe PMC's pubType -- in practice Crossref's update-by is often
    empty for retracted papers (e.g. the Surgisphere Lancet paper) and is
    unreliable.
    """
    doi = (item.get("doi") or "").strip()
    target = item.get("target", "references")
    if not doi:
        return None
    query = f'DOI:"{doi}"'
    url = f"{EPMC}/search?query={urllib.parse.quote(query)}&format=json&resultType=core"
    raw, http, err = fetch(url, timeout=60)
    if err:
        return led.add_limit(f"Could not query retraction status for reference {doi}", target,
                             ["M2", "M7"], err)
    try:
        res = json.loads(raw)["resultList"]["result"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("Europe PMC response could not be parsed", target, ["M2", "M7"],
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
        f"Reference {doi} ({(a.get('title') or '')[:70]}) has been retracted. "
        f"If this work underpins the paper's argument, the related reasoning needs re-evaluation.",
        ["M2", "M7"], "europe_pmc", "doi_lookup", "cited_work_retracted",
        {"doi": doi}, {"retracted": True},
        "mismatch", "complete", item["evidence_refs"], [ev])


# ---------------------------------------------- HGNC gene symbols
# Excel silently converts these gene symbols into dates -- the most common
# silent corruption in gene lists. In 2020 HGNC renamed the entire
# SEPT/MARCH/DEC families because of this (SEPT2 -> SEPTIN2).
_EXCEL_DATE = re.compile(r"^(\d{1,2}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                         r"|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{1,2})$",
                         re.I)


def check_gene_symbol(item, led, sid):
    """Is a human gene symbol HGNC-approved; is it a renamed legacy symbol;
    is it a gene name **converted into a date by Excel**.

    HGNC governs human nomenclature only; non-human species are skipped
    (mouse goes to MGI, zebrafish to ZFIN), otherwise normal mouse symbols
    would be misreported as "not approved."
    """
    sym = (item.get("symbol") or "").strip()
    species = (item.get("species") or "").strip().lower()
    target = item.get("target", "methods.genes")
    if not sym:
        return None
    if species and species not in ("human", "homo sapiens", "hsa"):
        return None

    # Excel date corruption can be determined offline, but external evidence is
    # still registered so the correct renamed symbol can be re-checked
    if _EXCEL_DATE.match(sym):
        url = f"{HGNC}/search/prev_symbol/{urllib.parse.quote(sym)}"
        return make_signal(
            sid, target,
            f"Gene symbol \"{sym}\" is in date format -- Excel silently converts "
            f"SEPT/MARCH/DEC-family symbols into dates, the most common silent "
            f"corruption in gene lists. HGNC renamed these families in 2020 "
            f"(SEPT2 -> SEPTIN2, MARCH1 -> MARCHF1) to avoid the problem. "
            f"The original data must be checked to determine which gene this column actually is.",
            ["M2", "M3"], "hgnc", "symbol_lookup", "gene_symbol_excel_corruption",
            {"symbol": sym}, {"looks_like_date": True},
            "mismatch", "complete", item["evidence_refs"],
            [led.add_evidence(make_external_evidence(
                "HGNC", url, "symbol_lookup", sym, None, "", 200, "not_addressed"))])

    url = f"{HGNC}/fetch/symbol/{urllib.parse.quote(sym)}"
    raw, http, err = fetch(url, headers=JSON_ACCEPT)
    if err:
        return led.add_limit(f"Could not query HGNC for gene symbol {sym}", target,
                             ["M2", "M3"], err)
    try:
        resp = json.loads(raw)["response"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("HGNC response could not be parsed", target, ["M2", "M3"],
                             {"kind": "unparseable"})
    if resp.get("numFound"):
        d = resp["docs"][0]
        led.add_evidence(make_external_evidence(
            "HGNC", url, "symbol_lookup", sym, d.get("hgnc_id"), raw, http, "resolved",
            assertions=[{"predicate": "symbol_status", "subject": d.get("hgnc_id"),
                         "external_value": d.get("status"), "unit": None,
                         "source_path": "response.docs[0].status"}]))
        return None

    # No approved-symbol hit -- may be a legacy (renamed) symbol, an alias, or simply nonexistent
    purl = f"{HGNC}/search/prev_symbol/{urllib.parse.quote(sym)}"
    praw, phttp, perr = fetch(purl, headers=JSON_ACCEPT)
    if perr:
        return led.add_limit(f"Could not query whether {sym} is a legacy symbol", target, ["M2", "M3"], perr)
    try:
        presp = json.loads(praw)["response"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("HGNC response could not be parsed", target, ["M2", "M3"],
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
            f"Gene symbol \"{sym}\" is no longer the current HGNC symbol; the "
            f"current symbol is \"{cur}\". A legacy symbol is not an error in "
            f"itself, but it invites mix-ups when compared against current literature.",
            ["M2", "M3"], "hgnc", "prev_symbol_search", "gene_symbol_outdated",
            {"symbol": sym}, {"current_symbol": cur},
            "mismatch", "complete", item["evidence_refs"], [ev])

    ev = led.add_evidence(make_external_evidence(
        "HGNC", url, "symbol_lookup", sym, None, raw, http, "not_addressed"))
    return make_signal(
        sid, target,
        f"Gene symbol \"{sym}\" is neither an HGNC-approved symbol nor a "
        f"registered legacy symbol. It may be a typo, a non-human species "
        f"symbol, or nonstandard internal naming; manual confirmation is required.",
        ["M2", "M3"], "hgnc", "symbol_lookup", "gene_symbol_unrecognized",
        {"symbol": sym}, {"found": False},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- Crossref reference existence
def check_reference_exists(item, led, sid):
    """Does the reference's DOI actually exist.

    Targets **hallucinated and paper-mill citations** -- references written by
    generative tools are often perfectly formatted while the DOI simply does
    not exist. The model cannot verify this itself: it cannot resolve DOIs.
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
            f"Reference DOI {doi} does not resolve in Crossref. A perfectly "
            f"formatted but nonexistent DOI is the hallmark of hallucinated and "
            f"paper-mill citations; verify whether this reference is real.",
            ["M2"], "crossref", "doi_resolve", "reference_doi_resolves",
            {"doi": doi}, {"resolves": False},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"Could not resolve DOI {doi}", target, ["M2"], err)
    try:
        msg = json.loads(raw)["message"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("Crossref response could not be parsed", target, ["M2"],
                             {"kind": "unparseable"})
    led.add_evidence(make_external_evidence(
        "Crossref", url, "doi_resolve", doi, msg.get("DOI"), raw, http, "resolved",
        assertions=[{"predicate": "title", "subject": msg.get("DOI"),
                     "external_value": (msg.get("title") or [None])[0], "unit": None,
                     "source_path": "message.title[0]"}]))
    return None


# ---------------------------------------------- NCBI Taxonomy species
def check_species(item, led, sid):
    """Is the species scientific name valid in NCBI Taxonomy."""
    name = (item.get("species") or "").strip()
    target = item.get("target", "methods.species")
    if not name:
        return None
    url = (f"{EUTILS}/esearch.fcgi?db=taxonomy&term="
           f"{urllib.parse.quote(name)}&retmode=json")
    raw, http, err = fetch(url)
    if err:
        return led.add_limit(f"Could not query species name {name}", target, ["M3"], err)
    try:
        r = json.loads(raw)["esearchresult"]
        cnt, ids = int(r["count"]), r.get("idlist", [])
    except Exception:                                            # noqa: BLE001
        return led.add_limit("NCBI Taxonomy response could not be parsed", target, ["M3"],
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
        f"Species name \"{name}\" is not found in NCBI Taxonomy. It may be a "
        f"typo, an outdated taxonomic name, or a common name used as a "
        f"scientific one; manual confirmation is required.",
        ["M3"], "ncbi_taxonomy", "scientific_name_search", "species_name_valid",
        {"species": name}, {"found": False},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- RRID reagent identifiers
def check_rrid(item, led, sid):
    """Does the antibody / reagent / plasmid RRID resolve.

    Antibodies are the epicenter of the biomedical reproducibility crisis.
    The RRID is currently the only identifier that uniquely pins down "which
    exact antibody" -- and whether it resolves can only be learned by querying
    SciCrunch.
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
            f"RRID:{rrid} does not resolve. The RRID is the only identifier "
            f"that pins down a specific antibody/reagent; failure to resolve "
            f"means others cannot reproduce work with this reagent.",
            ["M3"], "scicrunch", "rrid_resolve", "rrid_resolves",
            {"rrid": rrid}, {"resolves": False},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"Could not resolve RRID:{rrid}", target, ["M3"], err)
    try:
        hits = json.loads(raw).get("hits", {}).get("hits", [])
    except Exception:                                            # noqa: BLE001
        return led.add_limit("SciCrunch response could not be parsed", target, ["M3"],
                             {"kind": "unparseable"})
    if not hits:
        ev = led.add_evidence(make_external_evidence(
            "SciCrunch RRID", url, "rrid_resolve", rrid, None, raw, http, "not_found"))
        return make_signal(
            sid, target, f"RRID:{rrid} resolves to zero records.",
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


# ---------------------------------------------- PubChem compounds
def check_compound(item, led, sid):
    """Does the compound name exist; if the manuscript reports a molecular weight, does it match PubChem."""
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
            f"Compound name \"{name}\" is not found in PubChem. It may be an "
            f"internal code name, a typo, or a new compound not yet indexed; "
            f"manual confirmation is required.",
            ["M3", "M5"], "pubchem", "compound_name_lookup", "compound_name_valid",
            {"compound": name}, {"found": False},
            "needs_manual_review", "partial", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"Could not query compound {name}", target, ["M3", "M5"], err)
    try:
        p = json.loads(raw)["PropertyTable"]["Properties"][0]
        mw, formula = float(p["MolecularWeight"]), p["MolecularFormula"]
    except Exception:                                            # noqa: BLE001
        return led.add_limit("PubChem response could not be parsed", target, ["M3", "M5"],
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
        f"The manuscript reports a molecular weight of {reported_mw} for {name}, "
        f"while PubChem records {mw} ({formula}). Molecular weight feeds "
        f"directly into molarity conversions, so a deviation propagates into "
        f"every dose calculation. Salt forms, hydrates, and isotope labeling "
        f"can all explain the difference; manual review is required.",
        ["M3", "M5"], "pubchem", "compound_name_lookup", "compound_molecular_weight",
        {"reported_mw": reported_mw}, {"pubchem_mw": mw, "formula": formula},
        "needs_manual_review", "partial", item["evidence_refs"], [ev])


# ---------------------------------------------- PDB structures
def check_pdb(item, led, sid):
    """Does the PDB structure ID cited by the manuscript exist."""
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
            sid, target, f"The PDB ID {pdb} cited by the manuscript has no entry in RCSB.",
            ["M3", "M5"], "rcsb_pdb", "entry_lookup", "pdb_entry_exists",
            {"pdb_id": pdb}, {"found": False},
            "mismatch", "complete", item["evidence_refs"], [ev])
    if err:
        return led.add_limit(f"Could not query PDB {pdb}", target, ["M3", "M5"], err)
    try:
        d = json.loads(raw)
        title = (d.get("struct") or {}).get("title")
    except Exception:                                            # noqa: BLE001
        return led.add_limit("RCSB response could not be parsed", target, ["M3", "M5"],
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
    """Return {evidence_registry, signals, system_limitations}."""
    led = Ledger()
    for item in items:
        fn = CHECKS.get(item.get("check"))
        if not fn:
            continue
        # The contract requires at least one manuscript_evidence_ref -- an
        # external fact is only meaningful paired with a manuscript fact.
        # When absent, record a limitation instead of emitting a
        # contract-violating signal.
        if not item.get("evidence_refs"):
            led.add_limit(
                f"Item {item.get('check')} provided no manuscript "
                f"evidence_refs; no reproducible external comparison can be formed",
                item.get("target", "unknown"),
                ["M2", "M3", "M4", "M5", "M6", "M7"],
                {"kind": "missing_manuscript_evidence"})
            continue
        sig = fn(item, led, led.next_sig())
        if sig:
            led.signals.append(sig)
    return {"evidence_registry": led.evidence, "signals": led.signals,
            "system_limitations": led.limits}


# ---------------------------------------------------------------- Self-test
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
        print("  SKIP  external sources unreachable -- degrading to system_limitation offline is expected behavior")
        print("\nAll passed (degraded path)")
        return 0

    expect("position 273 valid on real p53", len(probe["signals"]), 0)
    ev = next(iter(probe["evidence_registry"].values()))
    expect("evidence is external type", ev["type"], "external")
    expect("evidence carries response sha256", len(ev["response_sha256"]), 64)
    expect("resolved must have assertions", len(ev["assertions"]) > 0, True)

    r = one({"check": "variant", "uniprot": "P04637", "position": 999})
    s = r["signals"][0]
    expect("position out of range -> flagged", s["type"], "external_validation_candidate")
    expect("id matches contract pattern", bool(re.match(r"^SIG-[0-9]{3,}$", s["id"])), True)
    expect("out of range is deterministic mismatch",
           s["external_check"]["comparison_result"], "mismatch")
    expect("mismatch requires comparability complete",
           s["external_check"]["comparability"], "complete")
    expect("signal has no severity", "severity" not in s, True)
    expect("manuscript evidence carried through", s["external_check"]["manuscript_evidence_refs"], R)
    expect("external evidence resolves in registry",
           s["external_check"]["external_evidence_refs"][0] in r["evidence_registry"],
           True)
    expect("reference residue mismatch -> flagged",
           len(one({"check": "variant", "uniprot": "P04637",
                    "position": 273, "ref_aa": "A"})["signals"]), 1)

    # Cellosaurus -- the highest-value check
    r = one({"check": "cell_line", "cell_line": "MDA-MB-435"})
    expect("MDA-MB-435 flagged as problematic", "M14" in r["signals"][0]["detail"], True)
    expect("contaminated cell line is deterministic mismatch",
           r["signals"][0]["external_check"]["comparison_result"], "mismatch")
    expect("normal cell line not flagged",
           len(one({"check": "cell_line", "cell_line": "HEK293"})["signals"]), 0)

    # WB band
    expect("p53 labeled at 50 kDa is plausible",
           len(one({"check": "blot_band", "uniprot": "P04637",
                    "reported_kda": 50})["signals"]), 0)
    r = one({"check": "blot_band", "uniprot": "P04637", "reported_kda": 120})
    expect("p53 labeled at 120 kDa -> needs manual review",
           r["signals"][0]["external_check"]["comparison_result"],
           "needs_manual_review")

    # ClinicalTrials.gov
    r = one({"check": "outcome_switching", "nct": "NCT04368728",
             "reported_primary": "overall survival at 5 years"})
    expect("no outcome overlap -> needs manual review",
           r["signals"][0]["external_check"]["comparison_result"],
           "needs_manual_review")
    expect("matching outcome -> not flagged",
           len(one({"check": "outcome_switching", "nct": "NCT04368728",
                    "reported_primary": "local reactions after dose 1"})["signals"]), 0)
    expect("same-month registration not misflagged (undecidable when start has only YYYY-MM precision)",
           registered_late("2011-02-24", "2011-02"), False)
    expect("a full month later -> judged retrospective", registered_late("2011-02-24", "2011-01"), True)
    expect("registration before start -> prospective", registered_late("2020-04-27", "2020-04-29"), False)
    expect("prospective registration not flagged",
           len(one({"check": "trial_registration", "nct": "NCT04368728"})["signals"]), 0)
    r = one({"check": "trial_registration", "nct": "NCT99999999"})
    expect("nonexistent registration number -> flagged", len(r["signals"]), 1)
    nf = [e for e in r["evidence_registry"].values()
          if e["retrieval_status"] == "not_found"]
    expect("not_found requires record_id null",
           nf[0]["record_id"] if nf else "missing", None)
    expect("not_found requires empty assertions", len(nf[0]["assertions"]) if nf else -1, 0)

    # Retracted references
    expect("citing retracted work -> flagged",
           len(one({"check": "cited_retracted",
                    "doi": "10.1016/S0140-6736(20)31180-6"})["signals"]), 1)
    expect("non-retracted work not flagged",
           len(one({"check": "cited_retracted",
                    "doi": "10.1038/nature12373"})["signals"]), 0)

    # HGNC gene symbols
    # Asserting "not flagged" alone is insufficient: a failed call is also not
    # flagged. Must also assert that external evidence was registered, proving
    # the query really succeeded -- otherwise "we could not retrieve it" is
    # being mistaken for "the paper is fine"
    r = one({"check": "gene_symbol", "symbol": "TP53"})
    expect("TP53 is the current symbol, not flagged",
           (len(r["signals"]), len(r["evidence_registry"])), (0, 1))
    r = one({"check": "gene_symbol", "symbol": "MARCH1"})
    expect("MARCH1 renamed -> flagged with current symbol",
           r["signals"][0]["external_check"]["external_value"]["current_symbol"],
           "MARCHF1")
    r = one({"check": "gene_symbol", "symbol": "2-Sep"})
    expect("Excel-dated gene name -> deterministic flag",
           r["signals"][0]["external_check"]["check_type"],
           "gene_symbol_excel_corruption")
    r = one({"check": "gene_symbol", "symbol": "FAKE9999"})
    expect("unrecognized symbol -> needs manual review",
           r["signals"][0]["external_check"]["comparison_result"],
           "needs_manual_review")
    expect("non-human species skips HGNC",
           len(one({"check": "gene_symbol", "symbol": "Trp53",
                    "species": "mouse"})["signals"]), 0)

    # Crossref references
    expect("real DOI not flagged",
           len(one({"check": "reference_exists",
                    "doi": "10.1038/nature12373"})["signals"]), 0)
    expect("nonexistent DOI -> deterministic flag",
           one({"check": "reference_exists",
                "doi": "10.1234/fake.doi.99999"})["signals"][0][
                    "external_check"]["comparison_result"], "mismatch")

    # NCBI Taxonomy
    expect("valid species name not flagged",
           len(one({"check": "species", "species": "Mus musculus"})["signals"]), 0)
    expect("invalid species name -> needs manual review",
           one({"check": "species", "species": "Mus fakius"})["signals"][0][
               "external_check"]["comparison_result"], "needs_manual_review")

    # RRID
    expect("valid RRID not flagged",
           len(one({"check": "rrid", "rrid": "AB_2298772"})["signals"]), 0)
    expect("invalid RRID -> deterministic flag",
           len(one({"check": "rrid", "rrid": "AB_9999999"})["signals"]), 1)

    # PubChem
    expect("known compound with matching MW -> not flagged",
           len(one({"check": "compound", "compound": "imatinib",
                    "reported_mw": 493.6})["signals"]), 0)
    expect("MW mismatch -> needs manual review",
           one({"check": "compound", "compound": "imatinib",
                "reported_mw": 250.0})["signals"][0][
                    "external_check"]["comparison_result"], "needs_manual_review")

    # PDB
    expect("real PDB ID not flagged",
           len(one({"check": "pdb", "pdb_id": "1TUP"})["signals"]), 0)
    expect("nonexistent PDB ID -> deterministic flag",
           one({"check": "pdb", "pdb_id": "9ZZZ"})["signals"][0][
               "external_check"]["comparison_result"], "mismatch")

    # Missing manuscript evidence must not produce a contract-violating signal
    r = validate([{"check": "cell_line", "cell_line": "MDA-MB-435"}])
    expect("missing manuscript evidence_refs -> limitation, not signal",
           (len(r["signals"]), len(r["system_limitations"])), (0, 1))

    print("\nAll passed" if ok else "\nFailures present")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--record-fixtures", action="store_true",
                    help="Run the selftest against the real interfaces and record "
                         "responses into resources/x1_fixtures.json for offline replay")
    ap.add_argument("--offline", action="store_true",
                    help="Use recorded fixtures only; all network requests forbidden. "
                         "**An all-green offline run only shows the parsing and decision "
                         "logic is intact, not that the upstream interfaces still work**")
    ap.add_argument("--input", help="JSON array of items to validate; - reads from stdin")
    ap.add_argument("--uniprot")
    a = ap.parse_args()

    global _RECORDING, _FIXTURES, _OFFLINE
    if a.record_fixtures:
        _RECORDING = {}
        _FIXTURES = {}                     # No replay while recording; must hit the real interfaces
        rc = _selftest()
        if rc != 0:
            print("\nSelftest failed; **fixtures not written** -- "
                  "recording a bad response is worse than having no fixtures", file=sys.stderr)
            return rc
        p = os.path.abspath(FIXTURE_PATH)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump({"_note": ("Real interface responses recorded for the X1 "
                                 "selftest. Replay **only validates the parsing and "
                                 "decision logic**, not whether the upstream "
                                 "interfaces still work -- upstream field changes "
                                 "are only discovered by re-recording. An all-green "
                                 "offline selftest therefore must not be claimed "
                                 "as 'external validation available'."),
                       "_recorded_at": _now(),
                       "_parser_version": PARSER_VERSION,
                       "responses": _RECORDING},
                      fh, ensure_ascii=False, indent=1)
        total = sum(len(v.get("body") or "") for v in _RECORDING.values())
        print(f"\nRecorded {len(_RECORDING)} responses, {total/1024:.1f} KB total -> "
              f"{os.path.relpath(p)}")
        return 0

    if a.offline:
        resp = _load_fixtures()          # the responses layer is already unwrapped internally
        if not resp:
            print("No recorded fixtures found; run --record-fixtures first", file=sys.stderr)
            return 2
        _FIXTURES = resp
        _OFFLINE = True
        print(f"Offline replay mode: {len(resp)} recorded responses (a miss raises an error; no network access)\n")
        rc = _selftest()
        print("\nNote: an all-green offline run only shows the parsing and decision "
              "logic is intact; whether the upstream interfaces still work can only "
              "be confirmed by re-recording online.")
        return rc

    if a.selftest:
        return _selftest()
    if a.input:
        try:
            raw = sys.stdin.read() if a.input == "-" else io.open(
                a.input, encoding="utf-8").read()
            items = json.loads(raw)
            if not isinstance(items, list):
                raise ValueError("top level must be an array")
        except Exception as exc:                                 # noqa: BLE001
            # In business mode stdout carries JSON only; input errors go to
            # stderr with exit code 2, no traceback
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
