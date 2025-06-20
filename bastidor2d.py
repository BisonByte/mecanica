# -*- coding: utf-8 -*-
"""Analisis de bastidores (marcos) 2D usando el metodo de rigidez.

Este modulo define estructuras para nodos y barras de bastidor y una clase
`Bastidor2D` que ensambla la matriz global de rigidez aplicando solo las
ecuaciones de equilibrio. Permite calcular desplazamientos y reacciones
en un bastidor plano.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


@dataclass
class NodoBastidor:
    """Nodo con tres grados de libertad: desplazamiento x, y y rotación."""
    x: float
    y: float
    carga_x: float = 0.0
    carga_y: float = 0.0
    momento: float = 0.0
    restringido_x: bool = False
    restringido_y: bool = False
    restringido_rot: bool = False


@dataclass
class BarraBastidor:
    """Barra de bastidor con propiedades mecánicas."""
    n_i: int
    n_j: int
    E: float  # Módulo de elasticidad
    A: float  # Área de la sección
    I: float  # Momento de inercia


class Bastidor2D:
    """Analiza un bastidor plano mediante el método de rigidez."""

    def __init__(self, nodos: Dict[int, NodoBastidor], barras: List[BarraBastidor]):
        self.nodos = nodos
        self.barras = barras

    def resolver(self) -> Tuple[np.ndarray, Dict[int, Tuple[float, float, float]]]:
        """Devuelve desplazamientos nodales y reacciones."""
        nodos = sorted(self.nodos.keys())
        dof_map = {n: i * 3 for i, n in enumerate(nodos)}
        n_dof = 3 * len(nodos)

        K = np.zeros((n_dof, n_dof))
        f_ext = np.zeros(n_dof)

        # Cargas externas
        for idx in nodos:
            n = self.nodos[idx]
            base = dof_map[idx]
            f_ext[base] = n.carga_x
            f_ext[base + 1] = n.carga_y
            f_ext[base + 2] = n.momento

        # Ensamblaje de elementos
        for barra in self.barras:
            ni = self.nodos[barra.n_i]
            nj = self.nodos[barra.n_j]
            dx = nj.x - ni.x
            dy = nj.y - ni.y
            L = np.hypot(dx, dy)
            c = dx / L
            s = dy / L

            A = barra.A
            E = barra.E
            I = barra.I

            EA_L = E * A / L
            EI = E * I
            k_local = np.array([
                [EA_L, 0, 0, -EA_L, 0, 0],
                [0, 12 * EI / L**3, 6 * EI / L**2, 0, -12 * EI / L**3, 6 * EI / L**2],
                [0, 6 * EI / L**2, 4 * EI / L, 0, -6 * EI / L**2, 2 * EI / L],
                [-EA_L, 0, 0, EA_L, 0, 0],
                [0, -12 * EI / L**3, -6 * EI / L**2, 0, 12 * EI / L**3, -6 * EI / L**2],
                [0, 6 * EI / L**2, 2 * EI / L, 0, -6 * EI / L**2, 4 * EI / L],
            ])

            T = np.array([
                [c, s, 0, 0, 0, 0],
                [-s, c, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 0, 0, c, s, 0],
                [0, 0, 0, -s, c, 0],
                [0, 0, 0, 0, 0, 1],
            ])

            k_global = T.T @ k_local @ T

            idx_i = dof_map[barra.n_i]
            idx_j = dof_map[barra.n_j]

            # Submatrices
            for r in range(3):
                for c in range(3):
                    K[idx_i + r, idx_i + c] += k_global[r, c]
                    K[idx_i + r, idx_j + c] += k_global[r, c + 3]
                    K[idx_j + r, idx_i + c] += k_global[r + 3, c]
                    K[idx_j + r, idx_j + c] += k_global[r + 3, c + 3]

        # Identificar grados de libertad libres
        free = []
        for idx in nodos:
            n = self.nodos[idx]
            base = dof_map[idx]
            if not n.restringido_x:
                free.append(base)
            if not n.restringido_y:
                free.append(base + 1)
            if not n.restringido_rot:
                free.append(base + 2)

        free = np.array(free, dtype=int)
        K_ff = K[np.ix_(free, free)]
        f_f = f_ext[free]

        disp = np.zeros(n_dof)
        if K_ff.size > 0:
            disp_free = np.linalg.solve(K_ff, f_f)
            disp[free] = disp_free

        reactions = K @ disp - f_ext

        reacc_nodales = {}
        for idx in nodos:
            base = dof_map[idx]
            rx = reactions[base]
            ry = reactions[base + 1]
            rm = reactions[base + 2]
            reacc_nodales[idx] = (rx, ry, rm)

        return disp, reacc_nodales
