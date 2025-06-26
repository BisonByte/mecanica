import matplotlib.pyplot as plt

class Viga:
    """Representa una viga con cargas puntuales"""
    def __init__(self, longitud, cargas=None):
        self.longitud = float(longitud)
        self.cargas = cargas if cargas else []  # lista de (posicion, Fy, Fx)

    def fuerza_vertical_total(self):
        return sum(c[1] for c in self.cargas)

    def momentos_en(self, ref):
        return sum(c[1] * (c[0] - ref) for c in self.cargas)


class BastidorConPasador:
    """Analiza dos vigas conectadas por un pasador"""
    def __init__(self, viga_izq, viga_der):
        self.viga_izq = viga_izq
        self.viga_der = viga_der
        self.RA = 0
        self.RB = 0
        self.C = 0  # Fuerza vertical en el pasador

    @property
    def longitud_total(self):
        return self.viga_izq.longitud + self.viga_der.longitud

    def calcular_reacciones(self):
        L = self.longitud_total
        Fy_tot = (self.viga_izq.fuerza_vertical_total() +
                   self.viga_der.fuerza_vertical_total())

        M_A = (self.viga_izq.momentos_en(0) +
                self.viga_der.momentos_en(self.viga_izq.longitud))

        self.RB = (M_A) / L
        self.RA = Fy_tot - self.RB
        return self.RA, self.RB

    def calcular_fuerza_pasador(self):
        # Equilibrio viga izquierda
        Fy_left = self.viga_izq.fuerza_vertical_total()
        M_left = self.viga_izq.momentos_en(0)
        self.C = (M_left - self.RA * 0) / self.viga_izq.longitud
        # check signo
        self.C = Fy_left + self.RA - self.C
        return self.C

    def resumen(self):
        self.calcular_reacciones()
        self.calcular_fuerza_pasador()
        print(f"RA={self.RA:.2f} N, RB={self.RB:.2f} N, C={self.C:.2f} N")

    def graficar_dcl(self):
        fig, axes = plt.subplots(3, 1, figsize=(8, 8))
        # DCL completo
        axes[0].set_title('Estructura Completa')
        self._dibujar_viga(axes[0], 0, self.longitud_total,
                           self.viga_izq.cargas +
                           [(x+self.viga_izq.longitud, Fy, Fx)
                            for x, Fy, Fx in self.viga_der.cargas],
                           reacciones=[(0, self.RA), (self.longitud_total, self.RB)])
        # Izquierda
        axes[1].set_title('Viga Izquierda')
        self._dibujar_viga(axes[1], 0, self.viga_izq.longitud,
                           self.viga_izq.cargas,
                           reacciones=[(0, self.RA), (self.viga_izq.longitud, -self.C)])
        # Derecha
        axes[2].set_title('Viga Derecha')
        self._dibujar_viga(axes[2], 0, self.viga_der.longitud,
                           self.viga_der.cargas,
                           reacciones=[(0, self.C), (self.viga_der.longitud, self.RB)])
        for ax in axes:
            ax.set_xlim(-0.5, max(self.longitud_total, self.viga_der.longitud)+0.5)
            ax.axhline(0, color='black', linewidth=2)
            ax.set_ylim(-1, 1)
            ax.axis('off')
        plt.tight_layout()
        plt.show()

    def _dibujar_viga(self, ax, x0, L, cargas, reacciones):
        ax.plot([x0, x0+L], [0, 0], 'k-', lw=3)
        for pos, Fy, _ in cargas:
            ax.arrow(x0+pos, 0.2 if Fy<0 else -0.2, 0, -Fy/abs(Fy)*0.4,
                     head_width=0.1, head_length=0.1, fc='red', ec='red')
        for pos, Fy in reacciones:
            ax.arrow(x0+pos, 0, 0, Fy/abs(Fy)*0.5,
                     head_width=0.1, head_length=0.1, fc='blue', ec='blue')

if __name__ == '__main__':
    # Ejemplo sencillo
    v1 = Viga(3.0, [(1.5, -500, 0)])  # carga puntual hacia abajo en el centro
    v2 = Viga(2.0, [(1.0, -200, 0)])
    modelo = BastidorConPasador(v1, v2)
    modelo.resumen()
    modelo.graficar_dcl()
