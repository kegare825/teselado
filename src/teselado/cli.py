from enum import Enum
from pathlib import Path

import typer

from teselado import __version__
from teselado.config import Settings
from teselado.ingest.loaders import dataset_summary
from teselado.ingest.synthetic import list_cities, write_sample_dataset
from teselado.pipeline import run_cluster_only, run_pipeline
from teselado.simulation.compare import (
    compare_distances_from_settings,
    compare_from_settings,
    compare_methods_from_settings,
    export_comparison,
    export_distance_comparison,
)
from teselado.viz.render import export_visualizations_from_files

app = typer.Typer(
    name="teselado",
    help="Geospatial zone tessellation and last-mile delivery simulation.",
    no_args_is_help=True,
)


class ClusterMethod(str, Enum):
    """Clustering backend: hard K-Means or Fuzzy C-Means."""

    kmeans = "kmeans"
    fuzzy = "fuzzy"


@app.command()
def version() -> None:
    """Show package version."""
    typer.echo(f"teselado {__version__}")


@app.command()
def generate(
    city: str = typer.Option("demo", help="City key for synthetic data."),
    restaurants: int = typer.Option(50, help="Number of restaurants."),
    orders: int = typer.Option(500, help="Number of orders."),
    output: Path = typer.Option(Path("data/sample"), help="Output directory."),
    seed: int = typer.Option(42, help="Random seed."),
) -> None:
    """Generate synthetic restaurant and order datasets."""
    rest_path, orders_path, metadata_path = write_sample_dataset(
        output,
        city=city,
        n_restaurants=restaurants,
        n_orders=orders,
        seed=seed,
    )
    typer.echo(f"Wrote {rest_path}")
    typer.echo(f"Wrote {orders_path}")
    typer.echo(f"Wrote {metadata_path}")


@app.command("list-cities")
def list_cities_cmd() -> None:
    """List available synthetic cities and bounding boxes."""
    for entry in list_cities():
        typer.echo(
            f"{entry['city']}: {entry['label']} "
            f"[{entry['lat_min']}, {entry['lat_max']}] x "
            f"[{entry['lng_min']}, {entry['lng_max']}]"
        )


@app.command()
def info(
    data_dir: Path = typer.Option(Path("data/sample"), help="Dataset directory."),
) -> None:
    """Show a summary of a dataset directory."""
    summary = dataset_summary(data_dir)
    typer.echo(f"City: {summary['city']}")
    typer.echo(f"Restaurants: {summary['n_restaurants']}")
    typer.echo(f"Orders: {summary['n_orders']}")
    typer.echo(
        f"Order timestamps: {summary['date_range']['min']} → {summary['date_range']['max']}"
    )


@app.command()
def run(
    city: str = typer.Option("demo", help="City label (used when generating missing data)."),
    data_dir: Path = typer.Option(Path("data/sample"), help="Input data directory."),
    output: Path = typer.Option(Path("outputs"), help="Output directory."),
    method: ClusterMethod = typer.Option(
        ClusterMethod.kmeans, help="Clustering backend: kmeans or fuzzy."
    ),
    k_min: int = typer.Option(3, help="Minimum k for auto selection."),
    k_max: int = typer.Option(8, help="Maximum k for auto selection."),
    grid_step: float | None = typer.Option(None, help="Tessellation grid step in degrees."),
) -> None:
    """Run the full pipeline: cluster → tessellate → simulate → export."""
    if not (data_dir / "orders.parquet").exists():
        typer.echo(f"No data in {data_dir}, generating synthetic sample...")
        write_sample_dataset(data_dir, city=city)

    cfg = Settings(
        data_dir=data_dir,
        output_dir=output,
        city=city,
        method=method.value,
        k_min=k_min,
        k_max=k_max,
        grid_step=grid_step,
    )
    result = run_pipeline(cfg)
    typer.echo(f"Selected k={result.k}, zones={len(result.zones)}, method={method.value}")
    typer.echo(f"Wrote {result.output_dir / 'zones.geojson'}")
    typer.echo(f"Wrote {result.output_dir / 'report.json'}")
    typer.echo(f"Wrote {result.output_dir / 'map.html'}")
    typer.echo(f"Wrote {result.output_dir / 'dashboard.html'}")
    typer.echo(f"Avg delivery time: {result.metrics['avg_delivery_time_min']} min")
    typer.echo(f"Orders/hour: {result.metrics.get('orders_per_hour', 0)}")
    typer.echo(f"Courier utilisation: {result.metrics.get('courier_utilisation', 0)}")
    if "boundary_ambiguity" in result.metrics:
        amb = result.metrics["boundary_ambiguity"]
        typer.echo(
            f"Boundary ambiguity: {amb['boundary_point_ratio'] * 100:.1f}% of orders "
            f"sit near a zone edge (mean membership margin {amb['mean_margin']})"
        )


@app.command("compare-distances")
def compare_distances(
    data_dir: Path = typer.Option(Path("data/sample"), help="Input data directory."),
    output: Path = typer.Option(
        Path("outputs/distance_comparison.json"), help="Output JSON path."
    ),
    k: int = typer.Option(5, help="Fixed k for zone tessellation."),
    modes: str = typer.Option(
        "haversine,osmnx",
        help="Comma-separated distance models on the same zones.",
    ),
    city: str = typer.Option("demo", help="City key for OSMnx graph bbox/cache."),
) -> None:
    """Compare haversine vs OSMnx road distances on the same zone tessellation."""
    cfg = Settings(data_dir=data_dir, city=city, k=k, method="fuzzy")
    mode_list = [value.strip() for value in modes.split(",") if value.strip()]
    comparisons = compare_distances_from_settings(cfg, k=k, modes=mode_list)
    export_distance_comparison(comparisons, output)

    for item in comparisons:
        m = item.metrics
        typer.echo(
            f"distance={item.distance_mode}, k={item.k}: "
            f"avg_delivery={m['avg_delivery_time_min']} min, "
            f"sla={m['sla_hit_rate']}, orders/h={m['orders_per_hour']}, "
            f"utilisation={m['courier_utilisation']}"
        )
    typer.echo(f"Wrote {output}")


@app.command("compare-methods")
def compare_methods(
    data_dir: Path = typer.Option(Path("data/sample"), help="Input data directory."),
    output: Path = typer.Option(
        Path("outputs/method_comparison.json"), help="Output JSON path."
    ),
    k: int = typer.Option(5, help="Fixed k for both clustering methods."),
    methods: str = typer.Option(
        "kmeans,fuzzy",
        help="Comma-separated clustering methods (same haversine simulation).",
    ),
) -> None:
    """Compare K-Means vs Fuzzy C-Means at the same k (clustering-only comparison)."""
    cfg = Settings(data_dir=data_dir, k=k)
    method_list = [value.strip() for value in methods.split(",") if value.strip()]
    comparisons = compare_methods_from_settings(cfg, k=k, methods=method_list)
    export_comparison(comparisons, output)

    for item in comparisons:
        m = item.metrics
        line = (
            f"method={item.method}, k={item.k}: "
            f"avg_delivery={m['avg_delivery_time_min']} min, "
            f"sla={m['sla_hit_rate']}, orders/h={m['orders_per_hour']}, "
            f"utilisation={m['courier_utilisation']}"
        )
        if "boundary_ambiguity" in m:
            amb = m["boundary_ambiguity"]
            line += f", boundary_ambiguity={amb['boundary_point_ratio']}"
        typer.echo(line)
    typer.echo(f"Wrote {output}")


@app.command()
def compare(
    data_dir: Path = typer.Option(Path("data/sample"), help="Input data directory."),
    output: Path = typer.Option(Path("outputs/comparison.json"), help="Output JSON path."),
    k_values: str = typer.Option("3,5,8", help="Comma-separated k values to compare."),
) -> None:
    """Compare simulation KPIs across multiple zone counts."""
    cfg = Settings(data_dir=data_dir)
    values = [int(v.strip()) for v in k_values.split(",") if v.strip()]
    comparisons = compare_from_settings(cfg, k_values=values)
    export_comparison(comparisons, output)

    for item in comparisons:
        m = item.metrics
        typer.echo(
            f"k={item.k} ({item.method}): avg_delivery={m['avg_delivery_time_min']} min, "
            f"sla={m['sla_hit_rate']}, orders/h={m['orders_per_hour']}, "
            f"utilisation={m['courier_utilisation']}"
        )
    typer.echo(f"Wrote {output}")


@app.command()
def cluster(
    input: Path = typer.Option(Path("data/sample"), "--input", help="Input data directory."),
    k: int = typer.Option(5, help="Fixed number of clusters."),
    output: Path = typer.Option(Path("outputs"), help="Output directory."),
    method: ClusterMethod = typer.Option(
        ClusterMethod.kmeans, help="Clustering backend: kmeans or fuzzy."
    ),
    grid_step: float | None = typer.Option(None, help="Tessellation grid step."),
) -> None:
    """Run clustering and tessellation with a fixed k."""
    result = run_cluster_only(
        input, k=k, output_dir=output, grid_step=grid_step or 0.003, method=method.value
    )
    typer.echo(f"k={result.k}, zones={len(result.zones)}, method={method.value}")
    typer.echo(f"Wrote {result.output_dir / 'zones.geojson'}")
    typer.echo(f"Wrote {result.output_dir / 'map.html'}")
    typer.echo(f"Wrote {result.output_dir / 'dashboard.html'}")
    if "boundary_ambiguity" in result.metrics:
        amb = result.metrics["boundary_ambiguity"]
        typer.echo(
            f"Boundary ambiguity: {amb['boundary_point_ratio'] * 100:.1f}% of orders "
            f"sit near a zone edge (mean membership margin {amb['mean_margin']})"
        )


@app.command("fetch-osm")
def fetch_osm(
    city: str = typer.Option("demo", help="City key with a predefined bbox."),
    output: Path = typer.Option(Path("data/osm"), help="Output directory."),
    cache_dir: Path = typer.Option(Path("data/cache/osm"), help="Overpass cache directory."),
) -> None:
    """Fetch restaurant POIs from OpenStreetMap and write restaurants.parquet."""
    from teselado.ingest.osm import load_osm_restaurants

    restaurants = load_osm_restaurants(city, cache_dir=cache_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "restaurants.parquet"
    restaurants.to_parquet(path, index=False)
    typer.echo(f"Fetched {len(restaurants)} restaurants from OSM")
    typer.echo(f"Wrote {path}")


@app.command()
def viz(
    input: Path = typer.Option(Path("outputs"), "--input", help="Output directory."),
    data_dir: Path = typer.Option(Path("data/sample"), help="Source dataset directory."),
    zones: Path | None = typer.Option(None, help="GeoJSON path override."),
    report: Path | None = typer.Option(None, help="Report JSON path override."),
) -> None:
    """Build or refresh map.html and dashboard.html from pipeline outputs."""
    paths = export_visualizations_from_files(
        output_dir=input,
        data_dir=data_dir,
        zones_path=zones,
        report_path=report,
    )
    typer.echo(f"Wrote {paths['map']}")
    typer.echo(f"Wrote {paths['dashboard']}")
