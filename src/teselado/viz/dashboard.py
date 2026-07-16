"""Self-contained HTML dashboard for simulation KPIs."""

from __future__ import annotations

import html
import json
from pathlib import Path


def _fmt(value) -> str:
    return html.escape(str(value))


def build_dashboard_html(metrics: dict, map_filename: str = "map.html") -> str:
    """Render a standalone HTML dashboard from simulation metrics."""
    zones = metrics.get("zones", {})
    zone_rows = []
    for zone_id in sorted(zones, key=lambda z: int(z)):
        z = zones[zone_id]
        zone_rows.append(
            f"<tr>"
            f"<td>{_fmt(zone_id)}</td>"
            f"<td>{_fmt(z.get('order_count', 0))}</td>"
            f"<td>{_fmt(z.get('avg_delivery_time_min', '—'))}</td>"
            f"<td>{_fmt(z.get('sla_hit_rate', '—'))}</td>"
            f"<td>{_fmt(z.get('orders_per_hour', '—'))}</td>"
            f"<td>{_fmt(z.get('courier_utilisation', '—'))}</td>"
            f"</tr>"
        )

    zones_table = "\n".join(zone_rows) or "<tr><td colspan='6'>No zone data</td></tr>"
    metrics_json = html.escape(json.dumps(metrics, indent=2))

    ambiguity = metrics.get("boundary_ambiguity")
    ambiguity_card = ""
    if ambiguity:
        boundary_pct = round(ambiguity.get("boundary_point_ratio", 0) * 100, 1)
        ambiguity_card = (
            "<div class='card'>"
            "<div class='label'>Boundary ambiguity (fuzzy)</div>"
            f"<div class='value'>{_fmt(boundary_pct)}%</div>"
            "</div>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Teselado Dashboard</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --accent: #38bdf8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 1.8rem; }}
    .subtitle {{ color: var(--muted); margin-bottom: 24px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card {{
      background: var(--card);
      border-radius: 12px;
      padding: 16px;
      border: 1px solid #334155;
    }}
    .card .label {{ color: var(--muted); font-size: 0.85rem; }}
    .card .value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card);
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #334155;
    }}
    th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ color: var(--muted); font-size: 0.85rem; text-transform: uppercase; }}
    a {{ color: var(--accent); }}
    pre {{
      background: var(--card);
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 16px;
      overflow: auto;
      color: #cbd5e1;
      font-size: 0.8rem;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Teselado — Delivery Zones Dashboard</h1>
    <p class="subtitle">
      k={_fmt(metrics.get('selected_k', '—'))} zones |
      <a href="{_fmt(map_filename)}">Open interactive map</a>
    </p>

    <div class="cards">
      <div class="card"><div class="label">Total orders</div><div class="value">{_fmt(metrics.get('total_orders', 0))}</div></div>
      <div class="card"><div class="label">Avg delivery</div><div class="value">{_fmt(metrics.get('avg_delivery_time_min', 0))} min</div></div>
      <div class="card"><div class="label">SLA hit rate</div><div class="value">{_fmt(metrics.get('sla_hit_rate', 0))}</div></div>
      <div class="card"><div class="label">Orders / hour</div><div class="value">{_fmt(metrics.get('orders_per_hour', 0))}</div></div>
      <div class="card"><div class="label">Courier utilisation</div><div class="value">{_fmt(metrics.get('courier_utilisation', 0))}</div></div>
      {ambiguity_card}
    </div>

    <h2>Zone KPIs</h2>
    <table>
      <thead>
        <tr>
          <th>Zone</th><th>Orders</th><th>Avg delivery (min)</th>
          <th>SLA hit rate</th><th>Orders/hour</th><th>Utilisation</th>
        </tr>
      </thead>
      <tbody>
        {zones_table}
      </tbody>
    </table>

    <h2>Raw report JSON</h2>
    <pre>{metrics_json}</pre>
  </div>
</body>
</html>
"""


def export_dashboard(metrics: dict, path: Path, map_filename: str = "map.html") -> Path:
    """Write a standalone HTML dashboard."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_dashboard_html(metrics, map_filename), encoding="utf-8")
    return path
