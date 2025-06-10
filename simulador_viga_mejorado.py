import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

class SimuladorVigaMejorado:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Viga Mecánica - Versión Completa")
        self.root.geometry("1200x900")  # Aumentado el tamaño de la ventana
        
        # Configurar tema y estilo moderno
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        # Paleta de colores clara y acentos azules
        bg_color = "#f7f7f7"
        fg_color = "#333333"
        accent = "#007acc"

        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color)
        style.configure("TLabelframe.Label", background=bg_color,
                        foreground=accent, font=("Helvetica", 11, "bold"))
        style.configure("TButton", font=("Helvetica", 10, "bold"),
                        background=accent, foreground="white")
        style.map("TButton",
                   background=[('active', '#005a9e')],
                   foreground=[('active', 'white')])
        style.configure("TLabel", font=("Helvetica", 10),
                        background=bg_color, foreground=fg_color)
        style.configure("TEntry", font=("Helvetica", 10))
        style.configure("TNotebook", background=bg_color)
        style.configure("TNotebook.Tab", font=("Helvetica", 10, "bold"))

        self.root.configure(bg=bg_color)
        
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
        self.crear_widgets()
        
        # Mostrar mensaje inicial
        self.mostrar_mensaje_inicial()
        
        # Dibujar la viga inicial
        self.dibujar_viga_actual()
        
    
    def crear_widgets(self):
        # Usar un Notebook para organizar mejor la interfaz
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=20, pady=10)

        tab_config = ttk.Frame(notebook)
        tab_seccion = ttk.Frame(notebook)
        tab_result = ttk.Frame(notebook)

        notebook.add(tab_config, text="Configuración y Cargas")
        notebook.add(tab_seccion, text="Sección y Formas")
        notebook.add(tab_result, text="Resultados")

        # Sección configuración y cargas
        self.crear_seccion_configuracion_viga(tab_config)
        self.crear_seccion_cargas_puntuales(tab_config)
        self.crear_seccion_cargas_distribuidas(tab_config)
        self.crear_seccion_botones_calculo(tab_config)

        # Sección propiedades de la sección y formas irregulares
        self.crear_seccion_propiedades_seccion(tab_seccion)
        self.crear_widgets_formas_irregulares(tab_seccion)

        # Resultados y gráficos
        self.crear_seccion_resultados(tab_result)
        self.crear_seccion_graficos(tab_result)
    
    def crear_seccion_configuracion_viga(self, parent):
        frame_config = ttk.LabelFrame(parent, text="⚙ Configuración de la Viga")
        frame_config.pack(fill="x", pady=10, padx=10)
    
        # Longitud de la viga
        ttk.Label(frame_config, text="Longitud (m):").grid(row=0, column=0, padx=5, pady=5)
        longitud_scale = ttk.Scale(frame_config, variable=self.longitud, from_=5, to=30, orient="horizontal", length=200)
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
        frame_puntuales.pack(fill="x", pady=10, padx=10)
    
        ttk.Label(frame_puntuales, text="Posición (m):").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame_puntuales, textvariable=self.posicion_carga, width=10).grid(row=0, column=1, padx=5, pady=5)
    
        ttk.Label(frame_puntuales, text="Magnitud (N):").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame_puntuales, textvariable=self.magnitud_carga, width=10).grid(row=0, column=3, padx=5, pady=5)
    
        ttk.Button(frame_puntuales, text="➕ Agregar", command=self.agregar_carga_puntual).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(frame_puntuales, text="🗑️ Limpiar", command=self.limpiar_cargas_puntuales).grid(row=1, column=2, columnspan=2, padx=5, pady=5)
    
    def crear_seccion_cargas_distribuidas(self, parent):
        frame_distribuidas = ttk.LabelFrame(parent, text="📅 Cargas Distribuidas")
        frame_distribuidas.pack(fill="x", pady=10, padx=10)
    
        ttk.Label(frame_distribuidas, text="Inicio (m):").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame_distribuidas, textvariable=self.inicio_dist, width=10).grid(row=0, column=1, padx=5, pady=5)
    
        ttk.Label(frame_distribuidas, text="Fin (m):").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame_distribuidas, textvariable=self.fin_dist, width=10).grid(row=0, column=3, padx=5, pady=5)
    
        ttk.Label(frame_distribuidas, text="Magnitud (N/m):").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame_distribuidas, textvariable=self.magnitud_dist, width=10).grid(row=1, column=1, padx=5, pady=5)
    
        ttk.Button(frame_distribuidas, text="➕ Agregar", command=self.agregar_carga_distribuida).grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(frame_distribuidas, text="🗑️ Limpiar", command=self.limpiar_cargas_distribuidas).grid(row=2, column=2, columnspan=2, padx=5, pady=5)
    
    def crear_seccion_botones_calculo(self, parent):
        frame_botones = ttk.Frame(parent)
        frame_botones.pack(fill="x", pady=10, padx=10)
        
        # Crear un estilo personalizado para los botones
        style = ttk.Style()
        style.configure("Action.TButton", font=("Arial", 10, "bold"), padding=5)
        style.configure("Warning.TButton", background="#ff9999", font=("Arial", 10, "bold"), padding=5)
        
        # Botones principales con iconos
        btn_calcular = ttk.Button(frame_botones, text="🧮 Calcular Reacciones", 
                                 command=self.calcular_reacciones, style="Action.TButton")
        btn_calcular.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        btn_centro_masa = ttk.Button(frame_botones, text="📍 Calcular Centro de Masa", 
                                    command=self.calcular_centro_masa, style="Action.TButton")
        btn_centro_masa.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        btn_diagramas = ttk.Button(frame_botones, text="📊 Mostrar Diagramas", 
                                  command=self.mostrar_diagramas, style="Action.TButton")
        btn_diagramas.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Segunda fila de botones
        btn_limpiar = ttk.Button(frame_botones, text="🗑️ Limpiar Todo", 
                                command=self.limpiar_todo, style="Warning.TButton")
        btn_limpiar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        btn_ayuda = ttk.Button(frame_botones, text="❓ Ayuda", 
                              command=self.mostrar_ayuda, style="Action.TButton")
        btn_ayuda.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        btn_ampliar = ttk.Button(frame_botones, text="🔍 Ampliar Gráfica", 
                                command=self.ampliar_grafica, style="Action.TButton")
        btn_ampliar.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        # Configurar el grid para que se expanda correctamente
        for i in range(3):
            frame_botones.columnconfigure(i, weight=1)
    
    def mostrar_mensaje_inicial(self):
        mensaje = "Bienvenido al Simulador de Viga Mecánica. Use los controles para configurar la viga y las cargas."
        self.texto_resultado.insert("1.0", mensaje)
        
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
            self.texto_resultado.insert("end", f"✅ Carga puntual: {mag}N en {pos}m\n")
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
            self.texto_resultado.insert("end", f"✅ Carga distribuida: {mag}N/m desde {inicio}m hasta {fin}m\n")
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
            self.texto_resultado.insert("end", f"\n{'='*50}\n")
            self.texto_resultado.insert("end", f"⚖️ CÁLCULO DE REACCIONES:\n")
            self.texto_resultado.insert("end", f"{'='*50}\n")
            for linea in procedimiento:
                self.texto_resultado.insert("end", linea + "\n")
            self.texto_resultado.insert("end", f"🔺 Reacción en A (RA): {RA:.2f} N\n")
            self.texto_resultado.insert("end", f"🔺 Reacción en B (RB): {RB:.2f} N\n")
            if self.tipo_apoyo_c.get() != "Ninguno":
                self.texto_resultado.insert("end", f"🔺 Reacción en C (RC): {RC:.2f} N\n")
            self.texto_resultado.insert("end", f"📊 Suma de fuerzas en Y: {suma_fuerzas_y:.2f} N\n")
            self.texto_resultado.insert("end", f"📊 Suma de fuerzas en X: {suma_fuerzas_x:.2f} N\n")
            self.texto_resultado.insert("end", f"🔄 Verificación equilibrio: {abs(RA + RB + RC - suma_fuerzas_y):.6f} N\n")
            self.texto_resultado.insert("end", f"🔄 Par Torsor: {par_torsor:.2f} N·m\n")
            self.texto_resultado.insert("end", f"📐 Ángulo de inclinación: {np.degrees(angulo):.2f}°\n")
            
            if abs(RA + RB + RC - suma_fuerzas_y) < 1e-10:
                self.texto_resultado.insert("end", f"✅ Sistema en equilibrio\n")
            else:
                self.texto_resultado.insert("end", f"❌ Error en equilibrio\n")
            
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

            self.texto_resultado.insert("end", "\n📍 CÁLCULO DEL CENTRO DE MASA:\n")
            self.texto_resultado.insert("end", f"Σ(x·F) = {suma_momentos:.2f} N·m\n")
            self.texto_resultado.insert("end", f"ΣF = {suma_cargas:.2f} N\n")
            self.texto_resultado.insert("end", f"x_cm = Σ(x·F) / ΣF = {x_cm:.2f} m\n")
            
            # Actualizar la visualización
            if self.modo_3d.get():
                self.dibujar_viga_3d(x_cm)
            else:
                self.dibujar_viga_actual(x_cm)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculo: {e}")
            
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
            
    def dibujar_viga_actual(self, x_cm=None):
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        L = self.longitud.get()
        h_inicial = self.altura_inicial.get()
        h_final = self.altura_final.get()

        # Configuración del estilo
        plt.style.use('default')  # Cambiado de 'seaborn-whitegrid' a 'default'
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

        # Dibujar cargas distribuidas
        for inicio, fin, mag in self.cargas_distribuidas:
            x_dist = np.linspace(inicio, fin, 50)
            y_dist = h_inicial + (h_final - h_inicial) * x_dist / L + 0.4
            ax.plot(x_dist, y_dist, '#ff7f0e', linewidth=2, zorder=15)
            for x_pos in x_dist[::5]:
                h = h_inicial + (h_final - h_inicial) * x_pos / L
                ax.arrow(x_pos, h+0.4, 0, -0.3, head_width=L*0.008, head_length=0.02, fc='#ff7f0e', ec='#ff7f0e', width=0.001, zorder=15)
            ax.text((inicio+fin)/2, h+0.5, f'{mag}N/m', ha='center', va='bottom', fontsize=10, color='#ff7f0e', fontweight='bold')

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

        # Dibujar cargas distribuidas
        for inicio, fin, mag in self.cargas_distribuidas:
            x_dist = np.linspace(inicio, fin, 10)
            for x_pos in x_dist:
                ax.quiver(x_pos, 0, 0.4, 0, 0, -0.3, color='orange', arrow_length_ratio=0.3, alpha=0.7)
            ax.text((inicio+fin)/2, 0, 0.5, f'{mag}N/m', ha='center', va='bottom', fontsize=8, color='orange')

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
            x_dist = np.linspace(inicio, fin, 50)
            y_dist = np.full_like(x_dist, 0.4)
            ax.plot(x_dist, y_dist, 'r-', linewidth=2)
            for x_pos in x_dist[::5]:
                ax.arrow(x_pos, 0.4, 0, -0.3, head_width=L*0.008, head_length=0.02, fc='red', ec='red', width=0.001)
            ax.text((inicio+fin)/2, 0.5, f'{mag}N/m', ha='center', va='bottom', fontsize=8, color='red')
            
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
            
        fig = plt.figure(figsize=(12, 24))
        gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1], hspace=0.4)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ax3 = fig.add_subplot(gs[2])
        ax4 = fig.add_subplot(gs[3])
        
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
            x_dist = np.linspace(inicio, fin, 50)
            y_dist = np.full_like(x_dist, 0.2)
            ax1.plot(x_dist, y_dist, 'r-', linewidth=2)
            for x_pos in x_dist[::5]:
                ax1.arrow(x_pos, 0.2, 0, -0.15, head_width=L*0.008, head_length=0.02, fc='red', ec='red', width=0.001)
            ax1.text((inicio+fin)/2, 0.25, f'{mag}N/m', ha='center', va='bottom', fontsize=7, color='red')
        
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
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ultima_figura = fig
        
        # Mostrar valores máximos en el área de resultados
        self.texto_resultado.insert("end", f"\n📈 VALORES MÁXIMOS:\n")
        self.texto_resultado.insert("end", f"Cortante máximo: +{cortante_max:.2f} N\n")
        self.texto_resultado.insert("end", f"Cortante mínimo: {cortante_min:.2f} N\n")
        self.texto_resultado.insert("end", f"Momento máximo: +{momento_max:.2f} N·m\n")
        self.texto_resultado.insert("end", f"Momento mínimo: {momento_min:.2f} N·m\n")
        self.texto_resultado.insert("end", f"Par Torsor: {par_torsor:.2f} N·m\n")
        
    def limpiar_cargas_puntuales(self):
        self.cargas_puntuales.clear()
        self.texto_resultado.insert("end", "🗑️ Cargas puntuales eliminadas\n")
        self.dibujar_viga_actual()
        
    def limpiar_cargas_distribuidas(self):
        self.cargas_distribuidas.clear()
        self.texto_resultado.insert("end", "🗑️ Cargas distribuidas eliminadas\n")
        self.dibujar_viga_actual()
        
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

        # Restablecer variables de la sección transversal
        self.ancho_superior.set(20)
        self.altura_superior.set(5)
        self.ancho_alma.set(5)
        self.altura_alma.set(30)
        self.ancho_inferior.set(15)
        self.altura_inferior.set(5)

        # Limpiar área de resultados
        self.texto_resultado.delete(1.0, tk.END)

        # Limpiar área gráfica
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()

        # Mostrar mensaje inicial
        self.mostrar_mensaje_inicial()

        # Redibujar la viga en su estado inicial
        self.dibujar_viga_actual()
        
    def mostrar_ayuda(self):
        ayuda = """
🎓 GUÍA COMPLETA DEL SIMULADOR DE VIGA

📐 CONCEPTOS BÁSICOS:
• Viga: Elemento estructural horizontal que soporta cargas
• Reacciones: Fuerzas en los apoyos que equilibran las cargas
• Cortante: Fuerza interna perpendicular al eje de la viga
• Momento: Tendencia a causar rotación en la viga

🔧 CONFIGURACIÓN:
• Longitud (5-30 m)
• Apoyos: Fijo (impide movimiento) y Móvil (permite deslizamiento)
• Altura inicial y final para vigas inclinadas
• Par torsor opcional

⬇️ TIPOS DE CARGAS:
• Puntuales: Fuerza concentrada en un punto específico
• Distribuidas: Fuerza repartida uniformemente en un tramo

📊 CÁLCULOS:
• Reacciones usando ΣF=0 y ΣM=0
• Centro de masa de las cargas
• Diagramas de cortante y momento
• Propiedades de la sección transversal
• Cálculo del centro de gravedad de figuras irregulares (clic en el lienzo para agregarlas)

✨ FUNCIONES EXTRA:
• Visualización en modo 3D
• Ampliar la gráfica en una ventana independiente

💡 CONSEJOS:
• Empieza con casos simples (1‑2 cargas)
• Verifica que las reacciones sumen la carga total
• El momento máximo indica dónde la viga sufre más
• Usa valores realistas para casos prácticos

🎯 EJEMPLO BÁSICO:
1. Viga de 10 m
2. Carga puntual: 100 N en 4 m
3. Calcular reacciones: RA=60 N, RB=40 N
4. Ver diagramas para análisis completo
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
            self.texto_resultado.insert("end", f"\n{'='*50}\n")
            self.texto_resultado.insert("end", f"PROPIEDADES DE LA SECCIÓN TRANSVERSAL:\n")
            self.texto_resultado.insert("end", f"{'='*50}\n")
            self.texto_resultado.insert("end", f"Área total: {area_total:.2f} cm²\n")
            self.texto_resultado.insert("end", f"Centro de gravedad (desde la base): {y_cg:.2f} cm\n")
            self.texto_resultado.insert("end", f"Momento de inercia: {I_total:.2f} cm⁴\n")

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

        ttk.Label(frame_formas, text="⚡ También puede hacer clic en el lienzo para agregar").grid(row=4, column=0, columnspan=4, pady=2)
        self.canvas_formas = tk.Canvas(frame_formas, width=400, height=300, bg="white")
        self.canvas_formas.grid(row=5, column=0, columnspan=4, pady=5)
        self.canvas_formas.bind("<Button-1>", self.colocar_forma)

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
            self.texto_resultado.insert("end", f"Forma agregada: {tipo} en ({x}, {y})\n")
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

            if tipo == "Rectángulo":
                self.canvas_formas.create_rectangle(x, y, x + ancho, y + alto, outline="black")
            elif tipo == "Triángulo":
                self.canvas_formas.create_polygon(x, y + alto, x + ancho / 2, y, x + ancho, y + alto, outline="black", fill="")
            elif tipo == "Círculo":
                self.canvas_formas.create_oval(x - ancho / 2, y - ancho / 2, x + ancho / 2, y + ancho / 2, outline="black")
            else:
                raise ValueError("Tipo de forma no válido")

            self.formas.append((tipo, x, y, ancho, alto))
            self.texto_resultado.insert("end", f"Forma agregada: {tipo} en ({x}, {y})\n")
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
                cx = x + ancho/2
                cy = y + ancho/2
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
        
        self.texto_resultado.insert("end", f"\nCentro de Gravedad: ({cg_x:.2f}, {cg_y:.2f})\n")
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
                ax.add_patch(plt.Circle((x+ancho/2, y+ancho/2), ancho/2, fill=False))
        
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

    def crear_seccion_resultados(self, parent):
        frame_resultados = ttk.LabelFrame(parent, text="Resultados")
        frame_resultados.pack(fill="x", pady=10, padx=10)

        self.texto_resultado = tk.Text(frame_resultados, height=10, wrap="word")
        self.texto_resultado.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_resultados, orient="vertical", command=self.texto_resultado.yview)
        scrollbar.pack(side="right", fill="y")

        self.texto_resultado.configure(yscrollcommand=scrollbar.set)

    def crear_seccion_graficos(self, parent):
        self.frame_grafico = ttk.Frame(parent)
        self.frame_grafico.pack(fill="both", expand=True, pady=10, padx=10)

    def run(self):
        self.root.mainloop()

def main():
    root = tk.Tk()
    app = SimuladorVigaMejorado(root)
    app.run()

if __name__ == "__main__":
    main()
