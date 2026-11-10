"""CSV/JSON exports and diagnostic plots."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from .coverage import evaluate_layout
from .dispersion import all_concentrations, grid_for
from .facility import Facility
from .optimisation import Candidate, choose_compromise


def write_outputs(facility: Facility, front: list[Candidate], output: str | Path,
                  threshold: float = 0.25) -> None:
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    with (out / "pareto_front.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_indices", "detector_count", "installation_cost",
                         "mean_uncovered_risk", "worst_uncovered_risk"])
        for c in front:
            writer.writerow([";".join(map(str, c.genes)), len(c.genes), *c.objectives])
    best = choose_compromise(front)
    (out / "best_layout.json").write_text(json.dumps({
        "facility": facility.name, "candidate_indices": best.genes,
        "detectors": [facility.candidate_points[i] for i in best.genes],
        "objectives": {"installation_cost": best.objectives[0],
                       "mean_uncovered_risk": best.objectives[1],
                       "worst_uncovered_risk": best.objectives[2]},
        "warning": "Synthetic prototype output; not a certified detector design."
    }, indent=2), encoding="utf-8")
    xx, yy = grid_for(facility)
    fields = all_concentrations(facility)
    fig, ax = plt.subplots(figsize=(9, 5))
    contour = ax.contourf(xx, yy, fields[0], levels=18, cmap="inferno")
    fig.colorbar(contour, ax=ax, label="Relative concentration")
    _draw_facility(ax, facility)
    ax.set(title=f"{facility.name}: relative concentration (scenario 1)", xlabel="X (m)", ylabel="Y (m)")
    fig.tight_layout(); fig.savefig(out / "concentration.png", dpi=160); plt.close(fig)
    _, _, _, masks = evaluate_layout(facility, best.genes, threshold)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.imshow(masks[0], origin="lower", extent=[0, facility.width, 0, facility.height],
              interpolation="nearest", cmap="YlGn", alpha=0.8, aspect="auto")
    _draw_facility(ax, facility)
    for i in best.genes:
        x, y = facility.candidate_points[i]; ax.scatter(x, y, marker="^", s=90, c="blue")
    ax.set(title="Illustrative detector response mask (scenario 1)", xlabel="X (m)", ylabel="Y (m)")
    fig.tight_layout(); fig.savefig(out / "coverage.png", dpi=160); plt.close(fig)
    (out / "summary.json").write_text(json.dumps({
        "facility": facility.name, "scenario_count": len(facility.scenarios),
        "candidate_count": len(facility.candidate_points), "pareto_layout_count": len(front),
        "threshold": threshold, "model": "dimensionless reflected Gaussian plume proxy"
    }, indent=2), encoding="utf-8")


def _draw_facility(ax, facility: Facility) -> None:
    for obstacle in facility.obstacles:
        ax.add_patch(plt.Rectangle((obstacle.x_min, obstacle.y_min),
                                   obstacle.x_max-obstacle.x_min,
                                   obstacle.y_max-obstacle.y_min,
                                   color="slategrey", alpha=0.85))
    ax.set_xlim(0, facility.width); ax.set_ylim(0, facility.height); ax.set_aspect("equal")
    ax.grid(alpha=0.15)
