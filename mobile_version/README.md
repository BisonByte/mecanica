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
