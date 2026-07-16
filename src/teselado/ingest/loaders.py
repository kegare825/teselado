"""Load and validate order and restaurant datasets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from teselado.ingest.schema import validate_orders, validate_restaurants


def load_metadata(data_dir: Path) -> dict:
    """Load data_dir/metadata.json if present."""
    path = Path(data_dir) / "metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_restaurants_df(data_dir: Path, validate: bool = True) -> pd.DataFrame:
    """Load restaurants DataFrame from data_dir/restaurants.parquet."""
    path = Path(data_dir) / "restaurants.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Restaurants file not found: {path}")
    df = pd.read_parquet(path)
    return validate_restaurants(df) if validate else df


def load_orders_df(data_dir: Path, validate: bool = True) -> pd.DataFrame:
    """Load orders DataFrame from data_dir/orders.parquet."""
    path = Path(data_dir) / "orders.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Orders file not found: {path}")
    df = pd.read_parquet(path)

    if validate:
        restaurants = None
        rest_path = Path(data_dir) / "restaurants.parquet"
        if rest_path.exists():
            restaurants = pd.read_parquet(rest_path)
        return validate_orders(df, restaurants)

    return df


def load_orders(data_dir: Path) -> np.ndarray:
    """Return (N, 2) array of [lat, lng] delivery coordinates."""
    df = load_orders_df(data_dir)
    return df[["lat", "lng"]].to_numpy(dtype=float)


def dataset_summary(data_dir: Path) -> dict:
    """Return a compact summary of the dataset in data_dir."""
    restaurants = load_restaurants_df(data_dir)
    orders = load_orders_df(data_dir)
    metadata = load_metadata(data_dir)

    return {
        "city": metadata.get("city", restaurants["city"].iloc[0]),
        "n_restaurants": len(restaurants),
        "n_orders": len(orders),
        "date_range": {
            "min": str(orders["placed_at"].min()),
            "max": str(orders["placed_at"].max()),
        },
        "metadata": metadata,
    }
