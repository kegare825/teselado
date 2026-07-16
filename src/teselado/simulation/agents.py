"""Delivery simulation agents."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Restaurant:
    id: str
    lat: float
    lng: float


@dataclass
class Courier:
    id: str
    lat: float
    lng: float
    zone_id: int
    available_at: float = 0.0
    orders_delivered: int = 0
    busy_minutes: float = 0.0


@dataclass
class Order:
    id: str
    restaurant_id: str
    restaurant_lat: float
    restaurant_lng: float
    customer_lat: float
    customer_lng: float
    zone_id: int
    placed_at: float
    assigned_courier: str | None = None
    assigned_at: float | None = None
    picked_up_at: float | None = None
    delivered_at: float | None = None


@dataclass
class SimulationResult:
    orders: list[Order] = field(default_factory=list)
    couriers: list[Courier] = field(default_factory=list)
    sim_duration_minutes: float = 0.0
