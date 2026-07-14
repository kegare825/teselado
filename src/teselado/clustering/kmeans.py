"""K-Means clustering with a configurable distance metric."""

from __future__ import annotations

from typing import Callable

import numpy as np


class KMeans:
    """K-Means clustering with a configurable distance metric."""

    def __init__(
        self,
        k: int = 3,
        tol: float = 0.001,
        max_iter: int = 3000,
        metric: Callable[[np.ndarray, np.ndarray], float] | None = None,
    ) -> None:
        self.k = k
        self.tol = tol
        self.max_iter = max_iter
        self.metric = metric or (lambda c, e: 1.3 * float(np.linalg.norm(e - c)))
        self.centroids_: dict[int, np.ndarray] = {}
        self.classifications_: dict[int, list[np.ndarray]] = {}

    def fit(self, data: np.ndarray) -> "KMeans":
        """Compute k-means clustering."""
        data = np.asarray(data, dtype=float)
        self.centroids_ = {i: data[i] for i in range(self.k)}

        for _ in range(self.max_iter):
            classifications: dict[int, list[np.ndarray]] = {j: [] for j in range(self.k)}

            for point in data:
                distances = [
                    self.metric(self.centroids_[centroid], point)
                    for centroid in self.centroids_
                ]
                label = int(np.argmin(distances))
                classifications[label].append(point)

            prev_centroids = self.centroids_.copy()

            for label, points in classifications.items():
                if points:
                    self.centroids_[label] = np.average(points, axis=0)

            optimized = True
            for label in self.centroids_:
                original = prev_centroids[label]
                current = self.centroids_[label]
                if np.any(original != 0) and np.sum(
                    (current - original) / original * 100.0
                ) > self.tol:
                    optimized = False

            if optimized:
                break

        self.classifications_ = classifications
        return self

    def predict(self, data: np.ndarray) -> np.ndarray | int:
        """Assign cluster labels to one or many points."""
        data = np.asarray(data, dtype=float)
        if data.ndim == 1:
            distances = [
                float(np.linalg.norm(data - self.centroids_[centroid]))
                for centroid in self.centroids_
            ]
            return int(np.argmin(distances))

        labels = np.empty(len(data), dtype=int)
        for idx, point in enumerate(data):
            labels[idx] = self.predict(point)
        return labels
