# Plan de refactor — Teselado

> **Estado (2026-07-16): completado.** El pipeline `ingest → cluster → tessellate → simulate → report`
> es ejecutable con `make run`, incluye CI, tests, documentación de portfolio, demo en GitHub Pages,
> comparación K-Means vs Fuzzy C-Means (haversine), ingest OSM, assigner MIP opcional y dashboard Streamlit.
> Este documento se conserva como registro histórico del refactor.

> **Objetivo original:** convertir el prototipo de 2020 en un proyecto de portfolio público, ejecutable sin credenciales, sin referencias a Just Eat, y demostrable como caso de uso senior DS/DE/BI full stack.

**Estado al inicio del refactor:** prototipo roto, sin README, con SQL interno de warehouse, librería `just-simulate` vendoreada, y `__pycache__` en git.

**Estado objetivo:** pipeline `ingest → cluster → tessellate → simulate → report` reproducible en 3 comandos. ✅

---

## Resumen ejecutivo

| Dimensión | Hoy | Objetivo |
|-----------|-----|----------|
| Ejecutable | No (`main.py` con `IndentationError`) | `make run` o `uv run teselado run` |
| Datos | Queries a `REDACTED_GCP_PROJECT` | Dataset sintético + Parquet versionado |
| Referencias JE | ~15 archivos afectados | 0 |
| Tests propios | 0 | ≥ 80 % en módulos core |
| Documentación | Ninguna | README + diagrama + screenshots |
| CI | Ninguna | GitHub Actions (lint + test) |

**Esfuerzo estimado:** 2–3 semanas (1 persona, tiempo parcial).

---

## Arquitectura objetivo

```
teselado/
├── README.md
├── pyproject.toml
├── Makefile
├── .gitignore
├── .github/workflows/ci.yml
├── data/
│   ├── raw/                    # generado, no commiteado
│   └── sample/                 # subset fijo para CI y demo
│       ├── restaurants.parquet
│       └── orders.parquet
├── outputs/                    # artefactos de ejecución (gitignored)
│   ├── zones.geojson
│   ├── simulation_metrics.json
│   └── map.html
├── src/teselado/
│   ├── __init__.py
│   ├── __main__.py             # python -m teselado
│   ├── cli.py                  # Typer CLI
│   ├── config.py               # pydantic-settings, sin SQL hardcodeado
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── synthetic.py        # generador de datos demo
│   │   └── loaders.py          # lectura Parquet/CSV
│   ├── clustering/
│   │   ├── __init__.py
│   │   ├── kmeans.py           # ← refactor de MyKMeans.py
│   │   ├── fuzzy.py            # ← lógica FCM de Clustered.py
│   │   └── selector.py         # elbow / silhouette para elegir k
│   ├── tessellation/
│   │   ├── __init__.py
│   │   ├── grid.py             # muestreo espacial + predict
│   │   └── hull.py             # convex hull por zona → GeoJSON
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── agents.py           # Restaurant, Customer, Courier (genéricos)
│   │   ├── assigner.py         # random + greedy (sin ortools al inicio)
│   │   ├── engine.py           # loop de simulación
│   │   └── metrics.py          # delivery time, utilisation, etc.
│   ├── geo/
│   │   ├── __init__.py
│   │   └── bounds.py           # ← refactor de infrastructure.bounding_box
│   └── viz/
│       ├── __init__.py
│       ├── map.py              # Folium / Plotly
│       └── report.py           # JSON + markdown summary
├── tests/
│   ├── test_clustering.py
│   ├── test_tessellation.py
│   ├── test_simulation.py
│   └── test_pipeline.py        # integración end-to-end con sample data
├── notebooks/
│   └── 01_exploratory.ipynb    # opcional, con datos sintéticos
└── docs/
    ├── architecture.md
    └── images/                 # screenshots para README
```

---

## Fases

### Fase 0 — Higiene y seguridad (día 1)

**Prioridad:** eliminar riesgo legal/IP antes de cualquier push público.

| Acción | Detalle |
|--------|---------|
| Crear `.gitignore` | `__pycache__/`, `*.pyc`, `.env`, `data/raw/`, `outputs/`, `.venv/`, `*.html` generados |
| Eliminar del tracking | `git rm -r --cached bin/__pycache__/` |
| **Eliminar** `bin/just-simulate-master/` | Librería interna JE completa; reescribir simulador mínimo propio (~300 líneas) |
| **Eliminar** `bin/config.py` | Contiene SQL de `REDACTED_GCP_PROJECT` |
| **Eliminar** `bin/exp_means.py`, `bin/t2.py`, `bin/old_tess_test.py` | Scripts de exploración con queries BQ y coords hardcodeadas |
| **Eliminar** `bin/SIM_test.py` | Depende de `just.simulate` + `REDACTED_GCP_PROJECT` |
| Auditar resto | `grep -ri "just-eat\|just-data\|delivery_sim\|delco\|skip_data" .` → debe devolver 0 |

**Entregable:** repo sin referencias JE, sin `.pyc` en git.

---

### Fase 1 — Estructura y dependencias (días 2–3)

| Acción | Detalle |
|--------|---------|
| Crear `pyproject.toml` | Python ≥ 3.11; deps: `numpy`, `pandas`, `scipy`, `shapely`, `pyclustering`, `folium`, `typer`, `pydantic-settings`, `pyarrow` |
| Mover lógica útil de `bin/` → `src/teselado/` | Ver tabla de migración abajo |
| Eliminar carpeta `bin/` | Una vez migrado todo |
| Crear `Makefile` | Targets: `install`, `generate-data`, `run`, `test`, `lint`, `clean` |
| Pin de versiones | Lock con `uv lock` o `pip-tools` |

**Entregable:** `pip install -e .` funciona; imports `from teselado.clustering.kmeans import KMeans`.

---

### Fase 2 — Migración de código propio (días 4–7)

#### Tabla de migración archivo por archivo

| Archivo actual | Destino | Acción | Bugs a corregir |
|----------------|---------|--------|-----------------|
| `bin/MyKMeans.py` | `src/teselado/clustering/kmeans.py` | Refactor | `predict()` debe devolver `np.ndarray` de labels; fix init loop; exponer `centroids_`, `labels_` |
| `bin/Clustered.py` | `src/teselado/clustering/fuzzy.py` + `tessellation/` | Split + fix | `sample`→`points`; `cclusters`→`clusters`; import shapely; `boundingbox`→`bounds.bounding_box` |
| `bin/infrastructure.py` | `src/teselado/geo/bounds.py` + `ingest/loaders.py` | Split | Eliminar `query()` y BigQuery; quedarse solo con `bounding_box`, `best_distribution` |
| `bin/main.py` | `src/teselado/cli.py` + `pipeline` | Reescribir | Implementar pipeline real, no pseudocódigo |
| `bin/config.py` | `src/teselado/config.py` | Reescribir | Settings con paths, k-range, city bbox; cero SQL |
| — | `src/teselado/ingest/synthetic.py` | **Nuevo** | Generador de restaurantes/pedidos en bbox configurable |
| — | `src/teselado/simulation/*` | **Nuevo** | Simulador propio, inspirado en conceptos de just-simulate pero sin copiar código |

#### API objetivo del pipeline (`cli.py`)

```bash
# Generar datos sintéticos para una ciudad
teselado generate --city demo --restaurants 200 --orders 5000

# Ejecutar pipeline completo
teselado run --city demo --k-min 3 --k-max 8 --output outputs/

# Solo clustering (sin simulación)
teselado cluster --input data/sample/orders.parquet --k 5

# Solo visualización de resultados previos
teselado viz --input outputs/zones.geojson
```

#### Pseudocódigo del pipeline (reemplaza `main.py` roto)

```python
def run_pipeline(cfg: Settings) -> PipelineResult:
    points = load_orders(cfg.data_path)                          # ingest
    k = select_k(points, k_min=cfg.k_min, k_max=cfg.k_max)    # clustering
    model = KMeans(k=k).fit(points)
    zones = tessellate(model, points, resolution=cfg.grid_step)  # tessellation
    metrics = simulate(zones, points, cfg.sim_params)            # simulation
    export_geojson(zones, cfg.output_dir / "zones.geojson")     # viz
    export_report(metrics, cfg.output_dir / "report.json")
    return PipelineResult(zones=zones, metrics=metrics)
```

---

### Fase 3 — Dataset sintético (días 5–6)

**Problema:** sin acceso a BQ, el proyecto debe demostrar la misma lógica con datos creíbles.

#### Estrategia

1. **`synthetic.py`** genera:
   - `restaurants`: N puntos lat/lng en un bbox (ej. ciudad ficticia o Sevilla con coords reales pero datos inventados)
   - `orders`: M puntos distribuidos con mayor densidad cerca de restaurantes (mixture of Gaussians)
   - Campos genéricos: `order_id`, `restaurant_id`, `lat`, `lng`, `timestamp`, `city`

2. **`data/sample/`** commiteado:
   - Subset fijo (seed=42) para que CI y README siempre den el mismo resultado
   - ~50 restaurantes, ~500 pedidos

3. **Opcional futuro:** conectar a dataset público (NYC TLC trips, OpenStreetMap POIs) como fuente alternativa en `ingest/osm.py`.

#### Esquema de datos (sin nombres JE)

```yaml
restaurants:
  - restaurant_id: str
    lat: float
    lng: float
    city: str

orders:
  - order_id: str
    restaurant_id: str
    lat: float          # destino (cliente)
    lng: float
    placed_at: datetime
    city: str
```

---

### Fase 4 — Simulador propio (días 7–10)

No copiar `just-simulate`. Implementar versión mínima con las métricas que demuestran valor:

| Componente | Responsabilidad |
|------------|-----------------|
| `agents.py` | `Restaurant`, `Customer`, `Courier` con lat/lng |
| `assigner.py` | Greedy: asignar pedido al courier más cercano libre |
| `engine.py` | Cola de eventos simplificada (placed → assigned → delivered) |
| `metrics.py` | `avg_delivery_time`, `orders_per_hour`, `courier_utilisation`, `orders_by_zone` |

**Métricas de portfolio (las que cuentan en una entrevista):**

- Tiempo medio de entrega por zona
- % pedidos entregados dentro de SLA (ej. 30 min)
- Utilización de couriers
- Comparativa: 3 zonas vs 5 zonas vs 8 zonas

---

### Fase 5 — Visualización y BI (días 10–12)

| Artefacto | Herramienta | Para qué |
|-----------|-------------|----------|
| `outputs/map.html` | Folium | Mapa interactivo con polígonos de zona + puntos |
| `outputs/report.json` | JSON estructurado | Métricas por zona, consumible por dashboard |
| `outputs/dashboard.html` (opcional) | Plotly o Streamlit | Capa BI interactiva |

**Screenshot obligatorio en README:** mapa con 5 zonas coloreadas + tabla de KPIs.

---

### Fase 6 — Tests y CI (días 12–14)

#### Tests mínimos

```python
# test_clustering.py
def test_kmeans_predict_returns_array():
    model = KMeans(k=3).fit(sample_points)
    labels = model.predict(grid_points)
    assert labels.shape == (len(grid_points),)
    assert set(labels) <= {0, 1, 2}

# test_tessellation.py
def test_tessellate_produces_valid_polygons():
    zones = tessellate(model, points)
    assert len(zones) == 3
    for z in zones:
        assert z.geometry.is_valid

# test_pipeline.py
def test_end_to_end_with_sample_data(tmp_path):
    result = run_pipeline(Settings(data_path="data/sample/", output_dir=tmp_path))
    assert (tmp_path / "zones.geojson").exists()
    assert result.metrics["avg_delivery_time_min"] > 0
```

#### GitHub Actions (`.github/workflows/ci.yml`)

```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v
      - run: ruff check src/ tests/
```

---

### Fase 7 — Documentación de portfolio (días 14–16)

#### README.md (estructura)

1. **Título + badge CI**
2. **Problema de negocio** (2 párrafos): optimización de zonas last-mile
3. **Solución** (diagrama mermaid)
4. **Stack técnico**
5. **Quick start** (3 comandos)
6. **Resultados** (screenshots + tabla KPIs de ejemplo)
7. **Decisiones técnicas** (por qué K-Means + FCM, por qué greedy assigner)
8. **Roadmap** (HDBSCAN, OSMnx distancias reales, MIP assigner)

#### Narrativa para CV/LinkedIn

> Diseñé un framework de optimización territorial para operaciones de last-mile delivery: particiono demanda geoespacial con clustering, genero teselados operativos y evalúo escenarios de asignación de couriers mediante simulación discreta, cuantificando impacto en tiempo de entrega y utilización de flota.

#### `docs/architecture.md`

- Diagrama de flujo de datos
- Decisiones de diseño
- Trade-offs (euclidean vs road network distance)

---

## Checklist de limpieza Just Eat

Ejecutar antes de hacer el repo público:

- [ ] `grep -ri "just-eat" .` → 0 resultados
- [ ] `grep -ri "just-data" .` → 0 resultados
- [ ] `grep -ri "delivery_sim" .` → 0 resultados
- [ ] `grep -ri "delco_analytics" .` → 0 resultados
- [ ] `grep -ri "skip_data_lake" .` → 0 resultados
- [ ] `grep -ri "order_id" .` → 0 resultados
- [ ] `grep -ri "diego.peteiro" .` → 0 resultados
- [ ] `grep -ri "Aaron-JE\|aarondlc" .` → 0 resultados (o anonimizar coautoría si procede)
- [ ] Carpeta `just-simulate-master/` eliminada
- [ ] Sin credenciales GCP en repo ni en historial git (`git log -p | grep -i "just-data"`)

Si el historial git contiene SQL sensible, considerar **rebase interactivo** o `git filter-repo` para reescribir historial antes de publicar.

---

## Orden de ejecución recomendado

```
Fase 0 (higiene JE)
    ↓
Fase 1 (estructura + pyproject.toml)
    ↓
Fase 3 (dataset sintético)  ← en paralelo con Fase 2
    ↓
Fase 2 (migrar + corregir bugs)
    ↓
Fase 4 (simulador)
    ↓
Fase 5 (viz)
    ↓
Fase 6 (tests + CI)
    ↓
Fase 7 (README + docs)
```

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Historial git con SQL JE | `git filter-repo` o repo nuevo limpio |
| `pyclustering` abandonado | Encapsular detrás de interfaz; migrar a `sklearn.cluster` si falla |
| Simulador demasiado simple para impresionar | Documentar extensiones (MIP, event-driven) en roadmap |
| Scope creep | Fase 4 con greedy assigner; MIP como v2 |
| Sin datos reales | Explicar en README que es metodología demostrable con datos sintéticos |

---

## Definición de "hecho" (DoD)

El proyecto está listo para portfolio cuando:

1. `make run` genera `outputs/map.html` y `outputs/report.json` sin errores
2. `make test` pasa en local y en CI
3. `grep` de limpieza JE devuelve 0
4. README tiene ≥ 1 screenshot y quick start de 3 comandos
5. Un revisor externo puede clonar, instalar y ejecutar en < 10 minutos
6. La narrativa cubre DS (clustering), DE (pipeline reproducible) y BI (KPIs + mapa)

---

## Próximo paso inmediato

Empezar por **Fase 0**: crear `.gitignore`, eliminar `just-simulate-master/` y archivos con SQL JE, y sacar `__pycache__` del tracking.

¿Quieres que ejecute la Fase 0 ahora?
