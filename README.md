# Teselado

[![CI](https://github.com/kegare825/teselado/actions/workflows/ci.yml/badge.svg)](https://github.com/kegare825/teselado/actions/workflows/ci.yml)

**Geospatial zone tessellation and last-mile delivery simulation.**

Originally prototyped in 2020, refactored into a reproducible open-source pipeline for
portfolio use. The project partitions synthetic delivery demand into operational zones,
evaluates tessellations, and simulates courier assignment with business KPIs.

> *Framework de optimización territorial para operaciones de last-mile delivery:
> clustering espacial → teselado operativo → simulación discreta → KPIs de negocio.*

## Problem

Last-mile delivery operators need to decide how many zones to run and how to staff them.
Too few zones create long routes and SLA breaches; too many zones increase idle couriers
and management overhead.

This project answers: **given order and restaurant locations, how do zone counts affect
delivery time, SLA compliance, and courier utilisation?**

## Solution

```mermaid
flowchart LR
    A[Parquet dataset] --> B[Clustering]
    B --> C[Tessellation]
    C --> D[Simulation]
    D --> E[GeoJSON + KPIs]
    D --> F[Map + Dashboard]
```

1. **Ingest** synthetic restaurants and orders (Parquet, seed=42)
2. **Cluster** delivery coordinates with K-Means and automatic k selection
3. **Tessellate** the city into zone polygons via grid sampling
4. **Simulate** a discrete-event delivery process with greedy courier assignment
5. **Export** GeoJSON, JSON metrics, Folium map, and HTML dashboard

See [docs/architecture.md](docs/architecture.md) for design decisions and trade-offs.

## Stack

| Layer | Tools |
|-------|-------|
| DS | K-Means, elbow k-selection, haversine distances |
| DE | Typer CLI, Parquet, pydantic-settings, reproducible pipeline |
| BI | `report.json`, `dashboard.html`, interactive `map.html` |
| Viz | Folium, Shapely, GeoJSON |
| Quality | pytest, ruff, GitHub Actions |

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

make sample    # generate data/sample (seed=42)
make run       # full pipeline → outputs/
make test      # 22 tests
```

Open the results:

```bash
xdg-open outputs/map.html        # interactive zone map
xdg-open outputs/dashboard.html  # KPI dashboard
```

## CLI

```bash
teselado generate --city demo --restaurants 50 --orders 500
teselado run --k-min 3 --k-max 8
teselado cluster --k 5
teselado compare --k-values 3,5,8
teselado viz
teselado info
```

## Sample results (`data/sample`, k=5)

| KPI | Value |
|-----|-------|
| Orders | 500 |
| Zones (k) | 5 |
| Avg delivery time | 145.5 min |
| SLA hit rate (30 min) | 21.4% |
| Orders / hour | 16.5 |
| Courier utilisation | 8.0% |

### Zone comparison (`teselado compare`)

| k | Avg delivery | SLA hit | Orders/h |
|---|-------------|---------|----------|
| 3 | 147.3 min | 25.6% | 16.4 |
| 5 | 145.5 min | 21.4% | 16.5 |
| 8 | **38.1 min** | **55.2%** | **19.9** |

More zones improve delivery time on this synthetic dataset — useful for scenario analysis.

### Visual outputs

After `make run`, open `outputs/map.html` to explore:

- coloured zone polygons
- restaurant and order points
- per-zone legend with order counts

> **Portfolio tip:** capture a screenshot of `outputs/map.html` and save it as
> `docs/images/map.png` for your CV or README.

## Project structure

```
src/teselado/
├── ingest/        # synthetic data + loaders
├── clustering/    # K-Means + k selector
├── tessellation/  # zone polygons
├── simulation/    # discrete-event engine
├── viz/           # map + dashboard export
└── pipeline.py    # orchestration
```

## Technical decisions

- **K-Means + elbow**: fast, interpretable baseline for zone partitioning
- **Greedy assigner**: nearest available courier; easy to explain, good for prototyping
- **Synthetic data**: no proprietary warehouse dependencies; safe for public repos
- **Haversine distances**: no OSM graph required; swappable later for road networks

## Roadmap

- [ ] OSM / Overpass restaurant ingestion (`ingest/osm.py`)
- [ ] Road-network distances with OSMnx
- [ ] Silhouette / HDBSCAN for k selection
- [ ] MIP assigner with OR-Tools
- [ ] Streamlit live dashboard

## Development

```bash
make lint
make test
make compare
```

CI runs on Python 3.11 and 3.12 via GitHub Actions.

## License

MIT — see [LICENSE](LICENSE).

## Authors

Carlos Moreno Morera & Aarón González (original prototype, 2020).
