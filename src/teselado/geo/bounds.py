"""Geospatial and statistical utility functions."""

import scipy.stats as st


def bounding_box(coords):
    """Return axis-aligned bounding box corners for a list of (x, y) coordinates."""
    min_x = max_x = coords[0][0]
    min_y = max_y = coords[0][1]

    for x, y in coords:
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    return [
        (min_x, min_y),
        (max_x, min_y),
        (max_x, max_y),
        (min_x, max_y),
    ]


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
