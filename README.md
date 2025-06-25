
# Cómo está hecho el simulador de viga mecánica

Este repositorio contiene un programa escrito en **Python** para analizar y visualizar el comportamiento de una viga mecánica. Utiliza **Tkinter** para la interfaz gráfica y, si está disponible, el paquete **`ttkbootstrap`** para darle un aspecto mucho más moderno. Las gráficas se generan con `matplotlib`, los cálculos con `numpy` y la vista en 3D con `mpl_toolkits`.

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
* **Par torsor (torque) en cualquier punto** y fuerza equivalente de cargas distribuidas.
* **Centro de masa en 3D** y cálculo de fuerza a partir de un par torsor.
* También calcula propiedades como el **área total**, **centro de gravedad de la sección transversal**, y **momento de inercia**.
* **Nuevo**: análisis de **armaduras** mediante el método de nodos.
* **Nuevo**: análisis de **bastidores** (marcos 2D) con cálculo automático de reacciones y fuerzas internas.
* **Nuevo**: botón **Ejemplo** que carga un bastidor de muestra y muestra sus resultados.
* **Extra**: cálculo por el **método de secciones** y visualización de **diagramas de cuerpo libre** de cada nodo y secciones del bastidor.

---

### 5. Representaciones gráficas

El simulador puede dibujar:

* La **viga con sus cargas** y sus **reacciones**.
* Las **cargas distribuidas** también se muestran con su **vector equivalente** y magnitud en el diagrama de cuerpo libre.
* **Diagramas de fuerza cortante y momento flector**.
* **Vista 3D rotativa** de la viga con cargas y apoyos.
* **Vista de la sección transversal** y el centro de gravedad de figuras combinadas.
* **Armaduras y bastidores** con fuerzas internas coloreadas.

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

El programa puede aprovechar **`ttkbootstrap`** para mostrar un aspecto totalmente renovado (botones planos, colores actuales y fuentes más limpias). Si no se cuenta con esa biblioteca, se usa el tema `clam` de `tkinter` como alternativa.
El botón de tema permite alternar entre un estilo claro (*flatly*) y uno oscuro (*darkly*).

---

### 8. Herramientas de la interfaz

* **🧮 Calcular Reacciones**: resuelve las fuerzas de apoyo de la viga.
* **📍 Calcular Centro de Masa**: muestra el punto donde actúa la resultante de las cargas.
* **📊 Mostrar Diagramas**: genera los diagramas de cortante, momento y torsión.
* **🌀 Par en Punto**: introduce una posición y obtén el torque interno en ese lugar.
* **🔍 Ampliar Gráfica**: abre las gráficas en una ventana aparte.
* **🎞️ Animar 3D**: activa una rotación automática de la vista 3D.
* **❓ Ayuda**: despliega un resumen de uso.
* **🗑️ Limpiar Todo**: borra todas las cargas y reinicia la configuración.
* **🌓/🌞 Modo Oscuro/Claro**: alterna el tema visual de la aplicación.
* **🏗️ Calcular Armadura**: resuelve fuerzas internas en nodos y miembros.
* **🏗️ Ejemplo Bastidor**: carga un marco de ejemplo y muestra sus resultados.

### 9. Par torsor en un punto

Esta función permite obtener el momento torsor (torque interno) en una posición específica de la viga.
Solo escribe la coordenada en metros en el cuadro **Par en Punto** y presiona el botón del mismo nombre.
El valor se mostrará en el registro y en los diagramas.

### 10. Uso

1. Clona este repositorio o descarga el código.
2. Asegúrate de tener **Python 3**, `tkinter`, `matplotlib` y `numpy` instalados.
   Para un aspecto moderno instala opcionalmente `ttkbootstrap` con `pip install ttkbootstrap`.
3. Ejecuta `python3 simulador_viga_mejorado.py`.
4. Configura la viga y agrega las cargas necesarias.
5. Usa **Par en Punto** para consultar el momento torsor si lo necesitas.
6. Revisa los resultados en la pestaña de **Resultados**.
