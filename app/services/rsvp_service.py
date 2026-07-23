"""Бизнес-логика подтверждения присутствия."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import RSVP
from app.schemas import RSVPCreate

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    return " ".join(name.split()).lower()


def save_rsvp(db: Session, data: RSVPCreate) -> RSVP:
    """Создаёт или обновляет запись RSVP (upsert по нормализованному имени).

    Повторная отправка тем же человеком обновляет существующую запись,
    а не плодит дубликаты. Возвращает сохранённую запись.
    """
    settings = get_settings()

    guests_count = data.guests_count if settings.enable_guests_count_field else 0
    if not data.attending:
        guests_count = 0

    normalized = _normalize(data.full_name)

    record = db.scalar(select(RSVP).where(RSVP.normalized_name == normalized))
    if record is None:
        record = RSVP(normalized_name=normalized)
        db.add(record)

    record.full_name = data.full_name
    record.attending = data.attending
    record.guests_count = guests_count

    db.commit()
    db.refresh(record)
    return record
