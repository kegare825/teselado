"""Tests for haversine vs OSMnx distance comparison."""

from pathlib import Path
from unittest.mock import patch

import pytest

from teselado.config import Settings
from teselado.ingest.synthetic import write_sample_dataset
from teselado.simulation.compare import compare_distance_models, compare_distances_from_settings
from teselado.simulation.distance import OsmnxCalculator
from teselado.simulation.engine import SimulationParams
from teselado.tessellation.zones import Zone
import shapely.geometry


def _sample_zone() -> Zone:
    polygon = shapely.geometry.box(37.36, -6.04, 37.40, -5.98)
    return Zone(zone_id=0, polygon=polygon, centroid=(37.38, -6.01), order_count=3)


@pytest.fixture
def sample_data(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    write_sample_dataset(data_dir, city="demo", n_restaurants=10, n_orders=40, seed=11)
    return data_dir


def test_compare_distance_models_haversine_only(sample_data: Path):
    from teselado.ingest.loaders import load_orders_df, load_restaurants_df

    orders_df = load_orders_df(sample_data)
    restaurants_df = load_restaurants_df(sample_data)
    zones = [_sample_zone()]
    params = SimulationParams(num_couriers=2, city="demo")

    comparisons = compare_distance_models(
        zones, orders_df, restaurants_df, params, modes=["haversine"]
    )
    assert len(comparisons) == 1
    assert comparisons[0].distance_mode == "haversine"
    assert comparisons[0].metrics["avg_delivery_time_min"] >= 0


@patch("teselado.simulation.compare.simulate")
def test_compare_distance_models_runs_both_modes(mock_simulate, sample_data: Path):
    from teselado.ingest.loaders import load_orders_df, load_restaurants_df

    mock_simulate.side_effect = [
        {"avg_delivery_time_min": 100.0, "sla_hit_rate": 0.2, "distance_mode": "haversine"},
        {"avg_delivery_time_min": 130.0, "sla_hit_rate": 0.15, "distance_mode": "osmnx"},
    ]
    orders_df = load_orders_df(sample_data)
    restaurants_df = load_restaurants_df(sample_data)
    zones = [_sample_zone()]
    params = SimulationParams(city="demo")

    comparisons = compare_distance_models(
        zones, orders_df, restaurants_df, params, modes=["haversine", "osmnx"]
    )
    assert [item.distance_mode for item in comparisons] == ["haversine", "osmnx"]
    assert mock_simulate.call_count == 2


def test_osmnx_calculator_uses_graph_shortest_path():
    import networkx as nx

    graph = nx.Graph()
    graph.add_node(1, x=-6.0, y=37.38)
    graph.add_node(2, x=-6.01, y=37.39)
    graph.add_edge(1, 2, length=1500.0)

    calc = OsmnxCalculator(graph=graph)
    with patch("osmnx.distance.nearest_nodes", side_effect=[1, 2]):
        distance = calc.distance_km(37.38, -6.0, 37.39, -6.01)
    assert distance == pytest.approx(1.5)


def test_compare_distances_from_settings(sample_data: Path):
    cfg = Settings(data_dir=sample_data, city="demo", method="fuzzy", k=2)
    comparisons = compare_distances_from_settings(cfg, k=2, modes=["haversine"])
    assert len(comparisons) == 1
