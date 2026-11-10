"""Detector response, obstacle line-of-sight and risk-weighted layout scoring."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from .dispersion import all_concentrations, grid_for
from .facility import Facility, Obstacle

FloatArray = NDArray[np.float64]


def _segment_intersects_rect(a: tuple[float, float], b: tuple[float, float], r: Obstacle) -> bool:
    """Liang-Barsky segment/axis-aligned rectangle intersection."""
    x0, y0 = a; x1, y1 = b
    dx, dy = x1 - x0, y1 - y0
    p = (-dx, dx, -dy, dy)
    q = (x0 - r.x_min, r.x_max - x0, y0 - r.y_min, r.y_max - y0)
    u0, u1 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if abs(pi) < 1e-12:
            if qi < 0:
                return False
            continue
        t = qi / pi
        if pi < 0:
            u0 = max(u0, t)
        else:
            u1 = min(u1, t)
        if u0 > u1:
            return False
    return True


def _visible(facility: Facility, source: tuple[float, float], detector: tuple[float, float]) -> bool:
    return not any(_segment_intersects_rect(source, detector, o) for o in facility.obstacles)


def evaluate_layout(
    facility: Facility, selected: tuple[int, ...] | list[int], threshold: float = 0.25,
    unit_cost: float = 1.0,
) -> tuple[float, float, float, list[FloatArray]]:
    """Return (cost, mean uncovered risk, worst uncovered risk, scenario coverage masks)."""
    if not selected:
        raise ValueError("A layout must contain at least one detector.")
    candidates = [facility.candidate_points[i] for i in selected]
    concentrations = all_concentrations(facility)
    xx, yy = grid_for(facility)
    masks: list[FloatArray] = []
    scenario_uncovered: list[float] = []
    weights = np.zeros_like(xx)
    for scenario, field in zip(facility.scenarios, concentrations):
        risk = np.maximum(field - threshold, 0.0) * scenario.risk_weight
        weights += risk
        response = np.zeros_like(field)
        for detector in candidates:
            # A detector responds to the field at its nearest grid cell. This is a
            # deliberately transparent proxy, not a vendor response-time model.
            ix = int(np.argmin(np.abs(xx[0, :] - detector[0])))
            iy = int(np.argmin(np.abs(yy[:, 0] - detector[1])))
            local = float(field[iy, ix])
            for source in scenario.sources:
                if _visible(facility, (source.x, source.y), detector):
                    distance = np.hypot(detector[0] - source.x, detector[1] - source.y)
                    response = np.maximum(response, local * np.exp(-distance / 30.0))
        mask = response >= threshold
        masks.append(mask)
        denom = float(risk.sum())
        scenario_uncovered.append(float((risk * (~mask)).sum() / denom) if denom > 0 else 0.0)
    total_weight = float(weights.sum())
    mean_uncovered = float(np.mean(scenario_uncovered))
    return len(selected) * unit_cost, mean_uncovered, max(scenario_uncovered), masks
