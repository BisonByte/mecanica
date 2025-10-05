"""API router that exposes beam related endpoints."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from ..schemas import BeamPayload
from ..services.analysis import run_beam_analysis

router = APIRouter(prefix="/api/beam", tags=["beam"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.post("/analyze")
async def analyze_beam(payload: BeamPayload) -> JSONResponse:
    result = run_beam_analysis(payload)
    enriched = {
        **result,
        "metadata": {
            "export_format": payload.analysis.export_format,
            "unit_system": payload.analysis.unit_system,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    return JSONResponse(enriched)


@router.get("/templates")
async def beam_templates() -> Dict[str, List[Dict[str, Any]]]:
    """Return curated templates ready to be loaded from the UI."""

    return {
        "categories": [
            {
                "name": "DidÃ¡cticos",
                "items": [
                    {
                        "id": "simple-span",
                        "title": "Viga biapoyada con carga puntual",
                        "description": "Caso clÃ¡sico con carga puntual centrada.",
                        "payload": {
                            "length": 8.0,
                            "support_a_type": "Fijo",
                            "support_b_type": "Movil",
                            "point_loads": [
                                {"label": "Carga central", "position": 4.0, "magnitude": 25.0}
                            ],
                        },
                    },
                    {
                        "id": "uniform-load",
                        "title": "Carga distribuida uniforme",
                        "description": "Carga distribuida constante en todo el claro.",
                        "payload": {
                            "length": 12.0,
                            "support_a_type": "Fijo",
                            "support_b_type": "Movil",
                            "distributed_loads": [
                                {"label": "UDL", "start": 0.0, "end": 12.0, "intensity": 3.5}
                            ],
                        },
                    },
                ],
            },
            {
                "name": "Avanzados",
                "items": [
                    {
                        "id": "cantilever",
                        "title": "Voladizo con torsor",
                        "description": "Analiza un voladizo sometido a torsor externo.",
                        "payload": {
                            "length": 6.0,
                            "support_a_type": "Fijo",
                            "support_b_type": "Ninguno",
                            "torsor": 18.0,
                            "point_loads": [
                                {"label": "Carga libre", "position": 4.5, "magnitude": 12.0}
                            ],
                        },
                    }
                ],
            },
        ]
    }


def render_dashboard(
    request: Request,
    *,
    default_payload: Dict[str, Any],
    user: Dict[str, Any],
    current_year: int,
) -> HTMLResponse:
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "default_payload": default_payload,
            "current_year": current_year,
            "user": user,
        },
    )

