import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import ttkbootstrap as ttkb
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    ttkb = None
    BOOTSTRAP_AVAILABLE = False
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.animation import FuncAnimation
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, List, Tuple

from beam import (
    CargaDistribuida,
    CargaPuntual,
    Viga,
    calcular_reacciones_viga,
    centro_de_masa_viga,
)
from analysis import (
    Armadura2D,
    Barra,
    BarraBastidor,
    Bastidor2D,
    Nodo,
    NodoBastidor,
    resolver_armadura,
    resolver_bastidor,
)

class SimuladorVigaMejorado:
    def __init__(self, root, bootstrap=False):
        self.root = root
        self.bootstrap = bootstrap
        self.root.title("Simulador de Viga Mecánica - Versión Completa")
        self.root.geometry("1200x900")  # Aumentado el tamaño de la ventana

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
        self.resultado_par = tk.StringVar(value="-")

        # Guardar reacciones para cálculos posteriores
        self.reaccion_a = 0.0
        self.reaccion_b = 0.0
        self.reaccion_c = 0.0

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
        # Espaciado de la cuadrícula para el lienzo de formas
        self.grid_spacing = 20
        self.texto_bastidor = None
        self.fig_bastidor = None
        self.ax_bastidor = None
        self.canvas_bastidor = None
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
        notebook.pack(fill="both", expand=True, padx=20, pady=10)

        tab_config = ttk.Frame(notebook)
        tab_seccion = ttk.Frame(notebook)
        tab_result = ttk.Frame(notebook)
        tab_armadura = ttk.Frame(notebook)
        tab_bastidor = ttk.Frame(notebook)

        notebook.add(tab_config, text="Configuración y Cargas")
        notebook.add(tab_seccion, text="Sección y Formas")
        notebook.add(tab_result, text="Resultados")
        notebook.add(tab_armadura, text="Armadura 2D")
        notebook.add(tab_bastidor, text="Bastidor 2D")

        # Sección configuración y cargas
        tab_config.columnconfigure(0, weight=1)
        tab_config.columnconfigure(1, weight=1)

        frame_config = self.crear_seccion_configuracion_viga(tab_config)
        frame_puntual = self.crear_seccion_cargas_puntuales(tab_config)
        frame_dist = self.crear_seccion_cargas_distribuidas(tab_config)
        frame_botones = self.crear_seccion_botones_calculo(tab_config)

        frame_config.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        frame_puntual.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        frame_dist.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        frame_botones.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        # Sección propiedades de la sección y formas irregulares
        self.crear_seccion_propiedades_seccion(tab_seccion)
        self.crear_widgets_formas_irregulares(tab_seccion)

        # Resultados y gráficos
        self.crear_seccion_resultados(tab_result)
        self.crear_seccion_graficos(tab_result)
        self.crear_seccion_armadura(tab_armadura)
        self.crear_seccion_bastidor(tab_bastidor)
    
    def crear_seccion_configuracion_viga(self, parent):
        frame_config = ttk.LabelFrame(parent, text="⚙ Configuración de la Viga")
    
        # Longitud de la viga
        ttk.Label(frame_config, text="Longitud (m):").grid(row=0, column=0, padx=5, pady=5)
        longitud_scale = ttk.Scale(frame_config, variable=self.longitud, from_=5, to=50, orient="horizontal", length=200)
        longitud_scale.grid(row=0, column=1, padx=5, pady=5)
        # Permitir ingreso manual de la longitud
        ttk.Entry(frame_config, textvariable=self.longitud, width=8).grid(row=0, column=2, padx=5, pady=5)
    
        # Configuración de apoyos
        ttk.Label(frame_config, text="Apoyo A:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Combobox(frame_config, textvariable=self.tipo_apoyo_a, values=["Fijo", "Móvil"], width=10).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame_config, text="Apoyo B:").grid(row=1, column=2, padx=5, pady=5)
        ttk.Combobox(frame_config, textvariable=self.tipo_apoyo_b, values=["Fijo", "Móvil"], width=10).grid(row=1, column=3, padx=5, pady=5)
    
        # Apoyo C
        ttk.Label(frame_config, text="Apoyo C:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Combobox(frame_config, textvariable=self.tipo_apoyo_c, values=["Ninguno", "Fijo", "Móvil"], width=10).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(frame_config, text="Posición C (m):").grid(row=2, column=2, padx=5, pady=5)
        ttk.Entry(frame_config, textvariable=self.posicion_apoyo_c, width=10).grid(row=2, column=3, padx=5, pady=5)
    
        # Opción para 3D y par torsor
        ttk.Checkbutton(frame_config, text="Modo 3D", variable=self.modo_3d).grid(row=3, column=0, padx=5, pady=5)
        ttk.Label(frame_config, text="Par Torsor (N·m):").grid(row=3, column=1, padx=5, pady=5)
        ttk.Entry(frame_config, textvariable=self.par_torsor, width=10).grid(row=3, column=2, padx=5, pady=5)
    
        # Altura de la viga
        ttk.Label(frame_config, text="Altura inicial (m):").grid(row=4, column=0, padx=5, pady=5)
        ttk.Entry(frame_config, textvariable=self.altura_inicial, width=10).grid(row=4, column=1, padx=5, pady=5)
        ttk.Label(frame_config, text="Altura final (m):").grid(row=4, column=2, padx=5, pady=5)
        ttk.Entry(frame_config, textvariable=self.altura_final, width=10).grid(row=4, column=3, padx=5, pady=5)

        return frame_config
    
    def crear_seccion_propiedades_seccion(self, parent):
        frame_seccion = ttk.LabelFrame(parent, text="Propiedades de la Sección Transversal")
        frame_seccion.pack(fill="x", pady=10, padx=10)
    
        ttk.Label(frame_seccion, text="Ancho superior (cm):").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame_seccion, textvariable=self.ancho_superior, width=10).grid(row=0, column=1, padx=5, pady=5)
    
        ttk.Label(frame_seccion, text="Altura superior (cm):").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame_seccion, textvariable=self.altura_superior, width=10).grid(row=0, column=3, padx=5, pady=5)
    
        ttk.Label(frame_seccion, text="Ancho alma (cm):").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame_seccion, textvariable=self.ancho_alma, width=10).grid(row=1, column=1, padx=5, pady=5)
    
        ttk.Label(frame_seccion, text="Altura alma (cm):").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(frame_seccion, textvariable=self.altura_alma, width=10).grid(row=1, column=3, padx=5, pady=5)
    
        ttk.Label(frame_seccion, text="Ancho inferior (cm):").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(frame_seccion, textvariable=self.ancho_inferior, width=10).grid(row=2, column=1, padx=5, pady=5)
    
        ttk.Label(frame_seccion, text="Altura inferior (cm):").grid(row=2, column=2, padx=5, pady=5)
        ttk.Entry(frame_seccion, textvariable=self.altura_inferior, width=10).grid(row=2, column=3, padx=5, pady=5)
    
        ttk.Button(frame_seccion, text="Calcular Propiedades", command=self.calcular_propiedades_seccion).grid(row=3, column=0, columnspan=4, pady=10)
    
    def crear_seccion_cargas_puntuales(self, parent):
        frame_puntuales = ttk.LabelFrame(parent, text="⬇️ Cargas Puntuales")
    
        ttk.Label(frame_puntuales, text="Posición (m):").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame_puntuales, textvariable=self.posicion_carga, width=10).grid(row=0, column=1, padx=5, pady=5)
    
        ttk.Label(frame_puntuales, text="Magnitud (N):").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame_puntuales, textvariable=self.magnitud_carga, width=10).grid(row=0, column=3, padx=5, pady=5)
    
        ttk.Button(frame_puntuales, text="➕ Agregar", command=self.agregar_carga_puntual).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(frame_puntuales, text="🗑️ Limpiar", command=self.limpiar_cargas_puntuales).grid(row=1, column=2, columnspan=2, padx=5, pady=5)

        return frame_puntuales
    
    def crear_seccion_cargas_distribuidas(self, parent):
        frame_distribuidas = ttk.LabelFrame(parent, text="📅 Cargas Distribuidas")
    
        ttk.Label(frame_distribuidas, text="Inicio (m):").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame_distribuidas, textvariable=self.inicio_dist, width=10).grid(row=0, column=1, padx=5, pady=5)
    
        ttk.Label(frame_distribuidas, text="Fin (m):").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame_distribuidas, textvariable=self.fin_dist, width=10).grid(row=0, column=3, padx=5, pady=5)
    
        ttk.Label(frame_distribuidas, text="Magnitud (N/m):").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame_distribuidas, textvariable=self.magnitud_dist, width=10).grid(row=1, column=1, padx=5, pady=5)
    
        ttk.Button(frame_distribuidas, text="➕ Agregar", command=self.agregar_carga_distribuida).grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(frame_distribuidas, text="🗑️ Limpiar", command=self.limpiar_cargas_distribuidas).grid(row=2, column=2, columnspan=2, padx=5, pady=5)

        return frame_distribuidas
    
    def crear_seccion_botones_calculo(self, parent):
        frame_botones = ttk.Frame(parent)
        
        # Los estilos de botones se configuran en apply_theme
        
        # Botones principales con iconos
        btn_calcular = ttk.Button(frame_botones, text="🧮 Calcular Reacciones", style="Action.TButton")
        btn_calcular.config(command=lambda b=btn_calcular: self.on_button_click(b, self.calcular_reacciones))
        btn_calcular.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        btn_centro_masa = ttk.Button(frame_botones, text="📍 Calcular Centro de Masa", style="Action.TButton")
        btn_centro_masa.config(command=lambda b=btn_centro_masa: self.on_button_click(b, self.calcular_centro_masa))
        btn_centro_masa.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        btn_diagramas = ttk.Button(frame_botones, text="📊 Mostrar Diagramas", style="Action.TButton")
        btn_diagramas.config(command=lambda b=btn_diagramas: self.on_button_click(b, self.mostrar_diagramas))
        btn_diagramas.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        par_frame = ttk.Frame(frame_botones)
        ttk.Label(par_frame, text="x (m):").pack(side="left", padx=(0, 2))
        ttk.Entry(par_frame, textvariable=self.posicion_torsor, width=6).pack(side="left")
        btn_par_punto = ttk.Button(par_frame, text="🌀 Par en Punto", style="Action.TButton")
        btn_par_punto.pack(side="left", padx=2)
        btn_par_punto.config(command=lambda b=btn_par_punto: self.on_button_click(b, self.ejecutar_par_punto))
        ttk.Label(par_frame, textvariable=self.resultado_par, width=10).pack(side="left", padx=(4, 0))
        par_frame.grid(row=0, column=3, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Segunda fila de botones
        btn_limpiar = ttk.Button(frame_botones, text="🗑️ Limpiar Todo", style="Warning.TButton")
        btn_limpiar.config(command=lambda b=btn_limpiar: self.on_button_click(b, self.limpiar_todo))
        btn_limpiar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        btn_ayuda = ttk.Button(frame_botones, text="❓ Ayuda", style="Action.TButton")
        btn_ayuda.config(command=lambda b=btn_ayuda: self.on_button_click(b, self.mostrar_ayuda))
        btn_ayuda.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        btn_ampliar = ttk.Button(frame_botones, text="🔍 Ampliar Gráfica", style="Action.TButton")
        btn_ampliar.config(command=lambda b=btn_ampliar: self.on_button_click(b, self.ampliar_grafica))
        btn_ampliar.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        btn_animar_3d = ttk.Button(frame_botones, text="🎞️ Animar 3D", style="Action.TButton")
        btn_animar_3d.config(command=lambda b=btn_animar_3d: self.on_button_click(b, self.animar_viga_3d))
        btn_animar_3d.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        btn_guardar = ttk.Button(frame_botones, text="💾 Guardar JPG", style="Action.TButton")
        btn_guardar.config(command=lambda b=btn_guardar: self.on_button_click(b, self.guardar_grafica))
        btn_guardar.grid(row=1, column=4, padx=5, pady=5, sticky="ew")

        btn_tema = ttk.Button(frame_botones, textvariable=self.texto_tema, style="Action.TButton")
        btn_tema.config(command=lambda b=btn_tema: self.on_button_click(b, self.toggle_dark_mode))
        btn_tema.grid(row=1, column=5, padx=5, pady=5, sticky="ew")
        self.boton_tema = btn_tema

        # Configurar el grid para que se expanda correctamente
        for i in range(6):
            frame_botones.columnconfigure(i, weight=1)

        return frame_botones
    
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
            
        except (tk.TclError, ValueError) as e:
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
            
        except (tk.TclError, ValueError) as e:
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

            # Guardar reacciones para cálculos posteriores
            self.reaccion_a = RA
            self.reaccion_b = RB
            self.reaccion_c = RC

            self.dibujar_viga_con_reacciones(RA, RB, RC)
            
        except (ValueError, ZeroDivisionError, np.linalg.LinAlgError) as e:
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
            
        except (ValueError, ZeroDivisionError) as e:
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

        except (ValueError, ZeroDivisionError, np.linalg.LinAlgError) as e:
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

    def ejecutar_par_punto(self):
        """Obtiene el par torsor en la posición ingresada y actualiza la etiqueta."""
        valor = self.calcular_par_torsor_en_punto(self.posicion_torsor.get())
        if valor is not None:
            self.resultado_par.set(f"{valor:.2f} N·m")
            
    def dibujar_viga_actual(self, x_cm=None):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        L = self.longitud.get()
        h_inicial = self.altura_inicial.get()
        h_final = self.altura_final.get()

        # Configuración del estilo
        plt.style.use('ggplot')  # Estilo más atractivo para las gráficas
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

        # Dibujar cargas puntuales
        for pos, mag in self.cargas_puntuales:
            h = h_inicial + (h_final - h_inicial) * pos / L
            ax.arrow(pos, h+0.5, 0, -0.4, head_width=L*0.015, head_length=0.05, fc='#d62728', ec='#d62728', width=0.002, zorder=15)
            ax.text(pos, h+0.6, f'{mag}N', ha='center', va='bottom', fontsize=10, color='#d62728', fontweight='bold')

        # Dibujar cargas distribuidas como carga puntual equivalente
        for inicio, fin, mag in self.cargas_distribuidas:
            h_mid = h_inicial + (h_final - h_inicial) * ((inicio+fin)/2) / L
            F_eq = mag * (fin - inicio)
            ax.arrow((inicio+fin)/2, h_mid+0.8, 0, -0.6, head_width=L*0.015, head_length=0.05,
                     fc='#ff7f0e', ec='#ff7f0e', width=0.002, zorder=15)
            ax.text((inicio+fin)/2, h_mid+0.85, f'{F_eq:.1f}N', ha='center', va='bottom',
                    fontsize=10, color='#ff7f0e', fontweight='bold')

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

        fig = plt.figure(figsize=(12, 8))
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
        fig = plt.figure(figsize=(12, 8))
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
        
        fig, ax = plt.subplots(figsize=(12, 6))
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
        for pos, mag in self.cargas_puntuales:
            ax.arrow(pos, 0.5, 0, -0.4, head_width=L*0.015, head_length=0.05, fc='red', ec='red', width=0.002)
            ax.text(pos, 0.6, f'{mag}N', ha='center', va='bottom', fontsize=8, color='red')
            
        for inicio, fin, mag in self.cargas_distribuidas:
            F_eq = mag * (fin - inicio)
            ax.arrow((inicio+fin)/2, 0.75, 0, -0.5, head_width=L*0.015, head_length=0.03,
                     fc='red', ec='red', width=0.002)
            ax.text((inicio+fin)/2, 0.8, f'{F_eq:.1f}N', ha='center', va='bottom', fontsize=8, color='red')
            
        # Dibujar el par torsor
        par_torsor = self.par_torsor.get()
        if par_torsor != 0:
            # Dibujar una flecha circular para representar el par torsor
            center = L / 2
            radius = 0.2
            angle = np.linspace(0, 2*np.pi, 100)
            x = center + radius * np.cos(angle)
            y = radius * np.sin(angle)
            ax.plot(x, y, 'g-')
            # Agregar una punta de flecha
            ax.arrow(center + radius, 0, 0.05, 0.05, head_width=0.05, head_length=0.05, fc='g', ec='g')
            ax.text(center, 0.3, f'T={par_torsor:.2f}N·m', ha='center', va='bottom', fontsize=9, color='green')
            
        ax.set_xlim(-L*0.1, L*1.1)
        ax.set_ylim(-0.6, 1.0)
        ax.set_xlabel('Posición (m)', fontsize=10)
        ax.set_title('Viga con Reacciones Calculadas', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig
        
    def dibujar_diagramas(self, x, cortante, momento, RA, RB, RC):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
            
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(
            4, 1, figsize=(12, 24), constrained_layout=True
        )
        
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
            ax1.arrow((inicio+fin)/2, 0.55, 0, -0.35, head_width=L*0.015, head_length=0.03, fc='red', ec='red', width=0.002)
            ax1.text((inicio+fin)/2, 0.6, f'{F_eq:.1f}N', ha='center', va='bottom', fontsize=7, color='red')
        
        ax1.set_xlim(-L*0.1, L*1.1)
        ax1.set_ylim(-0.6, 0.7)
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

        # Añadir valor del par torsor al diagrama de torsión
        ax4.text(L*1.05, par_torsor, f'T: {par_torsor:.2f}N·m', va='center', ha='left', fontsize=8)
        

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

        # Limpiar área de resultados
        self.limpiar_resultados()

        # Limpiar área gráfica
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        # Mostrar mensaje inicial
        self.mostrar_mensaje_inicial()

        # Redibujar la viga en su estado inicial
        self.dibujar_viga_actual()
        
    def mostrar_ayuda(self):
        ayuda = """
🎓 GUÍA RÁPIDA DEL SIMULADOR DE VIGA

🔹 CONFIGURACIÓN
• Longitud entre 5 y 50 m
• Apoyos A y B (Fijo/Móvil) y apoyo C opcional con posición
• Altura inicial y final para vigas inclinadas
• Par torsor opcional y modo 3D

🔹 CARGAS
• Puntuales: posición y magnitud
• Distribuidas: inicio y fin (dos puntos) y magnitud (N/m)

🔹 PAR EN PUNTO
• Escribe la posición x y presiona "Par en Punto" para conocer el momento torsor interno

🔹 QUÉ PUEDE HACER
• 🧮 Calcular Reacciones
• 📍 Calcular Centro de Masa de las cargas
• 📊 Mostrar Diagramas de cortante y momento
• Calcular Propiedades de la Sección (área, CG e inercia)
• Figuras Irregulares: añada rectángulos, triángulos o círculos y obtenga su centro de gravedad
• 🔍 Ampliar la gráfica en otra ventana
• 🗑️ Limpiar Todo para reiniciar
• Nuevo apartado **Bastidor 2D** para marcos planos

🔹 FORMULARIO DE CÁLCULOS
• Reacciones: ΣFy=0 y ΣM=0
• Carga distribuida: F=w·(xf−xi)
• Centro de masa: x_cm=Σ(x·F)/ΣF
• Par en punto: M(x)=T+ΣR_i(x−x_i)−ΣP_j(x−x_j)
• Momento de inercia: I=b h³/12
• Armaduras: ΣFx=0 y ΣFy=0
• Bastidores: se resuelve K·d=F

🔹 PASOS BÁSICOS
1. Configure la viga y apoyos
2. Agregue las cargas necesarias
3. Presione "Calcular Reacciones"
4. (Opcional) use "Par en Punto" para consultar el momento torsor
5. Revise resultados y diagramas en la pestaña de Resultados
        """
        
        ventana_ayuda = tk.Toplevel(self.root)
        ventana_ayuda.title("📚 Guía de Usuario")
        ventana_ayuda.geometry("600x500")
        
        texto_ayuda = tk.Text(ventana_ayuda, wrap="word", font=("Arial", 10))
        scroll_ayuda = ttk.Scrollbar(ventana_ayuda, orient="vertical", command=texto_ayuda.yview)
        texto_ayuda.configure(yscrollcommand=scroll_ayuda.set)
        
        texto_ayuda.insert("1.0", ayuda)
        texto_ayuda.config(state="disabled")  # Solo lectura
        
        texto_ayuda.pack(side="left", fill="both", expand=True)
        scroll_ayuda.pack(side="right", fill="y")

    def ampliar_grafica(self):
        if hasattr(self, 'ultima_figura'):
            nueva_ventana = tk.Toplevel(self.root)
            nueva_ventana.title("Gráfica Ampliada")
            
            canvas = FigureCanvasTkAgg(self.ultima_figura, master=nueva_ventana)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            toolbar = NavigationToolbar2Tk(canvas, nueva_ventana)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            messagebox.showinfo("Información", "No hay gráfica para ampliar.")

    def guardar_grafica(self):
        """Guarda la última gráfica generada en formato JPG."""
        if not hasattr(self, 'ultima_figura'):
            messagebox.showinfo("Información", "No hay gráfica para guardar.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension='.jpg',
            filetypes=[('JPEG', '*.jpg'), ('Todos los archivos', '*.*')]
        )
        if file_path:
            self.ultima_figura.savefig(file_path, format='jpg')
            self.log(f"💾 Gráfica guardada en {file_path}\n", 'success')
    
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

        except (ValueError, ZeroDivisionError) as e:
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
        frame_formas = ttk.LabelFrame(parent, text="Figuras Irregulares")
        frame_formas.pack(fill="x", pady=10, padx=10)

        # Tipo de forma
        ttk.Label(frame_formas, text="Tipo:").grid(row=0, column=0, padx=5, pady=2)
        self.tipo_forma = ttk.Combobox(frame_formas, values=["Rectángulo", "Triángulo", "Círculo"])
        self.tipo_forma.grid(row=0, column=1, padx=5, pady=2)
        self.tipo_forma.set("Rectángulo")

        # Coordenadas
        ttk.Label(frame_formas, text="X:").grid(row=1, column=0, padx=5, pady=2)
        self.x_forma = ttk.Entry(frame_formas, width=10)
        self.x_forma.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame_formas, text="Y:").grid(row=1, column=2, padx=5, pady=2)
        self.y_forma = ttk.Entry(frame_formas, width=10)
        self.y_forma.grid(row=1, column=3, padx=5, pady=2)

        # Dimensiones
        ttk.Label(frame_formas, text="Ancho:").grid(row=2, column=0, padx=5, pady=2)
        self.ancho_forma = ttk.Entry(frame_formas, width=10)
        self.ancho_forma.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame_formas, text="Alto:").grid(row=2, column=2, padx=5, pady=2)
        self.alto_forma = ttk.Entry(frame_formas, width=10)
        self.alto_forma.grid(row=2, column=3, padx=5, pady=2)

        ttk.Button(frame_formas, text="Agregar Forma", command=self.agregar_forma).grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(frame_formas, text="Calcular CG", command=self.calcular_cg_formas).grid(row=3, column=2, columnspan=2, pady=5)
        ttk.Button(frame_formas, text="Limpiar Lienzo", command=self.limpiar_lienzo_formas).grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(frame_formas, text="Ampliar Lienzo", command=self.ampliar_lienzo_formas).grid(row=4, column=2, columnspan=2, pady=5)
        ttk.Label(frame_formas, text="⚡ También puede hacer clic en el lienzo para agregar").grid(row=5, column=0, columnspan=5, pady=2)
        self.canvas_formas = tk.Canvas(frame_formas, width=400, height=300, bg="white")
        self.canvas_formas.grid(row=6, column=0, columnspan=5, pady=5)
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
        self.dibujar_cuadricula(self.canvas_formas)

        self.coord_label = ttk.Label(frame_formas, text="x=0, y=0")
        self.coord_label.grid(row=7, column=0, columnspan=5, pady=2)

        self.cg_label = ttk.Label(frame_formas, text="CG: -")
        self.cg_label.grid(row=8, column=0, columnspan=5, pady=2)

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
        except ValueError as e:
            messagebox.showerror("Error", f"Valores inválidos: {e}")

    def colocar_forma(self, event):
        """Permite agregar una forma haciendo clic en el lienzo."""
        try:
            tipo = self.tipo_forma.get()
            ancho = float(self.ancho_forma.get())
            alto = float(self.alto_forma.get())

            x = event.x
            y = event.y

            canvas = event.widget

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
                cy = y + alto/2
            elif tipo == "Triángulo":
                area = ancho * alto / 2
                cx = x + ancho/3
                cy = y + alto/3
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
                ax.add_patch(plt.Rectangle((x, y), ancho, alto, fill=False))
            elif tipo == "Triángulo":
                ax.add_patch(plt.Polygon([(x, y), (x+ancho, y), (x, y+alto)], fill=False))
            elif tipo == "Círculo":
                ax.add_patch(plt.Circle((x, y), ancho/2, fill=False))
        
        ax.plot(cg_x, cg_y, 'ro', markersize=10)
        ax.text(cg_x, cg_y, f'CG ({cg_x:.2f}, {cg_y:.2f})', ha='right', va='bottom')
        
        ax.set_aspect('equal', 'box')
        ax.set_xlim(min(forma[1] for forma in self.formas)-1, max(forma[1]+forma[3] for forma in self.formas)+1)
        ax.set_ylim(min(forma[2] for forma in self.formas)-1, max(forma[2]+forma[4] for forma in self.formas)+1)
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
            canvas.create_polygon(x, y + alto, x + ancho / 2, y, x + ancho, y + alto, outline="black", fill="")
        elif tipo == "Círculo":
            canvas.create_oval(x - ancho / 2, y - ancho / 2, x + ancho / 2, y + ancho / 2, outline="black")

    def dibujar_cuadricula(self, canvas):
        """Dibuja una cuadrícula de fondo en el canvas."""
        canvas.delete("grid")
        width = int(canvas["width"])
        height = int(canvas["height"])
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

    def obtener_forma_en(self, x, y):
        """Devuelve el índice de la forma que contiene el punto (x, y) o None."""
        for i, (tipo, fx, fy, ancho, alto) in enumerate(self.formas):
            if tipo == "Rectángulo":
                if fx <= x <= fx + ancho and fy <= y <= fy + alto:
                    return i
            elif tipo == "Triángulo":
                if fx <= x <= fx + ancho and fy <= y <= fy + alto:
                    return i
            elif tipo == "Círculo":
                if (x - fx)**2 + (y - fy)**2 <= (ancho/2)**2:
                    return i
        return None

    def iniciar_accion_formas(self, event):
        indice = self.obtener_forma_en(event.x, event.y)
        if indice is not None:
            self.forma_seleccionada = indice
            _, fx, fy, _, _ = self.formas[indice]
            self.desplazamiento_x = event.x - fx
            self.desplazamiento_y = event.y - fy
        else:
            self.colocar_forma(event)

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
        indice = self.obtener_forma_en(event.x, event.y)
        if indice is None:
            return
        tipo, x, y, ancho, alto = self.formas[indice]
        delta = getattr(event, 'delta', 0)
        if event.num == 5 or delta < 0:
            factor = 0.9
        else:
            factor = 1.1
        if tipo == "Círculo":
            ancho *= factor
            alto = ancho
        else:
            ancho *= factor
            alto *= factor
        self.formas[indice] = (tipo, x, y, ancho, alto)
        self.redibujar_formas()

    def iniciar_escalado_forma(self, event):
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
                                 text=f"{ancho:.1f} x {alto:.1f}",
                                 anchor="nw", fill="blue", tags="tooltip")

    def escalar_forma_drag(self, event):
        if self.forma_escalando is None:
            return
        tipo, x, y, ancho, alto = self.formas[self.forma_escalando]
        nuevo_ancho = max(1, self.ancho_inicial + (event.x - self.inicio_escala_x))
        nuevo_alto = max(1, self.alto_inicial + (event.y - self.inicio_escala_y))
        if tipo == "Círculo":
            nuevo_tam = max(nuevo_ancho, nuevo_alto)
            nuevo_ancho = nuevo_tam
            nuevo_alto = nuevo_tam
        self.formas[self.forma_escalando] = (tipo, x, y, nuevo_ancho, nuevo_alto)
        self.redibujar_formas()
        event.widget.delete("tooltip")
        event.widget.create_text(event.x + 10, event.y - 10,
                                 text=f"{nuevo_ancho:.1f} x {nuevo_alto:.1f}",
                                 anchor="nw", fill="blue", tags="tooltip")

    def finalizar_escalado_forma(self, event):
        if self.forma_escalando is not None:
            event.widget.delete("tooltip")
        self.forma_escalando = None

    def redibujar_formas(self):
        for canvas in [self.canvas_formas] + ([self.canvas_ampliado] if hasattr(self, "canvas_ampliado") else []):
            canvas.delete("all")
            self.dibujar_cuadricula(canvas)
            for tipo, x, y, ancho, alto in self.formas:
                self.dibujar_forma_canvas(canvas, tipo, x, y, ancho, alto)
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
                cx = x + ancho / 3
                cy = y + alto / 3
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
        self.canvas_ampliado = tk.Canvas(self.ventana_lienzo, width=800, height=600, bg="white")
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
        self.dibujar_cuadricula(self.canvas_ampliado)

        # Dibujar formas existentes en ambos lienzos
        self.redibujar_formas()

        self.coord_label_ampliado = ttk.Label(self.ventana_lienzo, text="x=0, y=0")
        self.coord_label_ampliado.pack()


    def crear_seccion_resultados(self, parent):
        frame_resultados = ttk.LabelFrame(parent, text="Resultados")
        frame_resultados.pack(fill="both", pady=10, padx=10)

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
        self.frame_grafico = ttk.Frame(parent)
        self.frame_grafico.pack(fill="both", expand=True, pady=10, padx=10)

    def crear_seccion_armadura(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        instrucciones = (
            "NODOS: id x y Fx Fy rx ry\n"
            "BARRAS: ni nj\n"
            "Escriba los datos debajo y presione Calcular."
        )
        ttk.Label(frame, text=instrucciones, justify="left").pack(anchor="w")

        self.texto_armadura = tk.Text(frame, height=8)
        self.texto_armadura.pack(fill="x", pady=5)
        ejemplo = (
            "NODOS\n"
            "1 0 0 0 0 1 1\n"
            "2 4 0 0 -1000 0 1\n"
            "3 4 3 0 0 0 0\n\n"
            "BARRAS\n"
            "1 2\n"
            "2 3"
        )
        self.texto_armadura.insert("1.0", ejemplo)

        btn = ttk.Button(frame, text="Calcular Armadura", command=self.calcular_armadura)
        btn.pack(pady=5)

        self.fig_armadura, self.ax_armadura = plt.subplots()
        self.canvas_armadura = FigureCanvasTkAgg(self.fig_armadura, frame)
        self.canvas_armadura.get_tk_widget().pack(fill="both", expand=True)

    def calcular_armadura(self):
        try:
            text = self.texto_armadura.get("1.0", "end").strip().splitlines()
            mode = None
            nodos = {}
            barras = []
            for line in text:
                l = line.strip()
                if not l:
                    continue
                if l.lower().startswith("nodos"):
                    mode = "n"
                    continue
                if l.lower().startswith("barras"):
                    mode = "b"
                    continue
                parts = l.split()
                if mode == "n" and len(parts) >= 7:
                    idx = int(parts[0])
                    nodos[idx] = Nodo(
                        x=float(parts[1]),
                        y=float(parts[2]),
                        carga_x=float(parts[3]),
                        carga_y=float(parts[4]),
                        restringido_x=bool(int(parts[5])),
                        restringido_y=bool(int(parts[6])),
                    )
                elif mode == "b" and len(parts) >= 2:
                    barras.append(Barra(n_i=int(parts[0]), n_j=int(parts[1])))

            arm = Armadura2D(nodos, barras)
            fuerzas, reacc = arm.resolver()

            self.ax_armadura.clear()
            for bar, F in zip(barras, fuerzas):
                n1 = nodos[bar.n_i]
                n2 = nodos[bar.n_j]
                color = "red" if F >= 0 else "blue"
                self.ax_armadura.plot([n1.x, n2.x], [n1.y, n2.y], color=color, marker="o")
                self.ax_armadura.text((n1.x + n2.x) / 2, (n1.y + n2.y) / 2, f"{F:.1f}", color=color)
            self.ax_armadura.axis("equal")
            self.ax_armadura.set_title("Fuerzas en barras (+Tensión / -Compresión)")
            self.canvas_armadura.draw()

            self.log("\n=== RESULTADOS ARMADURA ===\n", "title")
            for i, bar in enumerate(barras):
                self.log(f"Barra {bar.n_i}-{bar.n_j}: {fuerzas[i]:.2f} N\n", "data")
            for idx in sorted(nodos.keys()):
                rx, ry = reacc.get(idx, (0.0, 0.0))
                self.log(f"Nodo {idx}: Rx={rx:.2f} Ry={ry:.2f}\n", "data")
        except (ValueError, np.linalg.LinAlgError) as e:
            messagebox.showerror("Error", f"Error en armadura: {e}")

    def crear_seccion_bastidor(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        instrucciones = (
            "NODOS: id x y cx cy m rx ry rz\n"
            "BARRAS: ni nj E A I\n"
            "Escriba los datos debajo y presione Calcular."
        )
        ttk.Label(frame, text=instrucciones, justify="left").pack(anchor="w")

        self.texto_bastidor = tk.Text(frame, height=8)
        self.texto_bastidor.pack(fill="x", pady=5)
        ejemplo = (
            "NODOS\n"
            "1 0 0 0 0 0 1 1 1\n"
            "2 4 0 0 -1000 0 0 1 1\n"
            "3 4 3 0 0 0 0 0 0\n\n"
            "BARRAS\n"
            "1 2 2e11 0.02 8e-5\n"
            "2 3 2e11 0.02 8e-5"
        )
        self.texto_bastidor.insert("1.0", ejemplo)

        btn = ttk.Button(frame, text="Calcular Bastidor", command=self.calcular_bastidor)
        btn.pack(pady=5)

        self.fig_bastidor, self.ax_bastidor = plt.subplots()
        self.canvas_bastidor = FigureCanvasTkAgg(self.fig_bastidor, frame)
        self.canvas_bastidor.get_tk_widget().pack(fill="both", expand=True)

    def calcular_bastidor(self):
        try:
            text = self.texto_bastidor.get("1.0", "end").strip().splitlines()
            mode = None
            nodos = {}
            barras = []
            for line in text:
                l = line.strip()
                if not l:
                    continue
                if l.lower().startswith("nodos"):
                    mode = "n"
                    continue
                if l.lower().startswith("barras"):
                    mode = "b"
                    continue
                parts = l.split()
                if mode == "n" and len(parts) >= 9:
                    idx = int(parts[0])
                    nodos[idx] = NodoBastidor(
                        x=float(parts[1]),
                        y=float(parts[2]),
                        carga_x=float(parts[3]),
                        carga_y=float(parts[4]),
                        momento=float(parts[5]),
                        restringido_x=bool(int(parts[6])),
                        restringido_y=bool(int(parts[7])),
                        restringido_rot=bool(int(parts[8])),
                    )
                elif mode == "b" and len(parts) >= 5:
                    barras.append(
                        BarraBastidor(
                            n_i=int(parts[0]),
                            n_j=int(parts[1]),
                            E=float(parts[2]),
                            A=float(parts[3]),
                            I=float(parts[4]),
                        )
                    )

            bast = Bastidor2D(nodos, barras)
            disp, reacc = bast.resolver()

            self.ax_bastidor.clear()
            for bar in barras:
                n1 = nodos[bar.n_i]
                n2 = nodos[bar.n_j]
                self.ax_bastidor.plot([n1.x, n2.x], [n1.y, n2.y], "b-o")

            scale = 100
            for i, idx in enumerate(sorted(nodos.keys())):
                d = disp[i*3:i*3+2]
                n = nodos[idx]
                self.ax_bastidor.plot(n.x + scale*d[0], n.y + scale*d[1], "ro")

            self.ax_bastidor.set_title("Deformada (escala x{} )".format(scale))
            self.ax_bastidor.axis("equal")
            self.canvas_bastidor.draw()
            self.log("\n=== RESULTADOS BASTIDOR ===\n", "title")
            for idx in sorted(nodos.keys()):
                rx, ry, rm = reacc[idx]
                self.log(f"Nodo {idx}: Rx={rx:.2f} Ry={ry:.2f} M={rm:.2f}\n", "data")
        except (ValueError, np.linalg.LinAlgError) as e:
            messagebox.showerror("Error", f"Error en bastidor: {e}")

    def run(self):
        self.root.mainloop()

def main():
    if BOOTSTRAP_AVAILABLE:
        root = ttkb.Window(themename="flatly")
        app = SimuladorVigaMejorado(root, bootstrap=True)
    else:
        root = tk.Tk()
        app = SimuladorVigaMejorado(root)
    app.run()

if __name__ == "__main__":
    main()
