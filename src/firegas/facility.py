"""Facility and scenario data models with JSON loading."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Obstacle:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def contains(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


@dataclass(frozen=True)
class GasSource:
    x: float
    y: float
    strength: float = 1.0
    wind_direction_deg: float = 0.0
    wind_speed: float = 3.0
    sigma_y: float = 3.0
    sigma_x: float = 8.0


@dataclass(frozen=True)
class Scenario:
    name: str
    sources: tuple[GasSource, ...]
    risk_weight: float = 1.0


@dataclass(frozen=True)
class Facility:
    name: str
    width: float
    height: float
    resolution: float
    obstacles: tuple[Obstacle, ...]
    candidate_points: tuple[tuple[float, float], ...]
    scenarios: tuple[Scenario, ...]

    @classmethod
    def from_json(cls, path: str | Path) -> "Facility":
        raw: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
        obstacles = tuple(Obstacle(**item) for item in raw.get("obstacles", []))
        candidates = tuple((float(p[0]), float(p[1])) for p in raw["candidate_points"])
        scenarios = tuple(
            Scenario(
                name=s["name"],
                sources=tuple(GasSource(**source) for source in s["sources"]),
                risk_weight=float(s.get("risk_weight", 1.0)),
            )
            for s in raw["scenarios"]
        )
        facility = cls(
            name=raw["name"], width=float(raw["width"]), height=float(raw["height"]),
            resolution=float(raw.get("resolution", 1.0)), obstacles=obstacles,
            candidate_points=candidates, scenarios=scenarios,
        )
        facility.validate()
        return facility

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0 or self.resolution <= 0:
            raise ValueError("Facility dimensions and resolution must be positive.")
        if not self.candidate_points or not self.scenarios:
            raise ValueError("At least one candidate point and one scenario are required.")
        for x, y in self.candidate_points:
            if not (0 <= x <= self.width and 0 <= y <= self.height):
                raise ValueError(f"Candidate point {(x, y)} lies outside the facility.")
            if any(o.contains(x, y) for o in self.obstacles):
                raise ValueError(f"Candidate point {(x, y)} lies inside an obstacle.")
        for obstacle in self.obstacles:
            if obstacle.x_min >= obstacle.x_max or obstacle.y_min >= obstacle.y_max:
                raise ValueError("Obstacle bounds must have positive area.")
