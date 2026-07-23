"""Бизнес-логика подтверждения присутствия."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import RSVP
from app.schemas import RSVPCreate
from app.services.sheets_service import get_sheets_service

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
    record.synced_to_sheets = False

    db.commit()
    db.refresh(record)
    return record


def sync_to_sheets(record_id: int, full_name: str, attending: bool, guests_count: int) -> None:
    """Фоновая задача: отправить запись в Google Sheets и отметить успех в БД.

    Выполняется через BackgroundTasks, поэтому создаёт собственную сессию БД.
    Все ошибки Google обрабатываются внутри sheets_service (возврат False).
    """
    settings = get_settings()
    service = get_sheets_service(settings)
    ok = service.append_rsvp(full_name, attending, guests_count)
    if not ok:
        return

    # Отметить успешную синхронизацию отдельной короткой транзакцией.
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        record = db.get(RSVP, record_id)
        if record is not None:
            record.synced_to_sheets = True
            db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("Не удалось отметить synced_to_sheets для id=%s", record_id)
    finally:
        db.close()
