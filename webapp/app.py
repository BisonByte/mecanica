from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.middleware.sessions import SessionMiddleware

from .routers import auth_router, beam_router, render_dashboard
from .schemas import BeamPayload
from .services import users

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


DEFAULT_PAYLOAD = BeamPayload(
    length=10.0,
    support_a_type="Fijo",
    support_b_type="Movil",
    point_loads=[{"label": "Carga 1", "position": 4.0, "magnitude": 15.0}],
    distributed_loads=[
        {"label": "Carga distribuida", "start": 6.0, "end": 9.0, "intensity": 4.0}
    ],
)


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

    session_secret = os.getenv("SESSION_SECRET", "dev-secret-key-change")
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        same_site="lax",
        https_only=False,
    )

    users.ensure_db()
    users.ensure_default_admin()

    app.include_router(auth_router)
    app.include_router(beam_router)

    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    @app.get("/", response_class=HTMLResponse, name="landing")
    async def landing(request: Request) -> HTMLResponse:  # pragma: no cover - templated response
        return TEMPLATES.TemplateResponse(
            "landing.html",
            {
                "request": request,
                "current_year": datetime.utcnow().year,
            },
        )

    @app.get("/app", response_class=HTMLResponse, name="dashboard")
    async def dashboard(request: Request) -> HTMLResponse:  # pragma: no cover - templated response
        user = request.session.get("user")
        if not user:
            url = app.url_path_for("auth_login")
            return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
        payload = DEFAULT_PAYLOAD.model_dump()
        return render_dashboard(
            request,
            default_payload=payload,
            user=user,
            current_year=datetime.utcnow().year,
        )

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
