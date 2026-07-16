"""Synthetic restaurant and order data for demo cities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from teselado.ingest.schema import validate_orders, validate_restaurants

# Real geographic bounding boxes with fully synthetic business data.
CITY_BBOXES: dict[str, dict[str, float]] = {
    "demo": {
        "lat_min": 37.35,
        "lat_max": 37.42,
        "lng_min": -6.05,
        "lng_max": -5.95,
        "label": "Demo City (Seville area, synthetic)",
    },
    "sevilla": {
        "lat_min": 37.32,
        "lat_max": 37.42,
        "lng_min": -6.05,
        "lng_max": -5.90,
        "label": "Sevilla (synthetic delivery data)",
    },
}


@dataclass(frozen=True)
class CityBBox:
    lat_min: float
    lat_max: float
    lng_min: float
    lng_max: float
    label: str = ""

    @classmethod
    def from_name(cls, city: str) -> "CityBBox":
        if city not in CITY_BBOXES:
            raise ValueError(f"Unknown city '{city}'. Available: {list(CITY_BBOXES)}")
        raw = CITY_BBOXES[city]
        return cls(
            lat_min=raw["lat_min"],
            lat_max=raw["lat_max"],
            lng_min=raw["lng_min"],
            lng_max=raw["lng_max"],
            label=raw.get("label", city),
        )


def list_cities() -> list[dict[str, str | float]]:
    """Return available synthetic cities and their bounding boxes."""
    cities = []
    for key, bbox in CITY_BBOXES.items():
        cities.append(
            {
                "city": key,
                "label": bbox.get("label", key),
                "lat_min": bbox["lat_min"],
                "lat_max": bbox["lat_max"],
                "lng_min": bbox["lng_min"],
                "lng_max": bbox["lng_max"],
            }
        )
    return cities


def _generate_order_timestamps(n_orders: int, rng: np.random.Generator) -> pd.Series:
    """
    Generate placed_at timestamps with lunch and dinner peaks.

    Hours are UTC on a fixed summer day for reproducibility.
    """
    base = pd.Timestamp("2024-06-15", tz="UTC")
    peak_hours = [12, 13, 20, 21]
    weights = np.array([3.0 if h in peak_hours else 1.0 for h in range(24)])
    weights /= weights.sum()

    hours = rng.choice(24, size=n_orders, p=weights)
    minutes = rng.integers(0, 60, size=n_orders)
    seconds = rng.integers(0, 60, size=n_orders)

    timestamps = [
        base + pd.Timedelta(hours=int(h), minutes=int(m), seconds=int(s))
        for h, m, s in zip(hours, minutes, seconds)
    ]
    return pd.Series(timestamps, dtype="datetime64[ns, UTC]")


def generate_restaurants(
    city: str,
    n_restaurants: int = 50,
    seed: int = 42,
) -> pd.DataFrame:
    """Place restaurants uniformly inside the city bounding box."""
    bbox = CityBBox.from_name(city)
    rng = np.random.default_rng(seed)

    lats = rng.uniform(bbox.lat_min, bbox.lat_max, n_restaurants)
    lngs = rng.uniform(bbox.lng_min, bbox.lng_max, n_restaurants)

    df = pd.DataFrame(
        {
            "restaurant_id": [f"rest_{i:04d}" for i in range(n_restaurants)],
            "lat": lats,
            "lng": lngs,
            "city": city,
        }
    )
    return validate_restaurants(df)


def generate_orders(
    restaurants: pd.DataFrame,
    n_orders: int = 500,
    seed: int = 42,
    demand_sigma: float = 0.008,
) -> pd.DataFrame:
    """Generate customer delivery locations clustered around restaurants."""
    rng = np.random.default_rng(seed)
    city = restaurants["city"].iloc[0]

    weights = np.ones(len(restaurants))
    restaurant_ids = rng.choice(restaurants["restaurant_id"], size=n_orders, p=weights / weights.sum())
    placed_at = _generate_order_timestamps(n_orders, rng)

    rows = []
    for i, rest_id in enumerate(restaurant_ids):
        rest = restaurants.loc[restaurants["restaurant_id"] == rest_id].iloc[0]
        lat = float(rng.normal(rest["lat"], demand_sigma))
        lng = float(rng.normal(rest["lng"], demand_sigma))
        rows.append(
            {
                "order_id": f"order_{i:05d}",
                "restaurant_id": rest_id,
                "lat": lat,
                "lng": lng,
                "placed_at": placed_at.iloc[i],
                "city": city,
            }
        )

    df = pd.DataFrame(rows)
    return validate_orders(df, restaurants)


def build_metadata(
    city: str,
    n_restaurants: int,
    n_orders: int,
    seed: int,
) -> dict:
    """Build dataset metadata sidecar."""
    bbox = CityBBox.from_name(city)
    return {
        "city": city,
        "label": bbox.label,
        "seed": seed,
        "n_restaurants": n_restaurants,
        "n_orders": n_orders,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bbox": {
            "lat_min": bbox.lat_min,
            "lat_max": bbox.lat_max,
            "lng_min": bbox.lng_min,
            "lng_max": bbox.lng_max,
        },
    }


def write_sample_dataset(
    output_dir: Path,
    city: str = "demo",
    n_restaurants: int = 50,
    n_orders: int = 500,
    seed: int = 42,
) -> tuple[Path, Path, Path]:
    """Write restaurants.parquet, orders.parquet, and metadata.json."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    restaurants = generate_restaurants(city, n_restaurants, seed)
    orders = generate_orders(restaurants, n_orders, seed)
    metadata = build_metadata(city, n_restaurants, n_orders, seed)

    restaurants_path = output_dir / "restaurants.parquet"
    orders_path = output_dir / "orders.parquet"
    metadata_path = output_dir / "metadata.json"

    restaurants.to_parquet(restaurants_path, index=False)
    orders.to_parquet(orders_path, index=False)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return restaurants_path, orders_path, metadata_path
