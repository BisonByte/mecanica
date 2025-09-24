"""Service layer that orchestrates beam analysis computations."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException

from mechanics import DistributedLoad, PointLoad, compute_beam_analysis
from mechanics.viga import BeamComputationError

from ..schemas import BeamPayload


class BeamAnalysisService:
    """High level service in charge of translating payloads into results."""

    @staticmethod
    def run(payload: BeamPayload) -> Dict[str, Any]:
        try:
            return compute_beam_analysis(
                **payload.to_kwargs(),
                point_loads=[
                    PointLoad(position=load.position, magnitude=load.magnitude, label=load.label)
                    for load in payload.point_loads
                ],
                distributed_loads=[
                    DistributedLoad(
                        start=load.start, end=load.end, intensity=load.intensity, label=load.label
                    )
                    for load in payload.distributed_loads
                ],
            )
        except BeamComputationError as exc:  # pragma: no cover - validated upstream
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:  # pragma: no cover - validated upstream
            raise HTTPException(status_code=422, detail=str(exc)) from exc


def run_beam_analysis(payload: BeamPayload) -> Dict[str, Any]:
    """Convenience wrapper for callers that do not need the class."""

    return BeamAnalysisService.run(payload)
