from firegas.facility import Facility, Obstacle
from firegas.coverage import _segment_intersects_rect


def test_segment_intersection_cases():
    rect = Obstacle(2, 2, 4, 4)
    assert _segment_intersects_rect((0, 3), (6, 3), rect)
    assert not _segment_intersects_rect((0, 0), (1, 1), rect)
    assert _segment_intersects_rect((3, 3), (5, 3), rect)
    assert _segment_intersects_rect((0, 2), (6, 2), rect)


def test_facility_loads_and_candidates_are_valid():
    facility = Facility.from_json("data/facilities/process_unit.json")
    assert facility.width == 60
    assert len(facility.scenarios) == 3
    assert len(facility.candidate_points) >= 10
