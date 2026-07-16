"""Static PNG exports for README and portfolio assets."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from teselado.simulation.compare import DistanceComparison
from teselado.tessellation.zones import Zone
from teselado.viz.map import ZONE_COLORS


def _ratio_as_percent(value: float) -> float:
    return value * 100.0 if value <= 1.0 else value


def export_zone_map_png(
    zones: list[Zone],
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    path: Path,
    title: str = "Delivery zones (tessellation)",
    subtitle: str | None = None,
) -> Path:
    """
    Render zone polygons and points to a static PNG.

    Internal coordinates are stored as (lat, lng) but matplotlib expects
    x=longitude, y=latitude.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    for zone in zones:
        color = ZONE_COLORS[zone.zone_id % len(ZONE_COLORS)]
        zone_lats, zone_lngs = zone.polygon.exterior.xy
        ax.fill(
            zone_lngs,
            zone_lats,
            alpha=0.35,
            color=color,
            label=f"Zone {zone.zone_id} ({zone.order_count} orders)",
        )
        ax.plot(zone_lngs, zone_lats, color=color, linewidth=2)
        clat, clng = zone.centroid
        ax.scatter([clng], [clat], color=color, s=55, marker="x", linewidths=2)

    if not restaurants_df.empty:
        ax.scatter(
            restaurants_df["lng"],
            restaurants_df["lat"],
            s=22,
            c="#111827",
            marker="s",
            label="Restaurants",
            alpha=0.9,
            zorder=4,
        )

    if not orders_df.empty:
        ax.scatter(
            orders_df["lng"],
            orders_df["lat"],
            s=6,
            c="#64748b",
            alpha=0.25,
            label="Orders",
            zorder=3,
        )
        lng_pad = max((orders_df["lng"].max() - orders_df["lng"].min()) * 0.08, 0.01)
        lat_pad = max((orders_df["lat"].max() - orders_df["lat"].min()) * 0.08, 0.01)
        ax.set_xlim(orders_df["lng"].min() - lng_pad, orders_df["lng"].max() + lng_pad)
        ax.set_ylim(orders_df["lat"].min() - lat_pad, orders_df["lat"].max() + lat_pad)

    ax.set_title(title, fontsize=13, fontweight="bold")
    if subtitle:
        ax.text(
            0.5,
            1.01,
            subtitle,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=10,
            color="#475569",
        )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.95)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25, linewidth=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def export_distance_comparison_png(
    comparisons: list[DistanceComparison],
    path: Path,
    title: str = "Haversine vs OSM road network (same zones, same k)",
) -> Path:
    """Grouped bar chart comparing KPIs across distance models."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    labels = ["Avg delivery (min)", "SLA hit (%)", "Orders/h", "Utilisation (%)"]
    metric_keys = [
        "avg_delivery_time_min",
        "sla_hit_rate",
        "orders_per_hour",
        "courier_utilisation",
    ]

    x = np.arange(len(labels))
    width = 0.35 if len(comparisons) == 2 else 0.8 / max(len(comparisons), 1)

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"haversine": "#38bdf8", "osmnx": "#f97316"}

    for idx, item in enumerate(comparisons):
        values = []
        for key in metric_keys:
            raw = float(item.metrics.get(key, 0))
            if key in {"sla_hit_rate", "courier_utilisation"}:
                values.append(_ratio_as_percent(raw))
            else:
                values.append(raw)
        offset = (idx - (len(comparisons) - 1) / 2) * width
        bars = ax.bar(
            x + offset,
            values,
            width,
            label=item.distance_mode,
            color=colors.get(item.distance_mode, None),
        )
        for bar, value in zip(bars, values, strict=True):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_ylabel("Value")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(title="Distance model")
    ax.text(
        0.5,
        -0.18,
        "Same zone tessellation and courier assigner; only travel-time calculation changes.",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="#475569",
    )
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path
