"""API подтверждения присутствия."""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RSVPCreate, RSVPResponse
from app.services.rsvp_service import save_rsvp, sync_to_sheets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rsvp"])


@router.post("/rsvp", response_model=RSVPResponse)
def create_rsvp(
    data: RSVPCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RSVPResponse:
    # Honeypot: если скрытое поле заполнено — это бот. Тихо возвращаем "успех",
    # ничего не сохраняя, чтобы не подсказывать боту о срабатывании фильтра.
    if data.website:
        logger.info("RSVP отклонён honeypot-фильтром")
        return RSVPResponse(success=True, message="Спасибо!")

    record = save_rsvp(db, data)

    # Синхронизация в Google Sheets — в фоне, чтобы не задерживать ответ гостю.
    background_tasks.add_task(
        sync_to_sheets,
        record.id,
        record.full_name,
        record.attending,
        record.guests_count,
    )

    if record.attending:
        message = "Спасибо! Будем рады видеть вас на празднике ❤"
    else:
        message = "Спасибо, что дали знать. Будем скучать!"
    return RSVPResponse(success=True, message=message)
