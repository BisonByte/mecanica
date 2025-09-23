from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


SupportType = str


@dataclass(frozen=True)
class PointLoad:
    """Represents a point load acting on the beam.

    The magnitude follows the sign convention of the original desktop tool:
    positive values act downward, while negative values act upward.
    """

    position: float
    magnitude: float
    label: str = ""


@dataclass(frozen=True)
class DistributedLoad:
    """Represents a uniformly distributed load (UDL)."""

    start: float
    end: float
    intensity: float
    label: str = ""

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def equivalent_force(self) -> float:
        return self.intensity * self.length

    @property
    def centroid(self) -> float:
        return self.start + self.length / 2.0


class BeamComputationError(ValueError):
    """Raised when the beam definition is not physically valid."""


def _normalise_point_loads(point_loads: Optional[Sequence[PointLoad]]) -> List[PointLoad]:
    if not point_loads:
        return []
    normalised: List[PointLoad] = []
    for item in point_loads:
        if isinstance(item, PointLoad):
            normalised.append(item)
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            normalised.append(PointLoad(position=float(item[0]), magnitude=float(item[1])))
        elif isinstance(item, dict):
            normalised.append(
                PointLoad(
                    position=float(item.get("position", 0.0)),
                    magnitude=float(item.get("magnitude", 0.0)),
                    label=str(item.get("label", "")),
                )
            )
        else:
            raise TypeError(f"Unsupported point load definition: {item!r}")
    return normalised


def _normalise_distributed_loads(
    distributed_loads: Optional[Sequence[DistributedLoad]],
) -> List[DistributedLoad]:
    if not distributed_loads:
        return []
    normalised: List[DistributedLoad] = []
    for item in distributed_loads:
        if isinstance(item, DistributedLoad):
            normalised.append(item)
        elif isinstance(item, (tuple, list)) and len(item) >= 3:
            normalised.append(
                DistributedLoad(
                    start=float(item[0]),
                    end=float(item[1]),
                    intensity=float(item[2]),
                )
            )
        elif isinstance(item, dict):
            normalised.append(
                DistributedLoad(
                    start=float(item.get("start", 0.0)),
                    end=float(item.get("end", 0.0)),
                    intensity=float(item.get("intensity", 0.0)),
                    label=str(item.get("label", "")),
                )
            )
        else:
            raise TypeError(f"Unsupported distributed load definition: {item!r}")
    return normalised


def _validate_beam(
    length: float,
    support_c_type: Optional[SupportType],
    support_c_position: Optional[float],
    distributed_loads: Sequence[DistributedLoad],
) -> Optional[float]:
    if length <= 0:
        raise BeamComputationError("Beam length must be positive.")

    support_c_type = (support_c_type or "Ninguno").lower()
    if support_c_type in {"ninguno", "none", ""}:
        return None

    if support_c_position is None:
        raise BeamComputationError("Support C position must be provided when it exists.")

    if not 0 < support_c_position < length:
        raise BeamComputationError("Support C position must lie strictly within the beam span.")

    for load in distributed_loads:
        if load.end <= load.start:
            raise BeamComputationError("Distributed load end must be greater than start.")

    return float(support_c_position)


def _aggregate_loading(
    point_loads: Sequence[PointLoad],
    distributed_loads: Sequence[DistributedLoad],
) -> Tuple[float, float]:
    total_force = 0.0
    total_moment_a = 0.0

    for load in point_loads:
        total_force += load.magnitude
        total_moment_a += load.magnitude * load.position

    for load in distributed_loads:
        total_force += load.equivalent_force
        total_moment_a += load.equivalent_force * load.centroid

    return total_force, total_moment_a


def _horizontal_component(value: float, angle: float, support_type: SupportType) -> float:
    if support_type.lower() != "fijo":
        return 0.0
    return float(value * np.tan(angle))


def torsor_at(
    x: float,
    *,
    length: float,
    reactions: Dict[str, float],
    torsor_base: float,
    support_c_position: Optional[float],
    point_loads: Sequence[PointLoad],
    distributed_loads: Sequence[DistributedLoad],
) -> float:
    """Return the internal torsor (bending moment) at position `x`."""

    momento = torsor_base
    ra = reactions.get("A", 0.0)
    rb = reactions.get("B", 0.0)
    rc = reactions.get("C", 0.0)

    if x >= 0:
        momento += ra * x
    if support_c_position is not None and x >= support_c_position:
        momento += rc * (x - support_c_position)
    if x >= length:
        momento += rb * (x - length)

    for load in point_loads:
        if x > load.position:
            momento -= load.magnitude * (x - load.position)

    for load in distributed_loads:
        if x > load.start:
            if x <= load.end:
                span = x - load.start
                momento -= load.intensity * span * span / 2.0
            else:
                long_total = load.length
                momento -= load.intensity * long_total * (x - (load.start + long_total / 2.0))

    return float(momento)


def compute_beam_analysis(
    *,
    length: float,
    height_start: float = 0.0,
    height_end: float = 0.0,
    support_a_type: SupportType = "Fijo",
    support_b_type: SupportType = "Movil",
    support_c_type: Optional[SupportType] = "Ninguno",
    support_c_position: Optional[float] = None,
    point_loads: Optional[Sequence[PointLoad]] = None,
    distributed_loads: Optional[Sequence[DistributedLoad]] = None,
    torsor: float = 0.0,
    num_points: int = 800,
) -> Dict[str, object]:
    """Compute reactions and internal diagrams for a beam configuration."""

    loads_p = _normalise_point_loads(point_loads)
    loads_d = _normalise_distributed_loads(distributed_loads)

    support_c_pos = _validate_beam(length, support_c_type, support_c_position, loads_d)

    total_force, total_moment_a = _aggregate_loading(loads_p, loads_d)

    if support_c_pos is None:
        rb = (total_moment_a + torsor) / length
        ra = total_force - rb
        rc = 0.0
    else:
        rb = ((total_moment_a + torsor) - support_c_pos * total_force / 2.0) / (length - support_c_pos)
        ra = (total_force - rb) / 2.0
        rc = ra

    angle = np.arctan((height_end - height_start) / length)

    reactions = {
        "A": float(ra),
        "B": float(rb),
    }
    if support_c_pos is not None:
        reactions["C"] = float(rc)
    else:
        reactions["C"] = 0.0

    reaction_components = {
        "A": {
            "vertical": reactions["A"],
            "horizontal": _horizontal_component(reactions["A"], angle, support_a_type),
            "type": support_a_type,
        },
        "B": {
            "vertical": reactions["B"],
            "horizontal": _horizontal_component(reactions["B"], angle, support_b_type),
            "type": support_b_type,
        },
        "C": {
            "vertical": reactions.get("C", 0.0),
            "horizontal": _horizontal_component(reactions.get("C", 0.0), angle, support_c_type or "Ninguno"),
            "type": support_c_type or "Ninguno",
        },
    }

    x = np.linspace(0.0, length, max(num_points, 2))
    shear = np.zeros_like(x)
    moment = np.zeros_like(x)
    torsor_curve = np.zeros_like(x)

    for idx, xi in enumerate(x):
        v = reactions["A"]
        m = reactions["A"] * xi

        if support_c_pos is not None and xi >= support_c_pos:
            v += reactions["C"]
            m += reactions["C"] * (xi - support_c_pos)

        if xi >= length:
            v += reactions["B"]
            m += reactions["B"] * (xi - length)

        for load in loads_p:
            if xi > load.position:
                v -= load.magnitude
                m -= load.magnitude * (xi - load.position)

        for load in loads_d:
            if xi > load.start:
                if xi <= load.end:
                    span = xi - load.start
                    v -= load.intensity * span
                    m -= load.intensity * span * span / 2.0
                else:
                    long_total = load.length
                    v -= load.intensity * long_total
                    m -= load.intensity * long_total * (xi - (load.start + long_total / 2.0))

        shear[idx] = v
        moment[idx] = m
        torsor_curve[idx] = torsor_at(
            xi,
            length=length,
            reactions=reactions,
            torsor_base=torsor,
            support_c_position=support_c_pos,
            point_loads=loads_p,
            distributed_loads=loads_d,
        )

    center_of_mass = None
    if abs(total_force) > np.finfo(float).eps:
        center_of_mass = total_moment_a / total_force

    return {
        "reactions": reaction_components,
        "equilibrium": {
            "sum_vertical_loads": total_force,
            "sum_moment_about_a": total_moment_a,
            "torsor": torsor,
        },
        "diagrams": {
            "positions": x.tolist(),
            "shear": shear.tolist(),
            "moment": moment.tolist(),
        },
        "torsor": {
            "positions": x.tolist(),
            "values": torsor_curve.tolist(),
        },
        "center_of_mass": center_of_mass,
        "loads": {
            "point": [load.__dict__ for load in loads_p],
            "distributed": [
                {
                    "start": load.start,
                    "end": load.end,
                    "intensity": load.intensity,
                    "label": load.label,
                    "equivalent_force": load.equivalent_force,
                    "centroid": load.centroid,
                }
                for load in loads_d
            ],
        },
        "supports": {
            "A": {"type": support_a_type, "position": 0.0},
            "B": {"type": support_b_type, "position": length},
            "C": {
                "type": support_c_type or "Ninguno",
                "position": support_c_pos,
            },
        },
    }
