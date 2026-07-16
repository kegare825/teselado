"""Build simulation inputs from ingested datasets."""

from __future__ import annotations

import shapely.geometry

import pandas as pd

from teselado.simulation.agents import Courier, Order, Restaurant
from teselado.tessellation.zones import Zone


def _minutes_since_start(timestamps: pd.Series) -> pd.Series:
    start = timestamps.min()
    return (timestamps - start).dt.total_seconds() / 60.0


def assign_zone(lat: float, lng: float, zones: list[Zone]) -> int:
    """Assign a point to a zone polygon, falling back to nearest centroid."""
    point = shapely.geometry.Point(lat, lng)
    for zone in zones:
        if zone.polygon.contains(point):
            return zone.zone_id

    if not zones:
        return 0

    def dist(z: Zone) -> float:
        return (lat - z.centroid[0]) ** 2 + (lng - z.centroid[1]) ** 2

    return min(zones, key=dist).zone_id


def build_restaurants(restaurants_df: pd.DataFrame) -> dict[str, Restaurant]:
    return {
        row.restaurant_id: Restaurant(
            id=row.restaurant_id,
            lat=float(row.lat),
            lng=float(row.lng),
        )
        for row in restaurants_df.itertuples(index=False)
    }


def build_orders(
    orders_df: pd.DataFrame,
    restaurants: dict[str, Restaurant],
    zones: list[Zone],
) -> list[Order]:
    placed_minutes = _minutes_since_start(orders_df["placed_at"])
    built: list[Order] = []

    for row, placed_at in zip(orders_df.itertuples(index=False), placed_minutes):
        restaurant = restaurants[row.restaurant_id]
        zone_id = assign_zone(float(row.lat), float(row.lng), zones)
        built.append(
            Order(
                id=row.order_id,
                restaurant_id=row.restaurant_id,
                restaurant_lat=restaurant.lat,
                restaurant_lng=restaurant.lng,
                customer_lat=float(row.lat),
                customer_lng=float(row.lng),
                zone_id=zone_id,
                placed_at=float(placed_at),
            )
        )

    return built


def build_couriers(zones: list[Zone], num_couriers: int) -> list[Courier]:
    """Distribute couriers across zones, starting at zone centroids."""
    if not zones:
        return []

    couriers: list[Courier] = []
    base = max(1, num_couriers // len(zones))
    remainder = max(0, num_couriers - base * len(zones))

    courier_idx = 0
    for zone in zones:
        count = base + (1 if remainder > 0 else 0)
        if remainder > 0:
            remainder -= 1

        for _ in range(count):
            couriers.append(
                Courier(
                    id=f"courier_{courier_idx:03d}",
                    lat=zone.centroid[0],
                    lng=zone.centroid[1],
                    zone_id=zone.zone_id,
                )
            )
            courier_idx += 1

    return couriers
