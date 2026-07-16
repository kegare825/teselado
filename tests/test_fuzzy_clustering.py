import numpy as np
import pytest

from teselado.clustering.ambiguity import compute_ambiguity
from teselado.clustering.fuzzy_kmeans import FuzzyCMeans
from teselado.tessellation.zones import tessellate


def _well_separated_points(rng: np.random.Generator) -> np.ndarray:
    blob_a = rng.normal(loc=(0.0, 0.0), scale=0.01, size=(30, 2))
    blob_b = rng.normal(loc=(5.0, 5.0), scale=0.01, size=(30, 2))
    return np.vstack([blob_a, blob_b])


def test_fuzzy_cmeans_membership_sums_to_one():
    rng = np.random.default_rng(0)
    points = rng.random((40, 2))
    model = FuzzyCMeans(k=3).fit(points)

    membership = model.membership(points)
    assert membership.shape == (40, 3)
    np.testing.assert_allclose(membership.sum(axis=1), 1.0, atol=1e-6)


def test_fuzzy_cmeans_predict_matches_kmeans_interface():
    rng = np.random.default_rng(1)
    points = rng.random((30, 2))
    model = FuzzyCMeans(k=3).fit(points)

    labels = model.predict(points)
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {0, 1, 2}

    single_label = model.predict(points[0])
    assert single_label in (0, 1, 2)


def test_fuzzy_cmeans_rejects_non_fuzzifier():
    with pytest.raises(ValueError):
        FuzzyCMeans(k=3, m=1.0)


def test_fuzzy_cmeans_is_compatible_with_tessellate():
    rng = np.random.default_rng(2)
    points = rng.random((60, 2))
    model = FuzzyCMeans(k=3).fit(points)
    zones = tessellate(model, points, grid_step=0.05)

    assert len(zones) == 3
    for zone in zones:
        assert zone.polygon.is_valid
        assert zone.order_count >= 0


def test_ambiguity_is_low_for_well_separated_clusters():
    rng = np.random.default_rng(3)
    points = _well_separated_points(rng)
    model = FuzzyCMeans(k=2).fit(points)

    stats = compute_ambiguity(model.membership(points))
    assert stats["boundary_point_ratio"] < 0.1
    assert stats["mean_confidence"] > 0.9


def test_ambiguity_is_high_for_overlapping_clusters():
    rng = np.random.default_rng(4)
    points = rng.normal(loc=(0.0, 0.0), scale=1.0, size=(60, 2))
    model = FuzzyCMeans(k=2).fit(points)

    stats = compute_ambiguity(model.membership(points))
    assert stats["boundary_point_ratio"] > 0.0


def test_compute_ambiguity_handles_empty_input():
    stats = compute_ambiguity(np.empty((0, 2)))
    assert stats["boundary_point_ratio"] == 0.0
