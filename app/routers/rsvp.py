"""API подтверждения присутствия."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RSVPCreate, RSVPResponse
from app.services.rsvp_service import save_rsvp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rsvp"])


@router.post("/rsvp", response_model=RSVPResponse)
def create_rsvp(
    data: RSVPCreate,
    db: Session = Depends(get_db),
) -> RSVPResponse:
    # Honeypot: если скрытое поле заполнено — это бот. Тихо возвращаем "успех",
    # ничего не сохраняя, чтобы не подсказывать боту о срабатывании фильтра.
    if data.website:
        logger.info("RSVP отклонён honeypot-фильтром")
        return RSVPResponse(success=True, message="Спасибо!")

    record = save_rsvp(db, data)

    if record.attending:
        message = "Спасибо! Будем рады видеть вас на празднике ❤"
    else:
        message = "Спасибо, что дали знать. Будем скучать!"
    return RSVPResponse(success=True, message=message)
