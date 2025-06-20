from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np


@dataclass
class CargaPuntual:
    """Carga puntual aplicada en una posición."""
    posicion: float
    magnitud: float


@dataclass
class CargaDistribuida:
    """Carga distribuida con magnitud constante."""
    inicio: float
    fin: float
    magnitud: float

    @property
    def fuerza_equivalente(self) -> float:
        return self.magnitud * (self.fin - self.inicio)

    @property
    def centroide(self) -> float:
        return self.inicio + (self.fin - self.inicio) / 2


@dataclass
class Viga:
    """Representación simplificada de una viga."""
    longitud: float
    tipo_apoyo_a: str = "Fijo"
    tipo_apoyo_b: str = "Móvil"
    tipo_apoyo_c: str = "Ninguno"
    posicion_apoyo_c: float = 0.0
    par_torsor: float = 0.0
    cargas_puntuales: List[CargaPuntual] = field(default_factory=list)
    cargas_distribuidas: List[CargaDistribuida] = field(default_factory=list)

    def agregar_carga_puntual(self, pos: float, magnitud: float) -> None:
        self.cargas_puntuales.append(CargaPuntual(pos, magnitud))

    def agregar_carga_distribuida(self, inicio: float, fin: float, magnitud: float) -> None:
        self.cargas_distribuidas.append(CargaDistribuida(inicio, fin, magnitud))


def calcular_reacciones_viga(viga: Viga) -> Tuple[float, float, float]:
    """Calcula las reacciones de la viga."""
    suma_fuerzas_y = 0.0
    suma_momentos_a = 0.0
    L = viga.longitud

    for carga in viga.cargas_puntuales:
        suma_fuerzas_y += carga.magnitud
        suma_momentos_a += carga.magnitud * carga.posicion

    for dist in viga.cargas_distribuidas:
        F = dist.fuerza_equivalente
        x = dist.centroide
        suma_fuerzas_y += F
        suma_momentos_a += F * x

    T = viga.par_torsor

    if viga.tipo_apoyo_c == "Ninguno":
        RB = (suma_momentos_a + T) / L
        RA = suma_fuerzas_y - RB
        RC = 0.0
    else:
        c = viga.posicion_apoyo_c
        RB = ((suma_momentos_a + T) - c * suma_fuerzas_y / 2) / (L - c)
        RA = RC = (suma_fuerzas_y - RB) / 2

    return RA, RB, RC


def centro_de_masa_viga(viga: Viga) -> float:
    """Posición del centro de masa de las cargas."""
    suma_momentos = 0.0
    suma_cargas = 0.0

    for carga in viga.cargas_puntuales:
        suma_momentos += carga.posicion * carga.magnitud
        suma_cargas += carga.magnitud

    for dist in viga.cargas_distribuidas:
        F = dist.fuerza_equivalente
        x = dist.centroide
        suma_momentos += x * F
        suma_cargas += F

    if suma_cargas == 0:
        raise ValueError("No hay cargas definidas")

    return suma_momentos / suma_cargas


__all__ = [
    "CargaPuntual",
    "CargaDistribuida",
    "Viga",
    "calcular_reacciones_viga",
    "centro_de_masa_viga",
]
