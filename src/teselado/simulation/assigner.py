"""Greedy courier assignment strategies."""

from __future__ import annotations

from teselado.simulation.agents import Courier, Order
from teselado.simulation.distance import DistanceCalculator, HaversineCalculator


class GreedyAssigner:
    """Assign each order to the nearest available courier, preferring the order zone."""

    def __init__(self, calculator: DistanceCalculator | None = None) -> None:
        self.calculator = calculator or HaversineCalculator()

    def select(
        self,
        order: Order,
        couriers: list[Courier],
        current_time: float,
    ) -> Courier | None:
        available = [c for c in couriers if c.available_at <= current_time]
        if not available:
            return None

        zone_pool = [c for c in available if c.zone_id == order.zone_id]
        pool = zone_pool or available

        return min(
            pool,
            key=lambda c: self.calculator.distance_km(
                c.lat, c.lng, order.restaurant_lat, order.restaurant_lng
            ),
        )

    def select_with_wait(
        self,
        order: Order,
        couriers: list[Courier],
    ) -> tuple[Courier, float]:
        """
        Pick the courier that can start the order soonest.

        Returns the courier and the time when service can begin.
        """
        best_courier = min(couriers, key=lambda c: c.available_at)
        start_time = max(order.placed_at, best_courier.available_at)
        return best_courier, start_time
