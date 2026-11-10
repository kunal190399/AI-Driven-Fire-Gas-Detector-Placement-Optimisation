"""Small deterministic evolutionary multi-objective detector layout search."""
from __future__ import annotations

import random
from dataclasses import dataclass
from .coverage import evaluate_layout
from .facility import Facility


@dataclass(frozen=True)
class Candidate:
    genes: tuple[int, ...]
    objectives: tuple[float, float, float]


def dominates(a: Candidate, b: Candidate) -> bool:
    return all(x <= y for x, y in zip(a.objectives, b.objectives)) and any(
        x < y for x, y in zip(a.objectives, b.objectives)
    )


def pareto_front(population: list[Candidate]) -> list[Candidate]:
    return [c for c in population if not any(dominates(other, c) for other in population if other != c)]


def _score(facility: Facility, genes: tuple[int, ...], threshold: float) -> Candidate:
    cost, uncovered, worst, _ = evaluate_layout(facility, genes, threshold)
    return Candidate(genes, (cost, uncovered, worst))


def optimise(
    facility: Facility, population_size: int = 48, generations: int = 45,
    max_detectors: int = 8, threshold: float = 0.25, seed: int = 17,
) -> list[Candidate]:
    """Return a non-dominated archive; all objectives are minimised."""
    if population_size < 4 or generations < 1:
        raise ValueError("Use population_size >= 4 and generations >= 1.")
    rng = random.Random(seed)
    n = len(facility.candidate_points)
    max_detectors = min(max(1, max_detectors), n)

    def random_genes() -> tuple[int, ...]:
        count = rng.randint(1, max_detectors)
        return tuple(sorted(rng.sample(range(n), count)))

    population = [_score(facility, random_genes(), threshold) for _ in range(population_size)]
    archive: dict[tuple[int, ...], Candidate] = {}
    for _ in range(generations):
        combined = population + list(archive.values())
        for c in pareto_front(combined):
            archive[c.genes] = c
        pool = pareto_front(combined)
        next_population = list(pool[:max(2, population_size // 3)])
        while len(next_population) < population_size:
            parent = rng.choice(pool).genes
            genes = set(parent)
            if rng.random() < 0.5 and len(genes) < max_detectors:
                genes.add(rng.randrange(n))
            elif len(genes) > 1:
                genes.remove(rng.choice(tuple(genes)))
            else:
                genes.add(rng.randrange(n))
            if rng.random() < 0.25:
                genes = set(random_genes())
            child = tuple(sorted(genes))
            next_population.append(_score(facility, child, threshold))
        population = next_population
    for c in pareto_front(population + list(archive.values())):
        archive[c.genes] = c
    return sorted(pareto_front(list(archive.values())), key=lambda c: c.objectives)


def choose_compromise(front: list[Candidate]) -> Candidate:
    """Choose a normalised closest-to-ideal compromise; not a safety assertion."""
    if not front:
        raise ValueError("Pareto front is empty.")
    columns = list(zip(*(c.objectives for c in front)))
    minima = [min(col) for col in columns]
    spans = [max(col) - min(col) or 1.0 for col in columns]
    return min(front, key=lambda c: sum(((v - lo) / span) ** 2
                                        for v, lo, span in zip(c.objectives, minima, spans)))
