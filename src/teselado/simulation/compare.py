"""Compare simulation outcomes across zone counts and clustering methods."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from teselado.clustering.ambiguity import compute_ambiguity
from teselado.clustering.factory import CLUSTER_METHODS, build_model
from teselado.clustering.fuzzy_kmeans import FuzzyCMeans
from teselado.config import Settings
from teselado.ingest.loaders import load_orders_df, load_restaurants_df
from teselado.simulation.engine import SimulationParams, simulate
from teselado.tessellation.zones import tessellate


@dataclass
class ZoneComparison:
    k: int
    metrics: dict
    method: str = "kmeans"


@dataclass
class DistanceComparison:
    distance_mode: str
    metrics: dict
    k: int


def compare_distance_models(
    zones: list,
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    params: SimulationParams,
    modes: list[str] | None = None,
) -> list[DistanceComparison]:
    """
    Compare haversine vs OSMnx road-network travel times on the *same* zones.

    Clustering/tessellation is held fixed; only the distance model changes.
    """
    modes = modes or ["haversine", "osmnx"]
    k = len(zones)
    comparisons: list[DistanceComparison] = []

    for mode in modes:
        run_params = SimulationParams(
            num_couriers=params.num_couriers,
            avg_speed_kmh=params.avg_speed_kmh,
            sla_minutes=params.sla_minutes,
            restaurant_handle_minutes=params.restaurant_handle_minutes,
            assigner=params.assigner,
            distance_mode=mode,
            city=params.city,
            graph_cache_dir=params.graph_cache_dir,
        )
        metrics = simulate(zones, orders_df, restaurants_df, run_params)
        metrics["distance_mode"] = mode
        comparisons.append(DistanceComparison(distance_mode=mode, metrics=metrics, k=k))

    return comparisons


def compare_distances_from_settings(
    cfg: Settings,
    k: int | None = None,
    modes: list[str] | None = None,
) -> list[DistanceComparison]:
    """Build zones once, then compare distance models."""
    from teselado.ingest.loaders import load_orders

    orders_df = load_orders_df(cfg.data_dir)
    restaurants_df = load_restaurants_df(cfg.data_dir)
    points = load_orders(cfg.data_dir)

    selected_k = k or cfg.k or 5
    model = build_model(cfg.method, selected_k).fit(points)
    zones = tessellate(model, points, grid_step=cfg.grid_step)

    params = SimulationParams(
        num_couriers=cfg.num_couriers,
        avg_speed_kmh=cfg.avg_speed_kmh,
        sla_minutes=cfg.sla_minutes,
        restaurant_handle_minutes=cfg.restaurant_handle_minutes,
        city=cfg.city,
        graph_cache_dir=cfg.graph_cache_dir,
    )
    return compare_distance_models(
        zones, orders_df, restaurants_df, params, modes=modes
    )


def export_distance_comparison(
    comparisons: list[DistanceComparison], path: Path
) -> Path:
    import json

    payload = {
        "comparisons": [
            {
                "distance_mode": item.distance_mode,
                "k": item.k,
                "metrics": item.metrics,
            }
            for item in comparisons
        ]
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _run_scenario(
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    k: int,
    method: str,
    params: SimulationParams,
    grid_step: float | None,
) -> dict:
    """Cluster, tessellate, and simulate with haversine travel times."""
    points = orders_df[["lat", "lng"]].to_numpy(dtype=float)
    model = build_model(method, k).fit(points)
    zones = tessellate(model, points, grid_step=grid_step)
    metrics = simulate(zones, orders_df, restaurants_df, params)
    metrics["selected_k"] = k
    metrics["clustering_method"] = method
    metrics.setdefault("distance_mode", params.distance_mode)

    if isinstance(model, FuzzyCMeans):
        metrics["boundary_ambiguity"] = compute_ambiguity(model.membership(points))

    return metrics


def compare_zone_counts(
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    k_values: list[int],
    params: SimulationParams,
    grid_step: float | None = None,
    method: str = "kmeans",
) -> list[ZoneComparison]:
    """Run simulations for multiple fixed k values and return their KPIs."""
    comparisons: list[ZoneComparison] = []

    for k in k_values:
        metrics = _run_scenario(
            orders_df, restaurants_df, k, method, params, grid_step
        )
        comparisons.append(ZoneComparison(k=k, metrics=metrics, method=method))

    return comparisons


def compare_clustering_methods(
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    k: int,
    methods: list[str] | None = None,
    params: SimulationParams | None = None,
    grid_step: float | None = None,
) -> list[ZoneComparison]:
    """
    Compare K-Means vs Fuzzy C-Means at the same k.

    Both methods use identical haversine-based simulation parameters so KPI
    differences reflect clustering/tessellation only, not distance modelling.
    """
    params = params or SimulationParams()
    methods = methods or list(CLUSTER_METHODS)

    for method in methods:
        if method not in CLUSTER_METHODS:
            raise ValueError(
                f"Unknown clustering method '{method}'. Use one of {sorted(CLUSTER_METHODS)}."
            )

    return [
        ZoneComparison(
            k=k,
            method=method,
            metrics=_run_scenario(
                orders_df, restaurants_df, k, method, params, grid_step
            ),
        )
        for method in methods
    ]


def compare_from_settings(
    cfg: Settings,
    k_values: list[int] | None = None,
    method: str = "kmeans",
) -> list[ZoneComparison]:
    orders_df = load_orders_df(cfg.data_dir)
    restaurants_df = load_restaurants_df(cfg.data_dir)
    params = SimulationParams(
        num_couriers=cfg.num_couriers,
        avg_speed_kmh=cfg.avg_speed_kmh,
        sla_minutes=cfg.sla_minutes,
        restaurant_handle_minutes=cfg.restaurant_handle_minutes,
    )
    return compare_zone_counts(
        orders_df,
        restaurants_df,
        k_values or [3, 5, 8],
        params,
        grid_step=cfg.grid_step,
        method=method,
    )


def compare_methods_from_settings(
    cfg: Settings,
    k: int | None = None,
    methods: list[str] | None = None,
) -> list[ZoneComparison]:
    orders_df = load_orders_df(cfg.data_dir)
    restaurants_df = load_restaurants_df(cfg.data_dir)
    params = SimulationParams(
        num_couriers=cfg.num_couriers,
        avg_speed_kmh=cfg.avg_speed_kmh,
        sla_minutes=cfg.sla_minutes,
        restaurant_handle_minutes=cfg.restaurant_handle_minutes,
    )
    return compare_clustering_methods(
        orders_df,
        restaurants_df,
        k=k or cfg.k or 5,
        methods=methods,
        params=params,
        grid_step=cfg.grid_step,
    )


def export_comparison(comparisons: list[ZoneComparison], path: Path) -> Path:
    import json

    payload = {
        "comparisons": [
            {
                "k": item.k,
                "method": item.method,
                "metrics": item.metrics,
            }
            for item in comparisons
        ]
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
