"""Core calculation utilities for the beam simulator."""

from typing import List, Tuple

import numpy as np


# Types for clarity
PointLoad = Tuple[float, float]  # position, magnitude
DistLoad = Tuple[float, float, float]  # start, end, magnitude


def calcular_reacciones(
    longitud: float,
    cargas_puntuales: List[PointLoad],
    cargas_distribuidas: List[DistLoad],
    tipo_apoyo_c: str = "Ninguno",
    posicion_apoyo_c: float = 0.0,
    par_torsor: float = 0.0,
) -> Tuple[float, float, float]:
    """Return reactions (RA, RB, RC) for a simply supported beam with optional
    third support C and torsor."""
    suma_fuerzas_y = 0.0
    suma_momentos_a = 0.0

    for pos, mag in cargas_puntuales:
        suma_fuerzas_y += mag
        suma_momentos_a += mag * pos

    for inicio, fin, mag in cargas_distribuidas:
        longitud_carga = fin - inicio
        fuerza_total = mag * longitud_carga
        centroide = inicio + longitud_carga / 2
        suma_fuerzas_y += fuerza_total
        suma_momentos_a += fuerza_total * centroide

    if tipo_apoyo_c == "Ninguno":
        RB = (suma_momentos_a + par_torsor) / longitud
        RA = suma_fuerzas_y - RB
        RC = 0.0
    else:
        c = posicion_apoyo_c
        RB = ((suma_momentos_a + par_torsor) - c * suma_fuerzas_y / 2) / (longitud - c)
        RA = (suma_fuerzas_y - RB) / 2
        RC = RA

    return RA, RB, RC


def calcular_centro_masa(
    cargas_puntuales: List[PointLoad],
    cargas_distribuidas: List[DistLoad],
) -> float:
    """Return x coordinate of the resultant load."""
    suma_momentos = 0.0
    suma_cargas = 0.0

    for pos, mag in cargas_puntuales:
        suma_momentos += pos * mag
        suma_cargas += mag

    for inicio, fin, mag in cargas_distribuidas:
        longitud_carga = fin - inicio
        fuerza_total = mag * longitud_carga
        centroide = inicio + longitud_carga / 2
        suma_momentos += centroide * fuerza_total
        suma_cargas += fuerza_total

    if suma_cargas == 0:
        raise ValueError("No se definieron cargas")

    return suma_momentos / suma_cargas


def generar_diagramas(
    longitud: float,
    cargas_puntuales: List[PointLoad],
    cargas_distribuidas: List[DistLoad],
    tipo_apoyo_c: str = "Ninguno",
    posicion_apoyo_c: float = 0.0,
    par_torsor: float = 0.0,
    num_puntos: int = 500,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return x positions, shear force and bending moment diagrams."""
    RA, RB, RC = calcular_reacciones(
        longitud,
        cargas_puntuales,
        cargas_distribuidas,
        tipo_apoyo_c,
        posicion_apoyo_c,
        par_torsor,
    )
    c = posicion_apoyo_c
    x = np.linspace(0, longitud, num_puntos)
    cortante = np.zeros_like(x)
    momento = np.zeros_like(x)

    for i, xi in enumerate(x):
        V = RA
        M = RA * xi + par_torsor

        if tipo_apoyo_c != "Ninguno" and xi >= c:
            V += RC
            M += RC * (xi - c)

        if xi >= longitud:
            V += RB
            M += RB * (xi - longitud)

        for pos, mag in cargas_puntuales:
            if xi > pos:
                V -= mag
                M -= mag * (xi - pos)

        for inicio, fin, mag in cargas_distribuidas:
            if xi > inicio:
                if xi <= fin:
                    long_actual = xi - inicio
                    V -= mag * long_actual
                    M -= mag * long_actual ** 2 / 2
                else:
                    long_total = fin - inicio
                    V -= mag * long_total
                    M -= mag * long_total * (xi - (inicio + long_total / 2))

        cortante[i] = V
        momento[i] = M

    return x, cortante, momento


def par_en_punto(
    x: float,
    longitud: float,
    cargas_puntuales: List[PointLoad],
    cargas_distribuidas: List[DistLoad],
    tipo_apoyo_c: str = "Ninguno",
    posicion_apoyo_c: float = 0.0,
    par_torsor: float = 0.0,
) -> float:
    """Return internal torsor moment at position x."""
    RA, RB, RC = calcular_reacciones(
        longitud,
        cargas_puntuales,
        cargas_distribuidas,
        tipo_apoyo_c,
        posicion_apoyo_c,
        par_torsor,
    )
    c = posicion_apoyo_c
    momento = par_torsor

    if x >= 0:
        momento += RA * x
    if tipo_apoyo_c != "Ninguno" and x >= c:
        momento += RC * (x - c)
    if x >= longitud:
        momento += RB * (x - longitud)

    for pos, mag in cargas_puntuales:
        if x > pos:
            momento -= mag * (x - pos)

    for inicio, fin, mag in cargas_distribuidas:
        if x > inicio:
            if x <= fin:
                long_actual = x - inicio
                momento -= mag * long_actual ** 2 / 2
            else:
                long_total = fin - inicio
                momento -= mag * long_total * (x - (inicio + long_total / 2))

    return momento
