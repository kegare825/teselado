#!/usr/bin/env python3
"""Generate README screenshots and GitHub Pages demo assets."""

from __future__ import annotations

import shutil
from pathlib import Path

from teselado.config import Settings
from teselado.ingest.loaders import load_orders_df, load_restaurants_df
from teselado.pipeline import run_pipeline
from teselado.viz.static import export_kpi_chart_png, export_zone_map_png


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "outputs"
    images_dir = repo_root / "docs" / "images"
    demo_dir = repo_root / "docs" / "demo"

    cfg = Settings(data_dir=repo_root / "data" / "sample", output_dir=output_dir)
    result = run_pipeline(cfg)

    orders_df = load_orders_df(cfg.data_dir)
    restaurants_df = load_restaurants_df(cfg.data_dir)

    export_zone_map_png(
        result.zones,
        orders_df,
        restaurants_df,
        images_dir / "map.png",
        title=f"Teselado zones (k={result.k}, {cfg.method})",
    )
    export_kpi_chart_png(result.metrics, images_dir / "dashboard.png")

    demo_dir.mkdir(parents=True, exist_ok=True)
    for name in ("map.html", "dashboard.html", "zones.geojson", "report.json"):
        source = output_dir / name
        if source.exists():
            shutil.copy2(source, demo_dir / name)

    print(f"Wrote {images_dir / 'map.png'}")
    print(f"Wrote {images_dir / 'dashboard.png'}")
    print(f"Copied demo assets to {demo_dir}")


if __name__ == "__main__":
    main()
