"""Export zones and simulation metrics."""

from __future__ import annotations

import json
from pathlib import Path

import shapely.geometry

from teselado.tessellation.zones import Zone


def export_geojson(zones: list[Zone], path: Path) -> Path:
    """Write zone polygons as a GeoJSON FeatureCollection."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    features = []
    for zone in zones:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "zone_id": zone.zone_id,
                    "order_count": zone.order_count,
                    "centroid_lat": zone.centroid[0],
                    "centroid_lng": zone.centroid[1],
                },
                "geometry": shapely.geometry.mapping(zone.polygon),
            }
        )

    collection = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    return path


def export_report(metrics: dict, path: Path) -> Path:
    """Write simulation metrics as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return path


def load_geojson(path: Path) -> dict:
    """Load a GeoJSON FeatureCollection from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
