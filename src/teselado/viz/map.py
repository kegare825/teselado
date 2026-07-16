"""Interactive Folium map export."""

from __future__ import annotations

from pathlib import Path

import folium
import pandas as pd

from teselado.tessellation.zones import Zone

ZONE_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def _zone_color(zone_id: int) -> str:
    return ZONE_COLORS[zone_id % len(ZONE_COLORS)]


def _polygon_locations(polygon) -> list[list[float]]:
    """Convert a shapely polygon exterior to Folium [lat, lng] pairs."""
    return [[float(lat), float(lng)] for lat, lng in polygon.exterior.coords]


def build_map(
    zones: list[Zone],
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    metrics: dict | None = None,
) -> folium.Map:
    """Build a Folium map with zone polygons, orders, and restaurants."""
    if orders_df.empty:
        center = [0.0, 0.0]
    else:
        center = [
            float(orders_df["lat"].mean()),
            float(orders_df["lng"].mean()),
        ]

    zone_metrics = (metrics or {}).get("zones", {})
    title = f"Teselado — k={metrics.get('selected_k', len(zones))}" if metrics else "Teselado zones"
    fmap = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

    legend_rows = []
    for zone in zones:
        color = _zone_color(zone.zone_id)
        zmetrics = zone_metrics.get(zone.zone_id, zone_metrics.get(str(zone.zone_id), {}))
        avg_delivery = zmetrics.get("avg_delivery_time_min", "—")
        legend_rows.append(
            f"<span style='color:{color}'>■</span> Zone {zone.zone_id}: "
            f"{zone.order_count} orders, avg {avg_delivery} min"
        )

        folium.Polygon(
            locations=_polygon_locations(zone.polygon),
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.25,
            popup=(
                f"Zone {zone.zone_id}<br>"
                f"Orders: {zone.order_count}<br>"
                f"Avg delivery: {avg_delivery} min"
            ),
        ).add_to(fmap)

        folium.CircleMarker(
            location=[zone.centroid[0], zone.centroid[1]],
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=f"Zone {zone.zone_id} centroid",
        ).add_to(fmap)

    for row in restaurants_df.itertuples(index=False):
        folium.CircleMarker(
            location=[float(row.lat), float(row.lng)],
            radius=4,
            color="#16a34a",
            fill=True,
            fill_opacity=0.9,
            popup=f"Restaurant {row.restaurant_id}",
        ).add_to(fmap)

    for row in orders_df.itertuples(index=False):
        folium.CircleMarker(
            location=[float(row.lat), float(row.lng)],
            radius=2,
            color="#333333",
            fill=True,
            fill_opacity=0.5,
            popup=f"Order {row.order_id}",
        ).add_to(fmap)

    if metrics:
        summary = (
            f"<b>{title}</b><br>"
            f"Orders: {metrics.get('total_orders', len(orders_df))}<br>"
            f"Avg delivery: {metrics.get('avg_delivery_time_min', '—')} min<br>"
            f"SLA hit rate: {metrics.get('sla_hit_rate', '—')}<br>"
            f"Orders/hour: {metrics.get('orders_per_hour', '—')}<br>"
            f"Courier utilisation: {metrics.get('courier_utilisation', '—')}"
        )
    else:
        summary = f"<b>{title}</b>"

    legend_html = (
        "<div style='position: fixed; bottom: 30px; left: 30px; z-index: 9999; "
        "background: white; padding: 12px 14px; border: 1px solid #ccc; "
        "border-radius: 8px; font-size: 13px; max-width: 320px;'>"
        f"{summary}<hr style='margin:8px 0'>"
        + "<br>".join(legend_rows)
        + "</div>"
    )
    fmap.get_root().html.add_child(folium.Element(legend_html))  # type: ignore[attr-defined]
    return fmap


def export_map(
    zones: list[Zone],
    orders_df: pd.DataFrame,
    restaurants_df: pd.DataFrame,
    path: Path,
    metrics: dict | None = None,
) -> Path:
    """Write an interactive Folium map to HTML."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmap = build_map(zones, orders_df, restaurants_df, metrics)
    fmap.save(str(path))
    return path
