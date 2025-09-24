# Simulador de Estructuras Web

Plataforma profesional para el análisis de vigas que combina un backend FastAPI modular con una interfaz web rica en interacción. El proyecto conserva el motor de cálculo original y lo potencia con flujos guiados, plantillas de escenarios y herramientas de reporte listas para producción.

## Características principales

- **Arquitectura modular.** El backend se organiza en routers (`webapp/routers`), servicios (`webapp/services`) y esquemas (`webapp/schemas`) que encapsulan la lógica de análisis y facilitan la escalabilidad.
- **Motor de cálculo validado.** `mechanics/viga.py` mantiene los algoritmos de reacción y diagramas, con modelos reutilizables para cargas puntuales y distribuidas.
- **Experiencia de usuario profesional.** La vista `webapp/templates/index.html` introduce un panel maestro con resumen global, stepper de configuración, gestión avanzada de cargas y exportación inmediata.
- **Visualización y análisis enriquecidos.** `webapp/static/js/app.js` controla gráficos Chart.js, genera insights automáticos, administra plantillas desde `/api/beam/templates` y sincroniza la configuración con `localStorage`.
- **Diseño premium adaptable.** Los estilos en `webapp/static/css/main.css` definen un sistema visual oscuro con tarjetas, sidebar informativo y comportamiento responsive.
- **Pruebas numéricas.** `tests/test_viga.py` asegura la consistencia del motor ante cambios.

## Requisitos

- Python 3.10+
- `pip` y `virtualenv` (recomendado)

## Instalación y uso local

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows usar .venv\Scripts\activate
pip install -r requirements.txt
uvicorn webapp.app:app --reload
```

Visita `http://127.0.0.1:8000` para interactuar con el simulador.

## Ejecución de pruebas

```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Estructura del proyecto

- `mechanics/` – Motor de cálculo independiente de la interfaz.
- `webapp/app.py` – Punto de entrada FastAPI y configuración de la aplicación.
- `webapp/routers/` – Endpoints REST (análisis y plantillas de vigas).
- `webapp/schemas/` – Modelos Pydantic para la API.
- `webapp/services/` – Servicios que orquestan el cálculo y validación.
- `webapp/templates/` – Vistas Jinja2 con el layout profesional.
- `webapp/static/` – Recursos estáticos (CSS, JS, íconos).
- `tests/` – Pruebas unitarias de regresión numérica.

## Despliegue en hosting compartido (cPanel)

1. Crea un entorno virtual en tu hosting e instala dependencias con `pip install -r requirements.txt`.
2. Configura un dominio o subdominio que apunte a la carpeta del proyecto.
3. Declara un archivo `passenger_wsgi.py` que exponga la aplicación como `from webapp.app import app as application`.
4. Asegura que la carpeta `webapp/static` esté accesible como activos estáticos (puedes usar reglas de Passenger o un alias).
5. Reinicia el servicio Passenger/WSGI tras cada despliegue para recoger cambios.

Con esta estructura, el simulador queda preparado para integrarse en entornos profesionales, con posibilidades de extender flujos de trabajo, autenticación o generación de reportes avanzados.
