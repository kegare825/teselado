"""Generate visualization artifacts from pipeline outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from teselado.ingest.loaders import load_orders_df, load_restaurants_df
from teselado.tessellation.zones import Zone
from teselado.viz.dashboard import export_dashboard
from teselado.viz.export import load_geojson
from teselado.viz.map import export_map
import shapely.geometry


def zones_from_geojson(data: dict) -> list[Zone]:
    """Reconstruct Zone objects from a GeoJSON FeatureCollection."""
    zones: list[Zone] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = shapely.geometry.shape(feature["geometry"])
        zones.append(
            Zone(
                zone_id=int(props.get("zone_id", len(zones))),
                polygon=geom,
                centroid=(
                    float(props.get("centroid_lat", geom.centroid.x)),
                    float(props.get("centroid_lng", geom.centroid.y)),
                ),
                order_count=int(props.get("order_count", 0)),
            )
        )
    return zones


def export_visualizations(
    zones: list[Zone],
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    metrics: dict,
    output_dir: Path,
) -> dict[str, Path]:
    """Export map.html and dashboard.html alongside JSON artifacts."""
    output_dir = Path(output_dir)
    paths = {
        "map": export_map(
            zones,
            orders_df,
            restaurants_df,
            output_dir / "map.html",
            metrics=metrics,
        ),
        "dashboard": export_dashboard(
            metrics,
            output_dir / "dashboard.html",
            map_filename="map.html",
        ),
    }
    return paths


def export_visualizations_from_files(
    output_dir: Path,
    data_dir: Path,
    zones_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Path]:
    """Rebuild visualizations from existing GeoJSON and report files."""
    output_dir = Path(output_dir)
    zones_path = Path(zones_path or output_dir / "zones.geojson")
    report_path = Path(report_path or output_dir / "report.json")

    geojson = load_geojson(zones_path)
    metrics = json.loads(report_path.read_text(encoding="utf-8"))
    zones = zones_from_geojson(geojson)
    orders_df = load_orders_df(data_dir)
    restaurants_df = load_restaurants_df(data_dir)
    return export_visualizations(zones, orders_df, restaurants_df, metrics, output_dir)
