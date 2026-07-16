"""Distance models for delivery simulation (haversine vs road network)."""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from teselado.geo.bounds import bounding_box
from teselado.ingest.synthetic import CityBBox
from teselado.simulation.geo import haversine_km


class DistanceCalculator(Protocol):
    def distance_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float: ...

    def travel_minutes(
        self, lat1: float, lng1: float, lat2: float, lng2: float, speed_kmh: float
    ) -> float: ...


@dataclass
class HaversineCalculator:
    """Straight-line great-circle distance."""

    name: str = "haversine"

    def distance_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        return haversine_km(lat1, lng1, lat2, lng2)

    def travel_minutes(
        self, lat1: float, lng1: float, lat2: float, lng2: float, speed_kmh: float
    ) -> float:
        if speed_kmh <= 0:
            raise ValueError("speed_kmh must be positive")
        return (self.distance_km(lat1, lng1, lat2, lng2) / speed_kmh) * 60.0


@dataclass
class OsmnxCalculator:
    """Shortest-path distance on an OSM drive network."""

    graph: object
    name: str = "osmnx"

    def distance_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        import networkx as nx
        import osmnx as ox

        graph = self.graph
        origin = ox.distance.nearest_nodes(graph, lng1, lat1)
        destination = ox.distance.nearest_nodes(graph, lng2, lat2)
        try:
            length_m = nx.shortest_path_length(graph, origin, destination, weight="length")
        except nx.NetworkXNoPath:
            return haversine_km(lat1, lng1, lat2, lng2)
        return float(length_m) / 1000.0

    def travel_minutes(
        self, lat1: float, lng1: float, lat2: float, lng2: float, speed_kmh: float
    ) -> float:
        if speed_kmh <= 0:
            raise ValueError("speed_kmh must be positive")
        return (self.distance_km(lat1, lng1, lat2, lng2) / speed_kmh) * 60.0


def load_osmnx_graph(
    city: str,
    cache_dir: Path | None = None,
    dist_m: int = 3500,
):
    """
    Download or load a cached OSM drive graph for a known city.

    Uses a radius around the city-center rather than the full synthetic bbox,
    keeping Overpass queries fast enough for portfolio demos.
    """
    import osmnx as ox

    bbox = CityBBox.from_name(city)
    center_lat = (bbox.lat_min + bbox.lat_max) / 2
    center_lng = (bbox.lng_min + bbox.lng_max) / 2

    cache_path = None
    if cache_dir is not None:
        cache_path = Path(cache_dir) / f"{city}_drive_graph_{dist_m}m.pkl"
        if cache_path.exists():
            with cache_path.open("rb") as handle:
                return pickle.load(handle)

    graph = ox.graph_from_point(
        (center_lat, center_lng),
        dist=dist_m,
        network_type="drive",
        simplify=True,
    )
    graph = ox.distance.add_edge_lengths(graph)

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("wb") as handle:
            pickle.dump(graph, handle)

    return graph


def build_distance_calculator(
    mode: str,
    *,
    city: str = "demo",
    cache_dir: Path | None = None,
    points: np.ndarray | None = None,
) -> DistanceCalculator:
    """Create a distance calculator for simulation."""
    if mode == "haversine":
        return HaversineCalculator()

    if mode == "osmnx":
        try:
            graph = load_osmnx_graph(city, cache_dir=cache_dir)
        except ImportError as exc:
            raise ImportError(
                "OSMnx comparison requires `pip install teselado[roads]` (osmnx + networkx)."
            ) from exc
        return OsmnxCalculator(graph=graph)

    raise ValueError(f"Unknown distance mode '{mode}'. Use 'haversine' or 'osmnx'.")


def bbox_from_points(points: np.ndarray) -> list[tuple[float, float]]:
    """Build a bbox from an array of [lat, lng] points."""
    return bounding_box(points.tolist())
