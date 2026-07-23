"""Pydantic-схемы запросов/ответов."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class RSVPCreate(BaseModel):
    """Данные из формы подтверждения присутствия."""

    full_name: str = Field(..., min_length=2, max_length=150)
    attending: bool
    guests_count: int = Field(default=0, ge=0, le=2)

    # Honeypot: скрытое поле, которое заполняют только боты. Люди его не видят.
    # Ограничение длины не ставим — заполненность обрабатывает роутер (тихий успех),
    # чтобы не подсказывать боту 422-ошибкой о срабатывании фильтра.
    website: str = Field(default="", max_length=200)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = " ".join(v.split())  # схлопнуть пробелы + trim
        if len(v) < 2:
            raise ValueError("Имя слишком короткое")
        return v

    @model_validator(mode="after")
    def _zero_guests_if_not_attending(self) -> "RSVPCreate":
        if not self.attending:
            self.guests_count = 0
        return self


class RSVPResponse(BaseModel):
    success: bool
    message: str
