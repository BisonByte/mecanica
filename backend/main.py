"""FastAPI backend exposing beam simulator calculations."""

from typing import List
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import beam

app = FastAPI(title="Simulador de Viga API")


@app.get("/")
def read_index() -> FileResponse:
    """Serve the main frontend page."""
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    return FileResponse(frontend_dir / "index.html")


class PointLoad(BaseModel):
    pos: float
    mag: float


class DistLoad(BaseModel):
    inicio: float
    fin: float
    mag: float


class BeamRequest(BaseModel):
    longitud: float
    cargas_puntuales: List[PointLoad] = []
    cargas_distribuidas: List[DistLoad] = []
    tipo_apoyo_c: str = "Ninguno"
    posicion_apoyo_c: float = 0.0
    par_torsor: float = 0.0


@app.post("/calcular_reacciones")
def api_calcular_reacciones(data: BeamRequest):
    RA, RB, RC = beam.calcular_reacciones(
        data.longitud,
        [(c.pos, c.mag) for c in data.cargas_puntuales],
        [(d.inicio, d.fin, d.mag) for d in data.cargas_distribuidas],
        data.tipo_apoyo_c,
        data.posicion_apoyo_c,
        data.par_torsor,
    )
    return {"RA": RA, "RB": RB, "RC": RC}


@app.post("/calcular_centro_masa")
def api_centro_masa(data: BeamRequest):
    x_cm = beam.calcular_centro_masa(
        [(c.pos, c.mag) for c in data.cargas_puntuales],
        [(d.inicio, d.fin, d.mag) for d in data.cargas_distribuidas],
    )
    return {"x_cm": x_cm}


@app.post("/generar_diagramas")
def api_generar_diagramas(data: BeamRequest):
    x, cortante, momento = beam.generar_diagramas(
        data.longitud,
        [(c.pos, c.mag) for c in data.cargas_puntuales],
        [(d.inicio, d.fin, d.mag) for d in data.cargas_distribuidas],
        data.tipo_apoyo_c,
        data.posicion_apoyo_c,
        data.par_torsor,
    )
    return {
        "x": x.tolist(),
        "cortante": cortante.tolist(),
        "momento": momento.tolist(),
    }


class ParRequest(BeamRequest):
    x: float


class SectionPropsRequest(BaseModel):
    b1: float
    h1: float
    b2: float
    h2: float
    b3: float
    h3: float


@app.post("/par_en_punto")
def api_par_en_punto(data: ParRequest):
    M = beam.par_en_punto(
        data.x,
        data.longitud,
        [(c.pos, c.mag) for c in data.cargas_puntuales],
        [(d.inicio, d.fin, d.mag) for d in data.cargas_distribuidas],
        data.tipo_apoyo_c,
        data.posicion_apoyo_c,
        data.par_torsor,
    )
    return {"torsor": M}


@app.post("/propiedades_seccion")
def api_propiedades_seccion(req: SectionPropsRequest):
    """Return area, center of gravity and moment of inertia for an I-beam."""
    area_total = req.b1 * req.h1 + req.b2 * req.h2 + req.b3 * req.h3
    y_cg = (
        req.b1 * req.h1 * (req.h2 + req.h3 + req.h1 / 2)
        + req.b2 * req.h2 * (req.h3 + req.h2 / 2)
        + req.b3 * req.h3 * (req.h3 / 2)
    ) / area_total

    I_superior = (req.b1 * req.h1 ** 3) / 12 + req.b1 * req.h1 * (
        req.h2 + req.h3 + req.h1 / 2 - y_cg
    ) ** 2
    I_alma = (req.b2 * req.h2 ** 3) / 12 + req.b2 * req.h2 * (
        req.h3 + req.h2 / 2 - y_cg
    ) ** 2
    I_inferior = (req.b3 * req.h3 ** 3) / 12 + req.b3 * req.h3 * (
        req.h3 / 2 - y_cg
    ) ** 2
    I_total = I_superior + I_alma + I_inferior

    return {
        "area": area_total,
        "y_cg": y_cg,
        "inercia": I_total,
    }
