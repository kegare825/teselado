# Changelog

All notable changes to this project are documented in this file.

## [0.3.0] - 2026-07-16

### Added
- Fuzzy C-Means as a selectable clustering backend (`--method fuzzy`).
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
- Haversine distances are intentionally kept for all simulations so clustering-method
  comparisons remain apples-to-apples. Road-network distances are not used.

## [0.2.0] - 2026-07-16

### Added
- End-to-end pipeline: ingest → cluster → tessellate → simulate → export.
- Typer CLI, synthetic dataset, Folium map, HTML dashboard.
- pytest suite and GitHub Actions CI.

## [0.1.0] - 2020

- Original prototype: K-Means / Fuzzy C-Means tessellation and delivery simulation.
