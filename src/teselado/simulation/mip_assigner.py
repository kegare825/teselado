"""Optional MIP-based courier assignment via OR-Tools."""

from __future__ import annotations

from typing import Any

from teselado.simulation.agents import Courier, Order
from teselado.simulation.assigner import GreedyAssigner
from teselado.simulation.geo import haversine_km


class MipAssigner(GreedyAssigner):
    """
    Min-cost bipartite matching for orders that become available at the same time.

    Falls back to the greedy strategy when OR-Tools is unavailable or only one
    order is pending. Travel costs use the same haversine metric as GreedyAssigner.
    """

    def __init__(self) -> None:
        self._pending: list[tuple[Order, float]] = []
        self._last_time: float | None = None

    def select(
        self,
        order: Order,
        couriers: list[Courier],
        current_time: float,
    ) -> Courier | None:
        if self._last_time is not None and current_time > self._last_time:
            self._pending.clear()
        self._last_time = current_time
        self._pending.append((order, current_time))

        available = [c for c in couriers if c.available_at <= current_time]
        if not available:
            return None

        if len(self._pending) == 1 or len(available) == 1:
            return super().select(order, couriers, current_time)

        try:
            from ortools.linear_solver import pywraplp
        except ImportError:
            return super().select(order, couriers, current_time)

        pending_orders = [item[0] for item in self._pending]
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if solver is None:
            return super().select(order, couriers, current_time)

        assign: dict[tuple[int, int], Any] = {}
        for i, pending_order in enumerate(pending_orders):
            for j, courier in enumerate(available):
                cost = haversine_km(
                    courier.lat,
                    courier.lng,
                    pending_order.restaurant_lat,
                    pending_order.restaurant_lng,
                )
                if pending_order.zone_id == courier.zone_id:
                    cost *= 0.8
                assign[(i, j)] = solver.BoolVar(f"x_{i}_{j}")

        for i in range(len(pending_orders)):
            solver.Add(sum(assign[(i, j)] for j in range(len(available))) <= 1)

        for j in range(len(available)):
            solver.Add(sum(assign[(i, j)] for i in range(len(pending_orders))) <= 1)

        objective = solver.Objective()
        for (i, j), var in assign.items():
            pending_order = pending_orders[i]
            courier = available[j]
            cost = haversine_km(
                courier.lat,
                courier.lng,
                pending_order.restaurant_lat,
                pending_order.restaurant_lng,
            )
            if pending_order.zone_id == courier.zone_id:
                cost *= 0.8
            objective.SetCoefficient(var, cost)
        objective.SetMinimization()

        status = solver.Solve()
        if status != pywraplp.Solver.OPTIMAL:
            return super().select(order, couriers, current_time)

        for j, courier in enumerate(available):
            if assign[(len(pending_orders) - 1, j)].solution_value() > 0.5:
                self._pending.clear()
                return courier

        chosen = super().select(order, couriers, current_time)
        self._pending.clear()
        return chosen
