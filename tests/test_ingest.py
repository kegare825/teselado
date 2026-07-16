import json
from pathlib import Path

import pandas as pd
import pytest

from teselado.ingest.loaders import dataset_summary, load_orders_df
from teselado.ingest.schema import ORDER_COLUMNS, RESTAURANT_COLUMNS
from teselado.ingest.synthetic import (
    generate_orders,
    generate_restaurants,
    list_cities,
    write_sample_dataset,
)


def test_list_cities_includes_demo_and_sevilla():
    cities = {entry["city"] for entry in list_cities()}
    assert "demo" in cities
    assert "sevilla" in cities


def test_generate_restaurants_schema():
    df = generate_restaurants("demo", n_restaurants=10, seed=1)
    assert list(df.columns) == list(RESTAURANT_COLUMNS)
    assert len(df) == 10


def test_generate_orders_schema_and_referential_integrity():
    restaurants = generate_restaurants("demo", n_restaurants=5, seed=2)
    orders = generate_orders(restaurants, n_orders=20, seed=3)
    assert list(orders.columns) == list(ORDER_COLUMNS)
    assert orders["placed_at"].notna().all()
    assert set(orders["restaurant_id"]).issubset(set(restaurants["restaurant_id"]))


def test_write_sample_dataset_writes_metadata(tmp_path: Path):
    data_dir = tmp_path / "sample"
    rest_path, orders_path, metadata_path = write_sample_dataset(
        data_dir, city="sevilla", n_restaurants=10, n_orders=30, seed=9
    )
    assert rest_path.exists()
    assert orders_path.exists()
    assert metadata_path.exists()

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["city"] == "sevilla"
    assert metadata["seed"] == 9
    assert metadata["n_orders"] == 30


def test_dataset_summary(tmp_path: Path):
    data_dir = tmp_path / "sample"
    write_sample_dataset(data_dir, city="demo", n_restaurants=8, n_orders=16, seed=4)
    summary = dataset_summary(data_dir)
    assert summary["n_restaurants"] == 8
    assert summary["n_orders"] == 16
    assert "date_range" in summary


def test_canonical_sample_dataset_exists():
    """Committed data/sample must match the documented canonical size."""
    sample_dir = Path("data/sample")
    if not (sample_dir / "orders.parquet").exists():
        pytest.skip("Canonical sample dataset not present")

    summary = dataset_summary(sample_dir)
    metadata = summary["metadata"]
    assert summary["n_restaurants"] == 50
    assert summary["n_orders"] == 500
    assert metadata["seed"] == 42
    assert metadata["city"] == "demo"


def test_load_validates_missing_order_columns(tmp_path: Path):
    data_dir = tmp_path / "bad"
    data_dir.mkdir()
    pd.DataFrame(
        {"order_id": ["o1"], "lat": [1.0], "lng": [2.0]}
    ).to_parquet(data_dir / "orders.parquet", index=False)

    with pytest.raises(ValueError, match="missing columns"):
        load_orders_df(data_dir)
