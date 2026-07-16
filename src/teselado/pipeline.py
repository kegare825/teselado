"""End-to-end tessellation and simulation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from teselado.clustering.ambiguity import compute_ambiguity
from teselado.clustering.factory import build_model
from teselado.clustering.selector import select_k
from teselado.config import Settings
from teselado.ingest.loaders import load_orders, load_orders_df, load_restaurants_df
from teselado.simulation.engine import SimulationParams, simulate
from teselado.tessellation.zones import Zone, tessellate
from teselado.viz.export import export_geojson, export_report
from teselado.viz.render import export_visualizations


@dataclass
class PipelineResult:
    k: int
    zones: list[Zone]
    metrics: dict
    output_dir: Path


def _build_model(method: str, k: int):
    return build_model(method, k)


def _fuzzy_ambiguity_metrics(model, points) -> dict | None:
    from teselado.clustering.fuzzy_kmeans import FuzzyCMeans

    if not isinstance(model, FuzzyCMeans):
        return None
    return compute_ambiguity(model.membership(points))


def run_pipeline(cfg: Settings) -> PipelineResult:
    """Execute ingest → cluster → tessellate → simulate → export."""
    points = load_orders(cfg.data_dir)
    orders_df = load_orders_df(cfg.data_dir)
    restaurants_df = load_restaurants_df(cfg.data_dir)

    k = select_k(
        points,
        k_min=cfg.k_min,
        k_max=cfg.k_max,
        model_factory=lambda kk: _build_model(cfg.method, kk),
    )
    model = _build_model(cfg.method, k).fit(points)
    zones = tessellate(model, points, grid_step=cfg.grid_step)

    metrics = simulate(
        zones,
        orders_df,
        restaurants_df,
        SimulationParams(
            num_couriers=cfg.num_couriers,
            avg_speed_kmh=cfg.avg_speed_kmh,
            sla_minutes=cfg.sla_minutes,
            restaurant_handle_minutes=cfg.restaurant_handle_minutes,
        ),
    )
    metrics["selected_k"] = k
    metrics["clustering_method"] = cfg.method

    ambiguity = _fuzzy_ambiguity_metrics(model, points)
    if ambiguity is not None:
        metrics["boundary_ambiguity"] = ambiguity

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    export_geojson(zones, cfg.output_dir / "zones.geojson")
    export_report(metrics, cfg.output_dir / "report.json")
    export_visualizations(zones, orders_df, restaurants_df, metrics, cfg.output_dir)

    return PipelineResult(k=k, zones=zones, metrics=metrics, output_dir=cfg.output_dir)


def run_cluster_only(
    data_dir: Path,
    k: int,
    output_dir: Path,
    grid_step: float,
    method: str = "kmeans",
) -> PipelineResult:
    """Cluster and tessellate without automatic k selection or simulation."""
    points = load_orders(data_dir)
    model = _build_model(method, k).fit(points)
    zones = tessellate(model, points, grid_step=grid_step)

    metrics = {
        "selected_k": k,
        "clustering_method": method,
        "total_orders": len(points),
        "num_zones": len(zones),
        "zones": {
            z.zone_id: {"order_count": z.order_count} for z in zones
        },
    }

    ambiguity = _fuzzy_ambiguity_metrics(model, points)
    if ambiguity is not None:
        metrics["boundary_ambiguity"] = ambiguity

    output_dir.mkdir(parents=True, exist_ok=True)
    orders_df = load_orders_df(data_dir)
    restaurants_df = load_restaurants_df(data_dir)
    export_geojson(zones, output_dir / "zones.geojson")
    export_report(metrics, output_dir / "report.json")
    export_visualizations(zones, orders_df, restaurants_df, metrics, output_dir)

    return PipelineResult(k=k, zones=zones, metrics=metrics, output_dir=output_dir)
