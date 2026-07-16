"""OpenStreetMap restaurant ingestion via the public Overpass API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from teselado.ingest.schema import validate_restaurants
from teselado.ingest.synthetic import CITY_BBOXES, CityBBox


def available_osm_cities() -> list[str]:
    """Cities with predefined bounding boxes for OSM ingestion."""
    return list(CITY_BBOXES.keys())


def _overpass_query(bbox: CityBBox, city: str) -> str:
    return f"""
    [out:json][timeout:25];
    (
      node["amenity"="restaurant"]({bbox.lat_min},{bbox.lng_min},{bbox.lat_max},{bbox.lng_max});
      way["amenity"="restaurant"]({bbox.lat_min},{bbox.lng_min},{bbox.lat_max},{bbox.lng_max});
    );
    out center;
    """


def _fetch_overpass(query: str, endpoint: str) -> dict:
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"User-Agent": "teselado/0.2 portfolio-demo"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _elements_to_dataframe(elements: list[dict], city: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, element in enumerate(elements):
        if element.get("type") == "node":
            lat = element.get("lat")
            lng = element.get("lon")
        else:
            center = element.get("center") or {}
            lat = center.get("lat")
            lng = center.get("lon")

        if lat is None or lng is None:
            continue

        tags = element.get("tags") or {}
        name = tags.get("name", f"restaurant_{idx}")
        rows.append(
            {
                "restaurant_id": f"osm_{element.get('type')}_{element.get('id', idx)}",
                "lat": float(lat),
                "lng": float(lng),
                "city": city,
                "name": name,
            }
        )

    if not rows:
        raise ValueError("Overpass query returned no restaurant POIs for this bbox.")

    frame = pd.DataFrame(rows)
    return validate_restaurants(frame[["restaurant_id", "lat", "lng", "city"]])


def load_osm_restaurants(
    city: str,
    cache_dir: Path | None = None,
    endpoint: str = "https://overpass-api.de/api/interpreter",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Fetch restaurant POIs from OpenStreetMap for a known city bbox.

    Results are optionally cached as JSON under `cache_dir` to avoid repeated
    Overpass calls during development.
    """
    if city not in CITY_BBOXES:
        raise ValueError(f"Unknown city '{city}'. Available: {list(CITY_BBOXES)}")

    cache_path = None
    if cache_dir is not None:
        cache_path = Path(cache_dir) / f"{city}_restaurants.json"
        if use_cache and cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return _elements_to_dataframe(payload.get("elements", []), city)

    bbox = CityBBox.from_name(city)
    query = _overpass_query(bbox, city)

    try:
        payload = _fetch_overpass(query, endpoint)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Failed to reach the Overpass API. "
            "Check network connectivity or retry later."
        ) from exc

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return _elements_to_dataframe(payload.get("elements", []), city)
