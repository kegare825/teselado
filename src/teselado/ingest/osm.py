"""
Optional OpenStreetMap-based ingestion (future work).

Phase 3 keeps this as a documented extension point for public POI data.
A future implementation could:
  - fetch restaurant POIs via Overpass API for a city bbox
  - normalise to the canonical schema in data/schema.yaml
  - write Parquet datasets compatible with teselado.ingest.loaders
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from teselado.ingest.synthetic import CITY_BBOXES


def available_osm_cities() -> list[str]:
    """Cities with predefined bounding boxes that could be used for OSM ingestion."""
    return list(CITY_BBOXES.keys())


def load_osm_restaurants(city: str, cache_dir: Path | None = None) -> pd.DataFrame:
    """
    Placeholder for OSM restaurant ingestion.

    Raises NotImplementedError until a public Overpass integration is added.
    """
    raise NotImplementedError(
        "OSM ingestion is not implemented yet. "
        f"Use `teselado generate --city {city}` for synthetic data, "
        "or contribute an Overpass fetcher here."
    )
