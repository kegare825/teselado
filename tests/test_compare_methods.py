"""Tests for clustering-method comparison."""

from pathlib import Path

import pytest

from teselado.config import Settings
from teselado.ingest.synthetic import write_sample_dataset
from teselado.simulation.compare import compare_clustering_methods, compare_methods_from_settings
from teselado.simulation.engine import SimulationParams


@pytest.fixture
def sample_data(tmp_path: Path) -> tuple[Path, object, object]:
    data_dir = tmp_path / "data"
    write_sample_dataset(data_dir, city="demo", n_restaurants=15, n_orders=80, seed=3)
    from teselado.ingest.loaders import load_orders_df, load_restaurants_df

    return data_dir, load_orders_df(data_dir), load_restaurants_df(data_dir)


def test_compare_clustering_methods_uses_same_k_and_haversine(sample_data):
    _, orders_df, restaurants_df = sample_data
    comparisons = compare_clustering_methods(
        orders_df,
        restaurants_df,
        k=3,
        methods=["kmeans", "fuzzy"],
        params=SimulationParams(num_couriers=3),
    )

    assert len(comparisons) == 2
    assert {item.method for item in comparisons} == {"kmeans", "fuzzy"}
    assert all(item.k == 3 for item in comparisons)

    for item in comparisons:
        assert item.metrics["avg_delivery_time_min"] >= 0
        assert item.metrics["clustering_method"] == item.method

    fuzzy = next(item for item in comparisons if item.method == "fuzzy")
    assert "boundary_ambiguity" in fuzzy.metrics


def test_compare_methods_from_settings(sample_data):
    data_dir, _, _ = sample_data
    cfg = Settings(data_dir=data_dir, k=3)
    comparisons = compare_methods_from_settings(cfg, k=3, methods=["kmeans", "fuzzy"])
    assert len(comparisons) == 2


def test_compare_clustering_methods_rejects_unknown_method(sample_data):
    _, orders_df, restaurants_df = sample_data
    with pytest.raises(ValueError):
        compare_clustering_methods(
            orders_df,
            restaurants_df,
            k=3,
            methods=["kmeans", "unknown"],
        )
