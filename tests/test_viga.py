import math

from mechanics import DistributedLoad, PointLoad, compute_beam_analysis, torsor_at


def _almost_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def _nearest_index(values, target):
    return min(range(len(values)), key=lambda i: abs(values[i] - target))


def test_symmetrical_point_load_splits_reactions():
    result = compute_beam_analysis(
        length=10.0,
        point_loads=[PointLoad(position=5.0, magnitude=20.0)],
    )
    assert _almost_equal(result["reactions"]["A"]["vertical"], 10.0)
    assert _almost_equal(result["reactions"]["B"]["vertical"], 10.0)
    assert result["center_of_mass"] == 5.0


def test_distributed_load_equivalent_and_torsor_curve():
    load = DistributedLoad(start=4.0, end=10.0, intensity=5.0)
    result = compute_beam_analysis(length=12.0, distributed_loads=[load])

    dist_summary = result["loads"]["distributed"][0]
    assert _almost_equal(dist_summary["equivalent_force"], 30.0)
    assert _almost_equal(dist_summary["centroid"], 7.0)

    reactions = {key: info["vertical"] for key, info in result["reactions"].items()}
    torsor_value = torsor_at(
        8.0,
        length=12.0,
        reactions=reactions,
        torsor_base=result["equilibrium"]["torsor"],
        support_c_position=None,
        point_loads=[],
        distributed_loads=[load],
    )
    idx = _nearest_index(result["torsor"]["positions"], 8.0)
    assert math.isclose(torsor_value, result["torsor"]["values"][idx], rel_tol=1e-3)


def test_support_c_requires_position():
    try:
        compute_beam_analysis(length=8.0, support_c_type="Fijo", support_c_position=None)
    except ValueError as exc:
        assert "posicion" in str(exc).lower() or "position" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for missing support C position")
