"""Simulation KPI computation."""

from __future__ import annotations

from teselado.simulation.agents import Order, SimulationResult


def delivery_time_minutes(order: Order) -> float | None:
    if order.delivered_at is None:
        return None
    return order.delivered_at - order.placed_at


def compute_metrics(
    result: SimulationResult,
    sla_minutes: float,
) -> dict:
    """Compute portfolio KPIs from a simulation result."""
    completed = [o for o in result.orders if o.delivered_at is not None]
    delivery_times: list[float] = []
    for order in completed:
        dt = delivery_time_minutes(order)
        if dt is not None:
            delivery_times.append(dt)

    sla_hits = sum(1 for t in delivery_times if t <= sla_minutes)
    sim_hours = max(result.sim_duration_minutes / 60.0, 1e-9)
    num_couriers = max(len(result.couriers), 1)

    total_busy = sum(c.busy_minutes for c in result.couriers)
    capacity_minutes = result.sim_duration_minutes * num_couriers
    utilisation = total_busy / capacity_minutes if capacity_minutes > 0 else 0.0

    orders_by_zone: dict[int, dict] = {}
    for order in completed:
        zone = orders_by_zone.setdefault(
            order.zone_id,
            {
                "order_count": 0,
                "delivery_times": [],
            },
        )
        zone["order_count"] += 1
        dt = delivery_time_minutes(order)
        if dt is not None:
            zone["delivery_times"].append(dt)

    zone_metrics = {}
    for zone_id, data in orders_by_zone.items():
        times = data["delivery_times"]
        zone_sla = sum(1 for t in times if t <= sla_minutes)
        zone_metrics[zone_id] = {
            "order_count": data["order_count"],
            "avg_delivery_time_min": round(sum(times) / len(times), 2) if times else 0.0,
            "sla_hit_rate": round(zone_sla / len(times), 3) if times else 0.0,
            "orders_per_hour": round(data["order_count"] / sim_hours, 2),
            "courier_utilisation": round(utilisation, 3),
        }

    return {
        "total_orders": len(result.orders),
        "completed_orders": len(completed),
        "num_zones": len(zone_metrics),
        "num_couriers": num_couriers,
        "sim_duration_hours": round(sim_hours, 2),
        "avg_delivery_time_min": round(sum(delivery_times) / len(delivery_times), 2)
        if delivery_times
        else 0.0,
        "sla_hit_rate": round(sla_hits / len(delivery_times), 3) if delivery_times else 0.0,
        "orders_per_hour": round(len(completed) / sim_hours, 2),
        "courier_utilisation": round(utilisation, 3),
        "zones": zone_metrics,
    }
