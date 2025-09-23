import math

import numpy as np

from mechanics import DistributedLoad, PointLoad, compute_beam_analysis, torsor_at


def almost_equal(a, b, tol=1e-9):
    return abs(a - b) <= tol


def test_symmetrical_point_loads_share_reaction():
    result = compute_beam_analysis(
        length=10.0,
        point_loads=[PointLoad(position=5.0, magnitude=20.0)],
    )
    assert almost_equal(result["reactions"]["A"]["vertical"], 10.0)
    assert almost_equal(result["reactions"]["B"]["vertical"], 10.0)
    assert result["center_of_mass"] == 5.0


def test_distributed_load_equivalent_force_and_moment():
    result = compute_beam_analysis(
        length=12.0,
        distributed_loads=[DistributedLoad(start=4.0, end=10.0, intensity=5.0)],
    )
    distributed = result["loads"]["distributed"][0]
    assert almost_equal(distributed["equivalent_force"], 30.0)
    assert almost_equal(distributed["centroid"], 7.0)
    shear = np.array(result["diagrams"]["shear"])
    assert shear[0] == result["reactions"]["A"]["vertical"]
    assert math.isclose(torsor_at(8.0, length=12.0, reactions={"A": result["reactions"]["A"]["vertical"], "B": result["reactions"]["B"]["vertical"], "C": 0.0}, torsor_base=0.0, support_c_position=None, point_loads=[], distributed_loads=[DistributedLoad(start=4.0, end=10.0, intensity=5.0)]), result["torsor"]["values"][int(len(result["torsor"]["values"]) * 8 / 12)]], rel_tol=1e-3)


def test_support_c_requires_position():
    try:
        compute_beam_analysis(
            length=8.0,
            support_c_type="Fijo",
            support_c_position=None,
        )
    except ValueError as exc:
        assert "posicion" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for missing support C position")
