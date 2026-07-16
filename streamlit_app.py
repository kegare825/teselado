"""Streamlit dashboard for exploring pipeline outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DEFAULT_OUTPUT = Path("outputs")
DEFAULT_DATA = Path("data/sample")


def _load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    st.set_page_config(page_title="Teselado Dashboard", layout="wide")
    st.title("Teselado — Delivery Zones")
    st.caption("Live view of `report.json` and dataset summary.")

    output_dir = Path(st.sidebar.text_input("Output directory", value=str(DEFAULT_OUTPUT)))
    data_dir = Path(st.sidebar.text_input("Dataset directory", value=str(DEFAULT_DATA)))
    report_path = output_dir / "report.json"

    if not report_path.exists():
        st.warning(f"No report found at `{report_path}`. Run `teselado run` first.")
        st.code("teselado run --method fuzzy")
        return

    metrics = _load_report(report_path)
    method = metrics.get("clustering_method", "kmeans")
    k = metrics.get("selected_k", "—")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Method", method)
    col2.metric("Zones (k)", k)
    col3.metric("Avg delivery (min)", metrics.get("avg_delivery_time_min", 0))
    col4.metric("SLA hit rate", metrics.get("sla_hit_rate", 0))
    col5.metric("Orders/h", metrics.get("orders_per_hour", 0))

    if "boundary_ambiguity" in metrics:
        amb = metrics["boundary_ambiguity"]
        st.info(
            "Boundary ambiguity (fuzzy): "
            f"{amb.get('boundary_point_ratio', 0) * 100:.1f}% of orders near a zone edge."
        )

    map_path = output_dir / "map.html"
    if map_path.exists():
        st.subheader("Interactive map")
        st.components.v1.html(map_path.read_text(encoding="utf-8"), height=520, scrolling=True)
    else:
        st.write("Run `teselado viz` to generate `map.html`.")

    st.subheader("Zone KPIs")
    zones = metrics.get("zones", {})
    rows = []
    for zone_id, zone_metrics in sorted(zones.items(), key=lambda item: int(item[0])):
        rows.append({"zone": zone_id, **zone_metrics})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    orders_path = data_dir / "orders.parquet"
    if orders_path.exists():
        orders_df = pd.read_parquet(orders_path)
        st.subheader("Dataset snapshot")
        st.write(f"{len(orders_df)} orders loaded from `{orders_path}`")
        st.scatter_chart(orders_df, x="lng", y="lat", height=300)

    with st.expander("Raw report JSON"):
        st.json(metrics)


if __name__ == "__main__":
    main()
