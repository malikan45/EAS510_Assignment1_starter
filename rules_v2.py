"""EAS 510 - Project 1 - Phase 2: the V2 rule set.

Rules 1-3 are kept exactly as in `rules.py`. Your job is to ADD Rule 4 that
targets the systematic weakness you diagnosed from results_v1_hard.txt.

Constraint: the rules' `out_of` weights must still sum to 100 so the Final
Score stays on a /100 scale (the format validator enforces "Final Score:
<s>/100" equals the sum of the block's rule scores).

Example split that keeps the original spirit: Rules 1-3 -> 25/25/40 and
Rule 4 -> 10 (or trim the losers more aggressively).
"""
import cv2
import numpy as np

import rules

#: Import the original rules and append your new one.
RULES = (
    "rule1_metadata_v2",
    "rule2_histogram_v2",
    "rule3_template_v2",
    "rule4_edges",
)


def rule1_metadata_v2(target, input_path):
    out = rules.rule1_metadata(target, input_path).copy()
    out["score"] = int(round(out["score"] * 25 / out["out_of"]))
    out["out_of"] = 25
    return out


def rule2_histogram_v2(target, input_path):
    out = rules.rule2_histogram(target, input_path).copy()
    out["score"] = int(round(out["score"] * 25 / out["out_of"]))
    out["out_of"] = 25
    return out


def rule3_template_v2(target, input_path):
    return rules.rule3_template(target, input_path).copy()

def rule4_edges(target, input_path):
    out = {
        "rule": 4,
        "name": "Edges",
        "fired": False,
        "score": 0,
        "out_of": 10,
        "note": "Edge match 0.00",
        "metric": 0.0,
    }

    try:
        src = rules._arr(target["path"])
        suspect = rules._arr(input_path)

        if src is None or suspect is None:
            return out

        src_g = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        nd_g = cv2.cvtColor(suspect, cv2.COLOR_BGR2GRAY)

        src_g = rules._downscale(src_g, max_dim=320)
        nd_g = rules._downscale(nd_g, max_dim=320)

        src_edges = cv2.Canny(
            cv2.GaussianBlur(src_g, (3, 3), 0), 50, 150
        )

        if np.count_nonzero(src_edges) < 30:
            return out

        src_h, src_w = src_edges.shape
        nd_h, nd_w = nd_g.shape
        fit_scale = min(src_w / nd_w, src_h / nd_h)

        metric = 0.0

        for fraction in np.linspace(0.35, 1.0, 27):
            scale = fit_scale * float(fraction)
            width = max(1, round(nd_w * scale))
            height = max(1, round(nd_h * scale))

            if (
                width < 24
                or height < 24
                or width > src_w
                or height > src_h
            ):
                continue

            resized = cv2.resize(
                nd_g,
                (width, height),
                interpolation=cv2.INTER_AREA,
            )

            nd_edges = cv2.Canny(
                cv2.GaussianBlur(resized, (3, 3), 0), 50, 150
            )

            if (
                np.count_nonzero(nd_edges) < 30
                or float(nd_edges.std()) < 2.0
            ):
                continue

            res = cv2.matchTemplate(
                src_edges, nd_edges, cv2.TM_CCOEFF_NORMED
            )

            values = res[np.isfinite(res)]
            if values.size:
                metric = max(metric, float(values.max()))

        metric = max(0.0, min(1.0, metric))
        out["metric"] = round(metric, 3)
        out["note"] = f"Edge match {metric:.2f}"

        if metric >= 0.65:
            out["fired"] = True
            out["score"] = 10

    except cv2.error as error:
        out["note"] = f"OpenCV error {error.code}"

    return out
"""
def rule4_edges(target, input_path):
    TODO: replace with your Phase 2 rule that fixes the V1 weakness.

    Starter returns a no-op so the pipeline still runs before you implement it.
    Parity with rules.py rule dict: rule/name/fired/score/out_of/note/metric.
    return {
        "rule": 4,
        "name": "Edges",
        "fired": False,
        "score": 0,
        "out_of": 10,
        "note": "Not implemented",
        "metric": 0.0,
    }
"""
