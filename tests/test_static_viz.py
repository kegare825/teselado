"""Tests for static PNG exports."""

from pathlib import Path

import numpy as np
import pandas as pd

from teselado.clustering.kmeans import KMeans
from teselado.tessellation.zones import tessellate
from teselado.viz.static import export_kpi_chart_png, export_zone_map_png


def test_export_zone_map_png_writes_file(tmp_path: Path):
    rng = np.random.default_rng(0)
    points = rng.random((40, 2))
    model = KMeans(k=2).fit(points)
    zones = tessellate(model, points, grid_step=0.05)

    orders_df = pd.DataFrame({"lat": points[:, 0], "lng": points[:, 1]})
    restaurants_df = pd.DataFrame({"lat": [0.5], "lng": [0.5]})

    path = export_zone_map_png(zones, orders_df, restaurants_df, tmp_path / "map.png")
    assert path.exists()
    assert path.stat().st_size > 0


def test_export_kpi_chart_png_writes_file(tmp_path: Path):
    metrics = {
        "avg_delivery_time_min": 42.0,
        "sla_hit_rate": 0.35,
        "orders_per_hour": 12.5,
        "courier_utilisation": 0.18,
    }
    path = export_kpi_chart_png(metrics, tmp_path / "dashboard.png")
    assert path.exists()
    assert path.stat().st_size > 0
