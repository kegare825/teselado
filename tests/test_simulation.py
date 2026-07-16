import pandas as pd

from teselado.simulation.agents import Courier, Order
from teselado.simulation.assigner import GreedyAssigner
from teselado.simulation.engine import SimulationParams, run_event_simulation, simulate
from teselado.simulation.geo import travel_minutes
from teselado.simulation.metrics import compute_metrics
from teselado.tessellation.zones import Zone
import shapely.geometry


def _sample_zone() -> Zone:
    polygon = shapely.geometry.box(0.0, 0.0, 1.0, 1.0)
    return Zone(zone_id=0, polygon=polygon, centroid=(0.5, 0.5), order_count=1)


def test_travel_minutes_positive():
    minutes = travel_minutes(0.0, 0.0, 0.1, 0.1, speed_kmh=30.0)
    assert minutes > 0


def test_greedy_assigner_prefers_zone_courier():
    order = Order(
        id="o1",
        restaurant_id="r1",
        restaurant_lat=0.2,
        restaurant_lng=0.2,
        customer_lat=0.3,
        customer_lng=0.3,
        zone_id=1,
        placed_at=0.0,
    )
    couriers = [
        Courier(id="c0", lat=0.1, lng=0.1, zone_id=0),
        Courier(id="c1", lat=0.25, lng=0.25, zone_id=1),
    ]
    assigner = GreedyAssigner()
    selected = assigner.select(order, couriers, current_time=0.0)
    assert selected is not None
    assert selected.zone_id == 1


def test_event_simulation_completes_orders():
    orders = [
        Order(
            id="o1",
            restaurant_id="r1",
            restaurant_lat=0.0,
            restaurant_lng=0.0,
            customer_lat=0.05,
            customer_lng=0.05,
            zone_id=0,
            placed_at=0.0,
        ),
        Order(
            id="o2",
            restaurant_id="r1",
            restaurant_lat=0.0,
            restaurant_lng=0.0,
            customer_lat=0.08,
            customer_lng=0.08,
            zone_id=0,
            placed_at=5.0,
        ),
    ]
    couriers = [Courier(id="c0", lat=0.0, lng=0.0, zone_id=0)]
    result = run_event_simulation(orders, couriers, SimulationParams(num_couriers=1))
    assert len(result.orders) == 2
    assert all(o.delivered_at is not None for o in result.orders)
    assert result.orders[1].delivered_at >= result.orders[0].delivered_at


def test_compute_metrics_includes_portfolio_kpis():
    order = Order(
        id="o1",
        restaurant_id="r1",
        restaurant_lat=0.0,
        restaurant_lng=0.0,
        customer_lat=0.01,
        customer_lng=0.01,
        zone_id=0,
        placed_at=0.0,
        delivered_at=20.0,
    )
    courier = Courier(id="c0", lat=0.0, lng=0.0, zone_id=0, busy_minutes=20.0)
    from teselado.simulation.agents import SimulationResult

    result = SimulationResult(
        orders=[order],
        couriers=[courier],
        sim_duration_minutes=60.0,
    )
    metrics = compute_metrics(result, sla_minutes=30.0)
    assert metrics["avg_delivery_time_min"] == 20.0
    assert metrics["orders_per_hour"] == 1.0
    assert "courier_utilisation" in metrics
    assert 0 in metrics["zones"]


def test_simulate_with_dataframes():
    restaurants_df = pd.DataFrame(
        {
            "restaurant_id": ["r1"],
            "lat": [0.1],
            "lng": [0.1],
            "city": ["demo"],
        }
    )
    orders_df = pd.DataFrame(
        {
            "order_id": ["o1"],
            "restaurant_id": ["r1"],
            "lat": [0.15],
            "lng": [0.15],
            "placed_at": pd.to_datetime(["2024-06-15 12:00:00"], utc=True),
            "city": ["demo"],
        }
    )
    zones = [_sample_zone()]
    metrics = simulate(
        zones,
        orders_df,
        restaurants_df,
        SimulationParams(num_couriers=1),
    )
    assert metrics["completed_orders"] == 1
    assert metrics["avg_delivery_time_min"] > 0
