import numpy as np
from firegas.facility import Facility
from firegas.dispersion import scenario_concentration
from firegas.coverage import evaluate_layout
from firegas.optimisation import Candidate, dominates, optimise


def test_concentration_is_finite_and_normalised():
    facility = Facility.from_json("data/facilities/process_unit.json")
    field = scenario_concentration(facility, facility.scenarios[0])
    assert np.isfinite(field).all()
    assert field.min() >= 0
    assert np.isclose(field.max(), 1.0)


def test_layout_metrics_are_bounded():
    facility = Facility.from_json("data/facilities/process_unit.json")
    cost, mean_risk, worst_risk, masks = evaluate_layout(facility, [0, 5, 10])
    assert cost == 3
    assert 0 <= mean_risk <= 1
    assert 0 <= worst_risk <= 1
    assert len(masks) == len(facility.scenarios)


def test_dominance():
    assert dominates(Candidate((0,), (1, .2, .3)), Candidate((1,), (2, .3, .4)))
    assert not dominates(Candidate((0,), (1, .2, .3)), Candidate((1,), (1, .2, .3)))


def test_optimizer_returns_nonempty_front():
    facility = Facility.from_json("data/facilities/process_unit.json")
    front = optimise(facility, population_size=8, generations=2, max_detectors=4, seed=4)
    assert front
    assert all(len(c.genes) > 0 for c in front)
