"""EAS 510 - Project 1: Rule functions for the Digital Forensics Apprentice.

Each rule compares one suspect image against one registered original and
returns a dict:

    {
        "rule": 1,
        "name": "Metadata",
        "fired": bool,          # True if the rule found supporting evidence
        "score": int,           # points awarded out of "out_of"
        "out_of": int,
        "note": "Size ratio 0.85",   # short human-readable metric
        "metric": 0.85,              # raw similarity measure in [0, 1]
    }

The points budgets are fixed by the assignment: Rule 1 = 30, Rule 2 = 30,
Rule 3 = 40. The detector sums them into a 0-100 confidence score.

These starter implementations are deliberately WEAK baselines (they hinge on
simple thresholds). Improving them is the assignment.

Reads are cached per path so one suspect against many originals does not
re-decode images needlessly.
"""

import os
from functools import lru_cache

import numpy as np
import cv2
from PIL import Image

#: Rule names used by SimpleDetector.evaluate() (V1).
RULES = ("rule1_metadata", "rule2_histogram", "rule3_template")


@lru_cache(maxsize=256)
def _arr(path):
    return cv2.imread(path)


@lru_cache(maxsize=256)
def _hist(path):
    img = _arr(path)
    if img is None:
        return None
    hists = [cv2.calcHist([img], [i], None, [32], [0, 256]) for i in range(3)]
    hist_all = np.concatenate(hists).ravel().astype(np.float32)
    cv2.normalize(hist_all, hist_all)
    return hist_all


def _downscale(img, max_dim=512):
    """Fit an image into `max_dim` before expensive cv2 work."""
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    return img


@lru_cache(maxsize=256)
def _gray(path):
    img = _arr(path)
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
"""    return _downscale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))"""



@lru_cache(maxsize=256)
def _size(path):
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None


def rule1_metadata(target, input_path):
    """File size + dimensions. Compression and crops leave size fingerprints."""
    out = {"rule": 1, "name": "Metadata", "fired": False, "score": 0,
           "out_of": 30, "note": "Size ratio 0.00", "metric": 0.0}
    try:
        src_size = os.path.getsize(target["path"])
        in_size = os.path.getsize(input_path)
        src_w, src_h = _size(target["path"]) or (0, 0)
        in_w, in_h = _size(input_path) or (0, 0)
        size_ratio = min(src_size, in_size) / max(src_size, in_size)
        area_kept = (in_w * in_h) / max(1, src_w * src_h)
        metric = 0.5 * size_ratio + 0.5 * min(1.0, area_kept)
        out["metric"] = round(max(0.0, min(1.0, metric)), 3)
        out["note"] = f"Size ratio {out['metric']:.2f}"
        if out["metric"] >= 0.6:
            out["fired"] = True
            out["score"] = int(round(out["out_of"] * out["metric"]))
    except Exception:
        pass
    return out


def rule2_histogram(target, input_path):
    """Color histogram correlation. Robust to crops and spatial changes."""
    out = {"rule": 2, "name": "Histogram", "fired": False, "score": 0,
           "out_of": 30, "note": "Correlation 0.00", "metric": 0.0}
    try:
        hs, hi = _hist(target["path"]), _hist(input_path)
        if hs is None or hi is None:
            return out
        corr = float(cv2.compareHist(hs, hi, cv2.HISTCMP_CORREL))
        out["metric"] = round(max(0.0, min(1.0, corr)), 3)
        out["note"] = f"Correlation {out['metric']:.2f}"
        if out["metric"] >= 0.5:
            out["fired"] = True
            out["score"] = int(round(out["out_of"] * out["metric"]))
    except Exception:
        pass
    return out

    """Template matching. Detects when the suspect is contained in the original.

    cv2.matchTemplate needs the template (suspect) smaller than the target
    (original); on rotated/resized suspects this rule degrades fast. Fixing
    that becomes Rule 4 territory.
    """
def rule3_template(target, input_path):
    out = {"rule": 3, "name": "Template", "fired": False, "score": 0,
           "out_of": 40, "note": "Match score 0.00", "metric": 0.0}
    try:
        src_g = _gray(target["path"])
        nd_g = _gray(input_path)
        if src_g is None or nd_g is None:
            return out

        src_h, src_w = src_g.shape
        nd_h, nd_w = nd_g.shape

        metric = 0.0
        src_small = _downscale(src_g)
        scale = src_small.shape[1] / src_w

        if nd_h <= src_h and nd_w <= src_w:
            crop_small = cv2.resize(
                nd_g,
                (max(1, round(nd_w * scale)),
                 max(1, round(nd_h * scale))),
                interpolation=cv2.INTER_AREA,
            )

            if (
                min(crop_small.shape) >= 16
                and crop_small.shape[0] <= src_small.shape[0]
                and crop_small.shape[1] <= src_small.shape[1]
                and float(crop_small.std()) >= 2.0
                and float(src_small.std()) >= 2.0
            ):
                res = cv2.matchTemplate(
                    src_small, crop_small, cv2.TM_CCOEFF_NORMED
                )
                values = res[np.isfinite(res)]
                if values.size:
                    metric = max(metric, float(values.max()))

        src_ratio = src_w / src_h
        nd_ratio = nd_w / nd_h
        ratio_match = min(src_ratio, nd_ratio) / max(src_ratio, nd_ratio)

        if ratio_match >= 0.98:
            resized = cv2.resize(
                nd_g,
                (src_small.shape[1], src_small.shape[0]),
                interpolation=cv2.INTER_AREA,
            )

            if (
                min(src_small.shape) >= 16
                and float(resized.std()) >= 2.0
                and float(src_small.std()) >= 2.0
            ):
                res = cv2.matchTemplate(
                    src_small, resized, cv2.TM_CCOEFF_NORMED
                )
                values = res[np.isfinite(res)]
                if values.size:
                    metric = max(metric, float(values.max()))

        metric = max(0.0, min(1.0, metric))
        out["metric"] = round(metric, 3)
        out["note"] = f"Match score {out['metric']:.2f}"

        if metric >= 0.80:
            out["fired"] = True
            out["score"] = int(round(out["out_of"] * metric))
    except Exception:
        pass
    return out
