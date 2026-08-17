#!/usr/bin/env python3
"""Within-paper figure integrity audit (phase-1 capability; local compute, no network).

Detects suspicious duplication and splicing traces **among the paper's own
figures**. This is the most prevalent form of misconduct in biomedical papers,
and a class of check a general-purpose LLM **cannot do at all** — it requires
pixel-level computation.

Three check classes
-------------------
1. `duplicated_region_candidate` — duplicated regions across figures or far apart within one figure
2. `splice_discontinuity_candidate` — vertical discontinuities in blot backgrounds (splicing traces)
3. `uniform_patch_candidate` — abnormally uniform patches (traces of erasing/cloning)

**Most important design constraint: never auto-conclude "fabrication".**
Every output of this module is a `candidate`, `severity_hint` is always
`null`, routing goes to M5, and human review is **mandatory**. Image
duplication has many legitimate explanations: the same control image reused
across figures, templated schematics, magnified insets, montage layouts.
Automating that judgment into an accusation is the highest-risk action in
this project, so the contract forbids it.

False-positive guards
---------------------
- **Variance gating**: blank/background blocks (too-low local variance) are
  always skipped — otherwise every figure's white background would match
  every other, producing mountains of garbage.
- **Two-stage decision**: bucket by exact dHash first, then verify precisely
  with the Pearson correlation of actual pixels; only r >= 0.98 counts as a
  candidate.
- **Same-figure neighbor exclusion**: blocks too close together within one
  figure are not duplicates (that is texture continuity).
- **Missing dependencies never crash**: when numpy/PIL are unavailable the
  output is a `system_limitation`, not an error.

Known limitations (must be stated honestly — readers must not assume this is complete forensics)
------------------------------------------------------------------------------------------------
- **Only duplicates whose relative offset is an integer multiple of `STRIDE`
  are detected.** The method cuts blocks on a fixed grid and buckets by exact
  dHash, so copy-paste at arbitrary offsets can be missed. Offset-invariant
  detection needs keypoint matching (ORB/SIFT etc.) and is future work.
- **Rotated, scaled, or mirrored duplicates are not detected**; that likewise
  needs keypoint matching.
- **A miss is not exoneration**: silence from this module only means these
  three patterns did not fire; it is not a conclusion that "the figures are
  fine". Reports must phrase it that way.

Command line:
    python3 <skill dir>/scripts/figure_integrity_audit.py --selftest
    python3 <skill dir>/scripts/figure_integrity_audit.py --input <image dir>
"""

import argparse
import json
import os
import sys

RULE_VERSION = "2026-08-07"


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)

try:
    import numpy as np
    from PIL import Image
    DEPS_OK = True
    DEPS_ERR = None
except Exception as exc:                                    # pragma: no cover
    DEPS_OK = False
    DEPS_ERR = str(exc)

# ---------------------------------------------------------------- parameters
BLOCK = 64          # block side length (pixels)
STRIDE = 16         # sliding-window stride. See "Known limitations" above: only
                    # duplicates offset by integer multiples of the stride are detectable
MIN_STD = 12.0      # minimum block grayscale std; below this it is blank/background, skip
MIN_ENTROPY = 4.0   # minimum block grayscale entropy (bits). Line art/axes/grids have
                    # very low entropy (~1-2); real imagery such as micrographs/blots/
                    # scatter has high entropy (~6-7). Without this gate, repeated line
                    # elements in charts would yield masses of r=1.0 fake duplicates.
CORR_MIN = 0.98     # minimum Pearson correlation for precise verification
MIN_SELF_DIST = 96  # minimum center distance between two blocks in the same figure;
                    # closer pairs do not count as duplicates
MAX_SIDE = 1200     # downscale oversized images first to bound compute


def _system_limitation(detail, sid="SYS-001", category="figure_unreadable",
                       recommended_action="Re-run the figure integrity audit in an environment with numpy and Pillow"):
    return {
        "id": sid,
        "category": category,
        "impact": detail,
        "affected_modules": ["M5"],
        "affected_targets": [],
        "affected_fields": [],
        "evidence_refs": [],
        "recommended_action": recommended_action,
        "produced_by": "stage_3",
    }


def _sig(sid, target, detail, extra):
    """Figure-audit signal. severity_hint is always null — the contract forbids automated verdicts."""
    return {
        "id": sid,
        "type": "figure_integrity_candidate",
        "target": target,
        "detail": detail,
        "observation_refs": [],
        "evidence_refs": [],
        "routed_to": ["M5"],
        "produced_by": "stage_3",
        "image_audit": dict(
            extra,
            rule_version=RULE_VERSION,
            candidate=True,
            severity_hint=None,
            manual_review_required=True,
        ),
    }


# ---------------------------------------------------------------- image loading
def load_gray(path):
    im = Image.open(path).convert("L")
    w, h = im.size
    if max(w, h) > MAX_SIDE:
        scale = MAX_SIDE / float(max(w, h))
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
    return np.asarray(im, dtype=np.float64)


def dhash(block):
    """Difference hash: shrink to 9x8, compare horizontally adjacent pixels, yielding 64 bits."""
    im = Image.fromarray(block.astype(np.uint8)).resize((9, 8))
    a = np.asarray(im, dtype=np.int16)
    bits = a[:, 1:] > a[:, :-1]
    out = 0
    for b in bits.flatten():
        out = (out << 1) | int(b)
    return out


def popcount(x):
    return bin(x).count("1")


def shannon_entropy(block):
    """Shannon entropy of the 8-bit grayscale histogram. Line art ~1-2 bits, real imagery ~6-7 bits."""
    hist = np.bincount(block.astype(np.uint8).flatten(), minlength=256).astype(np.float64)
    total = hist.sum()
    if total <= 0:
        return 0.0
    p = hist / total
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def iter_blocks(arr, name):
    h, w = arr.shape
    for y in range(0, max(1, h - BLOCK + 1), STRIDE):
        for x in range(0, max(1, w - BLOCK + 1), STRIDE):
            blk = arr[y:y + BLOCK, x:x + BLOCK]
            if blk.shape != (BLOCK, BLOCK):
                continue
            sd = float(blk.std())
            if sd < MIN_STD:          # blank/background, skip
                continue
            ent = shannon_entropy(blk)
            if ent < MIN_ENTROPY:     # line art/axes/grid, skip
                continue
            yield {"image": name, "y": y, "x": x, "std": sd, "entropy": ent,
                   "hash": dhash(blk), "pixels": blk}


def pearson(a, b):
    av, bv = a.flatten(), b.flatten()
    av = av - av.mean()
    bv = bv - bv.mean()
    denom = np.sqrt((av * av).sum() * (bv * bv).sum())
    return float((av * bv).sum() / denom) if denom > 0 else 0.0


# ---------------------------------------------------------------- 1 duplicated regions
def find_duplicate_regions(images, max_signals=20):
    """images: {name: gray_array}. Returns a list of candidate duplicated-region signals."""
    blocks = []
    for name, arr in images.items():
        blocks.extend(iter_blocks(arr, name))

    # Bucket by exact dHash: pixel-level copy-paste produces identical hashes,
    # so bucketing is an effective O(n) prefilter that avoids O(n^2) pairwise
    # comparison.
    buckets = {}
    for b in blocks:
        buckets.setdefault(b["hash"], []).append(b)

    # Collect all matches first, then aggregate per figure pair into a single
    # signal — one duplicated area hits several adjacent grid blocks, and
    # reporting every pair would drown the real signal.
    pairs = []
    for _, group in buckets.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                b1, b2 = group[i], group[j]
                if b1["image"] == b2["image"]:
                    dy = abs(b1["y"] - b2["y"])
                    dx = abs(b1["x"] - b2["x"])
                    if (dy * dy + dx * dx) ** 0.5 < MIN_SELF_DIST:
                        continue
                r = pearson(b1["pixels"], b2["pixels"])
                if r < CORR_MIN:
                    continue
                pairs.append((b1, b2, r))

    by_pair = {}
    for b1, b2, r in pairs:
        key = tuple(sorted([b1["image"], b2["image"]]))
        by_pair.setdefault(key, []).append((b1, b2, r))

    sigs = []
    for n, (key, matches) in enumerate(sorted(by_pair.items()), 1):
        if n > max_signals:
            break
        same = key[0] == key[1]
        examples = [
            {"a": [m[0]["x"], m[0]["y"]], "b": [m[1]["x"], m[1]["y"]],
             "r": round(m[2], 4)} for m in matches[:5]
        ]
        best = max(m[2] for m in matches)
        sigs.append(_sig(
            f"SIG-{n:03d}",
            f"figure_integrity.{key[0]}",
            f"Detected {len(matches)} candidate duplicated blocks ({BLOCK}x{BLOCK}), "
            f"{'long-distance duplication within one figure' if same else f'cross-figure duplication: {key[0]} <-> {key[1]}'}, "
            f"max pixel correlation r={best:.4f}, first locations {examples[:3]}. "
            f"**Candidate only**: reuse of the same control image, templated schematics, "
            f"and magnified insets all produce legitimate duplication — a human must "
            f"check the original figures before judging.",
            {"check": "duplicated_region_candidate",
             "image_a": key[0], "image_b": key[1], "same_image": same,
             "match_count": len(matches), "max_correlation": round(best, 4),
             "examples": examples}))
    return sigs


# ---------------------------------------------------------------- 2 splicing traces
def find_splice_discontinuity(name, arr, z_threshold=6.0):
    """Abrupt changes in column-wise background statistics — the classic trace of blot splicing."""
    if arr.shape[1] < 40:
        return []
    col_med = np.median(arr, axis=0)
    d = np.abs(np.diff(col_med))
    if d.size < 8:
        return []
    mad = np.median(np.abs(d - np.median(d)))
    if mad < 1e-6:
        return []
    z = (d - np.median(d)) / (1.4826 * mad)
    peaks = np.where(z > z_threshold)[0]
    # Ignore the outer 5% margins (figure borders)
    margin = max(2, int(arr.shape[1] * 0.05))
    peaks = [int(p) for p in peaks if margin < p < arr.shape[1] - margin]
    if not peaks:
        return []
    return [_sig(
        "SIG-001",
        f"figure_integrity.{name}",
        f"Detected {len(peaks)} column-wise background discontinuities (x~{peaks[:5]}), "
        f"robust z-score above {z_threshold}. Blot-type images often show such "
        f"discontinuities at splice boundaries. **Candidate only**: lane spacing and the "
        f"figure's own panel layout produce the same signal — a human must check the "
        f"original figure.",
        {"check": "splice_discontinuity_candidate", "image": name,
         "columns": peaks[:20], "z_threshold": z_threshold})]


# ---------------------------------------------------------------- 3 abnormally uniform patches
def find_uniform_patches(name, arr, min_run=3):
    """Several consecutive blocks with near-zero variance — possible erasing or clone fill."""
    h, w = arr.shape
    flat = []
    for y in range(0, max(1, h - BLOCK + 1), BLOCK):
        for x in range(0, max(1, w - BLOCK + 1), BLOCK):
            blk = arr[y:y + BLOCK, x:x + BLOCK]
            if blk.shape == (BLOCK, BLOCK) and blk.std() < 0.5 and 20 < blk.mean() < 235:
                flat.append([int(x), int(y)])
    if len(flat) < min_run:
        return []
    return [_sig(
        "SIG-001",
        f"figure_integrity.{name}",
        f"Detected {len(flat)} nearly perfectly uniform non-extreme blocks (grayscale std "
        f"<0.5 and neither pure black nor pure white). **Candidate only**: solid-fill "
        f"schematic elements and legend backgrounds also hit this — a human must check.",
        {"check": "uniform_patch_candidate", "image": name,
         "patches": flat[:20], "patch_count": len(flat)})]


# ---------------------------------------------------------------- main entry
def audit_figures(paths):
    """paths: list of image file paths. Returns (signals, system_limitations)."""
    if not DEPS_OK:
        return [], [_system_limitation(
            f"The figure integrity audit requires numpy and Pillow, unavailable in this environment: {DEPS_ERR}")]

    if not isinstance(paths, (list, tuple)):
        raise ValueError("paths must be an array of image paths")

    images, limits = {}, []
    for p in paths:
        if not isinstance(p, (str, os.PathLike)):
            raise ValueError("every image path must be a string or PathLike")
        try:
            name = os.path.basename(os.fspath(p))
            if name in images:
                limits.append(_system_limitation(
                    f"Multiple input images share the name {name!r}; a unique asset mapping "
                    f"cannot be built, so duplicate basenames were skipped.",
                    sid=f"SYS-{len(limits) + 1:03d}", category="parse_failed",
                    recommended_action="Assign unique filenames or asset ids to the images and re-run"))
                continue
            images[name] = load_gray(p)
        except Exception as exc:
            limits.append(_system_limitation(
                f"Could not read image {os.path.basename(p)}: {exc}",
                sid=f"SYS-{len(limits) + 1:03d}"))

    if not images:
        return [], limits

    sigs = find_duplicate_regions(images)
    for name, arr in images.items():
        sigs.extend(find_splice_discontinuity(name, arr))
        sigs.extend(find_uniform_patches(name, arr))
    # Each detector can be called independently, so each numbers from SIG-001;
    # the aggregate entry point must renumber into report-unique, schema-valid
    # numeric ids.
    for i, sig in enumerate(sigs, 1):
        sig["id"] = f"SIG-{i:03d}"
    return sigs, limits


# ---------------------------------------------------------------- selftest
def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    if not DEPS_OK:
        print(f"  SKIP  numpy/PIL unavailable: {DEPS_ERR}")
        sigs, lims = audit_figures(["nonexistent.png"])
        expect("missing dependencies -> system_limitation, not a crash", len(lims) >= 1, True)
        print("\nAll passed (degraded path)")
        return 0

    rng = np.random.default_rng(42)

    # --- Build an image containing a genuine duplicated block ---
    # The planted location must fall on the stride grid: the method cuts blocks
    # on a grid and only detects duplicates offset by integer multiples of
    # STRIDE (see "Known limitations" above).
    base = rng.integers(0, 255, size=(256, 256)).astype(np.float64)
    patch = base[0:64, 0:64].copy()
    base[128:192, 128:192] = patch          # offset (128,128) = integer multiple of STRIDE
    imgs = {"dup.png": base}
    sigs = find_duplicate_regions(imgs)
    dup = [s for s in sigs if s["image_audit"]["check"] == "duplicated_region_candidate"]
    expect("planted duplicated block detected", len(dup) >= 1, True)
    if dup:
        expect("duplicate candidate has candidate=True", dup[0]["image_audit"]["candidate"], True)
        expect("duplicate candidate carries no severity", dup[0]["image_audit"]["severity_hint"], None)
        expect("human review mandatory", dup[0]["image_audit"]["manual_review_required"], True)
        expect("routed to M5", dup[0]["routed_to"], ["M5"])

    # --- Pure noise images must not false-match each other ---
    noise = {"a.png": rng.integers(0, 255, size=(256, 256)).astype(np.float64),
             "b.png": rng.integers(0, 255, size=(256, 256)).astype(np.float64)}
    s2 = find_duplicate_regions(noise)
    expect("two independent noise images have no duplicate false positives",
           len([x for x in s2 if x["image_audit"]["check"] == "duplicated_region_candidate"]), 0)

    # --- All-white backgrounds must never match each other (variance gate) ---
    blank = {"w1.png": np.full((256, 256), 255.0), "w2.png": np.full((256, 256), 255.0)}
    s3 = find_duplicate_regions(blank)
    expect("pure white background blocked by the variance gate", len(s3), 0)

    # --- Splicing traces ---
    spliced = rng.normal(120, 6, size=(128, 256))
    spliced[:, 128:] += 60                  # right half uniformly brighter = splice
    s4 = find_splice_discontinuity("blot.png", spliced)
    expect("planted splice discontinuity detected", len(s4) >= 1, True)
    smooth = rng.normal(120, 6, size=(128, 256))
    s5 = find_splice_discontinuity("smooth.png", smooth)
    expect("smooth background has no splice false positive", len(s5), 0)

    # --- Contract ---
    allsig = dup + s4
    expect("all signals share one type",
           {x["type"] for x in allsig}, {"figure_integrity_candidate"})
    expect("no signal carries severity", all("severity" not in x for x in allsig), True)
    expect("figure signal ids match the schema",
           all(__import__("re").match(r"^SIG-[0-9]{3,}$", x["id"]) for x in allsig), True)
    lim = _system_limitation("test")
    expect("figure system_limitation id matches the schema",
           bool(__import__("re").match(r"^SYS-[0-9]{3,}$", lim["id"])), True)

    print("\nAll passed" if ok else "\nFailures present")
    return 0 if ok else 1


def scan_directory(root):
    """Scan a directory and return a JSON-serializable result; controlled error when missing or not a directory."""
    if not isinstance(root, (str, os.PathLike)) or not os.path.isdir(root):
        raise ValueError(f"image input directory does not exist or is not a directory: {root!r}")
    paths = []
    for dirpath, _, files in os.walk(root):
        for f in sorted(files):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                paths.append(os.path.join(dirpath, f))
    sigs, lims = audit_figures(paths)
    from collections import Counter
    c = Counter(s["image_audit"]["check"] for s in sigs)
    return {
        "images_scanned": len(paths),
        "signals": sigs,
        "system_limitations": lims,
        "summary": {"signal_count": len(sigs), "by_check": dict(c),
                    "system_limitation_count": len(lims)},
    }


def _main(argv=None):
    parser = _JsonArgumentParser(description="Within-paper figure integrity candidate audit")
    parser.add_argument("legacy_input", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("--input", metavar="DIR", help="image directory to scan recursively")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    root = args.input or args.legacy_input
    if not root:
        parser.error("--input DIR is required (or use --selftest)")
    try:
        result = scan_directory(root)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "detail": str(exc)}},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
