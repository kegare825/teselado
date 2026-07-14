def test_package_imports():
    from teselado import __version__
    from teselado.clustering import Clustered, KMeans
    from teselado.geo import bounding_box

    assert __version__ == "0.2.0"
    assert bounding_box([(0, 0), (1, 2)]) == [(0, 0), (1, 0), (1, 2), (0, 2)]
    assert KMeans is not None
    assert Clustered is not None
