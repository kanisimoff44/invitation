"""Страничные маршруты: главная страница и .ics-календарь."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, Response
from fastapi.templating import Jinja2Templates

from app import config
from app.config import get_settings
from app.services.ics_service import build_ics

router = APIRouter()

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_STATIC_ICS = (
    Path(__file__).resolve().parent.parent / "static" / "files" / "wedding.ics"
)
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/")
def index(request: Request):
    settings = get_settings()
    context = {
        "request": request,
        "greeting": config.INVITATION_GREETING,
        "message": config.INVITATION_MESSAGE,
        "wedding_date": config.WEDDING_DATE,
        "wedding_date_display": config.WEDDING_DATE.strftime("%d.%m.%Y"),
        "venue_name": config.VENUE_NAME,
        "venue_address": config.VENUE_ADDRESS,
        "timeline": config.TIMELINE,
        "dresscode": config.DRESSCODE_TEXT,
        "enable_guests_count_field": settings.enable_guests_count_field,
    }
    return templates.TemplateResponse("index.html", context)


@router.get("/guests")
def guests_page(request: Request):
    """Мини-страница для организаторов: ввод токена и скачивание списка."""
    return templates.TemplateResponse("guests.html", {"request": request})


@router.get("/calendar.ics")
def calendar_ics():
    """Отдаёт .ics. Если предгенерированный файл есть — статикой, иначе на лету."""
    headers = {"Content-Disposition": 'attachment; filename="wedding.ics"'}
    if _STATIC_ICS.exists():
        return FileResponse(
            _STATIC_ICS, media_type="text/calendar; charset=utf-8", headers=headers
        )
    return Response(
        content=build_ics(),
        media_type="text/calendar; charset=utf-8",
        headers=headers,
    )


@router.get("/healthz")
def healthz():
    return {"status": "ok"}
