from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from ..services.users import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotApprovedError,
    authenticate_user,
    register_user,
)

router = APIRouter(tags=["auth"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/auth/login", response_class=HTMLResponse, name="auth_login")
async def login_form(request: Request) -> HTMLResponse:
    context: Dict[str, Any] = {
        "request": request,
        "page_title": "Iniciar sesión",
        "success_message": None,
        "error_message": None,
    }
    if request.query_params.get("registered") == "1":
        context["success_message"] = "Tu solicitud fue enviada. Te avisaremos cuando sea aprobada."
    return templates.TemplateResponse("auth/login.html", context)


@router.post("/auth/login", response_class=HTMLResponse)
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)) -> HTMLResponse:
    context: Dict[str, Any] = {
        "request": request,
        "page_title": "Iniciar sesión",
        "success_message": None,
        "error_message": None,
        "email": email,
    }
    try:
        user = authenticate_user(email, password)
    except InvalidCredentialsError as exc:
        context["error_message"] = str(exc)
        return templates.TemplateResponse("auth/login.html", context, status_code=status.HTTP_400_BAD_REQUEST)
    except UserNotApprovedError as exc:
        context["error_message"] = str(exc)
        return templates.TemplateResponse("auth/login.html", context, status_code=status.HTTP_403_FORBIDDEN)

    request.session["user"] = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name"),
        "is_admin": bool(user.get("is_admin", False)),
    }
    url = request.app.url_path_for("dashboard")
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/auth/register", response_class=HTMLResponse, name="auth_register")
async def register_form(request: Request) -> HTMLResponse:
    context: Dict[str, Any] = {
        "request": request,
        "page_title": "Crear cuenta",
        "error_message": None,
        "success_message": None,
    }
    if request.query_params.get("status") == "success":
        context["success_message"] = "Tu solicitud fue enviada. Te avisaremos por correo al aprobarla."
    return templates.TemplateResponse("auth/register.html", context)


@router.post("/auth/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    role: str = Form(""),
    password: str = Form(...),
    confirm_password: str = Form(...),
) -> HTMLResponse:
    context: Dict[str, Any] = {
        "request": request,
        "page_title": "Crear cuenta",
        "error_message": None,
        "full_name": full_name,
        "email": email,
        "role": role,
    }
    if password != confirm_password:
        context["error_message"] = "Las contraseñas no coinciden."
        return templates.TemplateResponse("auth/register.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        register_user(email=email, password=password, full_name=full_name, role=role or None)
    except UserAlreadyExistsError as exc:
        context["error_message"] = str(exc)
        return templates.TemplateResponse("auth/register.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    url = request.app.url_path_for("auth_login") + "?registered=1"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/auth/logout", name="auth_logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    url = request.app.url_path_for("auth_login")
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
