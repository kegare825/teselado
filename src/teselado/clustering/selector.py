"""Automatic selection of the number of clusters."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from teselado.clustering.kmeans import KMeans


def _inertia(model: Any, points: np.ndarray) -> float:
    total = 0.0
    labels = model.predict(points)
    for label in range(model.k):
        cluster_points = points[labels == label]
        if len(cluster_points) == 0:
            continue
        centroid = model.centroids_[label]
        total += float(np.sum((cluster_points - centroid) ** 2))
    return total


def select_k(
    points: np.ndarray,
    k_min: int = 3,
    k_max: int = 8,
    model_factory: Callable[[int], Any] | None = None,
) -> int:
    """
    Pick k using a simple elbow heuristic on within-cluster sum of squares.

    `model_factory` builds an unfitted model for a given k (default: `KMeans`).
    Any model exposing `fit` / `predict` / `centroids_` works, so the same
    heuristic is reused for `FuzzyCMeans` (via its hard, argmax-membership labels).
    """
    if k_min >= k_max:
        raise ValueError("k_min must be less than k_max")

    factory = model_factory or (lambda k: KMeans(k=k))
    points = np.asarray(points, dtype=float)
    k_values = list(range(k_min, k_max))
    inertias = []

    for k in k_values:
        model = factory(k).fit(points)
        inertias.append(_inertia(model, points))

    # Largest relative drop in inertia marks the elbow.
    improvements = [
        (inertias[i - 1] - inertias[i]) / inertias[i - 1] if inertias[i - 1] else 0.0
        for i in range(1, len(inertias))
    ]

    if not improvements:
        return k_min

    elbow_idx = int(np.argmax(improvements))
    return k_values[elbow_idx]
