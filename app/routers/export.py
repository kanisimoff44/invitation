"""Выгрузка списка гостей в xlsx (для организаторов)."""
from __future__ import annotations

import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services.export_service import build_guests_xlsx

router = APIRouter(prefix="/api", tags=["export"])

_XLSX_MEDIA = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@router.get("/guests/export.xlsx")
def export_guests(
    token: str = Query(default=""),
    all: bool = Query(default=False, description="Выгрузить всех, включая отказы"),
    db: Session = Depends(get_db),
):
    """Отдаёт xlsx со списком гостей.

    Защищено токеном из настройки EXPORT_TOKEN. Пока токен не задан — эндпоинт
    отвечает 404, чтобы список гостей не был открыт всем.
    По умолчанию выгружаются только те, кто придёт; `?all=true` — все ответы.
    """
    settings = get_settings()

    if not settings.export_token:
        # Фича не сконфигурирована — не раскрываем наличие эндпоинта.
        raise HTTPException(status_code=404, detail="Not found")

    # Сравнение в постоянное время (защита от подбора по времени).
    if not hmac.compare_digest(token, settings.export_token):
        raise HTTPException(status_code=403, detail="Неверный токен")

    content = build_guests_xlsx(db, attending_only=not all)

    stamp = datetime.now().strftime("%Y%m%d")
    filename = f"guests_{stamp}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        iter([content]), media_type=_XLSX_MEDIA, headers=headers
    )
