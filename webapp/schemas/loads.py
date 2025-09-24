"""Pydantic models that describe the load inputs supported by the API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class PointLoadPayload(BaseModel):
    """Definition of a point load acting over the beam span."""

    label: str = Field("", description="Etiqueta descriptiva opcional")
    position: float = Field(..., ge=0.0, description="Posición de la carga puntual en metros")
    magnitude: float = Field(..., description="Magnitud de la carga puntual en Newton")

    @field_validator("label", mode="before")
    @classmethod
    def _ensure_label(cls, value: Optional[str]) -> str:
        return (value or "").strip()


class DistributedLoadPayload(BaseModel):
    """Definition of an uniformly distributed load (UDL)."""

    label: str = Field("", description="Etiqueta descriptiva opcional")
    start: float = Field(..., ge=0.0, description="Inicio del tramo en metros")
    end: float = Field(..., description="Fin del tramo en metros")
    intensity: float = Field(..., description="Intensidad en N/m")

    @field_validator("label", mode="before")
    @classmethod
    def _ensure_label(cls, value: Optional[str]) -> str:
        return (value or "").strip()

    @model_validator(mode="after")
    def _check_interval(self) -> "DistributedLoadPayload":
        if self.end <= self.start:
            raise ValueError("El fin de la carga distribuida debe ser mayor al inicio.")
        return self
