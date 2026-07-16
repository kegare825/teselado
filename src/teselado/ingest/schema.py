"""Dataset schema constants and validation."""

from __future__ import annotations

import pandas as pd

RESTAURANT_COLUMNS = ("restaurant_id", "lat", "lng", "city")
ORDER_COLUMNS = ("order_id", "restaurant_id", "lat", "lng", "placed_at", "city")


def validate_restaurants(df: pd.DataFrame) -> pd.DataFrame:
    """Validate restaurant DataFrame schema and value ranges."""
    missing = [col for col in RESTAURANT_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Restaurants missing columns: {missing}")

    if df["restaurant_id"].duplicated().any():
        raise ValueError("Duplicate restaurant_id values found")

    if df["lat"].isna().any() or df["lng"].isna().any():
        raise ValueError("Restaurants contain null coordinates")

    return df[list(RESTAURANT_COLUMNS)].copy()


def validate_orders(df: pd.DataFrame, restaurants: pd.DataFrame | None = None) -> pd.DataFrame:
    """Validate orders DataFrame schema and referential integrity."""
    missing = [col for col in ORDER_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Orders missing columns: {missing}")

    if df["order_id"].duplicated().any():
        raise ValueError("Duplicate order_id values found")

    if df["lat"].isna().any() or df["lng"].isna().any():
        raise ValueError("Orders contain null coordinates")

    if restaurants is not None:
        valid_ids = set(restaurants["restaurant_id"])
        unknown = set(df["restaurant_id"]) - valid_ids
        if unknown:
            raise ValueError(f"Orders reference unknown restaurant_id values: {sorted(unknown)[:5]}")

    validated = df[list(ORDER_COLUMNS)].copy()
    validated["placed_at"] = pd.to_datetime(validated["placed_at"], utc=True)
    return validated
