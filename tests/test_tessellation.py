import numpy as np

from teselado.clustering.kmeans import KMeans
from teselado.tessellation.zones import tessellate


def test_tessellate_produces_valid_polygons():
    rng = np.random.default_rng(1)
    points = rng.random((60, 2))
    model = KMeans(k=3).fit(points)
    zones = tessellate(model, points, grid_step=0.05)

    assert len(zones) == 3
    for zone in zones:
        assert zone.polygon.is_valid
        assert zone.order_count >= 0
