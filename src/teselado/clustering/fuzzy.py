"""Fuzzy C-Means clustering and tessellation helpers."""

from __future__ import annotations

import numpy as np
from pyclustering.cluster.center_initializer import kmeans_plusplus_initializer
from pyclustering.cluster.fcm import fcm
from pyclustering.cluster.kmeans import kmeans

from teselado.geo.bounds import bounding_box


class Clustered:
    """Evaluate fuzzy clusters across a range of k values."""

    def __init__(self, start: int = 3, end: int = 8) -> None:
        self.start = start
        self.end = end
        self.points: list | np.ndarray | None = None
        self.results: list = []
        self._kmeans_instance = None

    def _kmeans(self, points, n_clusters: int = 10):
        initial_centers = kmeans_plusplus_initializer(points, n_clusters).initialize()
        instance = kmeans(points, initial_centers)
        instance.process()
        return instance.get_clusters(), instance.get_centers(), instance

    def _cmeans(self, points, n_clusters: int):
        initial_centers = kmeans_plusplus_initializer(
            points,
            n_clusters,
            kmeans_plusplus_initializer.FARTHEST_CENTER_CANDIDATE,
        ).initialize()
        fcm_instance = fcm(points, initial_centers)
        fcm_instance.process()
        return (
            fcm_instance.get_clusters(),
            fcm_instance.get_centers(),
            fcm_instance.get_membership(),
        )

    def get_clusters(self, points):
        """Return fuzzy clustering results for each k in [start, end)."""
        self.points = points
        self.results = [self._cmeans(points, i) for i in range(self.start, self.end)]
        return self.results

    def tessellate(self, points, kmeans_instance=None, n_centers: int | None = None):
        """
        Approximate Voronoi tessellation via grid sampling and convex hulls.

        Returns hull coordinate sequences per cluster. Full GeoJSON export lands in Phase 2.
        """
        if kmeans_instance is None:
            _, centers, kmeans_instance = self._kmeans(points, n_centers or self.start)
        else:
            centers = kmeans_instance.get_centers()

        self._kmeans_instance = kmeans_instance
        bbox = bounding_box(points)
        min_x, min_y = bbox[0]
        max_x, max_y = bbox[2]

        lat_sample = np.arange(min_y, max_y, 0.001)
        lon_sample = np.arange(min_x, max_x, 0.001)
        sampling_space = np.asarray(
            [[x, y] for x in lat_sample for y in lon_sample],
            dtype=np.float32,
        )

        prediction = kmeans_instance.predict(sampling_space)
        pol = [
            [list(sampling_space[index]) for index, label in enumerate(prediction) if label == k]
            for k in range(len(centers))
        ]

        import shapely.geometry

        return [
            shapely.geometry.MultiPoint(pol[i]).convex_hull.exterior.coords
            for i in range(len(pol))
            if pol[i]
        ]
