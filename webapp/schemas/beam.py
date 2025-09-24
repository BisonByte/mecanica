"""Schemas that describe the payload sent to the beam analysis endpoint."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .loads import DistributedLoadPayload, PointLoadPayload


class AnalysisOptions(BaseModel):
    """Advanced parameters that tune the computation."""

    num_points: int = Field(800, ge=100, le=5000, description="Número de nodos para diagramas")
    export_format: str = Field("json", description="Formato preferido de exportación")
    unit_system: str = Field("SI", description="Sistema de unidades para mostrar resultados")

    @field_validator("export_format")
    @classmethod
    def _validate_export_format(cls, value: str) -> str:
        value = (value or "json").lower()
        if value not in {"json", "csv", "xlsx"}:
            raise ValueError("Formato de exportación no soportado")
        return value

    @field_validator("unit_system")
    @classmethod
    def _validate_unit_system(cls, value: str) -> str:
        value = (value or "SI").upper()
        if value not in {"SI", "US"}:
            raise ValueError("Sistema de unidades desconocido")
        return value


class BeamPayload(BaseModel):
    """Payload completo para ejecutar un análisis de viga."""

    length: float = Field(..., gt=0, description="Longitud de la viga en metros")
    height_start: float = Field(0.0, description="Cota inicial de la viga")
    height_end: float = Field(0.0, description="Cota final de la viga")
    support_a_type: str = Field("Fijo", description="Tipo de apoyo A")
    support_b_type: str = Field("Movil", description="Tipo de apoyo B")
    support_c_type: str = Field("Ninguno", description="Tipo de apoyo intermedio C")
    support_c_position: Optional[float] = Field(
        None, description="Posición del apoyo C cuando corresponde"
    )
    torsor: float = Field(0.0, description="Par torsor externo aplicado")
    point_loads: List[PointLoadPayload] = Field(default_factory=list)
    distributed_loads: List[DistributedLoadPayload] = Field(default_factory=list)
    analysis: AnalysisOptions = Field(default_factory=AnalysisOptions)

    @field_validator("support_a_type", "support_b_type", "support_c_type", mode="before")
    @classmethod
    def _normalise_supports(cls, value: str) -> str:
        value = (value or "").strip() or "Ninguno"
        mapping = {
            "movil": "Movil",
            "móvil": "Movil",
            "hinge": "Movil",
            "fijo": "Fijo",
            "fixed": "Fijo",
            "roller": "Movil",
            "none": "Ninguno",
        }
        return mapping.get(value.lower(), value.title())

    @model_validator(mode="after")
    def _validate_support_c(self) -> "BeamPayload":
        if self.support_c_type.lower() not in {"ninguno", "none", ""} and self.support_c_position is None:
            raise ValueError("Debe especificarse la posición del apoyo C cuando está activo.")
        if self.support_c_position is not None and not 0 < self.support_c_position < self.length:
            raise ValueError("El apoyo C debe ubicarse dentro del claro de la viga.")
        return self

    def to_kwargs(self) -> dict:
        """Return a dictionary ready to be expanded into the computation service."""

        return {
            "length": self.length,
            "height_start": self.height_start,
            "height_end": self.height_end,
            "support_a_type": self.support_a_type,
            "support_b_type": self.support_b_type,
            "support_c_type": self.support_c_type,
            "support_c_position": self.support_c_position,
            "point_loads": self.point_loads,
            "distributed_loads": self.distributed_loads,
            "torsor": self.torsor,
            "num_points": self.analysis.num_points,
        }
