from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .routers import beam_router, render_dashboard
from .schemas import BeamPayload

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI(
        title="Simulador de Estructuras Web",
        description="Suite profesional para análisis de vigas.",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(beam_router)

    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:  # pragma: no cover - templated response
        default_payload = BeamPayload(
            length=10.0,
            support_a_type="Fijo",
            support_b_type="Movil",
            point_loads=[{"label": "Carga 1", "position": 4.0, "magnitude": 15.0}],
            distributed_loads=[
                {"label": "Carga distribuida", "start": 6.0, "end": 9.0, "intensity": 4.0}
            ],
        )
        return render_dashboard(request, default_payload.model_dump())

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
