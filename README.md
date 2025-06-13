
# Cómo está hecho el simulador de viga mecánica

Este repositorio contiene un programa escrito en **Python** para analizar y visualizar el comportamiento de una viga mecánica. Utiliza **Tkinter** para la interfaz gráfica, `matplotlib` para las gráficas, `numpy` para los cálculos y `mpl_toolkits` para la vista en 3D.

### 1. Estructura del código

El programa está estructurado en una **clase principal llamada `SimuladorVigaMejorado`**, donde se encuentra todo lo relacionado con el simulador. Dentro de esta clase se inicializa la ventana y se organizan todas las pestañas y botones.

---

### 2. Interfaz gráfica (ventana del simulador)

La ventana está dividida en **tres pestañas principales**:

* **Configuración y cargas**: aquí se puede cambiar la longitud de la viga, los tipos de apoyos (fijo, móvil o ninguno), y agregar cargas (puntuales o distribuidas).
* **Sección y formas**: permite calcular propiedades geométricas como el centro de gravedad y momento de inercia. También se pueden dibujar formas irregulares (triángulos, círculos y rectángulos) para analizar cómo afectan.
* **Resultados**: en esta pestaña se muestran los gráficos, los resultados de las reacciones, los diagramas de momento y cortante, y también la animación 3D si se activa.

---

### 3. Variables y entradas del usuario

El programa usa **variables `tk.DoubleVar` y `tk.StringVar`** para guardar valores como la longitud de la viga, magnitud de las cargas, tipo de apoyo, altura inicial/final, etc. Estas variables están conectadas directamente a las entradas del usuario (los campos de texto o sliders que se ven en pantalla).

---

### 4. Funcionalidades principales

#### ✅ Cargas

* Se pueden agregar **cargas puntuales** (con posición y magnitud).
* También se pueden agregar **cargas distribuidas** (entre dos puntos, con una intensidad constante).
* Soporta múltiples cargas a la vez.

#### ✅ Apoyos

* Tiene **dos apoyos principales (A y B)** y un apoyo opcional (C), que puede colocarse en cualquier parte.
* Cada apoyo puede ser **fijo, móvil o ninguno**, y esto afecta los cálculos de equilibrio.

#### ✅ Cálculos que realiza

* **Reacciones en los apoyos**, considerando todas las cargas y el par torsor.
* **Centro de masa** de todas las cargas.
* **Diagramas de cortante, momento flector y torsión**.
* **Par torsor en cualquier punto** y fuerza equivalente de cargas distribuidas.
* **Centro de masa en 3D** y cálculo de fuerza a partir de un par torsor.
* También calcula propiedades como el **área total**, **centro de gravedad de la sección transversal**, y **momento de inercia**.

---

### 5. Representaciones gráficas

El simulador puede dibujar:

* La **viga con sus cargas** y sus **reacciones**.
* **Diagramas de fuerza cortante y momento flector**.
* **Vista 3D rotativa** de la viga con cargas y apoyos.
* **Vista de la sección transversal** y el centro de gravedad de figuras combinadas.

Usa `matplotlib` para todos estos gráficos y los incrusta dentro de la ventana con `FigureCanvasTkAgg`.

---

### 6. Extras interesantes

* Tiene un **modo 3D** que rota la viga automáticamente.
* Cuenta con un **modo oscuro** opcional para la interfaz.
* Tiene una **opción de ayuda** con una guía escrita dentro del programa.
* También incluye **mensajes de error y advertencias** si el usuario pone mal los datos.
* Se pueden **ampliar las gráficas** y ver todo más grande en otra ventana.
* Incluye funciones para el **centro de masa en 3D**.

---

### 7. Estilo visual

Se aplicó un **tema moderno** (`clam`) con colores claros, botones azules, tipografías limpias, y organización visual con pestañas (`Notebook`) para que sea fácil de entender y usar.
Además se añadió un **modo oscuro** seleccionable desde los controles principales.

---

### 8. Par torsor en un punto

Esta función permite obtener el momento torsor interno en una posición específica de la viga.
Solo escribe la coordenada en metros en el cuadro **Par en Punto** y presiona el botón del mismo nombre.
El valor se mostrará en el registro y en los diagramas.

### 9. Uso

1. Clona este repositorio o descarga el código.
2. Asegúrate de tener **Python 3**, `tkinter`, `matplotlib` y `numpy` instalados.
3. Ejecuta `python3 simulador_viga_mejorado.py`.
4. Configura la viga y agrega las cargas necesarias.
5. Usa **Par en Punto** para consultar el momento torsor si lo necesitas.
6. Revisa los resultados en la pestaña de **Resultados**.
