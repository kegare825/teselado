"""Tests for optional MIP assigner."""

from teselado.simulation.agents import Courier, Order
from teselado.simulation.mip_assigner import MipAssigner


def test_mip_assigner_selects_zone_courier_for_single_order():
    assigner = MipAssigner()
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
    selected = assigner.select(order, couriers, current_time=0.0)
    assert selected is not None
    assert selected.zone_id == 1
