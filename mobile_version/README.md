# Versión Móvil del Simulador de Viga

Esta carpeta contiene una versión simplificada del simulador de viga que puede ejecutarse en un dispositivo móvil a través del navegador.

## Requisitos

- Python 3
- Bibliotecas estándar de Python (`http.server`, `cgi`, `wsgiref`)
- `matplotlib` y `numpy`

## Uso

1. Abre una terminal en tu dispositivo (o en tu PC) y ejecuta:
   ```bash
   python3 mobile_server.py
   ```
2. Desde el navegador del móvil, ingresa a la dirección que se muestra (por defecto `http://localhost:8000`).
3. Completa los datos de la viga y las cargas en el formulario y presiona **Calcular** para ver los resultados.

Esta versión es una adaptación básica y no incluye todas las funciones avanzadas del simulador de escritorio, pero permite calcular reacciones y visualizar la viga de forma sencilla en dispositivos móviles.

## Consejos para ejecutarlo en tu móvil

- **En Android** puedes usar la aplicación [Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) o la terminal de `Termux` para lanzar Python y ejecutar el servidor con:

  ```bash
  python3 mobile_server.py
  ```

- **En iOS** existen apps como `Pythonista` o `Pyto` que también permiten correr el script anterior.
- Si prefieres arrancar el servidor en tu PC, solo asegúrate de que el móvil esté en la misma red y abre `http://<IP_DEL_PC>:8000` en el navegador del teléfono.

## Guía paso a paso para Android e iOS

A continuación se describe un procedimiento detallado para poner en marcha la
versión móvil en cada plataforma.

### Android

1. Instala **Pydroid 3** o **Termux** desde la tienda de aplicaciones.
2. Copia la carpeta `mobile_version` a tu dispositivo o clona el repositorio en
   la terminal:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   ```
3. Abre la terminal de Pydroid 3 o Termux y entra en la carpeta copiada:
   ```bash
   cd ruta/a/mobile_version
   ```
4. Instala las dependencias (solo la primera vez):
   ```bash
   pip install matplotlib numpy
   ```
5. Ejecuta el servidor:
   ```bash
   python3 mobile_server.py
   ```
6. En la misma terminal aparecerá la dirección `http://localhost:8000`.
7. Abre el navegador del teléfono y escribe esa dirección para acceder al
   formulario del simulador.

### iOS

1. Instala **Pythonista** o **Pyto** desde la App Store.
2. Copia la carpeta `mobile_version` a tu dispositivo (por ejemplo mediante
   iCloud Drive).
3. Abre la aplicación elegida y navega hasta `mobile_server.py`.
4. Si es necesario, instala las bibliotecas con:
   ```bash
   pip install matplotlib numpy
   ```
5. Ejecuta el archivo `mobile_server.py`.
6. Cuando veas la dirección `http://localhost:8000`, abre Safari (u otro
   navegador) e ingresa esa URL.
7. Rellena el formulario y pulsa **Calcular** para obtener los resultados.

## Ejemplo rápido

Al acceder a la página aparecerá un formulario donde puedes indicar:

1. **Longitud de la viga** `L` (en metros).
2. **Cargas puntuales**, escribiendo cada una en una línea con el formato `posición, magnitud`.
3. **Cargas distribuidas**, en líneas `inicio, fin, magnitud`.
4. **Par torsor** y la casilla para usar un apoyo `C` si lo necesitas.

Tras rellenar los campos, pulsa **Calcular** y se mostrará la viga con las cargas y las reacciones obtenidas.
