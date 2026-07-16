"""Zone models and tessellation from cluster assignments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import shapely.geometry

from teselado.clustering.kmeans import KMeans
from teselado.geo.bounds import bounding_box


@dataclass
class Zone:
    zone_id: int
    polygon: shapely.geometry.Polygon
    centroid: tuple[float, float]
    order_count: int


def _grid_step_for_bbox(bbox: list[tuple[float, float]], max_points: int = 8000) -> float:
    min_x, min_y = bbox[0]
    max_x, max_y = bbox[2]
    area = max((max_x - min_x) * (max_y - min_y), 1e-9)
    step = float(np.sqrt(area / max_points))
    return max(step, 0.002)


def tessellate(
    model: KMeans,
    points: np.ndarray,
    grid_step: float | None = None,
    max_grid_points: int = 8000,
) -> list[Zone]:
    """
    Build zone polygons by sampling a grid, assigning labels, and taking convex hulls.
    """
    points = np.asarray(points, dtype=float)
    labels = model.predict(points)
    bbox = bounding_box(points.tolist())
    step = grid_step or _grid_step_for_bbox(bbox, max_grid_points)

    min_x, min_y = bbox[0]
    max_x, max_y = bbox[2]

    lat_vals = np.arange(min_y, max_y, step)
    lng_vals = np.arange(min_x, max_x, step)
    grid = np.asarray([[lat, lng] for lat in lat_vals for lng in lng_vals], dtype=float)

    if len(grid) == 0:
        grid = points.copy()

    grid_labels = model.predict(grid)
    zones: list[Zone] = []

    for zone_id in range(model.k):
        zone_grid = grid[grid_labels == zone_id]
        zone_orders = points[labels == zone_id]

        if len(zone_grid) < 3:
            if len(zone_orders) == 0:
                continue
            polygon = shapely.geometry.MultiPoint(zone_orders.tolist()).convex_hull
        else:
            polygon = shapely.geometry.MultiPoint(zone_grid.tolist()).convex_hull

        if polygon.is_empty or polygon.geom_type == "Point":
            continue

        if polygon.geom_type == "LineString":
            polygon = polygon.buffer(step)

        centroid_arr = model.centroids_[zone_id]
        zones.append(
            Zone(
                zone_id=zone_id,
                polygon=polygon,
                centroid=(float(centroid_arr[0]), float(centroid_arr[1])),
                order_count=int(np.sum(labels == zone_id)),
            )
        )

    return zones
