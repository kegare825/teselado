import json
from pathlib import Path

import pytest

from teselado.config import Settings
from teselado.ingest.synthetic import write_sample_dataset
from teselado.pipeline import run_pipeline


@pytest.fixture
def sample_data(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    write_sample_dataset(data_dir, city="demo", n_restaurants=20, n_orders=100, seed=7)
    return data_dir


def test_end_to_end_with_sample_data(sample_data: Path, tmp_path: Path):
    output_dir = tmp_path / "outputs"
    cfg = Settings(data_dir=sample_data, output_dir=output_dir, k_min=2, k_max=4)
    result = run_pipeline(cfg)

    assert (output_dir / "zones.geojson").exists()
    assert (output_dir / "report.json").exists()
    assert (output_dir / "map.html").exists()
    assert (output_dir / "dashboard.html").exists()
    assert result.k >= 2
    assert len(result.zones) == result.k
    assert result.metrics["avg_delivery_time_min"] >= 0
    assert "orders_per_hour" in result.metrics
    assert "courier_utilisation" in result.metrics
    assert result.metrics["clustering_method"] == "kmeans"
    assert "boundary_ambiguity" not in result.metrics


def test_end_to_end_with_fuzzy_method(sample_data: Path, tmp_path: Path):
    output_dir = tmp_path / "outputs_fuzzy"
    cfg = Settings(
        data_dir=sample_data, output_dir=output_dir, method="fuzzy", k_min=2, k_max=4
    )
    result = run_pipeline(cfg)

    assert result.metrics["clustering_method"] == "fuzzy"
    ambiguity = result.metrics["boundary_ambiguity"]
    assert 0.0 <= ambiguity["boundary_point_ratio"] <= 1.0
    assert 0.0 <= ambiguity["mean_confidence"] <= 1.0

    report = json.loads((output_dir / "report.json").read_text())
    assert "boundary_ambiguity" in report
