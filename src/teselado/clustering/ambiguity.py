"""Boundary ambiguity metrics for fuzzy clustering assignments."""

from __future__ import annotations

import numpy as np


def compute_ambiguity(membership: np.ndarray, boundary_threshold: float = 0.2) -> dict:
    """
    Quantify how many points sit near a zone boundary.

    A point is "ambiguous" when the gap between its top-1 and top-2 membership
    degree is below `boundary_threshold` — i.e. it could plausibly be served
    from either of its two closest zones. This is the concrete, measurable
    payoff of fuzzy clustering over hard K-Means: hard assignment cannot
    express this at all.
    """
    membership = np.asarray(membership, dtype=float)
    if membership.ndim != 2 or membership.shape[0] == 0:
        return {
            "mean_confidence": 0.0,
            "mean_margin": 0.0,
            "boundary_point_ratio": 0.0,
            "boundary_threshold": boundary_threshold,
        }

    sorted_membership = np.sort(membership, axis=1)[:, ::-1]
    top1 = sorted_membership[:, 0]
    top2 = sorted_membership[:, 1] if sorted_membership.shape[1] > 1 else np.zeros_like(top1)
    margin = top1 - top2

    return {
        "mean_confidence": round(float(np.mean(top1)), 3),
        "mean_margin": round(float(np.mean(margin)), 3),
        "boundary_point_ratio": round(float(np.mean(margin < boundary_threshold)), 3),
        "boundary_threshold": boundary_threshold,
    }
