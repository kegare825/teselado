from pathlib import Path

import pandas as pd
import shapely.geometry

from teselado.tessellation.zones import Zone
from teselado.viz.dashboard import build_dashboard_html, export_dashboard
from teselado.viz.map import build_map, export_map


def _sample_zone(zone_id: int = 0) -> Zone:
    polygon = shapely.geometry.box(37.36, -6.04, 37.38, -6.02)
    return Zone(
        zone_id=zone_id,
        polygon=polygon,
        centroid=(37.37, -6.03),
        order_count=3,
    )


def _sample_orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "restaurant_id": ["r1", "r1"],
            "lat": [37.365, 37.375],
            "lng": [-6.035, -6.025],
            "placed_at": pd.to_datetime(
                ["2024-06-15 12:00:00", "2024-06-15 13:00:00"], utc=True
            ),
            "city": ["demo", "demo"],
        }
    )


def _sample_restaurants() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "restaurant_id": ["r1"],
            "lat": [37.37],
            "lng": [-6.03],
            "city": ["demo"],
        }
    )


def test_build_map_returns_folium_map():
    fmap = build_map(
        [_sample_zone()],
        _sample_orders(),
        _sample_restaurants(),
        metrics={"selected_k": 1, "total_orders": 2, "avg_delivery_time_min": 12.5},
    )
    assert fmap is not None
    assert "37.37" in fmap.get_root().render()


def test_export_map_writes_html(tmp_path: Path):
    path = export_map(
        [_sample_zone()],
        _sample_orders(),
        _sample_restaurants(),
        tmp_path / "map.html",
        metrics={"selected_k": 1, "zones": {0: {"order_count": 2}}},
    )
    content = path.read_text(encoding="utf-8")
    assert "folium" in content.lower() or "leaflet" in content.lower()
    assert path.exists()


def test_export_dashboard_writes_html(tmp_path: Path):
    metrics = {
        "selected_k": 2,
        "total_orders": 10,
        "avg_delivery_time_min": 18.2,
        "sla_hit_rate": 0.8,
        "orders_per_hour": 12.5,
        "courier_utilisation": 0.65,
        "zones": {
            0: {
                "order_count": 5,
                "avg_delivery_time_min": 15.0,
                "sla_hit_rate": 0.9,
                "orders_per_hour": 6.0,
                "courier_utilisation": 0.6,
            }
        },
    }
    path = export_dashboard(metrics, tmp_path / "dashboard.html")
    content = path.read_text(encoding="utf-8")
    assert "Teselado" in content
    assert "18.2" in content
    assert path.exists()


def test_build_dashboard_html_contains_zone_table():
    html = build_dashboard_html(
        {
            "selected_k": 1,
            "total_orders": 1,
            "zones": {0: {"order_count": 1, "avg_delivery_time_min": 9}},
        }
    )
    assert "Zone KPIs" in html
    assert "<td>0</td>" in html
    assert "Avg delivery (min)" in html


def test_export_visualizations_from_pipeline_outputs(tmp_path: Path):
    from teselado.ingest.synthetic import write_sample_dataset
    from teselado.pipeline import run_pipeline
    from teselado.config import Settings

    data_dir = tmp_path / "data"
    output_dir = tmp_path / "outputs"
    write_sample_dataset(data_dir, n_restaurants=10, n_orders=30, seed=1)
    run_pipeline(Settings(data_dir=data_dir, output_dir=output_dir, k_min=2, k_max=3))

    assert (output_dir / "map.html").exists()
    assert (output_dir / "dashboard.html").exists()
