# -*- coding: utf-8 -*-
"""Analisis simplificado de armaduras y bastidores 2D usando ecuaciones de equilibrio."""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class Nodo:
    """Representa un nodo con coordenadas y cargas externas."""
    x: float
    y: float
    carga_x: float = 0.0
    carga_y: float = 0.0
    restringido_x: bool = False
    restringido_y: bool = False


@dataclass
class Barra:
    """Barra que conecta dos nodos."""
    n_i: int
    n_j: int


class Armadura2D:
    """Resuelve armaduras planas por el metodo de nodos (joints)."""

    def __init__(self, nodos: Dict[int, Nodo], barras: List[Barra]):
        self.nodos = nodos
        self.barras = barras

    def resolver(self) -> Tuple[np.ndarray, Dict[int, Tuple[float, float]]]:
        """Devuelve fuerzas en barras y reacciones (Rx, Ry) por nodo."""
        num_barras = len(self.barras)
        nodos = list(self.nodos.keys())
        num_nodos = len(nodos)

        # Mapear reacciones
        reaccion_vars = []
        for idx in nodos:
            n = self.nodos[idx]
            if n.restringido_x:
                reaccion_vars.append((idx, 'Rx'))
            if n.restringido_y:
                reaccion_vars.append((idx, 'Ry'))
        num_reacciones = len(reaccion_vars)

        # Variables: fuerzas en barras + reacciones
        num_vars = num_barras + num_reacciones
        A = np.zeros((2 * num_nodos, num_vars))
        b = np.zeros(2 * num_nodos)

        # Fuerzas de barras
        for k, barra in enumerate(self.barras):
            i = barra.n_i
            j = barra.n_j
            ni = self.nodos[i]
            nj = self.nodos[j]
            L = np.hypot(nj.x - ni.x, nj.y - ni.y)
            c = (nj.x - ni.x) / L
            s = (nj.y - ni.y) / L
            # Nodo i
            row_ix = nodos.index(i) * 2
            A[row_ix, k] = c
            A[row_ix + 1, k] = s
            # Nodo j
            row_jx = nodos.index(j) * 2
            A[row_jx, k] = -c
            A[row_jx + 1, k] = -s

        # Reacciones
        for r_idx, (n_id, comp) in enumerate(reaccion_vars):
            col = num_barras + r_idx
            row = nodos.index(n_id) * 2
            if comp == 'Rx':
                A[row, col] = 1
            else:
                A[row + 1, col] = 1

        # Vector b con cargas externas
        for idx in nodos:
            n = self.nodos[idx]
            row = nodos.index(idx) * 2
            b[row] = -n.carga_x
            b[row + 1] = -n.carga_y

        # Resolver sistema lineal
        x = np.linalg.solve(A, b)

        # Extraer resultados
        fuerzas_barras = x[:num_barras]
        reacciones = {}
        for r_idx, (n_id, comp) in enumerate(reaccion_vars):
            fuerza = x[num_barras + r_idx]
            rx, ry = reacciones.get(n_id, (0.0, 0.0))
            if comp == 'Rx':
                rx = fuerza
            else:
                ry = fuerza
            reacciones[n_id] = (rx, ry)

        return fuerzas_barras, reacciones


__all__ = ["Nodo", "Barra", "Armadura2D"]
