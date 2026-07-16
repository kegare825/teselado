"""Discrete-event delivery simulation engine."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import pandas as pd

from teselado.simulation.agents import Courier, Order, SimulationResult
from teselado.simulation.assigner import GreedyAssigner
from teselado.simulation.geo import travel_minutes
from teselado.simulation.inputs import build_couriers, build_orders, build_restaurants
from teselado.simulation.metrics import compute_metrics
from teselado.tessellation.zones import Zone


@dataclass
class SimulationParams:
    num_couriers: int = 5
    avg_speed_kmh: float = 25.0
    sla_minutes: float = 30.0
    restaurant_handle_minutes: float = 5.0


def _process_order(
    order: Order,
    couriers: list[Courier],
    assigner: GreedyAssigner,
    params: SimulationParams,
    current_time: float,
) -> float:
    """Assign and complete one order; returns delivered_at timestamp."""
    courier = assigner.select(order, couriers, current_time)
    if courier is None:
        courier, start_time = assigner.select_with_wait(order, couriers)
    else:
        start_time = max(current_time, courier.available_at)

    to_restaurant = travel_minutes(
        courier.lat,
        courier.lng,
        order.restaurant_lat,
        order.restaurant_lng,
        params.avg_speed_kmh,
    )
    pickup_complete = start_time + to_restaurant + params.restaurant_handle_minutes
    to_customer = travel_minutes(
        order.restaurant_lat,
        order.restaurant_lng,
        order.customer_lat,
        order.customer_lng,
        params.avg_speed_kmh,
    )
    delivered_at = pickup_complete + to_customer

    order.assigned_courier = courier.id
    order.assigned_at = start_time
    order.picked_up_at = pickup_complete
    order.delivered_at = delivered_at

    busy = delivered_at - min(start_time, order.placed_at)
    courier.available_at = delivered_at
    courier.lat = order.customer_lat
    courier.lng = order.customer_lng
    courier.orders_delivered += 1
    courier.busy_minutes += busy

    return delivered_at


def run_event_simulation(
    orders: list[Order],
    couriers: list[Courier],
    params: SimulationParams,
) -> SimulationResult:
    """
    Process orders through a discrete-event queue: placed → assigned → delivered.

    Events are processed in chronological order. If no courier is free at placement
    time, the order waits until the earliest courier becomes available.
    """
    assigner = GreedyAssigner()
    event_queue: list[tuple[float, int, str, Order]] = []
    for seq, order in enumerate(sorted(orders, key=lambda o: o.placed_at)):
        heapq.heappush(event_queue, (order.placed_at, seq, "placed", order))

    completed: list[Order] = []

    while event_queue:
        current_time, _, event_type, order = heapq.heappop(event_queue)

        if event_type == "placed":
            delivered_at = _process_order(
                order,
                couriers,
                assigner,
                params,
                current_time,
            )
            completed.append(order)
            heapq.heappush(
                event_queue,
                (delivered_at, len(completed), "delivered", order),
            )

    sim_duration = max((o.delivered_at or 0.0) for o in completed) if completed else 0.0
    return SimulationResult(
        orders=completed,
        couriers=couriers,
        sim_duration_minutes=sim_duration,
    )


def simulate(
    zones: list[Zone],
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    params: SimulationParams | None = None,
) -> dict:
    """Run the full simulation pipeline and return KPI metrics."""
    params = params or SimulationParams()
    restaurants = build_restaurants(restaurants_df)
    orders = build_orders(orders_df, restaurants, zones)
    couriers = build_couriers(zones, params.num_couriers)
    result = run_event_simulation(orders, couriers, params)
    return compute_metrics(result, sla_minutes=params.sla_minutes)
