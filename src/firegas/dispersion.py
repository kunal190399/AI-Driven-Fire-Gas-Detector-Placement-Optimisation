"""Relative concentration fields using a reflected Gaussian plume approximation."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from .facility import Facility, Scenario

FloatArray = NDArray[np.float64]


def grid_for(facility: Facility) -> tuple[FloatArray, FloatArray]:
    x = np.arange(0.0, facility.width + facility.resolution, facility.resolution)
    y = np.arange(0.0, facility.height + facility.resolution, facility.resolution)
    return np.meshgrid(x, y)


def scenario_concentration(facility: Facility, scenario: Scenario) -> FloatArray:
    """Return a dimensionless relative concentration field (not calibrated ppm)."""
    xx, yy = grid_for(facility)
    total = np.zeros_like(xx, dtype=float)
    for source in scenario.sources:
        theta = np.deg2rad(source.wind_direction_deg)
        dx, dy = xx - source.x, yy - source.y
        downwind = dx * np.cos(theta) + dy * np.sin(theta)
        crosswind = -dx * np.sin(theta) + dy * np.cos(theta)
        active = downwind >= 0
        longitudinal = np.maximum(downwind, 0.25)
        sigma_y = source.sigma_y * np.sqrt(1.0 + longitudinal / max(source.sigma_x, 0.1))
        plume = (source.strength / (source.wind_speed * sigma_y)) * np.exp(
            -0.5 * (crosswind / sigma_y) ** 2
        ) * np.exp(-downwind / max(source.sigma_x * 5.0, 0.1))
        total += np.where(active, plume, 0.0)
    for obstacle in facility.obstacles:
        blocked = ((xx >= obstacle.x_min) & (xx <= obstacle.x_max) &
                   (yy >= obstacle.y_min) & (yy <= obstacle.y_max))
        total[blocked] *= 0.15
    peak = float(total.max())
    return total / peak if peak > 0 else total


def all_concentrations(facility: Facility) -> list[FloatArray]:
    return [scenario_concentration(facility, s) for s in facility.scenarios]
