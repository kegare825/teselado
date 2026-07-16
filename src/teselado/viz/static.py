"""Static PNG exports for README and portfolio assets."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from teselado.tessellation.zones import Zone
from teselado.viz.map import ZONE_COLORS


def export_zone_map_png(
    zones: list[Zone],
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    path: Path,
    title: str = "Teselado delivery zones",
) -> Path:
    """Render zone polygons and points to a static PNG."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    for zone in zones:
        color = ZONE_COLORS[zone.zone_id % len(ZONE_COLORS)]
        xs, ys = zone.polygon.exterior.xy
        ax.fill(xs, ys, alpha=0.25, color=color, label=f"Zone {zone.zone_id}")
        ax.plot(xs, ys, color=color, linewidth=1.5)
        cx, cy = zone.centroid
        ax.scatter([cx], [cy], color=color, s=40, marker="x")

    if not restaurants_df.empty:
        ax.scatter(
            restaurants_df["lng"],
            restaurants_df["lat"],
            s=18,
            c="#111827",
            marker="s",
            label="Restaurants",
            alpha=0.8,
        )

    if not orders_df.empty:
        ax.scatter(
            orders_df["lng"],
            orders_df["lat"],
            s=8,
            c="#64748b",
            alpha=0.35,
            label="Orders",
        )

    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def export_kpi_chart_png(metrics: dict, path: Path, title: str = "Simulation KPIs") -> Path:
    """Render headline KPIs as a simple bar chart PNG."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    labels = ["Avg delivery (min)", "SLA hit rate", "Orders/h", "Utilisation"]
    values = [
        float(metrics.get("avg_delivery_time_min", 0)),
        float(metrics.get("sla_hit_rate", 0)) * 100,
        float(metrics.get("orders_per_hour", 0)),
        float(metrics.get("courier_utilisation", 0)) * 100,
    ]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, values, color=["#38bdf8", "#22c55e", "#f59e0b", "#a78bfa"])
    ax.set_title(title)
    ax.set_ylabel("Value")
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
