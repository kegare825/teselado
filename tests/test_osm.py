"""Tests for OSM ingestion helpers."""

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from teselado.ingest.osm import _elements_to_dataframe, load_osm_restaurants


def test_elements_to_dataframe_normalises_nodes_and_ways():
    payload = {
        "elements": [
            {"type": "node", "id": 1, "lat": 37.38, "lon": -6.0, "tags": {"name": "Bar"}},
            {
                "type": "way",
                "id": 2,
                "center": {"lat": 37.39, "lon": -6.01},
                "tags": {"amenity": "restaurant"},
            },
        ]
    }
    frame = _elements_to_dataframe(payload["elements"], city="demo")
    assert len(frame) == 2
    assert set(frame.columns) >= {"restaurant_id", "lat", "lng", "city"}
    assert frame["city"].eq("demo").all()


@patch("teselado.ingest.osm._fetch_overpass")
def test_load_osm_restaurants_uses_cache(mock_fetch, tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    payload = {
        "elements": [
            {"type": "node", "id": 10, "lat": 37.38, "lon": -6.0, "tags": {"name": "Tapa"}},
        ]
    }
    (cache_dir / "demo_restaurants.json").write_text(json.dumps(payload), encoding="utf-8")

    frame = load_osm_restaurants("demo", cache_dir=cache_dir)
    mock_fetch.assert_not_called()
    assert len(frame) == 1
    assert isinstance(frame, pd.DataFrame)
