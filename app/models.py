"""ORM-модели."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RSVP(Base):
    """Ответ гостя на приглашение (подтверждение присутствия)."""

    __tablename__ = "rsvp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Имя как ввёл гость (для отображения заказчику).
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)

    # Нормализованное имя (lower/trim/схлопнутые пробелы) — ключ дедупликации.
    # unique=True даёт возможность делать upsert через ON CONFLICT.
    normalized_name: Mapped[str] = mapped_column(
        String(150), nullable=False, unique=True, index=True
    )

    attending: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # 0 — иду один, 1 — +1, 2 — +2. Если attending=False, всегда 0.
    guests_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
