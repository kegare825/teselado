#!/usr/bin/env python3
"""Generate README screenshots and GitHub Pages demo assets.

Usage:
    python scripts/generate_portfolio_assets.py            # haversine + OSMnx (if available)
    python scripts/generate_portfolio_assets.py --no-roads # haversine only, never touches OSMnx

The OSMnx comparison needs the ``[roads]`` extra and (on a cold cache) network access
to Overpass. If either is missing the script logs a warning and falls back to a
haversine-only chart instead of failing, so the Pages workflow always produces assets.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from teselado.config import Settings
from teselado.ingest.loaders import load_orders_df, load_restaurants_df
from teselado.pipeline import run_pipeline
from teselado.simulation.compare import DistanceComparison, compare_distances_from_settings
from teselado.viz.static import export_distance_comparison_png, export_zone_map_png


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--no-roads",
        action="store_true",
        help="Skip the OSMnx road-network run; produce a haversine-only comparison chart.",
    )
    return parser.parse_args(argv)


def _distance_comparisons(cfg: Settings, k: int, use_roads: bool) -> list[DistanceComparison]:
    if use_roads:
        try:
            return compare_distances_from_settings(cfg, k=k, modes=["haversine", "osmnx"])
        except ImportError as exc:
            print(f"WARNING: OSMnx unavailable ({exc}); falling back to haversine only.")
        except Exception as exc:  # noqa: BLE001 - network/Overpass failures must not abort CI
            print(f"WARNING: OSMnx comparison failed ({type(exc).__name__}: {exc}); "
                  "falling back to haversine only.")
    return compare_distances_from_settings(cfg, k=k, modes=["haversine"])


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
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

    distance_comparisons = _distance_comparisons(cfg, result.k, use_roads=not args.no_roads)
    for item in distance_comparisons:
        m = item.metrics
        print(
            f"distance={item.distance_mode}, k={item.k}: "
            f"avg_delivery={m['avg_delivery_time_min']} min, sla={m['sla_hit_rate']}, "
            f"orders/h={m['orders_per_hour']}, utilisation={m['courier_utilisation']}"
        )
    title = None
    if len(distance_comparisons) == 1:
        title = "Haversine baseline (OSMnx road network not available in this run)"
    export_distance_comparison_png(
        distance_comparisons,
        images_dir / "distance_comparison.png",
        **({"title": title} if title else {}),
    )

    demo_dir.mkdir(parents=True, exist_ok=True)
    for name in ("map.html", "dashboard.html", "zones.geojson", "report.json"):
        source = output_dir / name
        if source.exists():
            shutil.copy2(source, demo_dir / name)

    print(f"Wrote {images_dir / 'map.png'}")
    print(f"Wrote {images_dir / 'distance_comparison.png'}")
    print(f"Copied demo assets to {demo_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
