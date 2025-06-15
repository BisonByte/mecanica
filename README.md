# Simulador de Viga Mecánica

Este repositorio contiene todas las piezas necesarias para analizar de manera interactiva el comportamiento de una viga simplemente apoyada. Incluye una **aplicación de escritorio** escrita en Python con Tkinter y una versión **web experimental** basada en FastAPI y React.

La idea principal es que puedas definir apoyos, aplicar cargas, obtener las reacciones y generar los diagramas de cortante y momento sin tener que realizar los cálculos manualmente. Además, cuenta con herramientas para visualizar la viga en 3D y para estudiar la sección transversal.

---

## Tecnologías utilizadas

- **Python 3** como lenguaje principal.
- **Tkinter** para la interfaz de la versión de escritorio. De forma opcional se usa `ttkbootstrap` para darle un estilo moderno.
- **NumPy** para los cálculos numéricos.
- **Matplotlib** para las gráficas 2D y la visualización 3D.
- **FastAPI** como backend para la versión web.
- **React** + **Tailwind** para la interfaz web (archivo `frontend/index.html`).

---

## Estructura del proyecto

```
/                       Código de la aplicación de escritorio
/backend                API REST con FastAPI (cálculos de viga)
/frontend               Pequeña interfaz React de prueba
/Dockerfile             Imagen para ejecutar el backend
simulador_viga_mejorado.py   Script principal del simulador GUI
```

### Aplicación de escritorio

El archivo `simulador_viga_mejorado.py` define la clase `SimuladorVigaMejorado`. Esta clase crea la ventana principal, gestiona las pestañas y conecta todos los botones con las funciones de cálculo. Algunas características importantes son:

- Definición de apoyos fijos, móviles u opcionales.
- Cargas puntuales y distribuidas (varias simultáneamente).
- Cálculo automático de reacciones y centro de masa.
- Generación de diagramas de cortante, momento flector y torsión.
- Vista 3D animada de la viga y representación de la sección transversal.
- Modo claro y oscuro a través de `ttkbootstrap`.

### Backend y frontend web

El directorio `backend` expone las funciones de cálculo mediante FastAPI. Los puntos principales son:

- `/calcular_reacciones` – calcula las reacciones en los apoyos.
- `/calcular_centro_masa` – devuelve la posición de la resultante de las cargas.
- `/generar_diagramas` – genera los datos de cortante y momento.
- `/par_en_punto` – obtiene el par torsor en un punto específico.

En `frontend/index.html` se encuentra una interfaz React muy sencilla que hace peticiones al backend usando Axios.

### Docker

El `Dockerfile` permite ejecutar el backend de manera aislada. Copia los archivos necesarios, instala las dependencias mínimas y lanza FastAPI con Uvicorn.

---

## Cómo utilizar el simulador

### Ejecutar la versión de escritorio

1. Clona este repositorio o descarga los archivos.
2. Instala las dependencias principales:
   ```bash
   pip install numpy matplotlib
   # opcional para aspecto moderno
   pip install ttkbootstrap
   ```
3. Ejecuta el script principal:
   ```bash
   python3 simulador_viga_mejorado.py
   ```
4. Configura la viga, añade las cargas deseadas y pulsa **Calcular Reacciones**.
5. Revisa los diagramas en la pestaña **Resultados** y utiliza **Par en Punto** si necesitas el torque interno en una posición.

### Ejecutar la versión web

1. Instala `fastapi` y `uvicorn`.
   ```bash
   pip install fastapi uvicorn numpy
   uvicorn backend.main:app --reload
   ```
2. Abre `frontend/index.html` en tu navegador y utiliza la interfaz para enviar datos al backend.

### Usar la imagen Docker

```bash
docker build -t simulador-viga .
docker run -p 8000:8000 simulador-viga
```

Con esto tendrás el backend corriendo en `http://localhost:8000` y podrás utilizar la interfaz React o cualquier cliente que realice peticiones HTTP.

---

## Funcionamiento interno

Los cálculos principales se encuentran en `backend/beam.py`. Este módulo implementa funciones para:

- Obtener las reacciones (RA, RB y opcional RC) de la viga.
- Calcular el centro de masa resultante.
- Generar los arreglos de cortante y momento a lo largo de la viga.
- Evaluar el par torsor en un punto dado.

La interfaz gráfica usa estas funciones y presenta los resultados de manera interactiva. Las entradas del usuario se almacenan en variables `tk.DoubleVar` y `tk.StringVar`, lo que permite actualizar las gráficas en tiempo real.

---

## Contribuciones

Este proyecto es una base educativa y puede ampliarse con nuevas características o mejoras en la interfaz. ¡Se agradecen los _pull requests_ y las sugerencias!

