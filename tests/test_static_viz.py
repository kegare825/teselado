"""Tests for static PNG exports."""

from pathlib import Path

import pandas as pd
import shapely.geometry

from teselado.simulation.compare import DistanceComparison
from teselado.tessellation.zones import Zone
from teselado.viz.static import export_distance_comparison_png, export_zone_map_png


def test_export_zone_map_png_plots_lat_lng_correctly(tmp_path: Path):
    polygon = shapely.geometry.box(37.36, -6.04, 37.40, -5.98)
    zones = [Zone(zone_id=0, polygon=polygon, centroid=(37.38, -6.01), order_count=5)]
    orders_df = pd.DataFrame({"lat": [37.38], "lng": [-6.01]})
    restaurants_df = pd.DataFrame({"lat": [37.39], "lng": [-6.00]})

    path = export_zone_map_png(zones, orders_df, restaurants_df, tmp_path / "map.png")
    assert path.exists()
    assert path.stat().st_size > 0


def test_export_distance_comparison_png_writes_file(tmp_path: Path):
    comparisons = [
        DistanceComparison(
            distance_mode="haversine",
            k=5,
            metrics={
                "avg_delivery_time_min": 120.0,
                "sla_hit_rate": 0.25,
                "orders_per_hour": 15.0,
                "courier_utilisation": 0.08,
            },
        ),
        DistanceComparison(
            distance_mode="osmnx",
            k=5,
            metrics={
                "avg_delivery_time_min": 145.0,
                "sla_hit_rate": 0.18,
                "orders_per_hour": 14.0,
                "courier_utilisation": 0.09,
            },
        ),
    ]
    path = export_distance_comparison_png(comparisons, tmp_path / "distance.png")
    assert path.exists()
    assert path.stat().st_size > 0
