# 🚀 Simulador de Estructuras Mecánicas (Vigas, Armaduras y Bastidores)

¡Hola! Este repositorio contiene una potente herramienta interactiva desarrollada en **Python** para analizar el comportamiento de elementos estructurales como vigas, armaduras y bastidores. Es ideal para estudiantes, ingenieros o cualquiera con curiosidad por la mecánica y la resistencia de materiales.

Con una interfaz gráfica intuitiva construida con **Tkinter** (y mejorada visualmente con **`ttkbootstrap`** si lo tienes instalado), el simulador te permite visualizar en tiempo real cómo las cargas y apoyos afectan a una estructura, calcular reacciones, diagramas de fuerzas y hasta propiedades de secciones transversales. Las gráficas se generan con `matplotlib`, y los cálculos avanzados se realizan eficientemente con `numpy`. ¡Incluso incluye una vista 3D!

---

## 🏗️ ¿Cómo está hecho el simulador?

El corazón de este programa es una **clase principal `SimuladorVigaMejorado`** que orquesta toda la aplicación. Desde aquí se gestiona la ventana principal, se organizan las distintas pestañas y se conectan todos los botones y campos de entrada con la lógica de cálculo.

### 1. Interfaz Gráfica (Ventana del Simulador)

La ventana principal está organizada en **seis pestañas bien definidas**, facilitando la navegación y el uso de las diversas funcionalidades:

* **⚙️ Configuración y Cargas**: Aquí puedes definir las propiedades de tu viga (longitud, altura inicial/final) y el tipo de apoyos (fijo, móvil, o ninguno). Además, es el lugar para añadir todas las cargas que actúan sobre ella: puntuales o distribuidas.
* **🏗️ Sección y Formas**: Permite explorar las propiedades geométricas de secciones transversales (como el centro de gravedad y el momento de inercia). También puedes dibujar y manipular formas irregulares (rectángulos, triángulos, círculos) para analizar su centro de gravedad combinado.
* **🏗️ Armaduras**: Dedicada al análisis de estructuras tipo celosía. Puedes definir nodos, miembros y cargas para calcular las fuerzas internas en cada barra y las reacciones en los apoyos. Incluye la visualización de los Diagramas de Cuerpo Libre (DCL) de los nodos y la aplicación del método de secciones.
* **🏗️ Bastidores**: Similar a las armaduras, pero para marcos articulados 2D. Calcula fuerzas en los miembros, reacciones en apoyos y te permite ver el DCL de cada nodo, incluso mostrando la carga estimada por pasador.
* **⚙️ Axial y Térmica**: Una sección clave para estudiar cómo los materiales se deforman bajo cargas axiales y cambios de temperatura. Calcula la deformación axial, térmica y total, así como la tensión resultante en una barra.
* **📊 Resultados**: La pestaña donde verás todo lo que el simulador ha calculado: reacciones de la viga, diagramas de fuerza cortante, momento flector y torsión, y la animación 3D de tu viga. También es donde se registra el historial de tus cálculos y advertencias.

### 2. Variables y Entradas del Usuario

El programa utiliza **variables `tk.DoubleVar` y `tk.StringVar`** de Tkinter. Estas variables actúan como puentes, conectando directamente los valores que ingresas en los campos de texto, sliders y menús desplegables de la interfaz con los cálculos internos del programa. Esto garantiza una interacción fluida y en tiempo real.

### 3. Funcionalidades Principales al Detalle

#### ✅ Cargas (Vigas)

* **Cargas Puntuales**: Define su posición exacta y su magnitud (fuerza).
* **Cargas Distribuidas**: Aplica cargas a lo largo de un segmento de la viga con una intensidad constante. El simulador calcula automáticamente su fuerza equivalente y centroide.
* Soporta la aplicación de múltiples cargas simultáneamente.

#### ✅ Apoyos (Vigas)

* **Dos apoyos principales (A y B)**: Ubicados en los extremos de la viga.
* **Un apoyo opcional (C)**: Que puedes colocar en cualquier punto de la viga.
* Cada apoyo puede ser **Fijo** (restringe movimiento horizontal y vertical) o **Móvil** (restringe solo movimiento vertical), afectando directamente las ecuaciones de equilibrio. También puedes seleccionar "Ninguno" para simular voladizos.

#### ✅ Cálculos que realiza (Vigas)

* **Reacciones en los apoyos**: Calcula las fuerzas verticales y horizontales necesarias para mantener la viga en equilibrio, considerando todas las cargas y el par torsor externo.
* **Centro de masa**: Determina el punto donde actúa la resultante de todas las cargas aplicadas.
* **Diagramas**: Genera los diagramas de **fuerza cortante**, **momento flector** y **torsión** a lo largo de la viga, fundamentales para entender las tensiones internas.
* **Par Torsor (Torque) en cualquier punto**: Puedes introducir una posición específica para obtener el momento torsor interno en ese lugar.
* **Centro de masa en 3D**: Capacidad para calcular el centroide de una colección de puntos con masa en un espacio tridimensional.
* **Fuerza equivalente de cargas distribuidas**: Calcula automáticamente la resultante de una carga distribuida para simplificar el análisis.
* **Propiedades de la sección transversal**: Calcula el **área total**, **centro de gravedad** y **momento de inercia** de secciones compuestas, crucial para el diseño estructural.
* **Nuevo: Análisis de Armaduras**: Resuelve fuerzas internas en miembros y reacciones en nodos mediante el método de nodos.
* **Nuevo: Análisis de Bastidores Articulados (Marcos 2D)**: Calcula fuerzas en miembros, reacciones y la carga estimada sobre cada rótula (pasador).
* **Nuevo: Deformación Axial y Térmica**: Calcula el cambio de longitud y la tensión en una barra debido a la aplicación de una fuerza axial y/o cambios de temperatura.

#### ✅ Representaciones Gráficas

El simulador utiliza `matplotlib` para crear visualizaciones claras y dinámicas:

* **Configuración de la viga**: Muestra la viga con sus cargas aplicadas, los apoyos y las reacciones calculadas. Las cargas distribuidas se representan con su vector equivalente.
* **Diagramas de esfuerzo**: Gráficos detallados de fuerza cortante, momento flector y torsión.
* **Vista 3D Rotativa**: Una visualización tridimensional de la viga que puedes animar para girar automáticamente y ver la estructura desde diferentes ángulos.
* **Vista de la sección transversal**: Dibuja la geometría de la sección y su centro de gravedad.
* **Armaduras y Bastidores**: Representaciones claras de la estructura con las fuerzas internas coloreadas (azul para tensión, rojo para compresión) y las reacciones en los apoyos. También puedes visualizar el Diagrama de Cuerpo Libre de cada nodo y de secciones transversales.
* **Gráfica de Deformación Axial/Térmica**: Visualiza la barra y cómo se alarga o acorta debido a las cargas y la temperatura.

### 4. Extras Interesantes

* **Modo 3D**: Permite una inmersión visual con la rotación automática de la viga.
* **Modo Oscuro/Claro**: Alterna entre un tema visual moderno (flatly) y uno oscuro (darkly) para mayor comodidad visual, especialmente útil en entornos de poca luz.
* **Ayuda Integrada**: Una guía escrita dentro del propio programa que resume las funcionalidades y las fórmulas clave utilizadas.
* **Mensajes de Error y Advertencias**: Te notifica si introduces datos incorrectos o si la estructura es inestable/indeterminada.
* **Ampliación de Gráficas**: Puedes abrir cualquier gráfica en una ventana separada para un análisis más detallado.

### 5. Herramientas de la Interfaz (Botones Clave)

* **🧮 Calcular Reacciones**: Inicia el proceso de cálculo de las fuerzas en los apoyos de la viga.
* **📍 Calcular Centro de Masa**: Determina el centro de gravedad de las cargas de la viga o de las formas irregulares de la sección.
* **📊 Mostrar Diagramas**: Genera y visualiza los diagramas de cortante, momento flector y torsión para la viga.
* **🌀 Par en Punto**: Calcula el par torsor interno en una posición específica de la viga.
* **🔍 Ampliar Gráfica**: Abre la gráfica activa en una nueva ventana para una visualización más grande.
* **🎞️ Animar 3D**: Activa la rotación automática de la vista 3D de la viga.
* **❓ Ayuda**: Despliega la guía de usuario integrada.
* **🗑️ Limpiar Todo**: Borra todas las cargas, apoyos, y reinicia la configuración de la viga, armadura y bastidor.
* **🌓/🌞 Modo Oscuro/Claro**: Cambia el tema visual de la aplicación.
* **🏗️ Calcular Armadura**: Resuelve las fuerzas internas en los miembros de la armadura y las reacciones en sus nodos.
* **🏗️ Ejemplo Bastidor**: Carga un bastidor predefinido para que puedas ver el programa en acción rápidamente.

---

## 🚀 ¡Empieza a Usar el Simulador!

1.  **Clona este repositorio** o descarga el código fuente directamente.
2.  **Asegúrate de tener Python 3 instalado**. Las dependencias clave son `tkinter` (incluido en la mayoría de las instalaciones de Python), `matplotlib` y `numpy`.
    * Puedes instalar `matplotlib` y `numpy` con pip:
        ```bash
        pip install matplotlib numpy
        ```
    * Para una interfaz moderna y pulida, instala opcionalmente `ttkbootstrap`:
        ```bash
        pip install ttkbootstrap
        ```
3.  **Ejecuta el programa** desde tu terminal:
    ```bash
    python3 simulador_viga_mejorado.py
    ```
4.  **Configura tu estructura**: Usa las diferentes pestañas para definir la geometría, los apoyos y las cargas.
5.  **Calcula y visualiza**: Presiona los botones de cálculo en cada sección y revisa los resultados, tanto numéricos en la pestaña de `Resultados` como gráficos en la sección de visualización.
6.  **Ejemplo de Bastidor con Pasador**: Si quieres ver un ejemplo rápido de cómo funciona el análisis de bastidores con pasadores, puedes ejecutar:
    ```bash
    python3 simulador_viga_mejorado.py --ejemplo-pasador
    ```

---

## 📱 ¿Y para dispositivos móviles?

Dado que este simulador está diseñado con `Tkinter`, que es una biblioteca de interfaz gráfica de escritorio, **no funciona directamente en navegadores móviles ni como una aplicación nativa para iOS o Android.**

Sin embargo, hay algunas maneras de usarlo desde tu teléfono:

* **Acceso Remoto (Recomendado)**: Puedes instalar y ejecutar el simulador en tu computadora de escritorio o portátil, y luego usar una aplicación de **escritorio remoto** (como TeamViewer, AnyDesk o la extensión Chrome Remote Desktop) en tu teléfono o tablet para conectarte a tu PC. ¡Así podrás interactuar con el simulador como si estuvieras frente a tu computadora!
* **Entornos Python en la Nube**: Otra opción es utilizar servicios en la nube que te permitan ejecutar código Python (como Google Colab con ciertas configuraciones para GUI, aunque es más avanzado y experimental para `Tkinter`). De esta forma, el procesamiento ocurre en un servidor y la interfaz podría ser accesible a través del navegador móvil.

¡Espero que disfrutes aprendiendo y experimentando con este simulador! Es una herramienta diseñada con pasión para hacer la mecánica estructural más accesible y visual.
