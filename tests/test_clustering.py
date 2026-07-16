import numpy as np

from teselado.clustering.kmeans import KMeans


def test_kmeans_predict_returns_array():
    rng = np.random.default_rng(0)
    points = rng.random((30, 2))
    model = KMeans(k=3).fit(points)
    labels = model.predict(points)
    assert labels.shape == (30,)
    assert set(labels.tolist()) <= {0, 1, 2}


def test_kmeans_single_point():
    points = np.array([[0.0, 0.0], [1.0, 1.0], [5.0, 5.0]])
    model = KMeans(k=2).fit(points)
    label = model.predict(np.array([0.1, 0.1]))
    assert label in (0, 1)
