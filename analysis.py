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
    """Resuelve armaduras planas por el método de nodos."""

    def __init__(self, nodos: Dict[int, Nodo], barras: List[Barra]):
        self.nodos = nodos
        self.barras = barras

    def resolver(self) -> Tuple[np.ndarray, Dict[int, Tuple[float, float]]]:
        num_barras = len(self.barras)
        nodos = list(self.nodos.keys())
        num_nodos = len(nodos)

        reaccion_vars = []
        for idx in nodos:
            n = self.nodos[idx]
            if n.restringido_x:
                reaccion_vars.append((idx, "Rx"))
            if n.restringido_y:
                reaccion_vars.append((idx, "Ry"))
        num_reacciones = len(reaccion_vars)

        num_vars = num_barras + num_reacciones
        A = np.zeros((2 * num_nodos, num_vars))
        b = np.zeros(2 * num_nodos)

        for k, barra in enumerate(self.barras):
            i = barra.n_i
            j = barra.n_j
            ni = self.nodos[i]
            nj = self.nodos[j]
            L = np.hypot(nj.x - ni.x, nj.y - ni.y)
            c = (nj.x - ni.x) / L
            s = (nj.y - ni.y) / L
            row_ix = nodos.index(i) * 2
            A[row_ix, k] = c
            A[row_ix + 1, k] = s
            row_jx = nodos.index(j) * 2
            A[row_jx, k] = -c
            A[row_jx + 1, k] = -s

        for r_idx, (n_id, comp) in enumerate(reaccion_vars):
            col = num_barras + r_idx
            row = nodos.index(n_id) * 2
            if comp == "Rx":
                A[row, col] = 1
            else:
                A[row + 1, col] = 1

        for idx in nodos:
            n = self.nodos[idx]
            row = nodos.index(idx) * 2
            b[row] = -n.carga_x
            b[row + 1] = -n.carga_y

        x = np.linalg.solve(A, b)

        fuerzas_barras = x[:num_barras]
        reacciones = {}
        for r_idx, (n_id, comp) in enumerate(reaccion_vars):
            fuerza = x[num_barras + r_idx]
            rx, ry = reacciones.get(n_id, (0.0, 0.0))
            if comp == "Rx":
                rx = fuerza
            else:
                ry = fuerza
            reacciones[n_id] = (rx, ry)

        return fuerzas_barras, reacciones

@dataclass
class NodoBastidor:
    """Nodo con tres grados de libertad para análisis de bastidores."""
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
    """Elemento de bastidor con propiedades mecánicas."""
    n_i: int
    n_j: int
    E: float
    A: float
    I: float

class Bastidor2D:
    """Analiza un bastidor plano mediante el método de rigidez."""

    def __init__(self, nodos: Dict[int, NodoBastidor], barras: List[BarraBastidor]):
        self.nodos = nodos
        self.barras = barras

    def resolver(self) -> Tuple[np.ndarray, Dict[int, Tuple[float, float, float]]]:
        nodos = sorted(self.nodos.keys())
        dof_map = {n: i * 3 for i, n in enumerate(nodos)}
        n_dof = 3 * len(nodos)

        K = np.zeros((n_dof, n_dof))
        f_ext = np.zeros(n_dof)

        for idx in nodos:
            n = self.nodos[idx]
            base = dof_map[idx]
            f_ext[base] = n.carga_x
            f_ext[base + 1] = n.carga_y
            f_ext[base + 2] = n.momento

        for barra in self.barras:
            ni = self.nodos[barra.n_i]
            nj = self.nodos[barra.n_j]
            dx = nj.x - ni.x
            dy = nj.y - ni.y
            L = np.hypot(dx, dy)
            c = dx / L
            s = dy / L

            EA_L = barra.E * barra.A / L
            EI = barra.E * barra.I
            k_local = np.array([
                [EA_L, 0, 0, -EA_L, 0, 0],
                [0, 12 * EI / L ** 3, 6 * EI / L ** 2, 0, -12 * EI / L ** 3, 6 * EI / L ** 2],
                [0, 6 * EI / L ** 2, 4 * EI / L, 0, -6 * EI / L ** 2, 2 * EI / L],
                [-EA_L, 0, 0, EA_L, 0, 0],
                [0, -12 * EI / L ** 3, -6 * EI / L ** 2, 0, 12 * EI / L ** 3, -6 * EI / L ** 2],
                [0, 6 * EI / L ** 2, 2 * EI / L, 0, -6 * EI / L ** 2, 4 * EI / L],
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
            for r in range(3):
                for c in range(3):
                    K[idx_i + r, idx_i + c] += k_global[r, c]
                    K[idx_i + r, idx_j + c] += k_global[r, c + 3]
                    K[idx_j + r, idx_i + c] += k_global[r + 3, c]
                    K[idx_j + r, idx_j + c] += k_global[r + 3, c + 3]

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

def resolver_armadura(nodos: Dict[int, Nodo], barras: List[Barra]) -> Tuple[np.ndarray, Dict[int, Tuple[float, float]]]:
    arm = Armadura2D(nodos, barras)
    return arm.resolver()

def resolver_bastidor(nodos: Dict[int, NodoBastidor], barras: List[BarraBastidor]) -> Tuple[np.ndarray, Dict[int, Tuple[float, float, float]]]:
    bastidor = Bastidor2D(nodos, barras)
    return bastidor.resolver()

__all__ = [
    "Nodo",
    "Barra",
    "Armadura2D",
    "NodoBastidor",
    "BarraBastidor",
    "Bastidor2D",
    "resolver_armadura",
    "resolver_bastidor",
]
