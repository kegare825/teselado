# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Fixed
- Courier utilisation was computed from order placement instead of service start, so
  queue wait was counted as busy time and overlapping waits pushed the ratio above 1
  (reported as "8.0%" while the actual value was 8.0). Busy time now starts at
  `assigned_at`; utilisation is a 0-1 ratio. Regression test added.
- `pages.yml` did not install the `[roads]` extra required by the asset script. The
  workflow now installs it and caches the OSM graph; `generate_portfolio_assets.py`
  falls back to a haversine-only chart (`--no-roads`) if OSMnx or Overpass is unavailable.

### Changed
- README: KPI tables regenerated with the real CLI, KPI definitions documented next to
  the numbers, note that k=8 gains are a courier-capacity effect, live-demo link
  documented as requiring GitHub Pages to be enabled, neutral technical wording.
- `docs/architecture.md`: MIP assigner documented as implemented (not a roadmap item);
  KPI definitions added.
- `REFACTOR_PLAN.md`: kept as a historical document with a status header.
- `test_mip_assigner`: MIP path gated with `pytest.importorskip("ortools")`; greedy
  fallback tested explicitly.

### Removed
- Legacy `Clustered` class (`clustering/fuzzy.py`); `FuzzyCMeans` is the only fuzzy backend.

## [0.3.0] - 2026-07-16

### Added
- Fuzzy C-Means as a selectable clustering backend (`--method fuzzy`).
- `teselado compare-distances`: haversine vs OSMnx road-network travel times on the
  same zone tessellation (`simulation/distance.py`, `[roads]` extra).
- `boundary_ambiguity` KPI in `report.json` for fuzzy runs.
- `teselado compare-methods` to compare K-Means vs Fuzzy C-Means at the same k
  using identical haversine simulation parameters.
- OpenStreetMap restaurant ingestion via Overpass (`teselado fetch-osm`).
- Optional MIP assigner with OR-Tools (`SimulationParams(assigner="mip")`).
- Streamlit dashboard (`streamlit run streamlit_app.py`).
- Static PNG exports and portfolio asset generator (`scripts/generate_portfolio_assets.py`).
- GitHub Pages demo workflow (`.github/workflows/pages.yml`).
- Analysis notebook (`notebooks/zone_analysis.ipynb`).
- Coverage and mypy checks in CI.

### Changed
- Author attribution: Aarón González as project author; Carlos Moreno Morera credited
  as contributor of the original K-Means module only.
- README enriched with business insight, screenshots, and demo link.
- Refactor plan marked as completed (historical document).

### Notes
- `teselado compare-methods` and `teselado compare` keep haversine distances for every
  run so that clustering-method / k comparisons isolate the tessellation. Road-network
  (OSMnx) distances are used by `teselado compare-distances`, which holds the
  tessellation fixed and switches only the travel-time model.

## [0.2.0] - 2026-07-16

### Added
- End-to-end pipeline: ingest → cluster → tessellate → simulate → export.
- Typer CLI, synthetic dataset, Folium map, HTML dashboard.
- pytest suite and GitHub Actions CI.

## [0.1.0] - 2020

- Original prototype: K-Means / Fuzzy C-Means tessellation and delivery simulation.
