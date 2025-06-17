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

## Ejemplo rápido

Al acceder a la página aparecerá un formulario donde puedes indicar:

1. **Longitud de la viga** `L` (en metros).
2. **Cargas puntuales**, escribiendo cada una en una línea con el formato `posición, magnitud`.
3. **Cargas distribuidas**, en líneas `inicio, fin, magnitud`.
4. **Par torsor** y la casilla para usar un apoyo `C` si lo necesitas.

Tras rellenar los campos, pulsa **Calcular** y se mostrará la viga con las cargas y las reacciones obtenidas.
