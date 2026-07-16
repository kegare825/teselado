"""
Fuzzy C-Means with a K-Means-compatible interface.

Unlike hard K-Means, every point keeps a *degree of membership* to every zone
instead of a single all-or-nothing label. This models delivery zones the way
they actually behave: an order placed near a boundary can realistically be
served from either adjacent zone, and the membership gap is a direct,
quantifiable proxy for that ambiguity — see `teselado.clustering.ambiguity`.

The class implements the same `k` / `centroids_` / `fit` / `predict` contract
as `teselado.clustering.kmeans.KMeans`, so it is a drop-in replacement inside
`tessellate()` and the pipeline.
"""

from __future__ import annotations

import numpy as np
from pyclustering.cluster.fcm import fcm


def _kmeans_plusplus_init(data: np.ndarray, k: int, seed: int) -> np.ndarray:
    """
    k-means++ seeding, implemented locally in plain numpy.

    pyclustering ships its own `kmeans_plusplus_initializer`, but it calls the
    long-removed `numpy.warnings` alias and hard-crashes on numpy>=2.0 — this
    tiny reimplementation avoids that broken, unmaintained dependency path.
    """
    rng = np.random.default_rng(seed)
    n = len(data)
    centers = [data[rng.integers(n)]]

    for _ in range(1, k):
        nearest_sq_dist = np.min(
            [np.sum((data - c) ** 2, axis=1) for c in centers], axis=0
        )
        total = nearest_sq_dist.sum()
        probabilities = nearest_sq_dist / total if total > 0 else np.full(n, 1.0 / n)
        centers.append(data[rng.choice(n, p=probabilities)])

    return np.asarray(centers, dtype=float)


class FuzzyCMeans:
    """Fuzzy C-Means clustering exposing the same interface as `KMeans`."""

    def __init__(
        self,
        k: int = 3,
        m: float = 2.0,
        tolerance: float = 0.001,
        itermax: int = 200,
        seed: int = 42,
    ) -> None:
        if m <= 1:
            raise ValueError("m (fuzzifier) must be greater than 1")

        self.k = k
        self.m = m
        self.tolerance = tolerance
        self.itermax = itermax
        self.seed = seed
        self.centroids_: dict[int, np.ndarray] = {}
        self.membership_: np.ndarray | None = None
        self._degree = 2.0 / (m - 1)

    def fit(self, data: np.ndarray) -> "FuzzyCMeans":
        """Compute fuzzy c-means clustering."""
        data = np.asarray(data, dtype=float)
        initial_centers = _kmeans_plusplus_init(data, self.k, self.seed)
        instance = fcm(
            data.tolist(),
            initial_centers,
            m=self.m,
            tolerance=self.tolerance,
            itermax=self.itermax,
        )
        instance.process()

        centers = np.asarray(instance.get_centers(), dtype=float)
        self.centroids_ = {i: centers[i] for i in range(self.k)}
        self.membership_ = np.asarray(instance.get_membership(), dtype=float)
        return self

    def membership(self, data: np.ndarray) -> np.ndarray:
        """
        Compute fuzzy membership degrees for arbitrary points against the fitted centers.

        Returns an (n_points, k) matrix using the standard FCM membership formula, so it
        can be evaluated on out-of-sample points (e.g. the tessellation grid) rather than
        only on the points used during `fit`.
        """
        points = np.atleast_2d(np.asarray(data, dtype=float))
        centers = np.asarray([self.centroids_[i] for i in range(self.k)], dtype=float)

        dists = np.linalg.norm(points[:, None, :] - centers[None, :, :], axis=2)
        dists = np.where(dists == 0, 1e-12, dists)

        ratio = dists[:, :, None] / dists[:, None, :]
        return 1.0 / np.sum(ratio**self._degree, axis=2)

    def predict(self, data: np.ndarray) -> np.ndarray | int:
        """Return the hard (argmax-membership) label for one or many points."""
        single = np.asarray(data).ndim == 1
        labels = np.argmax(self.membership(data), axis=1)
        return int(labels[0]) if single else labels
