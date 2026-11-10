"""Command-line runner."""
from __future__ import annotations
import argparse
from .facility import Facility
from .optimisation import optimise, choose_compromise
from .reporting import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimise synthetic fire/gas detector layouts.")
    parser.add_argument("--facility", default="data/facilities/process_unit.json")
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--population", type=int, default=48)
    parser.add_argument("--generations", type=int, default=45)
    parser.add_argument("--max-detectors", type=int, default=8)
    parser.add_argument("--threshold", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    facility = Facility.from_json(args.facility)
    front = optimise(facility, args.population, args.generations,
                     args.max_detectors, args.threshold, args.seed)
    write_outputs(facility, front, args.output, args.threshold)
    best = choose_compromise(front)
    print(f"Facility: {facility.name}")
    print(f"Pareto layouts: {len(front)}")
    print(f"Compromise detector indices: {best.genes}")
    print(f"Objectives (cost, mean risk, worst risk): {best.objectives}")
    print(f"Reports written to: {args.output}")

if __name__ == "__main__":
    main()
