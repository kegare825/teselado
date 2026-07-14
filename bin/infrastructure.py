"""Utility functions for geo and statistical analysis."""

import scipy.stats as st


def bounding_box(coords):
    """Return the axis-aligned bounding box corners for a list of (x, y) coords."""
    min_x = max_x = coords[0][0]
    min_y = max_y = coords[0][1]

    for item in coords:
        if item[0] < min_x:
            min_x = item[0]
        if item[0] > max_x:
            max_x = item[0]
        if item[1] < min_y:
            min_y = item[1]
        if item[1] > max_y:
            max_y = item[1]

    return [
        (min_x, min_y),
        (max_x, min_y),
        (max_x, max_y),
        (min_x, max_y),
    ]


# Backwards-compatible alias used by Clustered.py (will be removed in Phase 2).
boundingbox = bounding_box


def get_best_distribution(data):
    """Fit several distributions and return the best Kolmogorov-Smirnov match."""
    dist_names = [
        "norm",
        "exponweib",
        "weibull_max",
        "weibull_min",
        "pareto",
        "genextreme",
    ]
    dist_results = []
    params = {}

    for dist_name in dist_names:
        dist = getattr(st, dist_name)
        param = dist.fit(data)
        params[dist_name] = param
        _, p = st.kstest(data, dist_name, args=param)
        dist_results.append((dist_name, p))

    best_dist, best_p = max(dist_results, key=lambda item: item[1])
    return best_dist, best_p, params[best_dist]
