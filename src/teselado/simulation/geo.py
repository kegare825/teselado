"""Geospatial helpers for the delivery simulation."""

from __future__ import annotations

import numpy as np


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Approximate distance in km between two lat/lng points."""
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lng2 - lng1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return float(2 * r * np.arcsin(np.sqrt(a)))


def travel_minutes(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
    speed_kmh: float,
) -> float:
    """Travel time in minutes between two coordinates."""
    if speed_kmh <= 0:
        raise ValueError("speed_kmh must be positive")
    dist_km = haversine_km(lat1, lng1, lat2, lng2)
    return (dist_km / speed_kmh) * 60.0
