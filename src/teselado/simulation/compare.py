"""Compare simulation outcomes across different zone counts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from teselado.clustering.kmeans import KMeans
from teselado.config import Settings
from teselado.ingest.loaders import load_orders_df, load_restaurants_df
from teselado.simulation.engine import SimulationParams, simulate
from teselado.tessellation.zones import tessellate


@dataclass
class ZoneComparison:
    k: int
    metrics: dict


def compare_zone_counts(
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    k_values: list[int],
    params: SimulationParams,
    grid_step: float | None = None,
) -> list[ZoneComparison]:
    """Run simulations for multiple fixed k values and return their KPIs."""
    points = orders_df[["lat", "lng"]].to_numpy(dtype=float)
    comparisons: list[ZoneComparison] = []

    for k in k_values:
        model = KMeans(k=k).fit(points)
        zones = tessellate(model, points, grid_step=grid_step)
        metrics = simulate(zones, orders_df, restaurants_df, params)
        metrics["selected_k"] = k
        comparisons.append(ZoneComparison(k=k, metrics=metrics))

    return comparisons


def compare_from_settings(
    cfg: Settings,
    k_values: list[int] | None = None,
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
    )


def export_comparison(comparisons: list[ZoneComparison], path: Path) -> Path:
    import json

    payload = {
        "comparisons": [
            {"k": item.k, "metrics": item.metrics} for item in comparisons
        ]
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
