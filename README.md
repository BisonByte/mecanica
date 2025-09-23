# Simulador de Estructuras Web

Esta version modernizada del proyecto reemplaza la interfaz Tkinter por una aplicacion web full responsive con un back-end FastAPI. Conserva los calculos de vigas del simulador original y los expone mediante un API REST listo para integrarse con otros modulos de estructuras.

## Caracteristicas principales

- **Motor de analisis** reutilizable en `mechanics.viga` con dataclasses para cargas puntuales y distribuidas.
- **API FastAPI** (`webapp/app.py`) con validacion Pydantic y templates Jinja2.
- **Interfaz web profesional** en `webapp/templates/index.html` con graficas Chart.js y persistencia local.
- **Estilos premium** en `webapp/static/css/main.css` basados en modo oscuro elegante.
- **Tests de regresion** en `tests/test_viga.py` para asegurar la consistencia de los resultados numericos.

## Requisitos

- Python 3.10+
- pip y virtualenv (recomendado)

## Instalacion y uso local

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn webapp.app:app --reload
```

Visita `http://127.0.0.1:8000` en tu navegador para acceder al simulador.

## Ejecucion de pruebas

```bash
. .venv/Scripts/activate
pip install pytest
pytest
```

## Estructura del proyecto

- `mechanics/`  Motor de calculos independiente de la UI.
- `webapp/`     Aplicacion FastAPI, plantillas y activos estaticos.
- `tests/`      Pruebas unitarias de validacion numerica.
- `requirements.txt` Dependencias minimas para ejecutar el backend.

## Despliegue en hosting compartido (cPanel)

1. Crea un entorno virtual en tu hosting e instala las dependencias con `pip install -r requirements.txt`.
2. Configura un dominio o subdominio en cPanel apuntando al proyecto.
3. Define un archivo `passenger_wsgi.py` (Passenger) o `app.py` segun el proveedor para exponer `webapp.app:app`.
4. Si prefieres integracion con Laravel o PHP, puedes consumir el API desde un front-end Laravel y desplegar la SPA por separado; los assets estan en `webapp/static/`.
5. Asegura que el servicio uwsgi/Passenger apunte al entorno virtual y arranque el modulo `webapp.app`.

## Personalizacion

- Ajusta la paleta y los estilos en `webapp/static/css/main.css`.
- Modifica el diseno o crea nuevas vistas en `webapp/templates/`.
- Agrega nuevos endpoints en `webapp/app.py` reutilizando las clases del modulo `mechanics`.

Con esto, el simulador queda listo para uso profesional, integrable en plataformas existentes y con un diseno moderno enfocado en la experiencia de usuario.
