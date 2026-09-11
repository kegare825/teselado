"""Tests for the optional MIP assigner (OR-Tools) and its explicit greedy fallback."""

import sys

import pytest

from teselado.simulation.agents import Courier, Order
from teselado.simulation.mip_assigner import MipAssigner


def _order(order_id: str, lat: float, lng: float, zone_id: int) -> Order:
    return Order(
        id=order_id,
        restaurant_id=f"r_{order_id}",
        restaurant_lat=lat,
        restaurant_lng=lng,
        customer_lat=lat + 0.05,
        customer_lng=lng + 0.05,
        zone_id=zone_id,
        placed_at=0.0,
    )


def _couriers() -> list[Courier]:
    return [
        Courier(id="c0", lat=0.1, lng=0.1, zone_id=0),
        Courier(id="c1", lat=0.9, lng=0.9, zone_id=1),
    ]


def test_mip_path_solves_batch_assignment_with_ortools():
    """Two orders pending at the same instant trigger the OR-Tools matching."""
    pytest.importorskip("ortools")
    assigner = MipAssigner()
    couriers = _couriers()

    # First pending order: only one in the batch, greedy shortcut applies.
    first = assigner.select(_order("o1", 0.85, 0.85, zone_id=1), couriers, current_time=0.0)
    assert first is not None and first.id == "c1"

    # Second order at the same time: batch of two -> MIP min-cost matching.
    second = assigner.select(_order("o2", 0.15, 0.15, zone_id=0), couriers, current_time=0.0)
    assert second is not None and second.id == "c0"
    # The batch is consumed after a successful solve.
    assert assigner._pending == []


def test_single_pending_order_uses_greedy_shortcut():
    """With a single pending order the MIP is never built, regardless of OR-Tools."""
    assigner = MipAssigner()
    selected = assigner.select(_order("o1", 0.85, 0.85, zone_id=1), _couriers(), current_time=0.0)
    assert selected is not None
    assert selected.zone_id == 1


def test_greedy_fallback_when_ortools_missing(monkeypatch):
    """Explicitly simulate a missing OR-Tools install and verify the greedy fallback."""
    monkeypatch.setitem(sys.modules, "ortools", None)
    monkeypatch.setitem(sys.modules, "ortools.linear_solver", None)

    assigner = MipAssigner()
    couriers = _couriers()
    assigner.select(_order("o1", 0.85, 0.85, zone_id=1), couriers, current_time=0.0)
    selected = assigner.select(_order("o2", 0.15, 0.15, zone_id=0), couriers, current_time=0.0)

    assert selected is not None and selected.id == "c0"
    # Greedy fallback keeps the batch pending (only the MIP path clears it).
    assert len(assigner._pending) == 2


def test_returns_none_when_no_courier_available():
    assigner = MipAssigner()
    couriers = [Courier(id="c0", lat=0.1, lng=0.1, zone_id=0, available_at=100.0)]
    assert assigner.select(_order("o1", 0.1, 0.1, zone_id=0), couriers, current_time=0.0) is None
