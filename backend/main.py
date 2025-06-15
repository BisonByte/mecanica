"""FastAPI backend exposing beam simulator calculations."""

from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from . import beam

app = FastAPI(title="Simulador de Viga API")


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
    x, cortante, momento, torsion = beam.generar_diagramas(
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
        "torsion": torsion.tolist(),
    }


class ParRequest(BeamRequest):
    x: float


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
