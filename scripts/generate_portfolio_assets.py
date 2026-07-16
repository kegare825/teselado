#!/usr/bin/env python3
"""Generate README screenshots and GitHub Pages demo assets."""

from __future__ import annotations

import shutil
from pathlib import Path

from teselado.config import Settings
from teselado.ingest.loaders import load_orders_df, load_restaurants_df
from teselado.pipeline import run_pipeline
from teselado.simulation.compare import compare_distances_from_settings
from teselado.viz.static import export_distance_comparison_png, export_zone_map_png


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "outputs"
    images_dir = repo_root / "docs" / "images"
    demo_dir = repo_root / "docs" / "demo"
    cache_dir = repo_root / "data" / "cache" / "graphs"

    cfg = Settings(
        data_dir=repo_root / "data" / "sample",
        output_dir=output_dir,
        method="fuzzy",
        k_min=3,
        k_max=8,
        graph_cache_dir=cache_dir,
    )
    result = run_pipeline(cfg)

    orders_df = load_orders_df(cfg.data_dir)
    restaurants_df = load_restaurants_df(cfg.data_dir)

    export_zone_map_png(
        result.zones,
        orders_df,
        restaurants_df,
        images_dir / "map.png",
        title=f"Delivery zones — k={result.k} (Fuzzy C-Means tessellation)",
        subtitle=(
            "Coloured polygons = operational zones. "
            "Squares = restaurants, grey dots = order drop-offs."
        ),
    )

    distance_comparisons = compare_distances_from_settings(
        cfg,
        k=result.k,
        modes=["haversine", "osmnx"],
    )
    export_distance_comparison_png(
        distance_comparisons,
        images_dir / "distance_comparison.png",
    )

    demo_dir.mkdir(parents=True, exist_ok=True)
    for name in ("map.html", "dashboard.html", "zones.geojson", "report.json"):
        source = output_dir / name
        if source.exists():
            shutil.copy2(source, demo_dir / name)

    print(f"Wrote {images_dir / 'map.png'}")
    print(f"Wrote {images_dir / 'distance_comparison.png'}")
    print(f"Copied demo assets to {demo_dir}")


if __name__ == "__main__":
    main()
