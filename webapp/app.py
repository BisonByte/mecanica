from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, root_validator, validator

from mechanics import DistributedLoad, PointLoad, compute_beam_analysis
from mechanics.viga import BeamComputationError

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Simulador de Estructuras Web",
    description="Version web profesional del simulador de vigas y estructuras.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class PointLoadPayload(BaseModel):
    position: float = Field(..., ge=0, description="Posicion de la carga puntual en metros")
    magnitude: float = Field(..., description="Magnitud de la carga en Newton")
    label: Optional[str] = ""

    @validator("label", pre=True, always=True)
    def _default_label(cls, value: Optional[str]) -> str:
        return value or ""


class DistributedLoadPayload(BaseModel):
    start: float = Field(..., ge=0, description="Inicio del tramo en metros")
    end: float = Field(..., description="Fin del tramo en metros")
    intensity: float = Field(..., description="Intensidad en N/m")
    label: Optional[str] = ""

    @validator("label", pre=True, always=True)
    def _default_label(cls, value: Optional[str]) -> str:
        return value or ""

    @root_validator
    def _check_interval(cls, values):
        start = values.get("start")
        end = values.get("end")
        if start is not None and end is not None and end <= start:
            raise ValueError("El fin de la carga distribuida debe ser mayor que el inicio.")
        return values


class BeamPayload(BaseModel):
    length: float = Field(..., gt=0, description="Longitud de la viga en metros")
    height_start: float = 0.0
    height_end: float = 0.0
    support_a_type: str = "Fijo"
    support_b_type: str = "Movil"
    support_c_type: str = "Ninguno"
    support_c_position: Optional[float] = None
    torsor: float = 0.0
    num_points: int = Field(800, ge=50, le=5000)
    point_loads: List[PointLoadPayload] = []
    distributed_loads: List[DistributedLoadPayload] = []

    @root_validator
    def _normalise_support_c(cls, values):
        support_type = (values.get("support_c_type") or "").lower()
        position = values.get("support_c_position")
        if support_type in {"ninguno", "none", ""}:
            values["support_c_position"] = None
        elif position is None:
            raise ValueError("Debe proporcionar la posicion del apoyo C.")
        return values

    @validator("support_a_type", "support_b_type", "support_c_type", pre=True, always=True)
    def _strip_supports(cls, value: str) -> str:
        return (value or "").strip() or "Ninguno"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    default_payload = BeamPayload(
        length=10.0,
        support_a_type="Fijo",
        support_b_type="Movil",
        point_loads=[PointLoadPayload(position=4.0, magnitude=15.0, label="Carga 1")],
        distributed_loads=[
            DistributedLoadPayload(start=6.0, end=9.0, intensity=4.0, label="Carga Distribuida"),
        ],
    )
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_payload": default_payload.dict(),
            "current_year": datetime.utcnow().year,
        },
    )


@app.post("/api/beam/analyze")
async def analyze_beam(payload: BeamPayload):
    try:
        result = compute_beam_analysis(
            length=payload.length,
            height_start=payload.height_start,
            height_end=payload.height_end,
            support_a_type=payload.support_a_type,
            support_b_type=payload.support_b_type,
            support_c_type=payload.support_c_type,
            support_c_position=payload.support_c_position,
            point_loads=[
                PointLoad(position=load.position, magnitude=load.magnitude, label=load.label)
                for load in payload.point_loads
            ],
            distributed_loads=[
                DistributedLoad(start=load.start, end=load.end, intensity=load.intensity, label=load.label)
                for load in payload.distributed_loads
            ],
            torsor=payload.torsor,
            num_points=payload.num_points,
        )
        return JSONResponse(result)
    except BeamComputationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:  # pragma: no cover - unexpected issues
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}
