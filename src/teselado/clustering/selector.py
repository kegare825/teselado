"""Automatic selection of the number of clusters."""

from __future__ import annotations

import numpy as np

from teselado.clustering.kmeans import KMeans


def _inertia(model: KMeans, points: np.ndarray) -> float:
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
) -> int:
    """
    Pick k using a simple elbow heuristic on within-cluster sum of squares.
    """
    if k_min >= k_max:
        raise ValueError("k_min must be less than k_max")

    points = np.asarray(points, dtype=float)
    k_values = list(range(k_min, k_max))
    inertias = []

    for k in k_values:
        model = KMeans(k=k).fit(points)
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
