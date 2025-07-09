import tkinter as tk
from tkinter import ttk, messagebox

try:
    import ttkbootstrap as ttkb
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    ttkb = None
    BOOTSTRAP_AVAILABLE = False
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import argparse


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
        Fy_tot = (
            self.viga_izq.fuerza_vertical_total()
            + self.viga_der.fuerza_vertical_total()
        )

        M_A = self.viga_izq.momentos_en(0) + self.viga_der.momentos_en(
            self.viga_izq.longitud
        )

        self.RB = M_A / L
        self.RA = Fy_tot - self.RB
        return self.RA, self.RB

    def calcular_fuerza_pasador(self):
        Fy_left = self.viga_izq.fuerza_vertical_total()
        M_left = self.viga_izq.momentos_en(0)
        self.C = (M_left - self.RA * 0) / self.viga_izq.longitud
        self.C = Fy_left + self.RA - self.C
        return self.C

    def resumen(self):
        self.calcular_reacciones()
        self.calcular_fuerza_pasador()
        print(f"RA={self.RA:.2f} N, RB={self.RB:.2f} N, C={self.C:.2f} N")

    def graficar_dcl(self):
        fig, axes = plt.subplots(3, 1, figsize=(8, 8))
        axes[0].set_title("Estructura Completa")
        self._dibujar_viga(
            axes[0],
            0,
            self.longitud_total,
            self.viga_izq.cargas
            + [
                (x + self.viga_izq.longitud, Fy, Fx)
                for x, Fy, Fx in self.viga_der.cargas
            ],
            reacciones=[(0, self.RA), (self.longitud_total, self.RB)],
        )
        axes[1].set_title("Viga Izquierda")
        self._dibujar_viga(
            axes[1],
            0,
            self.viga_izq.longitud,
            self.viga_izq.cargas,
            reacciones=[(0, self.RA), (self.viga_izq.longitud, -self.C)],
        )
        axes[2].set_title("Viga Derecha")
        self._dibujar_viga(
            axes[2],
            0,
            self.viga_der.longitud,
            self.viga_der.cargas,
            reacciones=[(0, self.C), (self.viga_der.longitud, self.RB)],
        )
        for ax in axes:
            ax.set_xlim(
                -0.5,
                max(self.longitud_total, self.viga_der.longitud) + 0.5,
            )
            ax.axhline(0, color="black", linewidth=2)
            ax.set_ylim(-1, 1)
            ax.axis("off")
        plt.tight_layout()
        plt.show()

    def _dibujar_viga(self, ax, x0, L, cargas, reacciones):
        ax.plot([x0, x0 + L], [0, 0], "k-", lw=3)
        for pos, Fy, _ in cargas:
            ax.arrow(
                x0 + pos,
                0.2 if Fy < 0 else -0.2,
                0,
                -Fy / abs(Fy) * 0.4,
                head_width=0.1,
                head_length=0.1,
                fc="red",
                ec="red",
            )
        for pos, Fy in reacciones:
            ax.arrow(
                x0 + pos,
                0,
                0,
                Fy / abs(Fy) * 0.5,
                head_width=0.1,
                head_length=0.1,
                fc="blue",
                ec="blue",
            )


class SimuladorVigaMejorado:
    def __init__(self, root, bootstrap=False):
        self.root = root
        self.bootstrap = bootstrap
        self.root.title("Simulador de Viga Mecánica - Versión Completa")
        # Ajustar el tamaño de la ventana para un layout más compacto
        self.root.geometry("1000x800")

        # Configurar tema y estilo moderno
        if self.bootstrap:
            # En ttkbootstrap la instancia de estilo ya existe
            self.style = self.root.style
        else:
            self.style = ttk.Style()
            if 'clam' in self.style.theme_names():
                self.style.theme_use('clam')

        # Paletas de colores para modo claro y oscuro
        self.bg_light = "#f7f7f7"
        self.fg_light = "#333333"
        self.accent_light = "#007acc"
        self.active_light = "#005a9e"

        self.bg_dark = "#222222"
        self.fg_dark = "#f0f0f0"
        self.accent_dark = "#5599ff"
        self.active_dark = "#3e70ff"

        # Estado de tema
        self.dark_mode = tk.BooleanVar(value=False)
        self.texto_tema = tk.StringVar(value="🌓 Modo Oscuro")

        self.apply_theme()

        # Variables principales
        self.longitud = tk.DoubleVar(value=10.0)
        self.cargas_puntuales = []
        self.cargas_distribuidas = []
        self.tipo_apoyo_a = tk.StringVar(value="Fijo")
        self.tipo_apoyo_b = tk.StringVar(value="Móvil")
        self.tipo_apoyo_c = tk.StringVar(value="Ninguno")
        self.posicion_apoyo_c = tk.DoubleVar(value=5.0)

        # Nueva variable para el par torsor
        self.par_torsor = tk.DoubleVar(value=0.0)
        # Posición para evaluar el par torsor
        self.posicion_torsor = tk.DoubleVar(value=0.0)

        # Guardar reacciones para cálculos posteriores
        self.reaccion_a = 0.0
        self.reaccion_b = 0.0
        self.reaccion_c = 0.0
        # Componentes en X e Y
        self.reaccion_a_x = 0.0
        self.reaccion_a_y = 0.0
        self.reaccion_b_x = 0.0
        self.reaccion_b_y = 0.0
        self.reaccion_c_x = 0.0
        self.reaccion_c_y = 0.0

        # Lista de puntos para centro de masa 3D (x, y, z, m)
        self.puntos_masa_3d = []

        # Variables para nuevas cargas
        self.posicion_carga = tk.DoubleVar(value=0.0)
        self.magnitud_carga = tk.DoubleVar(value=10.0)
        self.inicio_dist = tk.DoubleVar(value=0.0)
        self.fin_dist = tk.DoubleVar(value=5.0)
        self.magnitud_dist = tk.DoubleVar(value=5.0)

        # Variable para modo 3D
        self.modo_3d = tk.BooleanVar(value=False)

        # Nuevas variables para la altura de la viga
        self.altura_inicial = tk.DoubleVar(value=0.0)
        self.altura_final = tk.DoubleVar(value=0.0)

        # Variables para la sección transversal
        self.ancho_superior = tk.DoubleVar(value=20)
        self.altura_superior = tk.DoubleVar(value=5)
        self.ancho_alma = tk.DoubleVar(value=5)
        self.altura_alma = tk.DoubleVar(value=30)
        self.ancho_inferior = tk.DoubleVar(value=15)
        self.altura_inferior = tk.DoubleVar(value=5)

        self.formas = []
        # Variables para arrastrar formas
        self.forma_seleccionada = None
        self.desplazamiento_x = 0
        self.desplazamiento_y = 0
        # Variables para escalar formas con el mouse
        self.forma_escalando = None
        self.inicio_escala_x = 0
        self.inicio_escala_y = 0
        self.ancho_inicial = 0
        self.alto_inicial = 0
        # Datos para armaduras/bastidores
        self.nodos_arm = []
        self.miembros_arm = []
        self.cargas_arm = []
        self.id_nodo_actual = 1
        # Valores por defecto para el método de secciones
        self.corte_valor = tk.DoubleVar(value=0.0)
        self.corte_eje = tk.StringVar(value="X")

        # INICIALIZACIÓN DE VARIABLES PARA ARMADURAS Y BASTIDORES AQUI
        self.nodo_x = tk.DoubleVar(value=0.0)
        self.nodo_y = tk.DoubleVar(value=0.0)
        self.nodo_apoyo_arm = tk.StringVar(value="Libre") # Cambiado el nombre a nodo_apoyo_arm para evitar conflicto

        self.miembro_inicio = tk.IntVar(value=1)
        self.miembro_fin = tk.IntVar(value=2)

        self.carga_nodo = tk.IntVar(value=1)
        self.carga_fx = tk.DoubleVar(value=0.0)
        self.carga_fy = tk.DoubleVar(value=0.0)

        # Datos para bastidores
        self.nodos_bast = []
        self.miembros_bast = []
        self.cargas_bast = []
        self.id_nodo_bast = 1
        self.corte_valor_bast = tk.DoubleVar(value=0.0)
        self.corte_eje_bast = tk.StringVar(value="X")

        self.nodo_x_bast = tk.DoubleVar(value=0.0)
        self.nodo_y_bast = tk.DoubleVar(value=0.0)
        self.nodo_apoyo_bast = tk.StringVar(value="Libre")
        self.nodo_pasadores_bast = tk.IntVar(value=1)

        self.miembro_inicio_bast = tk.IntVar(value=1)
        self.miembro_fin_bast = tk.IntVar(value=2)

        self.carga_nodo_bast = tk.IntVar(value=1)
        self.carga_fx_bast = tk.DoubleVar(value=0.0)
        self.carga_fy_bast = tk.DoubleVar(value=0.0)
        self.nodo_fuerza_bast = tk.IntVar(value=1) # Inicialización de la variable que faltaba


        # Espaciado de la cuadrícula para el lienzo de formas
        self.grid_spacing = 20

        # Variables para deformación axial y térmica
        self.modulo_young = tk.DoubleVar(value=200.0)  # GPa
        self.coef_expansion = tk.DoubleVar(value=12e-6)  # /°C
        self.longitud_inicial_def = tk.DoubleVar(value=2.0)  # m
        self.area_transversal = tk.DoubleVar(value=500.0)  # mm^2
        self.fuerza_tension = tk.DoubleVar(value=50.0)  # kN
        self.cambio_temperatura = tk.DoubleVar(value=30.0)  # °C

        self.crear_widgets()

        # Mostrar mensaje inicial
        self.mostrar_mensaje_inicial()

        # Dibujar la viga inicial
        self.dibujar_viga_actual()

    def on_button_click(self, button, action):
        """Flash the button and execute its action."""
        self.flash_button(button)
        self.root.after(10, action)

    def flash_button(self, button):
        orig_style = button.cget("style")
        button.configure(style="Flash.TButton")
        self.root.after(200, lambda: button.configure(style=orig_style))

    def apply_theme(self):
        """Aplicar paleta de colores según el modo actual."""
        if self.bootstrap:
            theme = "darkly" if self.dark_mode.get() else "flatly"
            # ttkbootstrap usa el estilo del root
            self.root.style.theme_use(theme)
            return

        if self.dark_mode.get():
            bg_color = self.bg_dark
            fg_color = self.fg_dark
            accent = self.accent_dark
            active = self.active_dark
        else:
            bg_color = self.bg_light
            fg_color = self.fg_light
            accent = self.accent_light
            active = self.active_light

        s = self.style
        s.configure("TFrame", background=bg_color)
        s.configure("TLabelframe", background=bg_color)
        s.configure("TLabelframe.Label", background=bg_color,
                    foreground=accent, font=("Helvetica", 11, "bold"))
        s.configure("TButton", font=("Helvetica", 10, "bold"),
                    background=accent, foreground="white")
        s.map("TButton",
              background=[('active', active)],
              foreground=[('active', 'white')])
        s.configure("Action.TButton", font=("Arial", 10, "bold"), padding=5,
                    background=accent, foreground="white")
        s.map("Action.TButton", background=[('active', active)],
               foreground=[('active', 'white')])
        s.configure("Warning.TButton", background="#ff9999", font=("Arial", 10, "bold"), padding=5)
        s.configure("Flash.TButton", background="#ffd966", font=("Arial", 10, "bold"))
        s.map("Flash.TButton", background=[('active', '#ffcc33')])
        s.configure("TLabel", font=("Helvetica", 10),
                    background=bg_color, foreground=fg_color)
        s.configure("TEntry", font=("Helvetica", 10))
        s.configure("TNotebook", background=bg_color)
        s.configure("TNotebook.Tab", font=("Helvetica", 10, "bold"))
        self.root.configure(bg=bg_color)

    def toggle_dark_mode(self):
        """Cambiar entre modo claro y oscuro."""
        self.dark_mode.set(not self.dark_mode.get())
        self.texto_tema.set("🌞 Modo Claro" if self.dark_mode.get() else "🌓 Modo Oscuro")
        self.apply_theme()

    def log(self, texto, tag="data"):
        """Inserta texto en la casilla de resultados con estilo."""
        self.texto_resultado.insert("end", texto, tag)
        self.texto_resultado.see("end")


    def crear_widgets(self):
        # Usar un Notebook para organizar mejor la interfaz
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=5) # Ajustar padding del notebook

        tab_config = ttk.Frame(notebook)
        tab_seccion = ttk.Frame(notebook)
        tab_armaduras = ttk.Frame(notebook)
        tab_bastidores = ttk.Frame(notebook)
        tab_axial_termica = ttk.Frame(notebook)
        tab_result = ttk.Frame(notebook)


        notebook.add(tab_config, text="🏗️Configuración y Cargas")
        notebook.add(tab_seccion, text="🏗️Sección y Formas")
        notebook.add(tab_armaduras, text="🏗️Armaduras")
        notebook.add(tab_bastidores, text="🏗️Bastidores")
        notebook.add(tab_axial_termica, text="⚙️Axial y Térmica")
        notebook.add(tab_result, text="🏗️Resultados")

        # Sección configuración y cargas
        tab_config.columnconfigure(0, weight=1)
        tab_config.columnconfigure(1, weight=1)

        frame_config = self.crear_seccion_configuracion_viga(tab_config)
        frame_puntual = self.crear_seccion_cargas_puntuales(tab_config)
        frame_dist = self.crear_seccion_cargas_distribuidas(tab_config)
        frame_botones = self.crear_seccion_botones_calculo(tab_config)

        frame_config.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5) # Ajustar padding
        frame_puntual.grid(row=1, column=0, sticky="nsew", padx=5, pady=5) # Ajustar padding
        frame_dist.grid(row=1, column=1, sticky="nsew", padx=5, pady=5) # Ajustar padding
        frame_botones.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5) # Ajustar padding

        # Sección propiedades de la sección y formas irregulares
        self.crear_seccion_propiedades_seccion(tab_seccion)
        self.crear_widgets_formas_irregulares(tab_seccion)

        # Armaduras
        self.crear_seccion_armaduras(tab_armaduras)
        # Bastidores
        self.crear_seccion_bastidores(tab_bastidores)
        # Deformación Axial y Térmica
        self.crear_seccion_axial_termica(tab_axial_termica)

        # Resultados y gráficos
        self.crear_seccion_resultados(tab_result)
        self.crear_seccion_graficos(tab_result)

    def crear_seccion_configuracion_viga(self, parent):
        frame_config = ttk.LabelFrame(parent, text="⚙ Configuración de la Viga", padding="10 10 10 10") # Ajustar padding
        frame_config.columnconfigure(1, weight=1) # Para que la barra de longitud se expanda

        # Longitud de la viga
        longitud_frame = ttk.Frame(frame_config)
        longitud_frame.grid(row=0, column=0, columnspan=4, padx=5, pady=2, sticky="ew") # Ocupar todo el ancho
        ttk.Label(longitud_frame, text="Longitud (m):").pack(side="left", padx=2, pady=2)
        ttk.Entry(longitud_frame, textvariable=self.longitud, width=8).pack(side="right", padx=2, pady=2)
        ttk.Scale(longitud_frame, variable=self.longitud, from_=5, to=50, orient="horizontal").pack(side="left", fill="x", expand=True, padx=2, pady=2)

        # Configuración de apoyos
        apoyos_frame = ttk.Frame(frame_config)
        apoyos_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=2, sticky="ew") # Ocupar todo el ancho
        ttk.Label(apoyos_frame, text="Apoyo A:").pack(side="left", padx=2, pady=2)
        ttk.Combobox(apoyos_frame, textvariable=self.tipo_apoyo_a, values=["Fijo", "Móvil"], width=8).pack(side="left", padx=2, pady=2)
        ttk.Label(apoyos_frame, text="Apoyo B:").pack(side="left", padx=2, pady=2)
        ttk.Combobox(apoyos_frame, textvariable=self.tipo_apoyo_b, values=["Fijo", "Móvil"], width=8).pack(side="left", padx=2, pady=2)
        ttk.Label(apoyos_frame, text="Apoyo C:").pack(side="left", padx=2, pady=2)
        ttk.Combobox(apoyos_frame, textvariable=self.tipo_apoyo_c, values=["Ninguno", "Fijo", "Móvil"], width=8).pack(side="left", padx=2, pady=2)
        ttk.Label(apoyos_frame, text="Posición C (m):").pack(side="left", padx=2, pady=2)
        ttk.Entry(apoyos_frame, textvariable=self.posicion_apoyo_c, width=8).pack(side="left", padx=2, pady=2)

        # Opción para 3D y par torsor
        extra_options_frame = ttk.Frame(frame_config)
        extra_options_frame.grid(row=2, column=0, columnspan=4, padx=5, pady=2, sticky="ew")
        ttk.Checkbutton(extra_options_frame, text="Modo 3D", variable=self.modo_3d).pack(side="left", padx=2, pady=2)
        ttk.Label(extra_options_frame, text="Par Torsor (N·m):").pack(side="left", padx=2, pady=2)
        ttk.Entry(extra_options_frame, textvariable=self.par_torsor, width=10).pack(side="left", padx=2, pady=2)

        # Altura de la viga
        altura_frame = ttk.Frame(frame_config)
        altura_frame.grid(row=3, column=0, columnspan=4, padx=5, pady=2, sticky="ew")
        ttk.Label(altura_frame, text="Altura inicial (m):").pack(side="left", padx=2, pady=2)
        ttk.Entry(altura_frame, textvariable=self.altura_inicial, width=10).pack(side="left", padx=2, pady=2)
        ttk.Label(altura_frame, text="Altura final (m):").pack(side="left", padx=2, pady=2)
        ttk.Entry(altura_frame, textvariable=self.altura_final, width=10).pack(side="left", padx=2, pady=2)

        return frame_config

    def crear_seccion_propiedades_seccion(self, parent):
        frame_seccion = ttk.LabelFrame(parent, text="Propiedades de la Sección Transversal", padding="10 10 10 10")
        frame_seccion.pack(fill="x", pady=5, padx=5) # Ajustar padding

        # Usar un grid más compacto para las dimensiones
        frame_seccion.columnconfigure(1, weight=1)
        frame_seccion.columnconfigure(3, weight=1)

        ttk.Label(frame_seccion, text="Ancho superior (cm):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_seccion, textvariable=self.ancho_superior, width=10).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_seccion, text="Altura superior (cm):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_seccion, textvariable=self.altura_superior, width=10).grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_seccion, text="Ancho alma (cm):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_seccion, textvariable=self.ancho_alma, width=10).grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_seccion, text="Altura alma (cm):").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_seccion, textvariable=self.altura_alma, width=10).grid(row=1, column=3, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_seccion, text="Ancho inferior (cm):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_seccion, textvariable=self.ancho_inferior, width=10).grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_seccion, text="Altura inferior (cm):").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_seccion, textvariable=self.altura_inferior, width=10).grid(row=2, column=3, padx=5, pady=2, sticky="ew")

        ttk.Button(frame_seccion, text="Calcular Propiedades", command=self.calcular_propiedades_seccion).grid(row=3, column=0, columnspan=4, pady=10)

    def crear_seccion_cargas_puntuales(self, parent):
        frame_puntuales = ttk.LabelFrame(parent, text="⬇️ Cargas Puntuales", padding="10 10 10 10") # Ajustar padding
        frame_puntuales.columnconfigure(1, weight=1)
        frame_puntuales.columnconfigure(3, weight=1)

        ttk.Label(frame_puntuales, text="Posición (m):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_puntuales, textvariable=self.posicion_carga, width=10).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_puntuales, text="Magnitud (N):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_puntuales, textvariable=self.magnitud_carga, width=10).grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        ttk.Button(frame_puntuales, text="➕ Agregar", command=self.agregar_carga_puntual).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(frame_puntuales, text="🗑️ Limpiar", command=self.limpiar_cargas_puntuales).grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")

        return frame_puntuales

    def crear_seccion_cargas_distribuidas(self, parent):
        frame_distribuidas = ttk.LabelFrame(parent, text="📅 Cargas Distribuidas", padding="10 10 10 10") # Ajustar padding
        frame_distribuidas.columnconfigure(1, weight=1)
        frame_distribuidas.columnconfigure(3, weight=1)

        ttk.Label(frame_distribuidas, text="Inicio (m):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_distribuidas, textvariable=self.inicio_dist, width=10).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_distribuidas, text="Fin (m):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_distribuidas, textvariable=self.fin_dist, width=10).grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_distribuidas, text="Magnitud (N/m):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(frame_distribuidas, textvariable=self.magnitud_dist, width=10).grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Button(frame_distribuidas, text="➕ Agregar", command=self.agregar_carga_distribuida).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(frame_distribuidas, text="🗑️ Limpiar", command=self.limpiar_cargas_distribuidas).grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky="ew")

        return frame_distribuidas

    def crear_seccion_botones_calculo(self, parent):
        frame_botones = ttk.Frame(parent, padding="5 5 5 5") # Ajustar padding

        # Los estilos de botones se configuran en apply_theme

        # Botones principales con iconos
        btn_calcular = ttk.Button(frame_botones, text="🧮 Calcular Reacciones", style="Action.TButton")
        btn_calcular.config(command=lambda b=btn_calcular: self.on_button_click(b, self.calcular_reacciones))
        btn_calcular.grid(row=0, column=0, padx=3, pady=3, sticky="ew") # Ajustar padding

        btn_centro_masa = ttk.Button(frame_botones, text="📍 Calcular Centro de Masa", style="Action.TButton")
        btn_centro_masa.config(command=lambda b=btn_centro_masa: self.on_button_click(b, self.calcular_centro_masa))
        btn_centro_masa.grid(row=0, column=1, padx=3, pady=3, sticky="ew") # Ajustar padding

        btn_diagramas = ttk.Button(frame_botones, text="📊 Mostrar Diagramas", style="Action.TButton")
        btn_diagramas.config(command=lambda b=btn_diagramas: self.on_button_click(b, self.mostrar_diagramas))
        btn_diagramas.grid(row=0, column=2, padx=3, pady=3, sticky="ew") # Ajustar padding

        par_frame = ttk.Frame(frame_botones)
        par_frame.grid(row=0, column=3, columnspan=2, padx=3, pady=3, sticky="ew") # Ajustar padding
        par_frame.columnconfigure(2, weight=1) # Para que la entrada de texto se expanda
        ttk.Label(par_frame, text="x (m):").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        ttk.Entry(par_frame, textvariable=self.posicion_torsor, width=6).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        btn_par_punto = ttk.Button(par_frame, text="🌀 Par en Punto", style="Action.TButton")
        btn_par_punto.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        btn_par_punto.config(command=lambda b=btn_par_punto: self.on_button_click(b, lambda: self.calcular_par_torsor_en_punto(self.posicion_torsor.get())))

        # Segunda fila de botones
        btn_limpiar = ttk.Button(frame_botones, text="🗑️ Limpiar Todo", style="Warning.TButton")
        btn_limpiar.config(command=lambda b=btn_limpiar: self.on_button_click(b, self.limpiar_todo))
        btn_limpiar.grid(row=1, column=0, padx=3, pady=3, sticky="ew") # Ajustar padding

        btn_ayuda = ttk.Button(frame_botones, text="❓ Ayuda", style="Action.TButton")
        btn_ayuda.config(command=lambda b=btn_ayuda: self.on_button_click(b, self.mostrar_ayuda))
        btn_ayuda.grid(row=1, column=1, padx=3, pady=3, sticky="ew") # Ajustar padding

        btn_ampliar = ttk.Button(frame_botones, text="🔍 Ampliar Gráfica", style="Action.TButton")
        btn_ampliar.config(command=lambda b=btn_ampliar: self.on_button_click(b, self.ampliar_grafica))
        btn_ampliar.grid(row=1, column=2, padx=3, pady=3, sticky="ew") # Ajustar padding

        btn_animar_3d = ttk.Button(frame_botones, text="🎞️ Animar 3D", style="Action.TButton")
        btn_animar_3d.config(command=lambda b=btn_animar_3d: self.on_button_click(b, self.animar_viga_3d))
        btn_animar_3d.grid(row=1, column=3, padx=3, pady=3, sticky="ew") # Ajustar padding

        btn_tema = ttk.Button(frame_botones, textvariable=self.texto_tema, style="Action.TButton")
        btn_tema.config(command=lambda b=btn_tema: self.on_button_click(b, self.toggle_dark_mode))
        btn_tema.grid(row=1, column=4, padx=3, pady=3, sticky="ew") # Ajustar padding
        self.boton_tema = btn_tema

        # Configurar el grid para que se expanda correctamente
        for i in range(5):
            frame_botones.columnconfigure(i, weight=1)

        return frame_botones

    def crear_seccion_axial_termica(self, parent):
        frame_axial_termica = ttk.LabelFrame(parent, text="📏 Deformación Axial y Térmica", padding="10 10 10 10")
        frame_axial_termica.pack(fill="both", expand=True, pady=5, padx=5) # Usar fill="both", expand=True

        # Configurar grid para dos columnas uniformes
        frame_axial_termica.columnconfigure(0, weight=1)
        frame_axial_termica.columnconfigure(1, weight=1)

        # Usar un sub-frame para las entradas para mejor organización
        input_frame = ttk.Frame(frame_axial_termica)
        input_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1) # Las entradas se expanden
        input_frame.columnconfigure(3, weight=1)

        # Módulo de Young (E)
        ttk.Label(input_frame, text="Módulo de Young (E en GPa):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(input_frame, textvariable=self.modulo_young, width=12).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        # Coeficiente de expansión térmica (alpha)
        ttk.Label(input_frame, text="Coef. Exp. Térmica (α en /°C):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(input_frame, textvariable=self.coef_expansion, width=12).grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        # Longitud inicial (L0)
        ttk.Label(input_frame, text="Longitud Inicial (L0 en m):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(input_frame, textvariable=self.longitud_inicial_def, width=12).grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        # Área transversal (A)
        ttk.Label(input_frame, text="Área Transversal (A en mm²):").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(input_frame, textvariable=self.area_transversal, width=12).grid(row=1, column=3, padx=5, pady=2, sticky="ew")

        # Fuerza de tensión (F)
        ttk.Label(input_frame, text="Fuerza de Tensión (F en kN):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(input_frame, textvariable=self.fuerza_tension, width=12).grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        # Cambio de temperatura (Delta T)
        ttk.Label(input_frame, text="Cambio de Temperatura (ΔT en °C):").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(input_frame, textvariable=self.cambio_temperatura, width=12).grid(row=2, column=3, padx=5, pady=2, sticky="ew")

        # Botones de acción
        button_frame = ttk.Frame(frame_axial_termica)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="Calcular Deformación", command=self.calcular_deformacion_axial_termica).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Limpiar Valores", command=self.limpiar_deformacion_axial_termica).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def calcular_deformacion_axial_termica(self):
        try:
            # Obtener valores de las variables y convertir a unidades base SI
            E_gpa = self.modulo_young.get()
            alpha = self.coef_expansion.get()
            L0_m = self.longitud_inicial_def.get()
            A_mm2 = self.area_transversal.get()
            F_kn = self.fuerza_tension.get()
            delta_T_c = self.cambio_temperatura.get()

            # Conversiones
            E = E_gpa * 1e9  # GPa a Pa (N/m²)
            A = A_mm2 * 1e-6  # mm² a m²
            F = F_kn * 1e3  # kN a N

            # Calcular deformación axial
            if A == 0 or E == 0:
                messagebox.showerror("Error de Cálculo", "El área transversal o el Módulo de Young no pueden ser cero.")
                return
            delta_axial = (F * L0_m) / (A * E)

            # Calcular deformación térmica
            delta_termica = alpha * L0_m * delta_T_c

            # Calcular deformación total
            delta_total = delta_axial + delta_termica

            # Calcular tensión
            sigma = F / A

            # Mostrar resultados
            self.log(f"\n{'='*50}\n", "title")
            self.log("📐 CÁLCULO DE DEFORMACIÓN AXIAL Y TÉRMICA:\n", "title")
            self.log(f"{'='*50}\n", "title")
            self.log(f"Parámetros:\n", "info")
            self.log(f"  E = {E_gpa:.2f} GPa\n", "data")
            self.log(f"  α = {alpha:.2e} /°C\n", "data")
            self.log(f"  L0 = {L0_m:.2f} m\n", "data")
            self.log(f"  A = {A_mm2:.2f} mm²\n", "data")
            self.log(f"  F = {F_kn:.2f} kN\n", "data")
            self.log(f"  ΔT = {delta_T_c:.2f} °C\n", "data")
            self.log("\nResultados:\n", "info")
            self.log(f"  Deformación Axial (δ_axial): {delta_axial:.6e} m\n", "data")
            self.log(f"  Deformación Térmica (δ_termica): {delta_termica:.6e} m\n", "data")
            self.log(f"  Deformación Total (δ_total): {delta_total:.6e} m\n", "success")
            self.log(f"  Tensión (σ): {sigma:.2f} Pa\n", "success")
            self.log(f"  δ_total + σ: {delta_total + sigma:.6e} (unidad combinada, no física)\n", "success")

            # Opcional: Graficar la deformación
            self.graficar_deformacion(L0_m, delta_axial, delta_termica, delta_total, sigma)

        except ValueError:
            messagebox.showerror("Error de Entrada", "Por favor, introduce valores numéricos válidos en todos los campos.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")

    def limpiar_deformacion_axial_termica(self):
        self.modulo_young.set(200.0)
        self.coef_expansion.set(12e-6)
        self.longitud_inicial_def.set(2.0)
        self.area_transversal.set(500.0)
        self.fuerza_tension.set(50.0)
        self.cambio_temperatura.set(30.0)
        self.log("Valores de deformación axial y térmica limpiados.\n", "warning")
        # Limpiar el gráfico también
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()


    def graficar_deformacion(self, L0, d_axial, d_termica, d_total, sigma):
        """Grafica la barra y su deformación."""
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 6))
        plt.style.use("seaborn-v0_8-whitegrid")

        # Dibujar la barra original
        ax.plot([0, L0], [0, 0], 'k-', linewidth=5, label='Longitud Inicial (L0)')

        # Ajustar el factor de escala para la visualización de la deformación
        # Esto es solo para que las deformaciones sean visibles en el gráfico.
        # Un factor de 1000000 convierte metros a micrómetros, haciendo la deformación más visible.
        escala_visual = 100000 # Escala para hacer visibles las deformaciones pequeñas

        # Dibujar la barra deformada axialmente
        ax.plot([0, L0 + d_axial * escala_visual], [0.1, 0.1], 'b--', linewidth=2, label=f'Deformación Axial (δ_axial)')
        ax.text(L0 + d_axial * escala_visual, 0.1, f'{d_axial*1e6:.2f} µm', color='blue', ha='left', va='center')

        # Dibujar la barra deformada térmicamente
        ax.plot([0, L0 + d_termica * escala_visual], [-0.1, -0.1], 'g-.', linewidth=2, label=f'Deformación Térmica (δ_termica)')
        ax.text(L0 + d_termica * escala_visual, -0.1, f'{d_termica*1e6:.2f} µm', color='green', ha='left', va='center')

        # Dibujar la barra con deformación total
        ax.plot([0, L0 + d_total * escala_visual], [0.2, 0.2], 'r-', linewidth=3, label=f'Deformación Total (δ_total)')
        ax.text(L0 + d_total * escala_visual, 0.2, f'{d_total*1e6:.2f} µm', color='red', ha='left', va='center')

        # Flecha de fuerza
        ax.arrow(L0 / 2, 0.5, 0, -0.2, head_width=0.02 * L0, head_length=0.1, fc='purple', ec='purple', width=0.005)
        ax.text(L0 / 2, 0.6, f'F={self.fuerza_tension.get():.1f} kN', ha='center', va='bottom', color='purple', fontsize=10, fontweight='bold')

        # Etiquetas de temperatura
        ax.text(L0 * 0.75, 0.4, f'ΔT={self.cambio_temperatura.get():.1f}°C', ha='center', va='bottom', color='orange', fontsize=10, fontweight='bold')
        ax.arrow(L0 * 0.75 - 0.1*L0, 0.4, 0.2*L0, 0, head_width=0.03, head_length=0.05, fc='orange', ec='orange', width=0.002)


        ax.set_xlim(-0.1 * L0, L0 + d_total * escala_visual + 0.1 * L0)
        ax.set_ylim(-0.3, 0.7) # Ajustar límites Y para mejor visualización
        ax.set_xlabel('Longitud (m)')
        ax.set_ylabel('Visualización (Escalada)')
        ax.set_title('Deformación Axial y Térmica de una Barra')
        ax.legend(loc='upper right')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.axvline(L0, color='gray', linestyle=':', label='Longitud Original')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

    def mostrar_mensaje_inicial(self):
        mensaje = "Bienvenido al Simulador de Viga Mecánica. Use los controles para configurar la viga y las cargas."
        self.log(mensaje, "info")

    def agregar_carga_puntual(self):
        try:
            pos = self.posicion_carga.get()
            mag = self.magnitud_carga.get()

            if not (0 <= pos <= self.longitud.get()):
                messagebox.showerror("Error", f"La posición debe estar entre 0 y {self.longitud.get()} m")
                return

            if mag == 0:
                messagebox.showwarning("Advertencia", "La magnitud no puede ser cero")
                return

            self.cargas_puntuales.append((pos, mag))
            self.log(f"✅ Carga puntual: {mag}N en {pos}m\n", "success")
            self.dibujar_viga_actual()

        except Exception as e:
            messagebox.showerror("Error", f"Valores inválidos: {e}")

    def agregar_carga_distribuida(self):
        try:
            inicio = self.inicio_dist.get()
            fin = self.fin_dist.get()
            mag = self.magnitud_dist.get()

            if not (0 <= inicio < fin <= self.longitud.get()):
                messagebox.showerror("Error", "Verifica que 0 ≤ inicio < fin ≤ longitud")
                return

            if mag == 0:
                messagebox.showwarning("Advertencia", "La magnitud no puede ser cero")
                return

            self.cargas_distribuidas.append((inicio, fin, mag))
            self.log(
                f"✅ Carga distribuida: {mag}N/m desde {inicio}m hasta {fin}m\n",
                "success",
            )
            self.dibujar_viga_actual()

        except Exception as e:
            messagebox.showerror("Error", f"Valores inválidos: {e}")

    def calcular_reacciones(self):
        try:
            if not self.cargas_puntuales and not self.cargas_distribuidas:
                messagebox.showwarning("Advertencia", "Agrega al menos una carga")
                return

            L = self.longitud.get()
            h_inicial = self.altura_inicial.get()
            h_final = self.altura_final.get()
            # Para cargas verticales no es necesario proyectar con el ángulo de
            # la viga. Se conserva para posibles extensiones, pero las
            # sumatorias solo consideran el componente vertical.
            angulo = np.arctan((h_final - h_inicial) / L)

            # Calcular fuerzas totales y momentos
            suma_fuerzas_x = 0
            suma_fuerzas_y = 0
            suma_momentos_a = 0

            # Cargas puntuales
            for pos, mag in self.cargas_puntuales:
                # Las cargas puntuales se consideran verticales
                suma_fuerzas_y += mag
                suma_momentos_a += mag * pos

            # Cargas distribuidas
            for inicio, fin, mag in self.cargas_distribuidas:
                longitud_carga = fin - inicio
                fuerza_total = mag * longitud_carga
                centroide = inicio + longitud_carga/2

                suma_fuerzas_y += fuerza_total
                suma_momentos_a += fuerza_total * centroide
                self.log(
                    f"🔹 Carga distribuida {inicio}-{fin} m -> F={fuerza_total:.2f} N\n",
                    "data",
                )

            # Incluir el par torsor en los cálculos
            par_torsor = self.par_torsor.get()

            # Modificar las ecuaciones de equilibrio para incluir el par torsor
            if self.tipo_apoyo_c.get() == "Ninguno":
                RB = (suma_momentos_a + par_torsor) / L
                RA = suma_fuerzas_y - RB
                RC = 0
                procedimiento = [
                    "Viga con dos apoyos:",
                    f"ΣFy = {suma_fuerzas_y:.2f} N",
                    f"ΣMA = {suma_momentos_a:.2f} N·m",
                    f"RB = (ΣMA + T)/L = ({suma_momentos_a:.2f} + {par_torsor:.2f})/{L:.2f}",
                    f"RB = {RB:.2f} N",
                    f"RA = ΣFy - RB = {suma_fuerzas_y:.2f} - {RB:.2f} = {RA:.2f} N"
                ]
            else:
                c = self.posicion_apoyo_c.get()
                RB = ((suma_momentos_a + par_torsor) - c * suma_fuerzas_y / 2) / (L - c)
                RA = RC = (suma_fuerzas_y - RB) / 2
                procedimiento = [
                    "Viga con tres apoyos:",
                    f"ΣFy = {suma_fuerzas_y:.2f} N",
                    f"ΣMA = {suma_momentos_a:.2f} N·m",
                    f"RB = ((ΣMA + T) - c*ΣFy/2)/(L - c) = ({suma_momentos_a:.2f} + {par_torsor:.2f} - {c:.2f}*{suma_fuerzas_y:.2f}/2)/({L:.2f} - {c:.2f})",
                    f"RB = {RB:.2f} N",
                    f"RA = RC = (ΣFy - RB)/2 = ({suma_fuerzas_y:.2f} - {RB:.2f})/2 = {RA:.2f} N"
                ]

            # Mostrar procedimiento y resultados
            self.log(f"\n{'='*50}\n", "title")
            self.log("⚖️ CÁLCULO DE REACCIONES:\n", "title")
            self.log(f"{'='*50}\n", "title")
            for linea in procedimiento:
                self.log(linea + "\n", "data")
            self.log(f"🔺 Reacción en A (RA): {RA:.2f} N\n", "data")
            self.log(f"🔺 Reacción en B (RB): {RB:.2f} N\n", "data")
            if self.tipo_apoyo_c.get() != "Ninguno":
                self.log(f"🔺 Reacción en C (RC): {RC:.2f} N\n", "data")
            self.log(f"📊 Suma de fuerzas en Y: {suma_fuerzas_y:.2f} N\n", "data")
            self.log(f"📊 Suma de fuerzas en X: {suma_fuerzas_x:.2f} N\n", "data")
            self.log(
                f"🔄 Verificación equilibrio: {abs(RA + RB + RC - suma_fuerzas_y):.6f} N\n",
                "data",
            )
            self.log(f"🔄 Par Torsor: {par_torsor:.2f} N·m\n", "data")
            self.log(f"📐 Ángulo de inclinación: {np.degrees(angulo):.2f}°\n", "data")

            if abs(RA + RB + RC - suma_fuerzas_y) < 1e-10:
                self.log("✅ Sistema en equilibrio\n", "success")
            else:
                self.log("❌ Error en equilibrio\n", "error")

            # Descomposición de reacciones en X e Y
            self.reaccion_a = RA
            self.reaccion_b = RB
            self.reaccion_c = RC
            self.reaccion_a_x = RA * np.tan(angulo) if self.tipo_apoyo_a.get() == "Fijo" else 0.0
            self.reaccion_b_x = RB * np.tan(angulo) if self.tipo_apoyo_b.get() == "Fijo" else 0.0
            self.reaccion_c_x = RC * np.tan(angulo) if self.tipo_apoyo_c.get() == "Fijo" else 0.0
            self.reaccion_a_y = RA
            self.reaccion_b_y = RB
            self.reaccion_c_y = RC
            self.log(f"RxA={self.reaccion_a_x:.2f} N, RyA={self.reaccion_a_y:.2f} N\n", "data")
            self.log(f"RxB={self.reaccion_b_x:.2f} N, RyB={self.reaccion_b_y:.2f} N\n", "data")
            if self.tipo_apoyo_c.get() != "Ninguno":
                self.log(f"RxC={self.reaccion_c_x:.2f} N, RyC={self.reaccion_c_y:.2f} N\n", "data")

            self.dibujar_viga_con_reacciones(RA, RB, RC)

        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculos: {e}")

    def calcular_centro_masa(self):
        try:
            if not self.cargas_puntuales and not self.cargas_distribuidas:
                messagebox.showwarning("Advertencia", "No hay cargas para calcular")
                return

            suma_momentos = 0
            suma_cargas = 0

            # Cargas puntuales
            for pos, mag in self.cargas_puntuales:
                suma_momentos += pos * mag
                suma_cargas += mag

            # Cargas distribuidas
            for inicio, fin, mag in self.cargas_distribuidas:
                longitud_carga = fin - inicio
                fuerza_total = mag * longitud_carga
                centroide = inicio + longitud_carga/2

                suma_momentos += centroide * fuerza_total
                suma_cargas += fuerza_total

            x_cm = suma_momentos / suma_cargas

            self.log("\n📍 CÁLCULO DEL CENTRO DE MASA:\n", "title")
            self.log(f"Σ(x·F) = {suma_momentos:.2f} N·m\n", "data")
            self.log(f"ΣF = {suma_cargas:.2f} N\n", "data")
            self.log(f"x_cm = Σ(x·F) / ΣF = {x_cm:.2f} m\n", "data")

            # Actualizar la visualización
            if self.modo_3d.get():
                self.dibujar_viga_3d(x_cm)
            else:
                self.dibujar_viga_actual(x_cm)

        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculo: {e}")

    def calcular_centro_masa_3d(self, puntos):
        """Calcula el centro de masa de una colección de puntos (x, y, z, m)."""
        if not puntos:
            messagebox.showwarning("Advertencia", "No hay puntos 3D definidos")
            return None
        M = sum(m for _, _, _, m in puntos)
        x_cm = sum(x * m for x, _, _, m in puntos) / M
        y_cm = sum(y * m for _, y, _, m in puntos) / M
        z_cm = sum(z * m for _, _, z, m in puntos) / M
        self.log(f"📍 Centro de masa 3D: ({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})\n", "data")
        return x_cm, y_cm, z_cm

    def calcular_fuerza_desde_torsor(self, torsor, distancia):
        """Calcula la fuerza F a partir del par torsor y la distancia."""
        if distancia == 0:
            messagebox.showerror("Error", "La distancia no puede ser cero")
            return None
        F = torsor / distancia
        self.log(f"💪 Fuerza calculada: F = {F:.2f} N\n", "data")
        return F

    def mostrar_diagramas(self):
        try:
            if not self.cargas_puntuales and not self.cargas_distribuidas:
                messagebox.showwarning("Advertencia", "Agrega cargas primero")
                return

            # Primero calcular reacciones usando el mismo algoritmo que
            # la función calcular_reacciones para mantener consistencia
            L = self.longitud.get()
            h_inicial = self.altura_inicial.get()
            h_final = self.altura_final.get()
            angulo = np.arctan((h_final - h_inicial) / L)

            suma_fuerzas_x = 0
            suma_fuerzas_y = 0
            suma_momentos_a = 0

            for pos, mag in self.cargas_puntuales:
                # Considerar cargas puntuales verticales
                suma_fuerzas_y += mag
                suma_momentos_a += mag * pos

            for inicio, fin, mag in self.cargas_distribuidas:
                longitud_carga = fin - inicio
                fuerza_total = mag * longitud_carga
                centroide = inicio + longitud_carga/2

                # Las cargas distribuidas son verticales
                suma_fuerzas_y += fuerza_total
                suma_momentos_a += fuerza_total * centroide

            par_torsor = self.par_torsor.get()
            c = self.posicion_apoyo_c.get()

            if self.tipo_apoyo_c.get() == "Ninguno":
                RB = (suma_momentos_a + par_torsor) / L
                RA = suma_fuerzas_y - RB
                RC = 0
            else:
                RB = ((suma_momentos_a + par_torsor) - c * suma_fuerzas_y / 2) / (L - c)
                RA = RC = (suma_fuerzas_y - RB) / 2

            # Crear puntos para diagramas
            x = np.linspace(0, L, 1000)
            cortante = np.zeros_like(x)
            momento = np.zeros_like(x)

            # Calcular cortante y momento
            for i, xi in enumerate(x):
                V = 0
                M = 0

                # Reacciones
                V += RA
                M += RA * xi

                if self.tipo_apoyo_c.get() != "Ninguno" and xi >= c:
                    V += RC
                    M += RC * (xi - c)

                if xi >= L:
                    V += RB
                    M += RB * (xi - L)

                # Contribución de cargas puntuales
                for pos, mag in self.cargas_puntuales:
                    if xi > pos:
                        V -= mag
                        M -= mag * (xi - pos)

                # Contribución de cargas distribuidas
                for inicio, fin, mag in self.cargas_distribuidas:
                    if xi > inicio:
                        if xi <= fin:
                            # Parte de la carga distribuida
                            long_actual = xi - inicio
                            V -= mag * long_actual
                            M -= mag * long_actual * long_actual / 2
                        else:
                            # Toda la carga distribuida
                            long_total = fin - inicio
                            V -= mag * long_total
                            M -= mag * long_total * (xi - (inicio + long_total/2))

                cortante[i] = V
                momento[i] = M

            self.dibujar_diagramas(x, cortante, momento, RA, RB, RC)

        except Exception as e:
            messagebox.showerror("Error", f"Error en diagramas: {e}")

    def calcular_par_torsor_en_punto(self, x):
        """Calcula el par torsor interno en la posición x."""
        if not self.cargas_puntuales and not self.cargas_distribuidas:
            messagebox.showwarning("Advertencia", "Agrega cargas primero")
            return None
        if self.reaccion_a == 0 and self.reaccion_b == 0 and self.reaccion_c == 0:
            messagebox.showwarning("Advertencia", "Calcule primero las reacciones")
            return None

        L = self.longitud.get()
        RA = self.reaccion_a
        RB = self.reaccion_b
        RC = self.reaccion_c
        c = self.posicion_apoyo_c.get()
        T = self.par_torsor.get()
        momento = T

        if x >= 0:
            momento += RA * x
        if self.tipo_apoyo_c.get() != "Ninguno" and x >= c:
            momento += RC * (x - c)
        if x >= L:
            momento += RB * (x - L)

        for pos, mag in self.cargas_puntuales:
            if x > pos:
                momento -= mag * (x - pos)

        for inicio, fin, mag in self.cargas_distribuidas:
            if x > inicio:
                if x <= fin:
                    long_actual = x - inicio
                    momento -= mag * long_actual * long_actual / 2
                else:
                    long_total = fin - inicio
                    momento -= mag * long_total * (x - (inicio + long_total / 2))

        self.log(f"🌀 Par torsor en x={x:.2f} m: {momento:.2f} N·m\n", "data")
        return momento

    def dibujar_viga_actual(self, x_cm=None):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 5), dpi=100) # Ajustar tamaño de figura
        L = self.longitud.get()
        h_inicial = self.altura_inicial.get()
        h_final = self.altura_final.get()

        # Configuración del estilo
        plt.style.use("seaborn-v0_8-darkgrid")  # Estilo más atractivo para las gráficas
        ax.set_facecolor('#f0f0f0')
        fig.patch.set_facecolor('#ffffff')

        # Dibujar viga inclinada
        ax.plot([0, L], [h_inicial, h_final], 'k-', linewidth=4, label='Viga', zorder=5)

        # Dibujar apoyos
        apoyo_a = '^' if self.tipo_apoyo_a.get() == 'Fijo' else 'o'
        apoyo_b = '^' if self.tipo_apoyo_b.get() == 'Fijo' else 'o'
        ax.plot(0, h_inicial, apoyo_a, markersize=15, color='#1f77b4', label='Apoyo A', zorder=10)
        ax.plot(L, h_final, apoyo_b, markersize=15, color='#1f77b4', label='Apoyo B', zorder=10)

        if self.tipo_apoyo_c.get() != "Ninguno":
            c = self.posicion_apoyo_c.get()
            h_c = h_inicial + (h_final - h_inicial) * c / L
            apoyo_c = '^' if self.tipo_apoyo_c.get() == 'Fijo' else 'o'
            ax.plot(c, h_c, apoyo_c, markersize=15, color='#2ca02c', label='Apoyo C', zorder=10)
            ax.text(c, h_c-0.15, f'C: {c}m', ha='center', va='top', fontsize=10, color='#2ca02c', fontweight='bold')
        # Dibujar cargas puntuales con tamaño de texto proporcional
        max_mag = max([abs(m) for _, m in self.cargas_puntuales] + [1])
        for pos, mag in self.cargas_puntuales:
            h = h_inicial + (h_final - h_inicial) * pos / L
            size = 8 + 4 * abs(mag) / max_mag
            ax.arrow(pos, h + 0.5, 0, -0.4, head_width=L * 0.015, head_length=0.05, fc='#d62728', ec='#d62728', width=0.002, zorder=15)
            ax.text(pos, h + 0.6, f'{mag}N', ha='center', va='bottom', fontsize=size, color='#d62728', fontweight='bold')

        # Dibujar cargas distribuidas segmentadas
        for inicio, fin, mag in self.cargas_distribuidas:
            h_mid = h_inicial + (h_final - h_inicial) * ((inicio + fin) / 2) / L
            F_eq = mag * (fin - inicio)
            n_arrows = max(2, int((fin - inicio) / (L * 0.1)))
            for i in range(n_arrows):
                x = inicio + (fin - inicio) * (i + 0.5) / n_arrows
                h = h_inicial + (h_final - h_inicial) * x / L
                ax.arrow(x, h + 0.7, 0, -0.3, head_width=L * 0.01, head_length=0.03, fc='#ff7f0e', ec='#ff7f0e', width=0.0015, zorder=14)
            ax.arrow((inicio + fin) / 2, h_mid + 0.8, 0, -0.6, head_width=L * 0.015, head_length=0.05, fc='#ff7f0e', ec='#ff7f0e', width=0.002, zorder=15)
            ax.text((inicio + fin) / 2, h_mid + 0.85, f'{F_eq:.1f}N', ha='center', va='bottom', fontsize=10, color='#ff7f0e', fontweight='bold')
        # Dibujar centro de masa si está disponible
        if x_cm is not None:
            h_cm = h_inicial + (h_final - h_inicial) * x_cm / L
            ax.plot(x_cm, h_cm, 'go', markersize=12, label='Centro de Masa', zorder=20)
            ax.text(x_cm, h_cm-0.15, f'CM: {x_cm:.2f}m', ha='center', va='top', fontsize=10, color='green', fontweight='bold')

        ax.set_xlim(-L*0.1, L*1.1)
        ax.set_ylim(min(h_inicial, h_final)-1, max(h_inicial, h_final)+1)
        ax.set_xlabel('Posición (m)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Altura (m)', fontsize=12, fontweight='bold')
        ax.set_title('Configuración de la Viga', fontsize=16, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=10, frameon=True, facecolor='white', edgecolor='gray')


        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

    def animar_viga_3d(self):
        """Muestra la viga en 3D con rotación automática."""
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig = plt.figure(figsize=(10, 6)) # Ajustar tamaño de figura
        ax = fig.add_subplot(111, projection="3d")
        L = self.longitud.get()

        ax.plot([0, L], [0, 0], [0, 0], "k-", linewidth=6, label="Viga")
        ax.scatter(0, 0, 0, marker="^", s=100, color="blue", label="Apoyo A")
        ax.scatter(
            L,
            0,
            0,
            marker="o" if self.tipo_apoyo_b.get() == "Móvil" else "^",
            s=100,
            color="blue",
            label="Apoyo B",
        )

        if self.tipo_apoyo_c.get() != "Ninguno":
            c = self.posicion_apoyo_c.get()
            apoyo_c = "^" if self.tipo_apoyo_c.get() == "Fijo" else "o"
            ax.scatter(c, 0, 0, color="green", s=100, marker=apoyo_c, label="Apoyo C")

        for pos, mag in self.cargas_puntuales:
            ax.quiver(pos, 0, 0.5, 0, 0, -0.4, color="red", arrow_length_ratio=0.3)

        for inicio, fin, mag in self.cargas_distribuidas:
            F_eq = mag * (fin - inicio)
            ax.quiver((inicio+fin)/2, 0, 0.8, 0, 0, -0.6, color="orange", arrow_length_ratio=0.3)
            ax.text((inicio+fin)/2, 0, 0.85, f"{F_eq:.1f}N", ha="center", va="bottom", fontsize=8, color="orange")

        ax.set_xlim(-L * 0.15, L * 1.15)
        ax.set_ylim(-0.8, 0.8)
        ax.set_zlim(-0.8, 1.3)
        ax.set_xlabel("Posición (m)", fontsize=12)
        ax.set_ylabel("Ancho (m)", fontsize=12)
        ax.set_zlabel("Altura (m)", fontsize=12)
        ax.set_title("Animación 3D de la Viga", fontsize=14)

        def update(angle):
            ax.view_init(30, angle)
            return ax,

        self.animacion_3d = FuncAnimation(
            fig, update, frames=np.linspace(0, 360, 120), interval=50
        )

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

    def dibujar_viga_3d(self, x_cm=None):
        fig = plt.figure(figsize=(10, 6)) # Ajustar tamaño de figura
        ax = fig.add_subplot(111, projection='3d')
        L = self.longitud.get()

        # Dibujar viga
        ax.plot([0, L], [0, 0], [0, 0], 'k-', linewidth=6, label='Viga')

        # Dibujar apoyos
        ax.scatter(0, 0, 0, marker='^', s=100, color='blue', label='Apoyo A')
        ax.scatter(L, 0, 0, marker='o' if self.tipo_apoyo_b.get() == 'Móvil' else '^', s=100, color='blue', label='Apoyo B')

        if self.tipo_apoyo_c.get() != "Ninguno":
            c = self.posicion_apoyo_c.get()
            apoyo_c = '^' if self.tipo_apoyo_c.get() == 'Fijo' else 'o'
            ax.scatter(c, 0, 0, color='green', s=100, marker=apoyo_c, label='Apoyo C')
            ax.text(c, 0, 0.1, f'C: {c}m', ha='center', va='bottom', fontsize=10, color='green')

        # Dibujar cargas puntuales
        for pos, mag in self.cargas_puntuales:
            ax.quiver(pos, 0, 0.5, 0, 0, -0.4, color='red', arrow_length_ratio=0.3)
            ax.text(pos, 0, 0.6, f'{mag}N', ha='center', va='bottom', fontsize=8, color='red')

        # Dibujar cargas distribuidas como carga puntual equivalente
        for inicio, fin, mag in self.cargas_distribuidas:
            F_eq = mag * (fin - inicio)
            ax.quiver((inicio+fin)/2, 0, 0.8, 0, 0, -0.6, color='orange', arrow_length_ratio=0.3)
            ax.text((inicio+fin)/2, 0, 0.85, f'{F_eq:.1f}N', ha='center', va='bottom', fontsize=8, color='orange')

        # Dibujar centro de masa si está disponible
        if x_cm is not None:
            ax.scatter(x_cm, 0, 0, color='green', s=100, marker='o', label='Centro de Masa')
            ax.text(x_cm, 0, 0.1, f'CM: {x_cm:.2f}m', ha='center', va='bottom', fontsize=10, color='green')

        ax.set_xlim(-L*0.15, L*1.15)
        ax.set_ylim(-0.8, 0.8)
        ax.set_zlim(-0.8, 1.3)
        ax.set_xlabel('Posición (m)', fontsize=12)
        ax.set_ylabel('Ancho (m)', fontsize=12)
        ax.set_zlabel('Altura (m)', fontsize=12)
        ax.set_title('Configuración de la Viga en 3D', fontsize=14)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

    def dibujar_viga_con_reacciones(self, RA, RB, RC=0):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 5)) # Ajustar tamaño de figura
        plt.style.use("seaborn-v0_8-whitegrid")
        L = self.longitud.get()

        # Dibujar viga
        ax.plot([0, L], [0, 0], 'k-', linewidth=4)

        # Dibujar apoyos y reacciones
        apoyo_a = '^' if self.tipo_apoyo_a.get() == 'Fijo' else 'o'
        apoyo_b = '^' if self.tipo_apoyo_b.get() == 'Fijo' else 'o'
        ax.plot(0, 0, apoyo_a, markersize=12, color='blue')
        ax.plot(L, 0, apoyo_b, markersize=12, color='blue')

        ax.arrow(0, -0.3, 0, 0.25, head_width=L*0.015, head_length=0.03, fc='blue', ec='blue', width=0.002)
        ax.text(0, -0.35, f'RA={RA:.2f}N', ha='center', va='top', fontsize=9, color='blue', weight='bold')

        ax.arrow(L, -0.3, 0, 0.25, head_width=L*0.015, head_length=0.03, fc='blue', ec='blue', width=0.002)
        ax.text(L, -0.35, f'RB={RB:.2f}N', ha='center', va='top', fontsize=9, color='blue', weight='bold')

        if self.tipo_apoyo_c.get() != "Ninguno":
            c = self.posicion_apoyo_c.get()
            apoyo_c = '^' if self.tipo_apoyo_c.get() == 'Fijo' else 'o'
            ax.plot(c, 0, apoyo_c, markersize=12, color='green')
            ax.arrow(c, -0.3, 0, 0.25, head_width=L*0.015, head_length=0.03, fc='green', ec='green', width=0.002)
            ax.text(c, -0.35, f'RC={RC:.2f}N', ha='center', va='top', fontsize=9, color='green', weight='bold')

        # Dibujar cargas

        max_mag = max([abs(m) for _, m in self.cargas_puntuales] + [1])
        for pos, mag in self.cargas_puntuales:
            size = 6 + 4 * abs(mag) / max_mag
            ax.arrow(pos, 0.5, 0, -0.4, head_width=L*0.015, head_length=0.05, fc='red', ec='red', width=0.002)
            ax.text(pos, 0.6, f'{mag}N', ha='center', va='bottom', fontsize=size, color='red')

        for inicio, fin, mag in self.cargas_distribuidas:
            F_eq = mag * (fin - inicio)
            n_arrows = max(2, int((fin - inicio) / (L * 0.1)))
            for i in range(n_arrows):
                x = inicio + (fin - inicio) * (i + 0.5) / n_arrows
                ax.arrow(x, 0.7, 0, -0.3, head_width=L*0.01, head_length=0.03, fc='orange', ec='orange', width=0.0015)
            ax.arrow((inicio+fin)/2, 0.75, 0, -0.5, head_width=L*0.015, head_length=0.03, fc='red', ec='red', width=0.002)
            ax.text((inicio+fin)/2, 0.8, f'{F_eq:.1f}N', ha='center', va='bottom', fontsize=8, color='red')
        par_torsor = self.par_torsor.get()
        if par_torsor != 0:
            # Dibujar una flecha circular para representar el par torsor
            center = L / 2
            radius = 0.2
            angle = np.linspace(0, 2*np.pi, 100)
            x = center + radius * np.cos(angle)
            y = radius * np.sin(angle)
            color = 'green' if par_torsor > 0 else 'purple'
            ax.plot(x, y, color=color)
            ax.arrow(center + radius, 0, 0.05, 0.05, head_width=0.05, head_length=0.05, fc=color, ec=color)
            ax.text(center, 0.3, f'T={par_torsor:.2f}N·m', ha='center', va='bottom', fontsize=9, color=color)
        ax.set_xlabel('Posición (m)', fontsize=10)
        ax.set_title('Viga con Reacciones Calculadas', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.margins(x=0.05, y=0.3)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

    def dibujar_diagramas(self, x, cortante, momento, RA, RB, RC):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(
            4, 1, figsize=(10, 18), constrained_layout=True # Ajustar tamaño de figura
        )
        plt.style.use("seaborn-v0_8-whitegrid")

        L = self.longitud.get()

        # Diagrama de la viga
        ax1.plot([0, L], [0, 0], 'k-', linewidth=4)
        apoyo_a = '^' if self.tipo_apoyo_a.get() == 'Fijo' else 'o'
        apoyo_b = '^' if self.tipo_apoyo_b.get() == 'Fijo' else 'o'
        ax1.plot(0, 0, apoyo_a, markersize=12, color='blue')
        ax1.plot(L, 0, apoyo_b, markersize=12, color='blue')

        ax1.arrow(0, -0.2, 0, 0.15, head_width=L*0.015, head_length=0.02, fc='blue', ec='blue', width=0.002)
        ax1.text(0, -0.25, f'RA={RA:.2f}N', ha='center', va='top', fontsize=8, color='blue')
        ax1.arrow(L, -0.2, 0, 0.15, head_width=L*0.015, head_length=0.02, fc='blue', ec='blue', width=0.002)
        ax1.text(L, -0.25, f'RB={RB:.2f}N', ha='center', va='top', fontsize=8, color='blue')

        if self.tipo_apoyo_c.get() != "Ninguno":
            apoyo_c = '^' if self.tipo_apoyo_c.get() == 'Fijo' else 'o'
            pos_c = self.posicion_apoyo_c.get()
            ax1.plot(pos_c, 0, apoyo_c, markersize=12, color='green')
            ax1.text(pos_c, -0.25, f'RC={RC:.2f}N', ha='center', va='top', fontsize=8, color='green')

        for pos, mag in self.cargas_puntuales:
            ax1.arrow(pos, 0.3, 0, -0.25, head_width=L*0.015, head_length=0.03, fc='red', ec='red', width=0.002)
            ax1.text(pos, 0.35, f'{mag}N', ha='center', va='bottom', fontsize=7, color='red')

        for inicio, fin, mag in self.cargas_distribuidas:
            F_eq = mag * (fin - inicio)
            n_arrows = max(2, int((fin - inicio) / (L * 0.1)))
            for i in range(n_arrows):
                x = inicio + (fin - inicio) * (i + 0.5) / n_arrows
                ax1.arrow(x, 0.55, 0, -0.25, head_width=L*0.01, head_length=0.03, fc='orange', ec='orange', width=0.0015)
            ax1.arrow((inicio+fin)/2, 0.6, 0, -0.4, head_width=L*0.015, head_length=0.03, fc='red', ec='red', width=0.002)
            ax1.text((inicio+fin)/2, 0.65, f'{F_eq:.1f}N', ha='center', va='bottom', fontsize=7, color='red')

        ax1.set_xlim(-L*0.1, L*1.1)
        ax1.set_ylim(-0.6, 0.7)
        ax1.margins(x=0.05, y=0.2)
        ax1.set_title('Configuración de Cargas y Reacciones', fontsize=12)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_xlabel('Posición (m)', fontsize=10)
        ax1.set_ylabel('Altura (m)', fontsize=10)

        # Diagrama de cortante
        ax2.plot(x, cortante, 'b-', linewidth=2)
        ax2.fill_between(x, cortante, alpha=0.3, color='blue')
        ax2.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        ax2.set_ylabel('Cortante (N)', fontsize=10)
        ax2.set_title('Diagrama de Fuerza Cortante', fontsize=12)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.set_xlim(-L*0.1, L*1.1)
        ax2.margins(x=0.05)

        for pos, _ in self.cargas_puntuales:
            ax2.plot(pos, 0, 'ko', markersize=4)
            ax3.plot(pos, 0, 'ko', markersize=4)
        for inicio, fin, _ in self.cargas_distribuidas:
            ax2.plot([inicio, fin], [0, 0], 'ks', markersize=3)
            ax3.plot([inicio, fin], [0, 0], 'ks', markersize=3)
        # Añadir valores máximos y mínimos al diagrama de cortante
        cortante_max = np.max(cortante)
        cortante_min = np.min(cortante)
        ax2.text(L*1.05, cortante_max, f'Max: {cortante_max:.2f}N', va='bottom', ha='left', fontsize=8)
        ax2.text(L*1.05, cortante_min, f'Min: {cortante_min:.2f}N', va='top', ha='left', fontsize=8)

        # Diagrama de momento
        ax3.plot(x, momento, 'r-', linewidth=2)
        ax3.fill_between(x, momento, alpha=0.3, color='red')
        ax3.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        ax3.set_xlabel('Posición (m)', fontsize=10)
        ax3.set_ylabel('Momento (N·m)', fontsize=10)
        ax3.set_title('Diagrama de Momento Flector', fontsize=12)
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.set_xlim(-L*0.1, L*1.1)
        ax3.margins(x=0.05)

        # Añadir valores máximos y mínimos al diagrama de momento
        momento_max = np.max(momento)
        momento_min = np.min(momento)
        ax3.text(L*1.05, momento_max, f'Max: {momento_max:.2f}N·m', va='bottom', ha='left', fontsize=8)
        ax3.text(L*1.05, momento_min, f'Min: {momento_min:.2f}N·m', va='top', ha='left', fontsize=8)

        # Diagrama de torsión
        par_torsor = self.par_torsor.get()
        torsion = np.full_like(x, par_torsor)
        ax4.plot(x, torsion, 'g-', linewidth=2)
        ax4.fill_between(x, torsion, alpha=0.3, color='green')
        ax4.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        ax4.set_xlabel('Posición (m)', fontsize=10)
        ax4.set_ylabel('Torsión (N·m)', fontsize=10)
        ax4.set_title('Diagrama de Torsión', fontsize=12)
        ax4.grid(True, alpha=0.3, linestyle='--')
        ax4.set_xlim(-L*0.1, L*1.1)
        ax4.margins(x=0.05)

        # Añadir valor del par torsor al diagrama de torsión
        ax4.text(L*1.05, par_torsor, f'T: {par_torsor:.2f}N·m', va='center', ha='left', fontsize=8)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

        # Mostrar valores máximos en el área de resultados
        self.log("\n📈 VALORES MÁXIMOS:\n", "title")
        self.log(f"Cortante máximo: +{cortante_max:.2f} N\n", "data")
        self.log(f"Cortante mínimo: {cortante_min:.2f} N\n", "data")
        self.log(f"Momento máximo: +{momento_max:.2f} N·m\n", "data")
        self.log(f"Momento mínimo: {momento_min:.2f} N·m\n", "data")
        self.log(f"Par Torsor: {par_torsor:.2f} N·m\n", "data")

    def limpiar_cargas_puntuales(self):
        self.cargas_puntuales.clear()
        self.log("🗑️ Cargas puntuales eliminadas\n", "warning")
        self.dibujar_viga_actual()

    def limpiar_cargas_distribuidas(self):
        self.cargas_distribuidas.clear()
        self.log("🗑️ Cargas distribuidas eliminadas\n", "warning")
        self.dibujar_viga_actual()

    def limpiar_resultados(self):
        """Borra el contenido de la casilla de resultados."""
        self.texto_resultado.delete(1.0, tk.END)

    def limpiar_todo(self):
        # Limpiar listas de cargas
        self.cargas_puntuales.clear()
        self.cargas_distribuidas.clear()

        # Restablecer variables a sus valores iniciales
        self.longitud.set(10.0)
        self.tipo_apoyo_a.set("Fijo")
        self.tipo_apoyo_b.set("Móvil")
        self.tipo_apoyo_c.set("Ninguno")
        self.posicion_apoyo_c.set(5.0)
        self.par_torsor.set(0.0)
        self.posicion_carga.set(0.0)
        self.magnitud_carga.set(10.0)
        self.inicio_dist.set(0.0)
        self.fin_dist.set(5.0)
        self.magnitud_dist.set(5.0)
        self.modo_3d.set(False)
        self.altura_inicial.set(0.0)
        self.altura_final.set(0.0)

        # Reiniciar reacciones y puntos de masa 3D
        self.reaccion_a = 0.0
        self.reaccion_b = 0.0
        self.reaccion_c = 0.0
        self.puntos_masa_3d.clear()

        # Restablecer variables de la sección transversal
        self.ancho_superior.set(20)
        self.altura_superior.set(5)
        self.ancho_alma.set(5)
        self.altura_alma.set(30)
        self.ancho_inferior.set(15)
        self.altura_inferior.set(5)

        # Limpiar datos de armaduras
        self.nodos_arm.clear()
        self.miembros_arm.clear()
        self.cargas_arm.clear()
        self.id_nodo_actual = 1
        # Limpiar datos de bastidores
        self.nodos_bast.clear()
        self.miembros_bast.clear()
        self.cargas_bast.clear()
        self.id_nodo_bast = 1

        # Limpiar variables de deformación axial y térmica
        self.modulo_young.set(200.0)
        self.coef_expansion.set(12e-6)
        self.longitud_inicial_def.set(2.0)
        self.area_transversal.set(500.0)
        self.fuerza_tension.set(50.0)
        self.cambio_temperatura.set(30.0)

        # Restablecer variables de armaduras/bastidores (importante para que el Combobox no de error)
        self.nodo_x.set(0.0)
        self.nodo_y.set(0.0)
        self.nodo_apoyo_arm.set("Libre") # Usar la variable corregida
        self.miembro_inicio.set(1)
        self.miembro_fin.set(2)
        self.carga_nodo.set(1)
        self.carga_fx.set(0.0)
        self.carga_fy.set(0.0)
        self.corte_valor.set(0.0)
        self.corte_eje.set("X")

        self.nodo_x_bast.set(0.0)
        self.nodo_y_bast.set(0.0)
        self.nodo_apoyo_bast.set("Libre")
        self.nodo_pasadores_bast.set(1)
        self.miembro_inicio_bast.set(1)
        self.miembro_fin_bast.set(2)
        self.carga_nodo_bast.set(1)
        self.carga_fx_bast.set(0.0)
        self.carga_fy_bast.set(0.0)
        self.nodo_fuerza_bast.set(1) # Reiniciar la variable corregida


        # Limpiar área de resultados
        self.limpiar_resultados()

        # Limpiar área gráfica
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        if hasattr(self, 'canvas_armadura'):
            self.canvas_armadura.delete('all')
        if hasattr(self, 'canvas_bastidor'):
            self.canvas_bastidor.delete('all')

        # Mostrar mensaje inicial
        self.mostrar_mensaje_inicial()

        # Redibujar la viga en su estado inicial
        self.dibujar_viga_actual()

    def mostrar_ayuda(self):
        ayuda_texto = """
🎓 GUÍA RÁPIDA DEL SIMULADOR DE ESTRUCTURAS

🔹 VIGAS
• Configuración: Longitud, apoyos (fijo/móvil/ninguno), altura inicial/final, par torsor.
• Cargas: Puntuales (posición, magnitud), Distribuidas (inicio, fin, magnitud).

---
📚 FÓRMULAS DE CÁLCULO (VIGAS)
---

➡️ CÁLCULO DE REACCIONES (Viga Simple con dos apoyos A y B):
Las reacciones (RA, RB) se calculan usando las ecuaciones de equilibrio.
Consideramos:
ΣFy = Suma de fuerzas verticales = 0
ΣMA = Suma de momentos alrededor del apoyo A = 0

Fórmulas principales:
1. ΣFy = RA + RB - ΣF_cargas = 0
   Donde:
   RA: Reacción en apoyo A (N)
   RB: Reacción en apoyo B (N)
   ΣF_cargas: Suma de todas las cargas puntuales y resultantes de distribuidas (N)

2. ΣMA = (RB * L) - Σ(F_carga_i * x_i) + T = 0
   Donde:
   L: Longitud total de la viga (m)
   F_carga_i: Magnitud de cada carga (N o resultante de N/m)
   x_i: Posición de cada carga desde A (m)
   T: Par torsor externo (N·m)

   De aquí, podemos despejar RB y luego RA.

---
➡️ DIAGRAMA DE FUERZA CORTANTE (V(x)):
La fuerza cortante en un punto 'x' es la suma algebraica de todas las fuerzas verticales a la izquierda de 'x'.

Fórmula general:
V(x) = ΣF_verticales_izq
   Donde:
   Las fuerzas hacia arriba son positivas, hacia abajo negativas.

---
➡️ DIAGRAMA DE MOMENTO FLECTOR (M(x)):
El momento flector en un punto 'x' es la suma algebraica de los momentos causados por todas las fuerzas a la izquierda de 'x'.

Fórmula general:
M(x) = Σ(F_vertical_izq_i * distancia_i) + ΣT_externos
   Donde:
   distancia_i: Distancia de la fuerza 'F_vertical_izq_i' al punto 'x'.
   Los momentos que causan compresión en la parte superior de la viga (cara cóncava hacia abajo) se consideran positivos.

---
➡️ CÁLCULO DEL CENTRO DE MASA (Cargas en viga):
El centro de masa (x_cm) para un sistema de cargas se calcula como:

Fórmula:
x_cm = Σ(F_i * x_i) / ΣF_i
   Donde:
   F_i: Cada carga puntual o resultante de carga distribuida (N)
   x_i: Posición de cada carga (m)

---
➡️ PROPIEDADES DE LA SECCIÓN TRANSVERSAL (para sección en I):
Para una sección en forma de I (3 rectángulos), el centro de gravedad (y_cg) y el momento de inercia (I_total) se calculan usando el teorema de los ejes paralelos.

Fórmulas (simplified):
Área Total = A_sup + A_alma + A_inf
y_cg = (A_sup*y_sup + A_alma*y_alma + A_inf*y_inf) / Área_Total
I_total = Σ(I_barra_i + A_i * d_i²)
   Donde:
   A: Área de cada rectángulo
   y: Posición del centroide de cada rectángulo desde la base
   I_barra: Momento de inercia de cada rectángulo alrededor de su propio centroide (bh³/12)
   d: Distancia del centroide de cada rectángulo al centro de gravedad total (y_cg)

---
➡️ DEFORMACIÓN AXIAL Y TÉRMICA:
• **Deformación Axial (δ_axial)**: Cambio de longitud debido a una fuerza axial.
  Fórmula: δ_axial = (F * L0) / (A * E)
  Donde: F = Fuerza, L0 = Longitud inicial, A = Área, E = Módulo de Young.

• **Deformación Térmica (δ_termica)**: Cambio de longitud debido a un cambio de temperatura.
  Fórmula: δ_termica = α * L0 * ΔT
  Donde: α = Coeficiente de expansión térmica, L0 = Longitud inicial, ΔT = Cambio de temperatura.

• **Deformación Total (δ_total)**: Suma de la deformación axial y térmica.
  Fórmula: δ_total = δ_axial + δ_termica

• **Tensión (σ)**: Fuerza por unidad de área.
  Fórmula: σ = F / A

---
🔹 ARMADURAS/BASTIDORES (PRÓXIMAMENTE)
• Se añadirán las fórmulas correspondientes para el método de nodos y el método de secciones una vez implementado el cálculo.

---
🔹 HERRAMIENTAS GENERALES
• 🧮 Calcular: Realiza los cálculos para la estructura activa.
• 📍 Calcular Centro de Masa: Para cargas de viga o formas irregulares.
• 📊 Mostrar Diagramas: Para viga.
• 🌀 Par en Punto: Para viga.
• 🔍 Ampliar Gráfica: Abre las gráficas en una ventana aparte.
• 🎞️ Animar 3D: Animación 3D de la viga.
• ❓ Ayuda: Despliega este resumen de uso.
• 🗑️ Limpiar Todo: Borra todas las configuraciones y reinicia.
• 🌓/🌞 Modo Oscuro/Claro: Alterna el tema visual.

🔹 PASOS BÁSICOS
1. Seleccione la pestaña "Viga" o "Armaduras".
2. Configure la estructura y agregue las cargas.
3. Presione "Calcular" en la sección correspondiente.
4. Revise resultados y diagramas en la pestaña de Resultados.
        """

        ventana_ayuda = tk.Toplevel(self.root)
        ventana_ayuda.title("📚 Guía de Usuario y Fórmulas")
        ventana_ayuda.geometry("700x700")

        texto_ayuda = tk.Text(ventana_ayuda, wrap="word", font=("Arial", 10), padx=10, pady=10)
        scroll_ayuda = ttk.Scrollbar(ventana_ayuda, orient="vertical", command=texto_ayuda.yview)
        texto_ayuda.configure(yscrollcommand=scroll_ayuda.set)

        texto_ayuda.insert("1.0", ayuda_texto)

        texto_ayuda.tag_config("title_formula", font=("Arial", 11, "bold", "underline"), foreground="#005a9e")
        texto_ayuda.tag_config("formula", font=("Consolas", 10, "italic"), foreground="#333333")
        texto_ayuda.tag_config("variable_def", font=("Arial", 9), foreground="#555555")

        start_index = texto_ayuda.search("FÓRMULAS DE CÁLCULO", "1.0", tk.END)
        if start_index:
            end_index = texto_ayuda.search("\n", start_index, tk.END)
            texto_ayuda.tag_add("title_formula", start_index, end_index)

        texto_ayuda.config(state="disabled")  # Solo lectura

        texto_ayuda.pack(side="left", fill="both", expand=True)
        scroll_ayuda.pack(side="right", fill="y")

    def ampliar_grafica(self):
        if hasattr(self, 'ultima_figura') and self.ultima_figura is not None:
            nueva_ventana = tk.Toplevel(self.root)
            nueva_ventana.title("Gráfica Ampliada")

            # Crear una nueva figura para la ventana ampliada para evitar problemas
            # con el embedding de la misma figura en dos canvas.
            amplified_fig = plt.figure(figsize=self.ultima_figura.get_size_inches() * self.ultima_figura.dpi / 50) # Escalar un poco
            amplified_fig.canvas.manager.set_window_title(nueva_ventana.title())

            # Copiar el contenido de la figura original a la nueva
            # Esto puede ser complejo para todas las propiedades, una manera sencilla es recrear los ejes y los plots.
            # Sin embargo, para simplicidad, si es la ultima figura de matplotlib, la re-dibuja.
            # Para armaduras y bastidores, self.ultima_figura ya es la figura completa de matplotlib.
            # Para la viga, las funciones dibujar_viga_actual, etc. ya crean una nueva figura.
            # Simplemente asignamos self.ultima_figura a una variable local y la pasamos al nuevo canvas.
            canvas = FigureCanvasTkAgg(self.ultima_figura, master=nueva_ventana)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(canvas, nueva_ventana)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            messagebox.showinfo("Información", "No hay gráfica para ampliar.")

    def calcular_propiedades_seccion(self):
        try:
            # Obtener dimensiones
            b1 = self.ancho_superior.get()
            h1 = self.altura_superior.get()
            b2 = self.ancho_alma.get()
            h2 = self.altura_alma.get()
            b3 = self.ancho_inferior.get()
            h3 = self.altura_inferior.get()

            # Calcular área total
            area_total = b1*h1 + b2*h2 + b3*h3

            # Calcular centro de gravedad
            y_cg = (b1*h1*(h2+h3+h1/2) + b2*h2*(h3+h2/2) + b3*h3*(h3/2)) / area_total

            # Calcular momento de inercia
            I_superior = (b1*h1**3)/12 + b1*h1*(h2+h3+h1/2-y_cg)**2
            I_alma = (b2*h2**3)/12 + b2*h2*(h3+h2/2-y_cg)**2
            I_inferior = (b3*h3**3)/12 + b3*h3*(h3/2-y_cg)**2
            I_total = I_superior + I_alma + I_inferior

            # Mostrar resultados
            self.log(f"\n{'='*50}\n", "title")
            self.log("PROPIEDADES DE LA SECCIÓN TRANSVERSAL:\n", "title")
            self.log(f"{'='*50}\n", "title")
            self.log(f"Área total: {area_total:.2f} cm²\n", "data")
            self.log(
                f"Centro de gravedad (desde la base): {y_cg:.2f} cm\n",
                "data",
            )
            self.log(f"Momento de inercia: {I_total:.2f} cm⁴\n", "data")

            # Dibujar la sección
            self.dibujar_seccion_transversal(b1, h1, b2, h2, b3, h3, y_cg)

        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculos: {e}")

    def dibujar_seccion_transversal(self, b1, h1, b2, h2, b3, h3, y_cg):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(6, 8))

        # Dibujar la sección
        ax.add_patch(plt.Rectangle((0, h2+h3), b1, h1, fill=False))
        ax.add_patch(plt.Rectangle(((b1-b2)/2, h3), b2, h2, fill=False))
        ax.add_patch(plt.Rectangle(((b1-b3)/2, 0), b3, h3, fill=False))

        # Dibujar línea del centro de gravedad
        ax.axhline(y=y_cg, color='r', linestyle='--')
        ax.text(b1, y_cg, f'CG: {y_cg:.2f} cm', va='bottom', ha='right', color='r')

        # Configurar ejes
        ax.set_xlim(-1, b1+1)
        ax.set_ylim(-1, h1+h2+h3+1)
        ax.set_aspect('equal', 'box')
        ax.set_xlabel('Ancho (cm)')
        ax.set_ylabel('Altura (cm)')
        ax.set_title('Sección Transversal')

        # Mostrar dimensiones
        ax.annotate(f'{b1} cm', (b1/2, h1+h2+h3+0.5), ha='center')
        ax.annotate(f'{h1} cm', (b1+0.5, h2+h3+h1/2), va='center')
        ax.annotate(f'{b2} cm', (b1/2, h3+h2/2), ha='center')
        ax.annotate(f'{h2} cm', ((b1+b2)/2+0.5, h3+h2/2), va='center')
        ax.annotate(f'{b3} cm', (b1/2, -0.5), ha='center')
        ax.annotate(f'{h3} cm', (b1+0.5, h3/2), va='center')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

    def crear_widgets_formas_irregulares(self, parent):
        frame_formas = ttk.LabelFrame(parent, text="Figuras Irregulares", padding="10 10 10 10")
        frame_formas.pack(fill="both", expand=True, pady=5, padx=5) # Expandir para llenar el espacio restante

        # Usar un Frame para los controles de entrada y botones, y que el canvas ocupe el resto
        control_frame = ttk.Frame(frame_formas)
        control_frame.pack(fill="x", pady=5)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(3, weight=1)

        # Tipo de forma
        ttk.Label(control_frame, text="Tipo:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.tipo_forma = ttk.Combobox(control_frame, values=["Rectángulo", "Triángulo", "Círculo"], width=10)
        self.tipo_forma.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.tipo_forma.set("Rectángulo")

        # Coordenadas
        ttk.Label(control_frame, text="X:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.x_forma = ttk.Entry(control_frame, width=8)
        self.x_forma.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(control_frame, text="Y:").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.y_forma = ttk.Entry(control_frame, width=8)
        self.y_forma.grid(row=1, column=3, padx=5, pady=2, sticky="ew")

        # Dimensiones
        ttk.Label(control_frame, text="Ancho:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.ancho_forma = ttk.Entry(control_frame, width=8)
        self.ancho_forma.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(control_frame, text="Alto:").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        self.alto_forma = ttk.Entry(control_frame, width=8)
        self.alto_forma.grid(row=2, column=3, padx=5, pady=2, sticky="ew")

        # Botones de agregar y calcular CG
        button_row_1 = ttk.Frame(control_frame)
        button_row_1.grid(row=3, column=0, columnspan=4, pady=5, sticky="ew")
        button_row_1.columnconfigure(0, weight=1)
        button_row_1.columnconfigure(1, weight=1)
        ttk.Button(button_row_1, text="Agregar Forma", command=self.agregar_forma).grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        ttk.Button(button_row_1, text="Calcular CG", command=self.calcular_cg_formas).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        # Botones de limpiar y ampliar
        button_row_2 = ttk.Frame(control_frame)
        button_row_2.grid(row=4, column=0, columnspan=4, pady=5, sticky="ew")
        button_row_2.columnconfigure(0, weight=1)
        button_row_2.columnconfigure(1, weight=1)
        ttk.Button(button_row_2, text="Limpiar Lienzo", command=self.limpiar_lienzo_formas).grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        ttk.Button(button_row_2, text="Ampliar Lienzo", command=self.ampliar_lienzo_formas).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        # Botones de cargar proyectos
        project_buttons_frame = ttk.Frame(control_frame)
        project_buttons_frame.grid(row=5, column=0, columnspan=4, pady=5, sticky="ew")
        project_buttons_frame.columnconfigure(0, weight=1)
        project_buttons_frame.columnconfigure(1, weight=1)
        project_buttons_frame.columnconfigure(2, weight=1)
        ttk.Button(project_buttons_frame, text="Cargar Proyecto 3 (Mesa)",
                   command=self.cargar_proyecto_3_cg_mesa).grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        ttk.Button(project_buttons_frame, text="Cargar CG (Solar)",
                   command=self.cargar_cg_solar).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(project_buttons_frame, text="Cargar Proyecto (Mancuerna)",
                   command=self.cargar_proyecto_mancuerna_cg).grid(row=0, column=2, padx=5, pady=2, sticky="ew")

        ttk.Label(frame_formas, text="⚡ También puede hacer clic derecho para escalar y arrastrar en el lienzo.").pack(pady=2) # Ajustar padding
        self.canvas_formas = tk.Canvas(frame_formas, bg="white", highlightbackground="gray", highlightthickness=1)
        self.canvas_formas.pack(fill="both", expand=True, pady=5, padx=5) # Expandir para llenar
        self.canvas_formas.bind("<Button-1>", self.iniciar_accion_formas)
        self.canvas_formas.bind("<B1-Motion>", self.arrastrar_forma)
        self.canvas_formas.bind("<ButtonRelease-1>", self.soltar_forma)
        self.canvas_formas.bind("<Button-3>", self.iniciar_escalado_forma)
        self.canvas_formas.bind("<B3-Motion>", self.escalar_forma_drag)
        self.canvas_formas.bind("<ButtonRelease-3>", self.finalizar_escalado_forma)
        self.canvas_formas.bind("<Motion>", self.mostrar_coordenadas)
        self.canvas_formas.bind("<MouseWheel>", self.escalar_forma)
        self.canvas_formas.bind("<Button-4>", self.escalar_forma)
        self.canvas_formas.bind("<Button-5>", self.escalar_forma)
        self.canvas_formas.bind("<Configure>", lambda e: self.redibujar_formas()) # Redibujar al cambiar tamaño
        self.dibujar_cuadricula(self.canvas_formas)

        self.coord_label = ttk.Label(frame_formas, text="x=0, y=0")
        self.coord_label.pack(pady=2)

        self.cg_label = ttk.Label(frame_formas, text="CG: -")
        self.cg_label.pack(pady=2)

    def crear_seccion_armaduras(self, parent):
        frame_arm = ttk.Frame(parent, padding="10 10 10 10") # Ajustar padding
        frame_arm.pack(fill="both", expand=True, padx=5, pady=5)

        frame_nodo = ttk.LabelFrame(frame_arm, text="Nodos", padding="5 5 5 5") # Ajustar padding
        frame_nodo.pack(fill="x", pady=3) # Ajustar padding
        frame_nodo.columnconfigure(1, weight=1)
        frame_nodo.columnconfigure(3, weight=1)
        frame_nodo.columnconfigure(5, weight=1)
        ttk.Label(frame_nodo, text="X:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_nodo, textvariable=self.nodo_x, width=8).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_nodo, text="Y:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_nodo, textvariable=self.nodo_y, width=8).grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_nodo, text="Apoyo:").grid(row=0, column=4, padx=2, pady=1, sticky="w")
        # Corrección: usar self.nodo_apoyo_arm como textvariable
        self.combobox_nodo_apoyo_arm = ttk.Combobox(frame_nodo, textvariable=self.nodo_apoyo_arm, values=["Libre", "Fijo", "Móvil"], width=8)
        self.combobox_nodo_apoyo_arm.grid(row=0, column=5, padx=2, pady=1, sticky="ew")
        self.combobox_nodo_apoyo_arm.set("Libre")
        ttk.Button(frame_nodo, text="Agregar Nodo", command=self.agregar_nodo).grid(row=0, column=6, padx=5, pady=1, sticky="ew")

        frame_miem = ttk.LabelFrame(frame_arm, text="Miembros", padding="5 5 5 5") # Ajustar padding
        frame_miem.pack(fill="x", pady=3) # Ajustar padding
        frame_miem.columnconfigure(1, weight=1)
        frame_miem.columnconfigure(3, weight=1)
        ttk.Label(frame_miem, text="Inicio:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_miem, textvariable=self.miembro_inicio, width=5).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_miem, text="Fin:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_miem, textvariable=self.miembro_fin, width=5).grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        ttk.Button(frame_miem, text="Agregar Miembro", command=self.agregar_miembro).grid(row=0, column=4, padx=5, pady=1, sticky="ew")

        frame_carga = ttk.LabelFrame(frame_arm, text="Cargas en Nodos", padding="5 5 5 5") # Ajustar padding
        frame_carga.pack(fill="x", pady=3) # Ajustar padding
        frame_carga.columnconfigure(1, weight=1)
        frame_carga.columnconfigure(3, weight=1)
        frame_carga.columnconfigure(5, weight=1)
        ttk.Label(frame_carga, text="Nodo:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_carga, textvariable=self.carga_nodo, width=5).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_carga, text="Fx:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_carga, textvariable=self.carga_fx, width=8).grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_carga, text="Fy:").grid(row=0, column=4, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_carga, textvariable=self.carga_fy, width=8).grid(row=0, column=5, padx=2, pady=1, sticky="ew")
        ttk.Button(frame_carga, text="Agregar Carga", command=self.agregar_carga_armadura).grid(row=0, column=6, padx=5, pady=1, sticky="ew")

        frame_secc = ttk.LabelFrame(frame_arm, text="Método de Secciones", padding="5 5 5 5") # Ajustar padding
        frame_secc.pack(fill="x", pady=3) # Ajustar padding
        frame_secc.columnconfigure(1, weight=1)
        frame_secc.columnconfigure(3, weight=1)
        frame_secc.columnconfigure(4, weight=1)
        frame_secc.columnconfigure(5, weight=1)
        ttk.Label(frame_secc, text="Corte:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_secc, textvariable=self.corte_valor, width=8).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_secc, text="Eje:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        self.corte_eje = ttk.Combobox(frame_secc, textvariable=self.corte_eje, values=["X", "Y"], width=5)
        self.corte_eje.grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        self.corte_eje.set("X")
        ttk.Button(frame_secc, text="Calcular Sección", command=self.calcular_seccion_armadura).grid(row=0, column=4, padx=5, pady=1, sticky="ew")
        ttk.Button(frame_secc, text="DCL Nodos", command=self.mostrar_dcl_nodos).grid(row=0, column=5, padx=5, pady=1, sticky="ew")

        # Botones principales para armaduras
        arm_buttons_frame = ttk.Frame(frame_arm)
        arm_buttons_frame.pack(fill="x", pady=5)
        arm_buttons_frame.columnconfigure(0, weight=1)
        arm_buttons_frame.columnconfigure(1, weight=1)
        ttk.Button(arm_buttons_frame, text="Calcular Armadura", command=self.calcular_armadura).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(arm_buttons_frame, text="Instrucciones", command=self.mostrar_instrucciones_armadura).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.canvas_armadura = tk.Canvas(frame_arm, bg="white", highlightbackground="gray", highlightthickness=1)
        self.canvas_armadura.pack(fill="both", expand=True, padx=5, pady=5)
        self.canvas_armadura.bind("<Configure>", lambda e: self.dibujar_armadura())

    def crear_seccion_bastidores(self, parent):
        frame_arm = ttk.Frame(parent, padding="10 10 10 10")
        frame_arm.pack(fill="both", expand=True, padx=5, pady=5)

        frame_nodo = ttk.LabelFrame(frame_arm, text="Nodos", padding="5 5 5 5")
        frame_nodo.pack(fill="x", pady=3)
        frame_nodo.columnconfigure(1, weight=1)
        frame_nodo.columnconfigure(3, weight=1)
        frame_nodo.columnconfigure(5, weight=1)
        frame_nodo.columnconfigure(7, weight=1)
        ttk.Label(frame_nodo, text="X:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_nodo, textvariable=self.nodo_x_bast, width=8).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_nodo, text="Y:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_nodo, textvariable=self.nodo_y_bast, width=8).grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_nodo, text="Apoyo:").grid(row=0, column=4, padx=2, pady=1, sticky="w")
        self.nodo_apoyo_bast = ttk.Combobox(frame_nodo, textvariable=self.nodo_apoyo_bast,
                     values=["Libre", "Fijo", "Móvil"], width=8)
        self.nodo_apoyo_bast.grid(row=0, column=5, padx=2, pady=1, sticky="ew")
        self.nodo_apoyo_bast.set("Libre")
        ttk.Label(frame_nodo, text="Pasadores:").grid(row=0, column=6, padx=2, pady=1, sticky="w")
        ttk.Spinbox(frame_nodo, from_=1, to=10, textvariable=self.nodo_pasadores_bast,
                    width=5).grid(row=0, column=7, padx=2, pady=1, sticky="ew")
        ttk.Button(frame_nodo, text="Agregar Nodo", command=self.agregar_nodo_bastidor).grid(row=0, column=8, padx=5, pady=1, sticky="ew")

        frame_miem = ttk.LabelFrame(frame_arm, text="Miembros", padding="5 5 5 5")
        frame_miem.pack(fill="x", pady=3)
        frame_miem.columnconfigure(1, weight=1)
        frame_miem.columnconfigure(3, weight=1)
        ttk.Label(frame_miem, text="Inicio:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_miem, textvariable=self.miembro_inicio_bast, width=5).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_miem, text="Fin:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_miem, textvariable=self.miembro_fin_bast, width=5).grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        ttk.Button(frame_miem, text="Agregar Miembro", command=self.agregar_miembro_bastidor).grid(row=0, column=4, padx=5, pady=1, sticky="ew")

        frame_carga = ttk.LabelFrame(frame_arm, text="Cargas en Nodos", padding="5 5 5 5")
        frame_carga.pack(fill="x", pady=3)
        frame_carga.columnconfigure(1, weight=1)
        frame_carga.columnconfigure(3, weight=1)
        frame_carga.columnconfigure(5, weight=1)
        ttk.Label(frame_carga, text="Nodo:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_carga, textvariable=self.carga_nodo_bast, width=5).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_carga, text="Fx:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_carga, textvariable=self.carga_fx_bast, width=8).grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_carga, text="Fy:").grid(row=0, column=4, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_carga, textvariable=self.carga_fy_bast, width=8).grid(row=0, column=5, padx=2, pady=1, sticky="ew")
        ttk.Button(frame_carga, text="Agregar Carga", command=self.agregar_carga_bastidor).grid(row=0, column=6, padx=5, pady=1, sticky="ew")

        frame_fuerza = ttk.LabelFrame(frame_arm, text="Fuerzas en Nodo", padding="5 5 5 5")
        frame_fuerza.pack(fill="x", pady=3)
        frame_fuerza.columnconfigure(1, weight=1)
        frame_fuerza.columnconfigure(2, weight=1)
        ttk.Label(frame_fuerza, text="Nodo:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        # Corrección: Usar self.nodo_fuerza_bast como textvariable
        ttk.Entry(frame_fuerza, textvariable=self.nodo_fuerza_bast, width=5).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Button(frame_fuerza, text="Calcular", command=self.calcular_fuerza_nodo_bastidor).grid(row=0, column=2, padx=5, pady=1, sticky="ew")

        frame_secc = ttk.LabelFrame(frame_arm, text="Método de Secciones", padding="5 5 5 5")
        frame_secc.pack(fill="x", pady=3)
        frame_secc.columnconfigure(1, weight=1)
        frame_secc.columnconfigure(3, weight=1)
        frame_secc.columnconfigure(4, weight=1)
        frame_secc.columnconfigure(5, weight=1)
        ttk.Label(frame_secc, text="Corte:").grid(row=0, column=0, padx=2, pady=1, sticky="w")
        ttk.Entry(frame_secc, textvariable=self.corte_valor_bast, width=8).grid(row=0, column=1, padx=2, pady=1, sticky="ew")
        ttk.Label(frame_secc, text="Eje:").grid(row=0, column=2, padx=2, pady=1, sticky="w")
        ttk.Combobox(frame_secc, textvariable=self.corte_eje_bast, values=["X", "Y"], width=5).grid(row=0, column=3, padx=2, pady=1, sticky="ew")
        ttk.Button(frame_secc, text="Calcular Sección", command=self.calcular_seccion_bastidor).grid(row=0, column=4, padx=5, pady=1, sticky="ew")
        ttk.Button(frame_secc, text="DCL Nodos", command=self.mostrar_dcl_nodos_bastidor).grid(row=0, column=5, padx=5, pady=1, sticky="ew")

        bast_buttons_frame = ttk.Frame(frame_arm)
        bast_buttons_frame.pack(fill="x", pady=5)
        bast_buttons_frame.columnconfigure(0, weight=1)
        bast_buttons_frame.columnconfigure(1, weight=1)
        ttk.Button(bast_buttons_frame, text="Calcular Bastidor", command=self.calcular_bastidor).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Pequeños botones de ayuda y ejemplo
        frame_ayuda_bast = ttk.Frame(bast_buttons_frame)
        frame_ayuda_bast.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        frame_ayuda_bast.columnconfigure(0, weight=1)
        frame_ayuda_bast.columnconfigure(1, weight=1)
        frame_ayuda_bast.columnconfigure(2, weight=1) # Añadir columna para el nuevo botón

        ttk.Button(frame_ayuda_bast, text="Ayuda", command=self.mostrar_instrucciones_bastidor).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(frame_ayuda_bast, text="Ejemplo", command=self.cargar_ejemplo_bastidor).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        # Nuevo botón para ampliar gráfica del bastidor
        ttk.Button(frame_ayuda_bast, text="Ampliar Gráfica", command=self.ampliar_grafica).grid(row=0, column=2, padx=2, pady=2, sticky="ew")


        # Canvas para representar el bastidor
        self.canvas_bastidor = tk.Canvas(frame_arm, bg="white", highlightbackground="gray", highlightthickness=1)
        self.canvas_bastidor.pack(fill="both", expand=True, padx=5, pady=5)
        self.canvas_bastidor.bind("<Configure>", lambda e: self.dibujar_bastidor())

    def agregar_forma(self):
        try:
            tipo = self.tipo_forma.get()
            x = float(self.x_forma.get())
            y = float(self.y_forma.get())
            ancho = float(self.ancho_forma.get())
            alto = float(self.alto_forma.get())

            if tipo not in ["Rectángulo", "Triángulo", "Círculo"]:
                raise ValueError("Tipo de forma no válido")

            self.formas.append((tipo, x, y, ancho, alto))
            self.redibujar_formas()
            self.log(f"Forma agregada: {tipo} en ({x}, {y})\n", "data")

        except Exception as e:
            messagebox.showerror("Error", f"Valores inválidos: {e}")

    def colocar_forma(self, event):
        """Permite agregar una forma haciendo clic en el lienzo."""
        try:
            tipo = self.tipo_forma.get()
            ancho = float(self.ancho_forma.get()) if self.ancho_forma.get() else 50
            alto = float(self.alto_forma.get()) if self.alto_forma.get() else 50

            x = event.x
            y = event.y

            canvas = event.widget

            if tipo == "Círculo":
                self.formas.append((tipo, x, y, ancho, alto))
            else: # Rectángulo o Triángulo, asumir el clic como esquina superior izquierda para visual
                # Ajustamos 'y' para que el punto del clic sea la esquina superior izquierda del rectángulo o el vértice superior del triángulo.
                # Al dibujar, 'create_rectangle' usa la esquina superior izquierda. Para el triángulo también queremos esa lógica visual.
                self.formas.append((tipo, x, y, ancho, alto))

            self.redibujar_formas()
            self.log(f"Forma agregada: {tipo} en ({x}, {y})\n", "data")
        except ValueError as e:
            messagebox.showerror("Error", f"Valores inválidos: {e}")

    def calcular_cg_formas(self):
        if not self.formas:
            messagebox.showwarning("Advertencia", "No hay formas para calcular")
            return

        area_total = 0
        cx_total = 0
        cy_total = 0

        for forma in self.formas:
            tipo, x, y, ancho, alto = forma
            if tipo == "Rectángulo":
                area = ancho * alto
                cx = x + ancho/2
                # Para un rectángulo dibujado desde la esquina superior izquierda (x,y), el centroide es (x + ancho/2, y + alto/2)
                cy = y + alto/2
            elif tipo == "Triángulo":
                area = ancho * alto / 2
                # Para un triángulo con vértice superior en (x,y), y base de ancho 'ancho' a una distancia 'alto' hacia abajo
                # El centroide está a 1/3 de la altura desde la base.
                # Si (x,y) es el vértice superior: (x,y), (x - ancho/2, y+alto), (x + ancho/2, y+alto)
                # CG: (x, y + 2*alto/3) desde el vértice superior (x,y)
                # O si (x,y) es esquina superior izquierda y base abajo: (x,y+alto), (x+ancho/2,y), (x+ancho,y+alto)
                # CG: (x + ancho/2, y + 2*alto/3)
                cx = x + ancho/2 # Suponiendo que 'x' es el punto medio horizontal de la base
                cy = y + (2 * alto / 3) # Suponiendo que 'y' es la parte superior del triángulo (vértice)
            elif tipo == "Círculo":
                area = np.pi * (ancho/2)**2
                cx = x
                cy = y
            else:
                continue  # Saltar formas no reconocidas

            area_total += area
            cx_total += cx * area
            cy_total += cy * area

        if area_total == 0:
            messagebox.showerror("Error", "Área total es cero")
            return

        cg_x = cx_total / area_total
        cg_y = cy_total / area_total

        self.log(f"\nCentro de Gravedad: ({cg_x:.2f}, {cg_y:.2f})\n", "data")
        self.dibujar_formas_irregulares(cg_x, cg_y)

    def dibujar_formas_irregulares(self, cg_x, cg_y):
        fig, ax = plt.subplots(figsize=(8, 8))

        for forma in self.formas:
            tipo, x, y, ancho, alto = forma
            if tipo == "Rectángulo":
                # plt.Rectangle toma (x,y) como esquina inferior izquierda
                ax.add_patch(plt.Rectangle((x, y), ancho, alto, fill=False))
            elif tipo == "Triángulo":
                # plt.Polygon toma una lista de vértices. Necesitamos definir los 3 vértices.
                # Si (x,y) es el vértice superior y la base es horizontal en (y+alto)
                vertices = [(x, y), (x - ancho/2, y + alto), (x + ancho/2, y + alto)]
                ax.add_patch(plt.Polygon(vertices, fill=False))
            elif tipo == "Círculo":
                # plt.Circle toma (x,y) como centro y luego el radio
                ax.add_patch(plt.Circle((x, y), ancho/2, fill=False))

        ax.plot(cg_x, cg_y, 'ro', markersize=10)
        ax.text(cg_x, cg_y, f'CG ({cg_x:.2f}, {cg_y:.2f})', ha='right', va='bottom')

        ax.set_aspect('equal', 'box')
        # Ajustar límites para abarcar una mesa de hasta 100x50 con un pequeño margen
        ax.set_xlim(min(0, min(f[1] for f in self.formas if f[1] is not None) - 10), max(100, max(f[1]+f[3] for f in self.formas if f[1] is not None) + 10))
        ax.set_ylim(min(0, min(f[2] for f in self.formas if f[2] is not None) - 10), max(50, max(f[2]+f[4] for f in self.formas if f[2] is not None) + 10))
        ax.set_title('Formas Irregulares y Centro de Gravedad')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig

    def dibujar_forma_canvas(self, canvas, tipo, x, y, ancho, alto):
        """Dibuja una forma en el canvas indicado."""
        if tipo == "Rectángulo":
            canvas.create_rectangle(x, y, x + ancho, y + alto, outline="black")
        elif tipo == "Triángulo":
            # Si x,y es la esquina superior izquierda del bounding box
            # Vértices: (x, y+alto), (x+ancho/2, y), (x+ancho, y+alto)
            canvas.create_polygon(x, y + alto, x + ancho / 2, y, x + ancho, y + alto, outline="black", fill="")
        elif tipo == "Círculo":
            # (x,y) es el centro
            radius = ancho / 2
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline="black")

    def dibujar_cuadricula(self, canvas):
        """Dibuja una cuadrícula de fondo en el canvas."""
        canvas.delete("grid")
        width = int(canvas.winfo_width()) if canvas.winfo_width() > 1 else int(canvas['width']) # Usar winfo_width/height para el tamaño real
        height = int(canvas.winfo_height()) if canvas.winfo_height() > 1 else int(canvas['height'])

        for x in range(0, width, self.grid_spacing):
            canvas.create_line(x, 0, x, height, fill="#e0e0e0", tags="grid")
        for y in range(0, height, self.grid_spacing):
            canvas.create_line(0, y, width, y, fill="#e0e0e0", tags="grid")
        # Ejes con flechas y numeración
        canvas.create_line(20, height-20, width-10, height-20, arrow=tk.LAST, tags="grid")
        canvas.create_line(20, height-20, 20, 10, arrow=tk.LAST, tags="grid")
        num_x = (width - 40) // self.grid_spacing
        num_y = (height - 30) // self.grid_spacing
        for i in range(1, num_x + 1):
            canvas.create_text(20 + i * self.grid_spacing, height-10, text=str(i), tags="grid")
        for i in range(1, num_y + 1):
            canvas.create_text(10, height-20 - i * self.grid_spacing, text=str(i), tags="grid")

    def mostrar_coordenadas(self, event):
        self.coord_label.config(text=f"x={event.x}, y={event.y}")

    def mostrar_coordenadas_ampliado(self, event):
        if hasattr(self, "coord_label_ampliado"):
            self.coord_label_ampliado.config(text=f"x={event.x}, y={event.y}")

    # ----- Funciones para Armaduras -----
    def agregar_nodo(self):
        x = self.nodo_x.get()
        y = self.nodo_y.get()
        apoyo = self.nodo_apoyo_arm.get() # Usar la variable corregida
        self.nodos_arm.append({'id': self.id_nodo_actual, 'x': x, 'y': y, 'apoyo': apoyo})
        self.log(f"Nodo {self.id_nodo_actual} agregado en ({x}, {y})\n", "data")
        self.id_nodo_actual += 1
        self.dibujar_armadura()

    def agregar_miembro(self):
        ini = self.miembro_inicio.get()
        fin = self.miembro_fin.get()
        if not any(n['id'] == ini for n in self.nodos_arm) or not any(n['id'] == fin for n in self.nodos_arm):
            messagebox.showerror("Error", "Los nodos inicial y final deben existir.")
            return

        self.miembros_arm.append({'inicio': ini, 'fin': fin, 'fuerza': 0.0})
        self.log(f"Miembro {ini}-{fin} agregado\n", "data")
        self.dibujar_armadura()

    def agregar_carga_armadura(self):
        nodo = self.carga_nodo.get()
        fx = self.carga_fx.get()
        fy = self.carga_fy.get()
        if not any(n['id'] == nodo for n in self.nodos_arm):
            messagebox.showerror("Error", "El nodo al que se aplica la carga debe existir.")
            return

        self.cargas_arm.append({'nodo': nodo, 'Fx': fx, 'Fy': fy})
        self.log(f"Carga en nodo {nodo}: Fx={fx}, Fy={fy}\n", "data")
        self.dibujar_armadura()

    def resolver_articulado(self, nodos, miembros, cargas):
        """Resuelve un conjunto de barras articuladas mediante el método de nodos."""
        n_miembros = len(miembros)
        var_map = {}
        idx = 0
        for i in range(n_miembros):
            var_map[f"m{i}"] = idx
            idx += 1

        for nodo in nodos:
            if nodo['apoyo'] == 'Fijo':
                var_map[f"Rx{nodo['id']}"] = idx; idx += 1
                var_map[f"Ry{nodo['id']}"] = idx; idx += 1
            elif nodo['apoyo'] == 'Móvil':
                var_map[f"Ry{nodo['id']}"] = idx; idx += 1

        num_vars = idx
        num_eqs = len(nodos) * 2

        A = np.zeros((num_eqs, num_vars))
        b = np.zeros(num_eqs)

        node_lookup = {n['id']: n for n in nodos}
        loads = {n['id']: {'Fx': 0.0, 'Fy': 0.0} for n in nodos}
        for c in cargas:
            loads[c['nodo']]['Fx'] += c['Fx']
            loads[c['nodo']]['Fy'] += c['Fy']

        eq = 0
        for nodo in nodos:
            for j, m in enumerate(miembros):
                if m['inicio'] == nodo['id'] or m['fin'] == nodo['id']:
                    n2_id = m['fin'] if m['inicio'] == nodo['id'] else m['inicio']
                    nd1 = node_lookup[nodo['id']]
                    nd2 = node_lookup[n2_id]
                    dx = nd2['x'] - nd1['x']
                    dy = nd2['y'] - nd1['y']
                    L = (dx**2 + dy**2) ** 0.5
                    if L == 0:
                        continue
                    cos_theta = dx / L
                    if m['inicio'] == nodo['id']:
                        A[eq, var_map[f"m{j}"]] += cos_theta
                    else:
                        A[eq, var_map[f"m{j}"]] -= cos_theta

            if nodo['apoyo'] == 'Fijo':
                A[eq, var_map[f"Rx{nodo['id']}"]] = 1

            b[eq] = -loads[nodo['id']]['Fx']
            eq += 1

            for j, m in enumerate(miembros):
                if m['inicio'] == nodo['id'] or m['fin'] == nodo['id']:
                    n2_id = m['fin'] if m['inicio'] == nodo['id'] else m['inicio']
                    nd1 = node_lookup[nodo['id']]
                    nd2 = node_lookup[n2_id]
                    dx = nd2['x'] - nd1['x']
                    dy = nd2['y'] - nd1['y']
                    L = (dx**2 + dy**2) ** 0.5
                    if L == 0:
                        continue
                    sin_theta = dy / L
                    if m['inicio'] == nodo['id']:
                        A[eq, var_map[f"m{j}"]] += sin_theta
                    else:
                        A[eq, var_map[f"m{j}"]] -= sin_theta

            if nodo['apoyo'] in ('Fijo', 'Móvil'):
                A[eq, var_map[f"Ry{nodo['id']}"]] = 1

            b[eq] = -loads[nodo['id']]['Fy']
            eq += 1

        if A.shape[0] != A.shape[1]:
            soluciones, *_ = np.linalg.lstsq(A, b, rcond=None)
        else:
            try:
                soluciones = np.linalg.solve(A, b)
            except np.linalg.LinAlgError:
                soluciones, *_ = np.linalg.lstsq(A, b, rcond=None)

        fuerzas = [soluciones[var_map[f"m{i}"]] for i in range(n_miembros)]
        reacciones = {}
        for nodo in nodos:
            if nodo['apoyo'] == 'Fijo':
                rx = soluciones[var_map[f"Rx{nodo['id']}"]]
                ry = soluciones[var_map[f"Ry{nodo['id']}"]]
                reacciones[nodo['id']] = (rx, ry)
            elif nodo['apoyo'] == 'Móvil':
                ry = soluciones[var_map[f"Ry{nodo['id']}"]]
                reacciones[nodo['id']] = (0.0, ry)

        return fuerzas, reacciones, num_vars, num_eqs

    def calcular_armadura(self):
        try:
            if not self.nodos_arm or not self.miembros_arm:
                messagebox.showwarning("Advertencia", "Agrega nodos y miembros a la armadura primero.")
                return

            fuerzas, reacciones, num_vars, num_eqs = self.resolver_articulado(
                self.nodos_arm, self.miembros_arm, self.cargas_arm)

            if num_vars > num_eqs:
                messagebox.showwarning(
                    "Advertencia",
                    "La armadura es estáticamente indeterminada. Puede que no tenga una solución única o sea inestable.",
                )
            elif num_vars < num_eqs:
                messagebox.showwarning(
                    "Advertencia",
                    "La armadura es estáticamente sobredeterminada. Puede que no sea soluble con las condiciones dadas.",
                )

            for j, m in enumerate(self.miembros_arm):
                m['fuerza'] = fuerzas[j]

            self.reacciones_arm = reacciones

            self.log(f"\n{'='*50}\n", "title")
            self.log("📐 ANÁLISIS DE ARMADURA:\n", "title")
            self.log(f"{'='*50}\n", "title")
            for j, m in enumerate(self.miembros_arm):
                tipo = "tensión" if m['fuerza'] >= 0 else "compresión"
                self.log(f"Miembro {m['inicio']}-{m['fin']}: {m['fuerza']:.2f} N ({tipo})\n", "data")

            for nid, r in self.reacciones_arm.items():
                self.log(f"Reacciones nodo {nid}: Rx={r[0]:.2f} N, Ry={r[1]:.2f} N\n", "data")

            self.dibujar_armadura()

        except np.linalg.LinAlgError as e:
            messagebox.showerror("Error de Cálculo", f"El sistema de ecuaciones no pudo resolverse (singular o mal condicionado): {e}. Verifica la estabilidad de la armadura.")
        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculo de armadura: {e}")

    def ajustar_vista_armadura(self):
        """Calcula la escala y desplazamiento para dibujar la armadura dentro del canvas."""
        if not hasattr(self, 'canvas_armadura') or not self.nodos_arm:
            self.escala_arm = 20
            self.offset_x_arm = 50
            self.offset_y_arm = 350
            return

        c = self.canvas_armadura
        width = c.winfo_width() if c.winfo_width() > 1 else int(c['width'])
        height = c.winfo_height() if c.winfo_height() > 1 else int(c['height'])

        margin = 50

        xs = [n['x'] for n in self.nodos_arm]
        ys = [n['y'] for n in self.nodos_arm]

        if not xs:
            self.escala_arm = 20
            self.offset_x_arm = width / 2
            self.offset_y_arm = height / 2
            return

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        rango_x = max(max_x - min_x, 1e-6)
        rango_y = max(max_y - min_y, 1e-6)

        escala_x = (width - 2 * margin) / rango_x
        escala_y = (height - 2 * margin) / rango_y

        self.escala_arm = min(escala_x, escala_y)

        self.offset_x_arm = margin - min_x * self.escala_arm + (width - 2 * margin - rango_x * self.escala_arm) / 2
        self.offset_y_arm = height - margin + min_y * self.escala_arm - (height - 2 * margin - rango_y * self.escala_arm) / 2

    def dibujar_armadura(self):
        if not hasattr(self, 'canvas_armadura'):
            return
        c = self.canvas_armadura
        self.ajustar_vista_armadura()
        c.delete('all')

        for nodo in self.nodos_arm:
            x = nodo['x'] * self.escala_arm + self.offset_x_arm
            y = self.offset_y_arm - nodo['y'] * self.escala_arm
            c.create_oval(x-5, y-5, x+5, y+5, fill='black', tags="nodo")
            c.create_text(x, y-10, text=str(nodo['id']), fill='black', tags="nodo_id")

            if nodo['apoyo'] == 'Fijo':
                c.create_polygon(x-10, y+10, x+10, y+10, x, y, fill='blue', outline='blue', tags="apoyo")
                c.create_line(x-15, y+10, x+15, y+10, fill='gray', tags="apoyo")
                for i in range(-1, 2):
                    c.create_line(x + i*5, y + 10, x + i*5 + 5, y + 15, fill='gray', tags="apoyo")
            elif nodo['apoyo'] == 'Móvil':
                c.create_oval(x-8, y+2, x+8, y+18, fill='blue', outline='blue', tags="apoyo")
                c.create_line(x-15, y+20, x+15, y+20, fill='gray', tags="apoyo")
                for i in range(-1, 2):
                    c.create_line(x + i*5, y + 20, x + i*5 + 5, y + 25, fill='gray', tags="apoyo")

        for m in self.miembros_arm:
            n1 = next(n for n in self.nodos_arm if n['id']==m['inicio'])
            n2 = next(n for n in self.nodos_arm if n['id']==m['fin'])

            x1 = n1['x'] * self.escala_arm + self.offset_x_arm
            y1 = self.offset_y_arm - n1['y'] * self.escala_arm
            x2 = n2['x'] * self.escala_arm + self.offset_x_arm
            y2 = self.offset_y_arm - n2['y'] * self.escala_arm

            color = 'black'
            if 'fuerza' in m:
                color = 'red' if m['fuerza'] < 0 else 'blue'

            c.create_line(x1, y1, x2, y2, fill=color, width=2, tags="miembro")

            if 'fuerza' in m:
                mid_x = (x1+x2)/2
                mid_y = (y1+y2)/2
                c.create_text(mid_x, mid_y, text=f"{m['fuerza']:.1f} N", fill=color, font=("Arial", 8, "bold"), tags="miembro_fuerza")

        arrow_len = 20
        for carg in self.cargas_arm:
            nodo = next(n for n in self.nodos_arm if n['id']==carg['nodo'])
            x = nodo['x'] * self.escala_arm + self.offset_x_arm
            y = self.offset_y_arm - nodo['y'] * self.escala_arm

            fx = carg['Fx']
            fy = carg['Fy']
            mag = (fx**2 + fy**2) ** 0.5
            if mag > 0:
                ux, uy = fx / mag, fy / mag
                c.create_line(x, y, x + ux * arrow_len, y - uy * arrow_len, arrow=tk.LAST, fill='green', width=2, tags="carga")
                c.create_text(x + ux * arrow_len + 15 * ux, y - uy * arrow_len - 15 * uy, text=f"{mag:.1f} N", fill='green', font=("Arial", 8, "bold"), tags="carga_mag")

        if hasattr(self, 'reacciones_arm'):
            reaction_arrow_len = 25
            for nodo in self.nodos_arm:
                if nodo['apoyo'] in ('Fijo', 'Móvil'):
                    if nodo['id'] in self.reacciones_arm:
                        rx, ry = self.reacciones_arm[nodo['id']]
                        x_node = nodo['x'] * self.escala_arm + self.offset_x_arm
                        y_node = self.offset_y_arm - nodo['y'] * self.escala_arm

                        if abs(rx) > 0.1:
                            x_end = x_node + (1 if rx > 0 else -1) * reaction_arrow_len
                            c.create_line(x_node, y_node, x_end, y_node, arrow=tk.LAST, fill='orange', width=2, tags="reaccion")
                            c.create_text(x_end, y_node - 10, text=f"{rx:.1f}", fill='orange', font=("Arial", 8, "bold"), tags="reaccion_mag")

                        if abs(ry) > 0.1:
                            y_end = y_node - (1 if ry > 0 else -1) * reaction_arrow_len
                            c.create_line(x_node, y_node, x_node, y_end, arrow=tk.LAST, fill='orange', width=2, tags="reaccion")
                            c.create_text(x_node + 10, y_end, text=f"{ry:.1f}", fill='orange', font=("Arial", 8, "bold"), tags="reaccion_mag")

        # Guardar la figura del canvas_armadura para poder ampliarla
        # Esto es un placeholder, ya que canvas de Tkinter no es una figura de Matplotlib directamente.
        # Si se desea ampliar el canvas de Tkinter, se necesitaría una lógica diferente o renderizarlo en Matplotlib.
        # Por ahora, nos centraremos en el bastidor, que sí usa Matplotlib.
        # Si se quiere ampliar armaduras, deberíamos dibujarlas también en un gráfico de Matplotlib.

    def mostrar_dcl_nodos(self):
        if not self.miembros_arm or not hasattr(self, 'reacciones_arm'):
            messagebox.showwarning("Advertencia", "Calcule primero la armadura para ver los DCLs.")
            return

        for nodo in self.nodos_arm:
            self.dibujar_dcl_nodo(nodo)

    def dibujar_dcl_nodo(self, nodo):
        ventana = tk.Toplevel(self.root)
        ventana.title(f"DCL Nodo {nodo['id']}")
        fig, ax = plt.subplots(figsize=(4,4))

        ax.plot(0,0,'ko', markersize=8)
        ax.text(0, 0.2, f"Nodo {nodo['id']}", ha='center', va='bottom', fontsize=10, fontweight='bold')

        node_lookup = {n['id']: n for n in self.nodos_arm}
        arrow_len = 1.0

        for m in self.miembros_arm:
            if m['inicio']==nodo['id'] or m['fin']==nodo['id']:
                other = m['fin'] if m['inicio']==nodo['id'] else m['inicio']
                n2 = node_lookup[other]
                dx = n2['x'] - nodo['x']
                dy = n2['y'] - nodo['y']
                L = (dx**2 + dy**2)**0.5
                if L == 0: continue
                u = (dx/L, dy/L)
                fuerza = m.get('fuerza', 0)
                color = 'red' if fuerza < 0 else 'blue'

                vec_x = u[0] * arrow_len * (1 if fuerza >= 0 else -1)
                vec_y = u[1] * arrow_len * (1 if fuerza >= 0 else -1)

                ax.arrow(0, 0, vec_x, vec_y, color=color, head_width=0.1, length_includes_head=True,
                         label=f"M{m['inicio']}-{m['fin']}: {fuerza:.1f} N")
                ax.text(vec_x*1.1, vec_y*1.1, f"{abs(fuerza):.1f}", color=color, ha='center', va='center')

        for c in self.cargas_arm:
            if c['nodo']==nodo['id']:
                mag = np.hypot(c['Fx'], c['Fy'])
                if mag > 0:
                    ux, uy = c['Fx']/mag, c['Fy']/mag
                    ax.arrow(0, 0, ux*arrow_len, uy*arrow_len, color='green', head_width=0.1, length_includes_head=True,
                             label=f"Carga: {mag:.1f} N")
                    ax.text(ux*arrow_len*1.1, uy*arrow_len*1.1, f"{mag:.1f}", color='green', ha='center', va='center')

        if nodo['apoyo'] in ('Fijo','Móvil') and hasattr(self,'reacciones_arm'):
            if nodo['id'] in self.reacciones_arm:
                rx, ry = self.reacciones_arm[nodo['id']]

                if abs(rx) > 0.01:
                    ax.arrow(0,0,(1 if rx > 0 else -1)*arrow_len,0,color='orange',head_width=0.1,length_includes_head=True,
                             label=f"Rx: {rx:.1f} N")
                    ax.text((1 if rx > 0 else -1)*arrow_len*1.1,0.1,f"{abs(rx):.1f}",color='orange',ha='center',va='center')

                if abs(ry) > 0.01:
                    ax.arrow(0,0,0,(1 if ry > 0 else -1)*arrow_len,color='orange',head_width=0.1,length_includes_head=True,
                             label=f"Ry: {ry:.1f} N")
                    ax.text(0.1,(1 if ry > 0 else -1)*arrow_len*1.1,f"{abs(ry):.1f}",color='orange',ha='center',va='center')

        ax.set_xlim(-1.5,1.5)
        ax.set_ylim(-1.5,1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f"DCL Nodo {nodo['id']}")

        canvas = FigureCanvasTkAgg(fig, master=ventana)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def calcular_seccion_armadura(self):
        corte = self.corte_valor.get()
        eje = self.corte_eje.get().lower()

        if not self.miembros_arm or not hasattr(self, 'reacciones_arm'):
            messagebox.showwarning("Advertencia", "Calcule primero la armadura para aplicar el método de secciones.")
            return

        node_lookup = {n['id']: n for n in self.nodos_arm}
        miembros_corte = []

        for m in self.miembros_arm:
            n1 = node_lookup[m['inicio']]
            n2 = node_lookup[m['fin']]
            p1 = n1['x'] if eje == 'x' else n1['y']
            p2 = n2['x'] if eje == 'x' else n2['y']

            if (p1 < corte < p2) or (p2 < corte < p1) or p1 == corte or p2 == corte:
                miembros_corte.append(m)

        if not miembros_corte:
            messagebox.showinfo("Sección", "Ningún miembro intersecta el corte especificado.")
            return

        self.log(f"\n{'='*50}\n", "title")
        self.log(f"📐 MÉTODO DE SECCIONES ({eje}={corte:.2f})\n", "title")
        self.log(f"{'='*50}\n", "title")
        self.log("Miembros intersectados por el corte:\n", "data")
        for m in miembros_corte:
            tipo = "tensión" if m['fuerza'] >= 0 else "compresión"
            self.log(f"  - Miembro {m['inicio']}-{m['fin']}: {m['fuerza']:.2f} N ({tipo})\n", "data")

        self.dibujar_dcl_seccion(corte, miembros_corte, eje)

    def dibujar_dcl_seccion(self, corte, miembros, eje):
        ventana = tk.Toplevel(self.root)
        ventana.title("DCL Sección")
        fig, ax = plt.subplots(figsize=(6,4))
        plt.style.use("seaborn-v0_8-whitegrid")
        node_lookup = {n['id']: n for n in self.nodos_arm}
        arrow_len = 0.8
        if eje == 'x':
            for m in self.miembros_arm:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]
                if n1['x'] <= corte and n2['x'] <= corte:
                    ax.plot([n1['x'], n2['x']], [n1['y'], n2['y']], 'k-')
            for nodo in self.nodos_arm:
                if nodo['x'] <= corte:
                    ax.plot(nodo['x'], nodo['y'], 'ko')
                    for c in self.cargas_arm:
                        if c['nodo'] == nodo['id']:
                            mag = np.hypot(c['Fx'], c['Fy'])
                            if mag:
                                ux, uy = c['Fx']/mag, -c['Fy']/mag
                                ax.arrow(nodo['x'], nodo['y'], ux*arrow_len, uy*arrow_len, color='green', head_width=0.1, length_includes_head=True)
                                ax.text(nodo['x']+ux*arrow_len, nodo['y']+uy*arrow_len, f"{mag:.1f}", color='green')
                    if nodo['apoyo'] in ('Fijo','Móvil') and hasattr(self,'reacciones_arm'):
                        rx, ry = self.reacciones_arm.get(nodo['id'], (0,0))
                        if abs(rx) > 0:
                            signx = 1 if rx >= 0 else -1
                            ax.arrow(nodo['x'], nodo['y'], signx*arrow_len, 0,
                                     color='orange', head_width=0.1,
                                     length_includes_head=True)
                            ax.text(nodo['x'] + signx*arrow_len, nodo['y'] + 0.05,
                                    f"Rx={rx:.1f}", color='orange', ha='center',
                                    va='bottom')
                        if abs(ry) > 0:
                            signy = 1 if ry >= 0 else -1
                            ax.arrow(nodo['x'], nodo['y'], 0, signy*arrow_len,
                                     color='orange', head_width=0.1,
                                     length_includes_head=True)
                            ax.text(0.1, nodo['y'] + signy*arrow_len,
                                    f"Ry={ry:.1f}", color='orange', ha='left',
                                    va='bottom' if signy > 0 else 'top')
            ax.axvline(corte, color='red', linestyle='--')
            for m in miembros:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]
                t = (corte - n1['x'])/(n2['x']-n1['x'])
                ycut = n1['y'] + t*(n2['y']-n1['y'])
                fuerza = m.get('fuerza',0)
                sign = 1 if fuerza>=0 else -1
                ax.arrow(corte, ycut, 0, sign*arrow_len, color='purple', head_width=0.1, length_includes_head=True)
                ax.text(corte, ycut+sign*arrow_len, f"{fuerza:.1f}", color='purple')
        else:
            for m in self.miembros_arm:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]
                if n1['y'] <= corte and n2['y'] <= corte:
                    ax.plot([n1['x'], n2['x']], [n1['y'], n2['y']], 'k-')
            for nodo in self.nodos_arm:
                if nodo['y'] <= corte:
                    ax.plot(nodo['x'], nodo['y'], 'ko')
                    for c in self.cargas_arm:
                        if c['nodo'] == nodo['id']:
                            mag = np.hypot(c['Fx'], c['Fy'])
                            if mag:
                                ux, uy = c['Fx']/mag, -c['Fy']/mag
                                ax.arrow(nodo['x'], nodo['y'], ux*arrow_len, uy*arrow_len, color='green', head_width=0.1, length_includes_head=True)
                                ax.text(nodo['x']+ux*arrow_len, nodo['y']+uy*arrow_len, f"{mag:.1f}", color='green')
                    if nodo['apoyo'] in ('Fijo','Móvil') and hasattr(self,'reacciones_arm'):
                        rx, ry = self.reacciones_arm.get(nodo['id'], (0,0))
                        if abs(rx) > 0:
                            signx = 1 if rx >= 0 else -1
                            ax.arrow(nodo['x'], nodo['y'], signx*arrow_len, 0,
                                     color='orange', head_width=0.1,
                                     length_includes_head=True)
                            ax.text(nodo['x'] + signx*arrow_len, nodo['y'] + 0.05,
                                    f"Rx={rx:.1f}", color='orange', ha='center',
                                    va='bottom')
                        if abs(ry) > 0:
                            signy = 1 if ry >= 0 else -1
                            ax.arrow(nodo['x'], nodo['y'], 0, signy*arrow_len,
                                     color='orange', head_width=0.1,
                                     length_includes_head=True)
                            ax.text(0.1, (1 if ry > 0 else -1)*arrow_len*1.1,f"{abs(ry):.1f}",color='orange',ha='center',va='center')
            ax.axhline(corte, color='red', linestyle='--')
            for m in miembros:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]
                t = (corte - n1['y'])/(n2['y']-n1['y'])
                xcut = n1['x'] + t*(n2['x']-n1['x'])
                fuerza = m.get('fuerza',0)
                sign = 1 if fuerza>=0 else -1
                ax.arrow(xcut, corte, sign*arrow_len, 0, color='purple', head_width=0.1, length_includes_head=True)
                ax.text(xcut+sign*arrow_len, corte, f"{fuerza:.1f}", color='purple')
        ax.set_aspect('equal')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title('Diagrama de Cuerpo Libre de la Sección')
        ax.margins(0.2)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=ventana)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def mostrar_instrucciones_armadura(self):
        texto = (
            "PASOS PARA ANALIZAR UNA ARMADURA:\n"
            "1. Agregue los nodos indicando sus coordenadas y tipo de apoyo.\n"
            "   (Ej: Nodo 1: X=0, Y=0, Apoyo=Fijo)\n"
            "2. Defina los miembros especificando el ID del nodo inicial y final.\n"
            "   (Ej: Miembro 1-2 conecta el nodo 1 con el nodo 2)\n"
            "3. Coloque las cargas en los nodos correspondientes, indicando componentes Fx y Fy.\n"
            "   (Ej: Carga en Nodo 2: Fx=0, Fy=-1000)\n"
            "4. Presione 'Calcular Armadura' para obtener las fuerzas internas en cada miembro y las reacciones.\n"
            "   Las barras en rojo están en compresión y en azul en tensión.\n"
            "   Las reacciones se muestran en naranja en los apoyos.\n"
            "5. Use 'DCL Nodos' para ver el diagrama de cuerpo libre de cada nodo.\n"
            "6. Use 'Método de Secciones' para analizar las fuerzas en un corte específico."
        )
        messagebox.showinfo("Instrucciones Armaduras", texto)

    def agregar_nodo_bastidor(self):
        x = self.nodo_x_bast.get()
        y = self.nodo_y_bast.get()
        apoyo = self.nodo_apoyo_bast.get()
        pas = self.nodo_pasadores_bast.get()
        self.nodos_bast.append({'id': self.id_nodo_bast, 'x': x, 'y': y,
                                'apoyo': apoyo, 'pasadores': pas})
        self.log(f"Nodo {self.id_nodo_bast} agregado en ({x}, {y}) con {pas} pasadores\n", "data")
        self.id_nodo_bast += 1
        self.dibujar_bastidor()

    def agregar_miembro_bastidor(self):
        ini = self.miembro_inicio_bast.get()
        fin = self.miembro_fin_bast.get()
        if not any(n['id'] == ini for n in self.nodos_bast) or not any(n['id'] == fin for n in self.nodos_bast):
            messagebox.showerror("Error", "Los nodos inicial y final deben existir.")
            return

        self.miembros_bast.append({'inicio': ini, 'fin': fin, 'fuerza': 0.0})
        self.log(f"Miembro {ini}-{fin} agregado\n", "data")
        self.dibujar_bastidor()

    def agregar_carga_bastidor(self):
        nodo = self.carga_nodo_bast.get()
        fx = self.carga_fx_bast.get()
        fy = self.carga_fy_bast.get()
        if not any(n['id'] == nodo for n in self.nodos_bast):
            messagebox.showerror("Error", "El nodo al que se aplica la carga debe existir.")
            return
        self.cargas_bast.append({'nodo': nodo, 'Fx': fx, 'Fy': fy})
        self.log(f"Carga en nodo {nodo}: Fx={fx}, Fy={fy}\n", "data")
        self.dibujar_bastidor()

    def cargar_ejemplo_bastidor(self):
        """Carga un bastidor de ejemplo y muestra inmediatamente sus resultados."""
        # Reiniciar listas
        self.nodos_bast.clear()
        self.miembros_bast.clear()
        self.cargas_bast.clear()
        self.id_nodo_bast = 1

        # Definir nodos (portal simple)
        self.nodos_bast.append({'id': 1, 'x': 0.0, 'y': 0.0,
                                'apoyo': 'Fijo', 'pasadores': 1})
        self.nodos_bast.append({'id': 2, 'x': 4.0, 'y': 0.0,
                                'apoyo': 'Fijo', 'pasadores': 1})
        self.nodos_bast.append({'id': 3, 'x': 0.0, 'y': 3.0,
                                'apoyo': 'Libre', 'pasadores': 1})
        self.nodos_bast.append({'id': 4, 'x': 4.0, 'y': 3.0,
                                'apoyo': 'Libre', 'pasadores': 1})
        self.id_nodo_bast = 5

        # Miembros
        self.miembros_bast.append({'inicio': 1, 'fin': 3, 'fuerza': 0.0})
        self.miembros_bast.append({'inicio': 3, 'fin': 4, 'fuerza': 0.0})
        self.miembros_bast.append({'inicio': 4, 'fin': 2, 'fuerza': 0.0})
        self.miembros_bast.append({'inicio': 1, 'fin': 2, 'fuerza': 0.0})

        # Carga en el nodo superior derecho
        self.cargas_bast.append({'nodo': 4, 'Fx': 0.0, 'Fy': -1000.0})

        self.log("\nEjemplo de bastidor cargado.\n", "title")
        self.dibujar_bastidor()
        self.calcular_bastidor()

    def calcular_bastidor(self):
        try:
            if not self.nodos_bast or not self.miembros_bast:
                messagebox.showwarning("Advertencia", "Agrega nodos y miembros a la bastidor primero.")
                return

            fuerzas, reacciones, num_vars, num_eqs = self.resolver_articulado(
                self.nodos_bast, self.miembros_bast, self.cargas_bast)

            if num_vars > num_eqs:
                messagebox.showwarning(
                    "Advertencia",
                    "El bastidor es estáticamente indeterminada. Puede que no tenga una solución única o sea inestable.",
                )
            elif num_vars < num_eqs:
                messagebox.showwarning(
                    "Advertencia",
                    "El bastidor es estáticamente sobredeterminada. Puede que no sea soluble con las condiciones dadas.",
                )

            for j, m in enumerate(self.miembros_bast):
                m['fuerza'] = fuerzas[j]

            self.reacciones_bast = reacciones

            self.log(f"\n{'='*50}\n", "title")
            self.log("📐 ANÁLISIS DE BASTIDOR:\n", "title")
            self.log(f"{'='*50}\n", "title")
            for j, m in enumerate(self.miembros_bast):
                tipo = "tensión" if m['fuerza'] >= 0 else "compresión"
                self.log(f"Miembro {m['inicio']}-{m['fin']}: {m['fuerza']:.2f} N ({tipo})\n", "data")

            for nid, r in self.reacciones_bast.items():
                self.log(f"Reacciones nodo {nid}: Rx={r[0]:.2f} N, Ry={r[1]:.2f} N\n", "data")

            self.dibujar_bastidor()

            # Mostrar fuerzas resultantes en cada nodo y por pasador
            self.mostrar_fuerzas_pasadores()

        except np.linalg.LinAlgError as e:
            messagebox.showerror("Error de Cálculo", f"El sistema de ecuaciones no pudo resolverse (singular o mal condicionado): {e}. Verifica la estabilidad del bastidor.")
        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculo de bastidor: {e}")

    def calcular_fuerza_nodo_bastidor(self):
        """Calcula y muestra la suma de fuerzas en un nodo específico."""
        nodo_id = self.nodo_fuerza_bast.get()

        if not self.miembros_bast or not hasattr(self, 'reacciones_bast'):
            messagebox.showwarning("Advertencia", "Calcule primero el bastidor.")
            return

        if not any(n['id'] == nodo_id for n in self.nodos_bast):
            messagebox.showerror("Error", "El nodo seleccionado no existe.")
            return

        node_lookup = {n['id']: n for n in self.nodos_bast}
        fx_total = 0.0
        fy_total = 0.0

        for c in self.cargas_bast:
            if c['nodo'] == nodo_id:
                fx_total += c['Fx']
                fy_total += c['Fy']

        if nodo_id in self.reacciones_bast:
            rx, ry = self.reacciones_bast[nodo_id]
            fx_total += rx
            fy_total += ry

        for m in self.miembros_bast:
            if m['inicio'] == nodo_id or m['fin'] == nodo_id:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]
                dx = n2['x'] - n1['x']
                dy = n2['y'] - n1['y']
                L = (dx**2 + dy**2) ** 0.5
                if L == 0:
                    continue
                ux = dx / L
                uy = dy / L
                sign = 1 if m['fin'] == nodo_id else -1
                fx_total += sign * m['fuerza'] * ux
                fy_total += sign * m['fuerza'] * uy

        self.log(f"\nFuerzas en nodo {nodo_id}: Fx={fx_total:.2f} N, Fy={fy_total:.2f} N\n", "data")

        total = (fx_total ** 2 + fy_total ** 2) ** 0.5
        n_pas = node_lookup[nodo_id].get('pasadores', 1)
        if n_pas <= 0:
            n_pas = 1
        fuerza_pasador = total / n_pas
        self.log(f"Fuerza por pasador ({n_pas}): {fuerza_pasador:.2f} N\n", "data")

    def obtener_fuerzas_nodo_bastidor(self, nodo_id):
        """Devuelve la resultante Fx,Fy en un nodo del bastidor."""
        node_lookup = {n['id']: n for n in self.nodos_bast}
        fx_total = 0.0
        fy_total = 0.0
        for c in self.cargas_bast:
            if c['nodo'] == nodo_id:
                fx_total += c['Fx']
                fy_total += c['Fy']

        if nodo_id in self.reacciones_bast:
            rx, ry = self.reacciones_bast[nodo_id]
            fx_total += rx
            fy_total += ry

        for m in self.miembros_bast:
            if m['inicio'] == nodo_id or m['fin'] == nodo_id:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]
                dx = n2['x'] - n1['x']
                dy = n2['y'] - n1['y']
                L = (dx**2 + dy**2) ** 0.5
                if L == 0:
                    continue
                ux = dx / L
                uy = dy / L
                sign = 1 if m['fin'] == nodo_id else -1
                fx_total += sign * m['fuerza'] * ux
                fy_total += sign * m['fuerza'] * uy

        return fx_total, fy_total

    def mostrar_fuerzas_pasadores(self):
        """Muestra en el registro las fuerzas en cada nodo y por pasador."""
        for nodo in self.nodos_bast:
            fx, fy = self.obtener_fuerzas_nodo_bastidor(nodo['id'])
            self.log(f"Fuerzas en nodo {nodo['id']}: Fx={fx:.2f} N, Fy={fy:.2f} N\n", "data")
            total = (fx**2 + fy**2) ** 0.5
            n_pas = nodo.get('pasadores', 1)
            if n_pas <= 0:
                n_pas = 1
            fuerza_pasador = total / n_pas
            self.log(f"Fuerza por pasador ({n_pas}): {fuerza_pasador:.2f} N\n", "data")

    def ajustar_vista_bastidor(self):
        if not hasattr(self, 'canvas_bastidor') or not self.nodos_bast:
            self.escala_bast = 20
            self.offset_x_bast = 50
            self.offset_y_bast = 350
            return

        c = self.canvas_bastidor
        width = c.winfo_width() if c.winfo_width() > 1 else int(c['width'])
        height = c.winfo_height() if c.winfo_height() > 1 else int(c['height'])

        margin = 50
        xs = [n['x'] for n in self.nodos_bast]
        ys = [n['y'] for n in self.nodos_bast]
        if not xs:
            self.escala_bast = 20
            self.offset_x_bast = width / 2
            self.offset_y_bast = height / 2
            return

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        rango_x = max(max_x - min_x, 1e-6)
        rango_y = max(max_y - min_y, 1e-6)

        escala_x = (width - 2 * margin) / rango_x
        escala_y = (height - 2 * margin) / rango_y

        self.escala_bast = min(escala_x, escala_y)

        self.offset_x_bast = margin - min_x * self.escala_bast + (width - 2 * margin - rango_x * self.escala_bast) / 2
        self.offset_y_bast = height - margin + min_y * self.escala_bast - (height - 2 * margin - rango_y * self.escala_bast) / 2

    def dibujar_bastidor(self):
        if not hasattr(self, 'canvas_bastidor'):
            return
        c = self.canvas_bastidor
        self.ajustar_vista_bastidor()
        c.delete('all')

        fig, ax = plt.subplots(figsize=(6, 5)) # Crear figura de Matplotlib para la representación
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('Coordenada X')
        ax.set_ylabel('Coordenada Y')
        ax.set_title('Bastidor')

        node_coords = {} # Para almacenar coordenadas matplotlib para el texto
        for nodo in self.nodos_bast:
            x_mpl = nodo['x']
            y_mpl = nodo['y']
            node_coords[nodo['id']] = (x_mpl, y_mpl)
            ax.plot(x_mpl, y_mpl, 'ko', markersize=8) # Nodos
            ax.text(x_mpl, y_mpl + 0.2, str(nodo['id']), ha='center', va='bottom', fontsize=8)

            # Dibujar apoyos
            if nodo['apoyo'] == 'Fijo':
                ax.plot([x_mpl - 0.2, x_mpl + 0.2], [y_mpl - 0.2, y_mpl - 0.2], 'b-', linewidth=2)
                ax.plot(x_mpl, y_mpl - 0.2, '^', markersize=10, color='blue')
            elif nodo['apoyo'] == 'Móvil':
                ax.plot([x_mpl - 0.2, x_mpl + 0.2], [y_mpl - 0.2, y_mpl - 0.2], 'b-', linewidth=2)
                ax.plot(x_mpl, y_mpl - 0.2, 'o', markersize=10, color='blue')

        for m in self.miembros_bast:
            n1 = node_coords[m['inicio']]
            n2 = node_coords[m['fin']]

            color = 'black'
            if 'fuerza' in m:
                color = 'red' if m['fuerza'] < 0 else 'blue'

            ax.plot([n1[0], n2[0]], [n1[1], n2[1]], color=color, linewidth=2)

            if 'fuerza' in m:
                mid_x = (n1[0]+n2[0])/2
                mid_y = (n1[1]+n2[1])/2
                # Añadir un fondo blanco al texto de la fuerza del miembro
                ax.text(mid_x, mid_y, f"{m['fuerza']:.1f} N", color=color, fontsize=8,
                        ha='center', va='center', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

        arrow_len_scale = 0.5 # Escala para el tamaño de las flechas de carga
        for carg in self.cargas_bast:
            nodo = node_coords[carg['nodo']]
            fx = carg['Fx']
            fy = carg['Fy']
            mag = (fx**2 + fy**2) ** 0.5
            if mag > 0:
                ux, uy = fx / mag, fy / mag
                # Ajustar el origen de la flecha para que se vea bien
                arrow_start_x = nodo[0] - ux * 0.1 # Un pequeño offset para que la flecha no empiece exactamente en el nodo
                arrow_start_y = nodo[1] - uy * 0.1
                ax.arrow(arrow_start_x, arrow_start_y, ux * arrow_len_scale, uy * arrow_len_scale,
                         head_width=0.1, head_length=0.15, fc='green', ec='green',
                         length_includes_head=True)
                ax.text(nodo[0] + ux * (arrow_len_scale + 0.1), nodo[1] + uy * (arrow_len_scale + 0.1),
                        f"{mag:.1f} N", color='green', fontsize=8, ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

        if hasattr(self, 'reacciones_bast'):
            reaction_arrow_len_scale = 0.6
            for nodo_id, r in self.reacciones_bast.items():
                nodo = node_coords[nodo_id]
                rx, ry = r
                if abs(rx) > 0.01:
                    ax.arrow(nodo[0], nodo[1], (1 if rx > 0 else -1) * reaction_arrow_len_scale, 0,
                             head_width=0.1, head_length=0.15, fc='orange', ec='orange',
                             length_includes_head=True)
                    ax.text(nodo[0] + (1 if rx > 0 else -1) * reaction_arrow_len_scale * 1.1, nodo[1],
                            f"Rx={rx:.1f}", color='orange', fontsize=8, ha='center', va='center',
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))
                if abs(ry) > 0.01:
                    ax.arrow(nodo[0], nodo[1], 0, (1 if ry > 0 else -1) * reaction_arrow_len_scale,
                             head_width=0.1, head_length=0.15, fc='orange', ec='orange',
                             length_includes_head=True)
                    ax.text(nodo[0], nodo[1] + (1 if ry > 0 else -1) * reaction_arrow_len_scale * 1.1,
                            f"Ry={ry:.1f}", color='orange', fontsize=8, ha='center', va='center',
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

        ax.autoscale_view()
        ax.margins(0.2)
        plt.tight_layout()

        # Limpiar el canvas de Tkinter y dibujar la figura de Matplotlib
        for widget in c.winfo_children():
            widget.destroy()
        canvas_widget = FigureCanvasTkAgg(fig, master=c)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(fill="both", expand=True)

        self.ultima_figura = fig # Guardar la figura para la función de ampliar

    def mostrar_dcl_nodos_bastidor(self):
        if not self.miembros_bast or not hasattr(self, 'reacciones_bast'):
            messagebox.showwarning("Advertencia", "Calcule primero el bastidor para ver los DCLs.")
            return
        for nodo in self.nodos_bast:
            self.dibujar_dcl_nodo_bastidor(nodo)

    def dibujar_dcl_nodo_bastidor(self, nodo):
        ventana = tk.Toplevel(self.root)
        ventana.title(f"DCL Nodo {nodo['id']}")
        fig, ax = plt.subplots(figsize=(4,4))

        ax.plot(0,0,'ko', markersize=8)
        ax.text(0, 0.2, f"Nodo {nodo['id']}", ha='center', va='bottom', fontsize=10, fontweight='bold')

        node_lookup = {n['id']: n for n in self.nodos_bast}
        arrow_len = 1.0

        for m in self.miembros_bast:
            if m['inicio']==nodo['id'] or m['fin']==nodo['id']:
                other = m['fin'] if m['inicio']==nodo['id'] else m['inicio']
                n2 = node_lookup[other]
                dx = n2['x'] - nodo['x']
                dy = n2['y'] - nodo['y']
                L = (dx**2 + dy**2)**0.5
                if L == 0: continue
                u = (dx/L, dy/L)
                fuerza = m.get('fuerza', 0)
                color = 'red' if fuerza < 0 else 'blue'

                vec_x = u[0] * arrow_len * (1 if fuerza >= 0 else -1)
                vec_y = u[1] * arrow_len * (1 if fuerza >= 0 else -1)

                ax.arrow(0, 0, vec_x, vec_y, color=color, head_width=0.1, length_includes_head=True)
                ax.text(vec_x*1.1, vec_y*1.1, f"{abs(fuerza):.1f}", color=color, ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

        for c in self.cargas_bast:
            if c['nodo']==nodo['id']:
                mag = np.hypot(c['Fx'], c['Fy'])
                if mag > 0:
                    ux, uy = c['Fx']/mag, c['Fy']/mag
                    ax.arrow(0, 0, ux*arrow_len, uy*arrow_len, color='green', head_width=0.1, length_includes_head=True)
                    ax.text(ux*arrow_len*1.1, uy*arrow_len*1.1, f"{mag:.1f}", color='green', ha='center', va='center',
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

        if nodo['apoyo'] in ('Fijo','Móvil') and hasattr(self,'reacciones_bast'):
            if nodo['id'] in self.reacciones_bast:
                rx, ry = self.reacciones_bast[nodo['id']]
                if abs(rx) > 0.01:
                    ax.arrow(0, 0, (1 if rx > 0 else -1) * arrow_len, 0, color='orange', head_width=0.1, length_includes_head=True)
                    ax.text((1 if rx > 0 else -1) * arrow_len * 1.1, 0.1, f"{abs(rx):.1f}", color='orange', ha='center', va='center',
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco
                if abs(ry) > 0.01:
                    ax.arrow(0, 0, 0, (1 if ry > 0 else -1) * arrow_len, color='orange', head_width=0.1, length_includes_head=True)
                    ax.text(0.1, (1 if ry > 0 else -1) * arrow_len * 1.1, f"{abs(ry):.1f}", color='orange', ha='center', va='center',
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

        ax.set_xlim(-1.5,1.5)
        ax.set_ylim(-1.5,1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f"DCL Nodo {nodo['id']}")

        canvas = FigureCanvasTkAgg(fig, master=ventana)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def calcular_seccion_bastidor(self):
        corte = self.corte_valor_bast.get()
        eje = self.corte_eje_bast.get().lower()

        if not self.miembros_bast or not hasattr(self, 'reacciones_bast'):
            messagebox.showwarning("Advertencia", "Calcule primero el bastidor para aplicar el método de secciones.")
            return

        node_lookup = {n['id']: n for n in self.nodos_bast}
        miembros_corte = []

        for m in self.miembros_bast:
            n1 = node_lookup[m['inicio']]
            n2 = node_lookup[m['fin']]

            p1 = n1['x'] if eje == 'x' else n1['y']
            p2 = n2['x'] if eje == 'x' else n2['y']

            if (p1 < corte < p2) or (p2 < corte < p1) or p1 == corte or p2 == corte:
                miembros_corte.append(m)

        self.log(f"\n{'='*50}\n", "title")
        self.log(f"📐 MÉTODO DE SECCIONES ({eje}={corte:.2f})\n", "title")
        self.log(f"{'='*50}\n", "title")

        if not miembros_corte:
            self.log("Ningún miembro intersecta el corte especificado.\n", "data")
            self.dibujar_dcl_seccion_bastidor(corte, [], eje)
            return

        self.log("Miembros intersectados por el corte:\n", "data")
        for m in miembros_corte:
            tipo = "tensión" if m['fuerza'] >= 0 else "compresión"
            self.log(f"  - Miembro {m['inicio']}-{m['fin']}: {m['fuerza']:.2f} N ({tipo})\n", "data")

        self.dibujar_dcl_seccion_bastidor(corte, miembros_corte, eje)

    def dibujar_dcl_seccion_bastidor(self, corte, miembros_cortados, eje):
        ventana = tk.Toplevel(self.root)
        ventana.title("Diagrama de Cuerpo Libre de la Sección")
        fig, ax = plt.subplots(figsize=(8, 6))
        plt.style.use("seaborn-v0_8-whitegrid")

        node_lookup = {n['id']: n for n in self.nodos_bast}
        arrow_scale = 0.8

        if eje == 'x':
            ax.axvline(corte, color='red', linestyle='--', linewidth=2, label=f'Corte en X={corte:.2f}')

            for m in self.miembros_bast:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]

                if n1['x'] <= corte and n2['x'] <= corte:
                    ax.plot([n1['x'], n2['x']], [n1['y'], n2['y']], 'k-', linewidth=1.5, alpha=0.7)

            for nodo in self.nodos_bast:
                if nodo['x'] <= corte:
                    ax.plot(nodo['x'], nodo['y'], 'ko', markersize=6)
                    ax.text(nodo['x'], nodo['y']+0.2, str(nodo['id']), fontsize=8, ha='center', va='bottom')

                    for c in self.cargas_bast:
                        if c['nodo'] == nodo['id']:
                            mag_c = np.hypot(c['Fx'], c['Fy'])
                            if mag_c > 0:
                                ux_c, uy_c = c['Fx']/mag_c, c['Fy']/mag_c
                                ax.arrow(nodo['x'], nodo['y'], ux_c*arrow_scale, uy_c*arrow_scale, color='green', head_width=0.08, length_includes_head=True)
                                ax.text(nodo['x'] + ux_c*arrow_scale*1.1, nodo['y'] + uy_c*arrow_scale*1.1, f"{mag_c:.1f}", color='green', fontsize=7, ha='center', va='center',
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

                    if nodo['apoyo'] in ('Fijo', 'Móvil') and hasattr(self, 'reacciones_bast'):
                        if nodo['id'] in self.reacciones_bast:
                            rx, ry = self.reacciones_bast[nodo['id']]
                            if abs(rx) > 0.01:
                                ax.arrow(nodo['x'], nodo['y'], (1 if rx > 0 else -1) * arrow_scale, 0, color='orange', head_width=0.08, length_includes_head=True)
                                ax.text(nodo['x'] + (1 if rx > 0 else -1) * arrow_scale * 1.1, nodo['y'] + 0.1, f"{abs(rx):.1f}", color='orange', fontsize=7, ha='center', va='center',
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco
                            if abs(ry) > 0.01:
                                ax.arrow(nodo['x'], nodo['y'], 0, (1 if ry > 0 else -1) * arrow_scale, color='orange', head_width=0.08, length_includes_head=True)
                                ax.text(nodo['x'] + 0.1, nodo['y'] + (1 if ry > 0 else -1) * arrow_scale * 1.1, f"{abs(ry):.1f}", color='orange', fontsize=7, ha='center', va='center',
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

            for m in miembros_cortados:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]

                if (n2['x'] - n1['x']) == 0:
                    x_cut = corte
                    y_cut = (n1['y'] + n2['y']) / 2
                else:
                    slope = (n2['y'] - n1['y']) / (n2['x'] - n1['x'])
                    y_cut = n1['y'] + slope * (corte - n1['x'])
                    x_cut = corte

                fuerza = m.get('fuerza', 0)
                color = 'red' if fuerza < 0 else 'blue'

                dx = n2['x'] - n1['x']
                dy = n2['y'] - n1['y']
                mag_m = (dx**2 + dy**2)**0.5
                if mag_m == 0: continue
                ux_m, uy_m = dx / mag_m, dy / mag_m

                vec_x = ux_m * arrow_scale * (1 if fuerza >= 0 else -1)
                vec_y = uy_m * arrow_scale * (1 if fuerza >= 0 else -1)

                ax.arrow(x_cut, y_cut, vec_x, vec_y, color=color, head_width=0.08, length_includes_head=True)
                ax.text(x_cut + vec_x*1.1, y_cut + vec_y*1.1, f"{abs(fuerza):.1f}", color=color, fontsize=7, ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

        elif eje == 'y':
            ax.axhline(corte, color='red', linestyle='--', linewidth=2, label=f'Corte en Y={corte:.2f}')

            for m in self.miembros_bast:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]

                if n1['y'] <= corte and n2['y'] <= corte:
                    ax.plot([n1['x'], n2['x']], [n1['y'], n2['y']], 'k-', linewidth=1.5, alpha=0.7)

            for nodo in self.nodos_bast:
                if nodo['y'] <= corte:
                    ax.plot(nodo['x'], nodo['y'], 'ko', markersize=6)
                    ax.text(nodo['x'], nodo['y']+0.2, str(nodo['id']), fontsize=8, ha='center', va='bottom')

                    for c in self.cargas_bast:
                        if c['nodo'] == nodo['id']:
                            mag_c = np.hypot(c['Fx'], c['Fy'])
                            if mag_c > 0:
                                ux_c, uy_c = c['Fx']/mag_c, c['Fy']/mag_c
                                ax.arrow(nodo['x'], nodo['y'], ux_c*arrow_scale, uy_c*arrow_scale, color='green', head_width=0.08, length_includes_head=True)
                                ax.text(nodo['x'] + ux_c*arrow_scale*1.1, nodo['y'] + uy_c*arrow_scale*1.1, f"{mag_c:.1f}", color='green', fontsize=7, ha='center', va='center',
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

                    if nodo['apoyo'] in ('Fijo', 'Móvil') and hasattr(self, 'reacciones_bast'):
                        if nodo['id'] in self.reacciones_bast:
                            rx, ry = self.reacciones_bast[nodo['id']]
                            if abs(rx) > 0.01:
                                ax.arrow(nodo['x'], nodo['y'], (1 if rx > 0 else -1) * arrow_scale, 0, color='orange', head_width=0.08, length_includes_head=True)
                                ax.text(nodo['x'] + (1 if rx > 0 else -1) * arrow_scale * 1.1, nodo['y'] + 0.1, f"{abs(rx):.1f}", color='orange', fontsize=7, ha='center', va='center',
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco
                            if abs(ry) > 0.01:
                                ax.arrow(nodo['x'], nodo['y'], 0, (1 if ry > 0 else -1) * arrow_scale, color='orange', head_width=0.08, length_includes_head=True)
                                ax.text(0.1, (1 if ry > 0 else -1) * arrow_scale * 1.1, f"{abs(ry):.1f}", color='orange', fontsize=7, ha='center', va='center',
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

            for m in miembros_cortados:
                n1 = node_lookup[m['inicio']]
                n2 = node_lookup[m['fin']]

                if (n2['y'] - n1['y']) == 0:
                    y_cut = corte
                    x_cut = (n1['x'] + n2['x']) / 2
                else:
                    slope_inv = (n2['x'] - n1['x']) / (n2['y'] - n1['y'])
                    x_cut = n1['x'] + slope_inv * (corte - n1['y'])
                    y_cut = corte

                fuerza = m.get('fuerza', 0)
                color = 'red' if fuerza < 0 else 'blue'

                dx = n2['x'] - n1['x']
                dy = n2['y'] - n1['y']
                mag_m = (dx**2 + dy**2)**0.5
                if mag_m == 0: continue
                ux_m, uy_m = dx / mag_m, dy / mag_m

                vec_x = ux_m * arrow_scale * (1 if fuerza >= 0 else -1)
                vec_y = uy_m * arrow_scale * (1 if fuerza >= 0 else -1)

                ax.arrow(x_cut, y_cut, vec_x, vec_y, color=color, head_width=0.08, length_includes_head=True)
                ax.text(x_cut + vec_x*1.1, y_cut + vec_y*1.1, f"{abs(fuerza):.1f}", color=color, fontsize=7, ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')) # Fondo blanco

        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('Coordenada X')
        ax.set_ylabel('Coordenada Y')
        ax.set_title('Diagrama de Cuerpo Libre de la Sección')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=ventana)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def mostrar_instrucciones_bastidor(self):
        """Mostrar guía de uso para el análisis de bastidores."""
        texto = (
            "PASOS PARA ANALIZAR UN BASTIDOR:\n"
            "1. Agregue los nodos indicando sus coordenadas y el tipo de apoyo (Libre, Fijo o Móvil).\n"
            "2. Defina los miembros especificando el ID del nodo inicial y final.\n"
            "3. Coloque las cargas sobre los nodos correspondientes, indicando las componentes Fx y Fy.\n"
            "4. Presione 'Calcular Bastidor' para obtener las fuerzas internas en cada miembro y las reacciones en los apoyos.\n"
            "   Las barras en rojo indican compresión y en azul tensión.\n"
            "5. Utilice 'DCL Nodos' para visualizar el diagrama de cuerpo libre de cada nodo.\n"
            "6. El botón 'Método de Secciones' permite mostrar el DCL de una porción del bastidor.\n"
            "7. El botón 'Ejemplo' carga un bastidor de muestra y calcula sus resultados automáticamente.\n"
            "\nLimitaciones: el análisis está pensado para bastidores planos de dos dimensiones, "
            "con miembros de dos fuerzas y uniones mediante pasadores lisos. "
            "Si el bastidor es indeterminado o inestable, el programa mostrará una advertencia y los resultados pueden no ser únicos."
        )
        messagebox.showinfo("Instrucciones Bastidores", texto)

    def obtener_forma_en(self, x, y):
        """Devuelve el índice de la forma que contiene el punto (x, y) o None."""
        for i, (tipo, fx, fy, ancho, alto) in enumerate(self.formas):
            if tipo == "Rectángulo":
                # Rectangle(x, y, width, height) donde (x,y) es la esquina inferior izquierda
                # Convertir a (x,y) de la esquina superior izquierda si se almacena así para el canvas
                # Si se almacena como esquina superior izquierda, y = y_superior
                # Entonces el rango es y_superior a y_superior + alto
                # Para un punto (x_click, y_click)
                if fx <= x <= fx + ancho and fy <= y <= fy + alto:
                    return i
            elif tipo == "Triángulo":
                # Asumiendo que el triángulo se almacena como (x, y) del vértice superior y (ancho, alto)
                # La base está en y+alto, y el ancho se extiende de x-ancho/2 a x+ancho/2
                # O si (x,y) es la esquina superior izquierda del bounding box:
                # Vértices: (x, y+alto), (x+ancho/2, y), (x+ancho, y+alto)
                # Para el clic, verificar dentro del bounding box (x a x+ancho, y a y+alto)
                if fx <= x <= fx + ancho and fy <= y <= fy + alto:
                    # Una comprobación más precisa para un triángulo rectángulo con la esquina superior izquierda en (fx, fy) y base en y+alto
                    # O un triángulo isósceles con el vértice superior en (fx, fy) y base en y+alto
                    # Simplificamos para el clic, considerando el bounding box.
                    # Si el triángulo tiene su vértice superior en (fx, fy) y base horizontal en (fy+alto)
                    # puntos: (fx,fy), (fx - ancho/2, fy+alto), (fx + ancho/2, fy+alto)
                    # La forma de almacenar y dibujar el triángulo es crucial aquí.
                    # En la funcion dibujar_forma_canvas, se usa (x, y+alto), (x+ancho/2, y), (x+ancho, y+alto)
                    # Esto implica que 'x,y' es la esquina superior izquierda del "bounding box" del triángulo.
                    # Así que el clic debe estar dentro de (x, y) a (x+ancho, y+alto).
                    # La verificación de punto en triángulo es más compleja para un triángulo genérico,
                    # pero para este caso simple de un triángulo que ocupa un rectángulo (x,y)-(x+ancho,y+alto),
                    # y si el clic está dentro del rectángulo, lo seleccionamos.
                    # Para un triángulo dibujado como (x, y+alto), (x+ancho/2, y), (x+ancho, y+alto)
                    # La ecuación de la línea que va del vértice superior (x+ancho/2, y) a la esquina inferior izquierda (x, y+alto) es:
                    # y' - y = ( (y+alto) - y ) / ( x - (x+ancho/2) ) * (x' - (x+ancho/2))
                    # y' - y = alto / (-ancho/2) * (x' - x - ancho/2)
                    # similarmente para el lado derecho.
                    # Para simplificar, si está dentro del rectángulo que lo encierra, lo consideramos.
                    return i
            elif tipo == "Círculo":
                # Asumimos que (fx, fy) es el centro del círculo y ancho/2 es el radio.
                radius = ancho / 2
                if (x - fx)**2 + (y - fy)**2 <= radius**2:
                    return i
        return None

    def iniciar_accion_formas(self, event):
        # Primero intentamos seleccionar una forma existente para arrastrar o escalar
        indice = self.obtener_forma_en(event.x, event.y)
        if indice is not None:
            # Si el botón presionado es el izquierdo (para arrastrar)
            if event.num == 1:
                self.forma_seleccionada = indice
                tipo, fx, fy, ancho, alto = self.formas[indice]
                self.desplazamiento_x = event.x - fx
                self.desplazamiento_y = event.y - fy # Y debe ser relativa a la esquina superior izquierda
            # Si el botón presionado es el derecho (para escalar)
            elif event.num == 3:
                self.iniciar_escalado_forma(event)
        else:
            # Si no se seleccionó ninguna forma, y es un clic izquierdo, intenta colocar una nueva
            if event.num == 1:
                try:
                    tipo = self.tipo_forma.get()
                    # Si los campos de ancho/alto están vacíos, usar valores por defecto
                    ancho_val = float(self.ancho_forma.get()) if self.ancho_forma.get() else 50
                    alto_val = float(self.alto_forma.get()) if self.alto_forma.get() else 50

                    x_click = event.x
                    y_click = event.y

                    # Para Rectángulo y Triángulo, (x_click, y_click) es la esquina superior izquierda del bounding box.
                    # Para Círculo, (x_click, y_click) es el centro.
                    self.formas.append((tipo, x_click, y_click, ancho_val, alto_val))
                    self.redibujar_formas()
                    self.log(f"Forma agregada: {tipo} en ({x_click}, {y_click})\n", "data")
                except ValueError as e:
                    messagebox.showerror("Error", f"Valores inválidos: {e}")

    def arrastrar_forma(self, event):
        if self.forma_seleccionada is None:
            return
        tipo, _, _, ancho, alto = self.formas[self.forma_seleccionada]
        nuevo_x = event.x - self.desplazamiento_x
        nuevo_y = event.y - self.desplazamiento_y
        self.formas[self.forma_seleccionada] = (tipo, nuevo_x, nuevo_y, ancho, alto)
        self.redibujar_formas()

    def soltar_forma(self, event):
        self.forma_seleccionada = None

    def escalar_forma(self, event):
        # Esta función es para el escalado con la rueda del ratón
        indice_seleccionado = self.obtener_forma_en(event.x, event.y)
        if indice_seleccionado is None:
            return
        tipo, x, y, ancho, alto = self.formas[indice_seleccionado]

        # Determinar el factor de escala (rueda arriba = zoom in, rueda abajo = zoom out)
        # event.delta es 120 o -120 en Windows, event.num 4 o 5 en Linux/macOS
        factor = 1.1 if (event.delta > 0 or event.num == 4) else 0.9

        # Calcular nuevas dimensiones
        nuevo_ancho = max(1, ancho * factor)
        nuevo_alto = max(1, alto * factor)

        if tipo == "Círculo":
            # Para círculos, ancho y alto son iguales (diámetro)
            nuevo_ancho = nuevo_alto = max(nuevo_ancho, nuevo_alto)
            # El centro (x,y) no cambia.
            self.formas[indice_seleccionado] = (tipo, x, y, nuevo_ancho, nuevo_alto)
        else:
            # Para rectángulos y triángulos, escalar desde la esquina superior izquierda (x,y)
            # Esto mantiene la esquina superior izquierda fija y expande hacia la derecha y abajo
            self.formas[indice_seleccionado] = (tipo, x, y, nuevo_ancho, nuevo_alto)

        self.redibujar_formas()


    def iniciar_escalado_forma(self, event):
        # Esta función es para el escalado arrastrando con el botón derecho
        indice = self.obtener_forma_en(event.x, event.y)
        if indice is None:
            return
        self.forma_escalando = indice
        tipo, x, y, ancho, alto = self.formas[indice]
        self.inicio_escala_x = event.x
        self.inicio_escala_y = event.y
        self.ancho_inicial = ancho
        self.alto_inicial = alto
        event.widget.delete("tooltip")
        event.widget.create_text(event.x + 10, event.y - 10,
                                 text=f"Ancho: {ancho:.1f}, Alto: {alto:.1f}",
                                 anchor="nw", fill="blue", tags="tooltip")


    def escalar_forma_drag(self, event):
        if self.forma_escalando is None:
            return
        tipo, x, y, _, _ = self.formas[self.forma_escalando] # Usamos x,y de la forma original

        # Calcular el cambio de arrastre desde el inicio del escalado
        dx = event.x - self.inicio_escala_x
        dy = event.y - self.inicio_escala_y # Asumimos que arrastrar hacia abajo/derecha aumenta, arriba/izquierda disminuye

        # Calcular nuevas dimensiones basadas en el cambio y las dimensiones iniciales
        # Asegurarse de que las dimensiones no se hagan demasiado pequeñas (mínimo 1)
        nuevo_ancho = max(1, self.ancho_inicial + dx)
        # Para escalado arrastrando el vértice inferior derecho, la altura aumenta si dy es positivo
        # Si (x,y) es la esquina superior izquierda del rectángulo, y arrastramos el inferior derecho:
        # la nueva altura sería self.alto_inicial + dy.
        nuevo_alto = max(1, self.alto_inicial + dy)

        if tipo == "Círculo":
            # Para círculos, mantener el ancho y alto iguales (radio)
            nuevo_tam = max(nuevo_ancho, nuevo_alto)
            nuevo_ancho = nuevo_alto = nuevo_tam

        # Actualizar las dimensiones de la forma
        self.formas[self.forma_escalando] = (tipo, x, y, nuevo_ancho, nuevo_alto)

        self.redibujar_formas()

        # Actualizar el tooltip en el canvas
        event.widget.delete("tooltip")
        event.widget.create_text(event.x + 10, event.y - 10,
                                 text=f"Ancho: {nuevo_ancho:.1f}, Alto: {nuevo_alto:.1f}",
                                 anchor="nw", fill="blue", tags="tooltip")


    def finalizar_escalado_forma(self, event):
        if self.forma_escalando is not None:
            event.widget.delete("tooltip")
        self.forma_escalando = None


    def redibujar_formas(self):
        # Asegurarse de que el canvas tenga un tamaño válido antes de dibujar
        if self.canvas_formas.winfo_width() == 1 or self.canvas_formas.winfo_height() == 1:
            # Si el canvas aún no está renderizado completamente, esperar y reintentar
            self.root.after(100, self.redibujar_formas)
            return

        for canvas_to_draw in [self.canvas_formas] + ([self.canvas_ampliado] if hasattr(self, "canvas_ampliado") else []):
            canvas_to_draw.delete("all")
            self.dibujar_cuadricula(canvas_to_draw)
            for tipo, x, y, ancho, alto in self.formas:
                self.dibujar_forma_canvas(canvas_to_draw, tipo, x, y, ancho, alto)
        self.actualizar_cg_label()


    def actualizar_cg_label(self):
        if not hasattr(self, "cg_label"):
            return
        if not self.formas:
            self.cg_label.config(text="CG: -")
            return
        area_total = 0
        cx_total = 0
        cy_total = 0
        for tipo, x, y, ancho, alto in self.formas:
            if tipo == "Rectángulo":
                area = ancho * alto
                cx = x + ancho / 2
                cy = y + alto / 2
            elif tipo == "Triángulo":
                area = ancho * alto / 2
                # CG para triángulo con vértice superior en (x,y) y base en (x +/- ancho/2, y+alto)
                cx = x + ancho / 2
                cy = y + (2 * alto / 3)
            elif tipo == "Círculo":
                area = np.pi * (ancho / 2) ** 2
                cx = x
                cy = y
            else:
                continue
            area_total += area
            cx_total += cx * area
            cy_total += cy * area
        if area_total == 0:
            self.cg_label.config(text="CG: -")
            return
        cg_x = cx_total / area_total
        cg_y = cy_total / area_total
        self.cg_label.config(text=f"CG: ({cg_x:.2f}, {cg_y:.2f})")

    def limpiar_lienzo_formas(self):
        self.canvas_formas.delete("all")
        self.formas.clear()
        if hasattr(self, "canvas_ampliado"):
            self.canvas_ampliado.delete("all")
        self.redibujar_formas()
        if hasattr(self, "cg_label"):
            self.cg_label.config(text="CG: -")

    def ampliar_lienzo_formas(self):
        self.ventana_lienzo = tk.Toplevel(self.root)
        self.ventana_lienzo.title("Lienzo Ampliado")
        self.canvas_ampliado = tk.Canvas(self.ventana_lienzo, width=800, height=600, bg="white", highlightbackground="gray", highlightthickness=1)
        self.canvas_ampliado.pack(fill="both", expand=True)
        self.canvas_ampliado.bind("<Button-1>", self.iniciar_accion_formas)
        self.canvas_ampliado.bind("<B1-Motion>", self.arrastrar_forma)
        self.canvas_ampliado.bind("<ButtonRelease-1>", self.soltar_forma)
        self.canvas_ampliado.bind("<Button-3>", self.iniciar_escalado_forma)
        self.canvas_ampliado.bind("<B3-Motion>", self.escalar_forma_drag)
        self.canvas_ampliado.bind("<ButtonRelease-3>", self.finalizar_escalado_forma)
        self.canvas_ampliado.bind("<Motion>", self.mostrar_coordenadas_ampliado)
        self.canvas_ampliado.bind("<MouseWheel>", self.escalar_forma)
        self.canvas_ampliado.bind("<Button-4>", self.escalar_forma)
        self.canvas_ampliado.bind("<Button-5>", self.escalar_forma)
        self.canvas_ampliado.bind("<Configure>", lambda e: self.redibujar_formas())
        self.dibujar_cuadricula(self.canvas_ampliado)

        # Dibujar formas existentes en ambos lienzos
        self.redibujar_formas()

        self.coord_label_ampliado = ttk.Label(self.ventana_lienzo, text="x=0, y=0")
        self.coord_label_ampliado.pack()

    def cargar_proyecto_3_cg_mesa(self):
        """Carga los datos del Proyecto 3 (Mesa) y muestra su centro de gravedad."""
        self.limpiar_lienzo_formas()

        # Las coordenadas de la tabla original son para el CG, no para el vértice superior izquierdo.
        # Ajustar para que el dibujo se haga desde (0,0) como base de la mesa.
        # Las coordenadas de los puntos deben ser compatibles con el dibujo de matplotlib.Rectangle(xy, width, height)
        # donde xy es la esquina inferior izquierda.

        # Original del problema de la mesa:
        # Rectángulo 1: 0,0 a 100,2 (x,y,ancho,alto) -> CG (50,1) Area 200
        self.formas.append(("Rectángulo", 0, 0, 100, 2))
        # Rectángulo 2: 0,2 a 2,50 -> CG (1,26) Area 96
        self.formas.append(("Rectángulo", 0, 2, 2, 48))
        # Rectángulo 3: 98,2 a 100,50 -> CG (99,26) Area 96
        self.formas.append(("Rectángulo", 98, 2, 2, 48))
        # Rectángulo 4: 2,48 a 98,50 -> CG (50,49) Area 192
        self.formas.append(("Rectángulo", 2, 48, 96, 2))
        # Rectángulo 5: 39,23 a 61,27 (hueco) - se resta el área y momentos
        # El ejercicio original tiene un hueco, pero el simulador actual suma formas.
        # Para simularlo, podríamos agregar un rectángulo con "masa negativa", pero la implementación actual no lo soporta.
        # Por ahora, solo se agregarán las formas positivas.
        # Si se desea un cálculo exacto del CG de la mesa con el hueco, se debe implementar la resta de áreas.

        # Recalcular CG basado en las formas añadidas
        area_total = 0
        sum_XA_formas = 0
        sum_YA_formas = 0

        for tipo, x, y, ancho, alto in self.formas:
            if tipo == "Rectángulo":
                area = ancho * alto
                cx = x + ancho / 2
                cy = y + alto / 2
            # Añadir otras formas si la mesa las incluyera
            else:
                area = 0 # Ignorar otros tipos por ahora
                cx = 0
                cy = 0

            area_total += area
            sum_XA_formas += cx * area
            sum_YA_formas += cy * area

        if area_total != 0:
            cg_x_proyecto = sum_XA_formas / area_total
            cg_y_proyecto = sum_YA_formas / area_total
        else:
            cg_x_proyecto = 0
            cg_y_proyecto = 0
            self.log("Error: El área total de las formas añadidas es cero, no se puede calcular el CG.\n", "error")


        self.cg_label.config(text=f"CG Mesa (Cal.): ({cg_x_proyecto:.2f}, {cg_y_proyecto:.2f})")
        self.redibujar_formas()

        self.log("\n\U0001F4CA Datos del Proyecto 3 (Mesa) cargados y calculados:\n", "title")
        self.log(f"Centro de Gravedad calculado (según formas añadidas): X={cg_x_proyecto:.2f}, Y={cg_y_proyecto:.2f}\n", "data")
        self.log("Se ha agregado un rect\u00e1ngulo representativo de la forma exterior de la mesa.\n", "info")
        self.log("Nota: Si el proyecto original incluye huecos, esta simulación actual solo suma las áreas positivas. Para un cálculo con huecos se necesitaría una implementación de resta de áreas.\n", "info")

        # Dibujar las formas y el CG calculado en el matplotlib
        self.dibujar_formas_irregulares(cg_x_proyecto, cg_y_proyecto)


    def cargar_cg_solar(self):
        """Carga los datos predefinidos del centro de gravedad para la figura 'Solar'."""
        self.limpiar_lienzo_formas()

        # Las formas para "Solar" no están definidas en el documento, solo el CG final.
        # Si se desea una representación visual completa, se necesitarían las geometrías de las partes.
        # Por ahora, solo se dibujará el punto del CG.
        cg_x_solar = 5.0
        cg_y_solar = 6.55

        self.cg_label.config(text=f"CG Solar: ({cg_x_solar:.2f}, {cg_y_solar:.2f})")

        self.log("\n\U0001F4CA Datos del Centro de Gravedad (Solar) cargados:\n", "title")
        self.log(f"Centro de Gravedad: X={cg_x_solar:.2f} cm, Y={cg_y_solar:.2f} cm\n", "data")
        self.log("Se ha cargado y visualizado el Centro de Gravedad de la figura 'Solar'.\n", "info")
        self.log("Nota: La visualizaci\u00f3n dibuja solo el punto del CG. Si tuvieras los detalles de las formas que componen 'Solar', podr\u00edas a\u00f1adirlas aqu\u00ed.\n", "info")

        # Dibujar solo el punto del CG en Matplotlib, ya que no se tienen las formas componentes
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.plot(cg_x_solar, cg_y_solar, 'ro', markersize=10, label='Centro de Gravedad')
        ax.text(cg_x_solar + 0.5, cg_y_solar + 0.5, f'CG ({cg_x_solar:.2f}, {cg_y_solar:.2f})',
                ha='left', va='bottom', color='red')

        # Ajustar límites para una mejor visualización de este CG específico
        ax.set_aspect('equal', 'box')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.set_title('Centro de Gravedad de la Figura Solar')
        ax.set_xlabel('Coordenada X (cm)')
        ax.set_ylabel('Coordenada Y (cm)')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()

        plt.tight_layout()
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig


    def cargar_proyecto_mancuerna_cg(self):
        """Carga los datos del Centro de Gravedad de la figura de mancuerna."""
        self.limpiar_lienzo_formas()

        # Coordenadas del Centro de Gravedad calculadas para la mancuerna (según la imagen)
        cg_x_mancuerna = 4.22
        cg_y_mancuerna = 14.02

        self.cg_label.config(text=f"CG Mancuerna: ({cg_x_mancuerna:.2f}, {cg_y_mancuerna:.2f})")

        self.log("\n\U0001F4CA Datos del Centro de Gravedad (Mancuerna) cargados:\n", "title")
        self.log(f"Centro de Gravedad: X={cg_x_mancuerna:.2f}, Y={cg_y_mancuerna:.2f}\n", "data")
        self.log("Se muestra el CG calculado. La visualizaci\u00f3n de la forma completa de la 'Mancuerna' no se dibuja autom\u00e1ticamente en este caso, ya que no se especificaron las formas individuales que la componen en el documento original. Si deseas que se dibuje, necesitar\u00eda los detalles de las formas (rect\u00e1ngulos, c\u00edrculos, etc.) que la componen y sus posiciones.\n", "info")

        # Dibujar solo el punto del CG en Matplotlib
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.plot(cg_x_mancuerna, cg_y_mancuerna, 'ro', markersize=10, label='Centro de Gravedad')
        ax.text(cg_x_mancuerna + 0.5, cg_y_mancuerna + 0.5, f'CG ({cg_x_mancuerna:.2f}, {cg_y_mancuerna:.2f})',
                ha='left', va='bottom', color='red')

        # Ajustar límites para una mejor visualización de este CG específico
        ax.set_aspect('equal', 'box')
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 30)
        ax.set_title('Centro de Gravedad de la Mancuerna')
        ax.set_xlabel('Coordenada X (cm)')
        ax.set_ylabel('Coordenada Y (cm)')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()

        plt.tight_layout()
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig


    def crear_seccion_resultados(self, parent):
        frame_resultados = ttk.LabelFrame(parent, text="Resultados", padding="10 10 10 10")
        frame_resultados.pack(fill="both", expand=True, pady=5, padx=5) # Ajustar padding y expansión

        btn_clear = ttk.Button(
            frame_resultados, text="Limpiar Resultados", command=self.limpiar_resultados
        )
        btn_clear.pack(anchor="ne", padx=5, pady=5)

        self.texto_resultado = tk.Text(
            frame_resultados,
            height=12,
            wrap="word",
            font=("Consolas", 10),
            background="#ffffff",
            foreground="#333333",
            relief="solid",
            borderwidth=1,
        )
        self.texto_resultado.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_resultados, orient="vertical", command=self.texto_resultado.yview)
        scrollbar.pack(side="right", fill="y")

        self.texto_resultado.configure(yscrollcommand=scrollbar.set)

        # Configurar estilos de texto
        self.texto_resultado.tag_config("title", font=("Consolas", 10, "bold"), foreground="#005a9e")
        self.texto_resultado.tag_config("success", foreground="green")
        self.texto_resultado.tag_config("error", foreground="red")
        self.texto_resultado.tag_config("warning", foreground="#a06000")
        self.texto_resultado.tag_config("data", foreground="#333333")
        self.texto_resultado.tag_config("info", foreground="#333333")

    def crear_seccion_graficos(self, parent):
        self.frame_grafico = ttk.Frame(parent, padding="5 5 5 5") # Ajustar padding
        self.frame_grafico.pack(fill="both", expand=True, pady=5, padx=5)

    def run(self):
        self.root.mainloop()

def main():
    parser = argparse.ArgumentParser(description="Simulador de Viga")
    parser.add_argument(
        "--ejemplo-pasador",
        action="store_true",
        help="Ejecutar ejemplo de bastidor con pasador",
    )
    args = parser.parse_args()

    if args.ejemplo_pasador:
        v1 = Viga(3.0, [(1.5, -500, 0)])
        v2 = Viga(2.0, [(1.0, -200, 0)])
        modelo = BastidorConPasador(v1, v2)
        modelo.resumen()
        modelo.graficar_dcl()
        return

    if BOOTSTRAP_AVAILABLE:
        root = ttkb.Window(themename="flatly")
        app = SimuladorVigaMejorado(root, bootstrap=True)
    else:
        root = tk.Tk()
        app = SimuladorVigaMejorado(root)
    app.run()

if __name__ == "__main__":
    main()