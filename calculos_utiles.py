# -*- coding: utf-8 -*-
"""Funciones utilitarias para cálculos estructurales.

Este módulo provee funciones independientes de la interfaz
para realizar los cálculos de reacciones en vigas,
centro de masa, análisis de armaduras y bastidores.

La idea es facilitar el ingreso de datos a través de
estructuras de Python o archivos externos sin usar la GUI.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import numpy as np


@dataclass
class CargaPuntual:
    posicion: float
    magnitud: float


@dataclass
class CargaDistribuida:
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
    """Calcula las reacciones en los apoyos de una viga.

    Devuelve una tupla (RA, RB, RC).
    """
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
    """Devuelve la posición del centro de masa de las cargas."""
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


# Funciones de envoltura para armaduras y bastidores usando las clases
# definidas en simulador_viga_mejorado.

from simulador_viga_mejorado import Nodo, Barra, Armadura2D, NodoBastidor, BarraBastidor, Bastidor2D


def resolver_armadura(nodos: Dict[int, Nodo], barras: List[Barra]) -> Tuple[np.ndarray, Dict[int, Tuple[float, float]]]:
    """Calcula fuerzas en barras y reacciones de una armadura plana."""
    arm = Armadura2D(nodos, barras)
    return arm.resolver()


def resolver_bastidor(nodos: Dict[int, NodoBastidor], barras: List[BarraBastidor]) -> Tuple[np.ndarray, Dict[int, Tuple[float, float, float]]]:
    """Obtiene desplazamientos nodales y reacciones de un bastidor plano."""
    bastidor = Bastidor2D(nodos, barras)
    return bastidor.resolver()


__all__ = [
    "CargaPuntual",
    "CargaDistribuida",
    "Viga",
    "calcular_reacciones_viga",
    "centro_de_masa_viga",
    "resolver_armadura",
    "resolver_bastidor",
]

