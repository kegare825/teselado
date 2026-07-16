"""Clustering backend factory shared by pipeline and comparison modules."""

from __future__ import annotations

from typing import Callable

from teselado.clustering.fuzzy_kmeans import FuzzyCMeans
from teselado.clustering.kmeans import KMeans

CLUSTER_METHODS: dict[str, Callable[[int], object]] = {
    "kmeans": lambda k: KMeans(k=k),
    "fuzzy": lambda k: FuzzyCMeans(k=k),
}


def build_model(method: str, k: int):
    try:
        factory = CLUSTER_METHODS[method]
    except KeyError as exc:
        raise ValueError(
            f"Unknown clustering method '{method}'. Use one of {sorted(CLUSTER_METHODS)}."
        ) from exc
    return factory(k)
