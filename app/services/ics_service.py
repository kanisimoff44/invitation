"""Генерация .ics-события свадьбы с корректной таймзоной.

Файл детерминирован (дата/время заданы в config), поэтому его достаточно
сгенерировать один раз в app/static/files/wedding.ics (см. scripts/generate_ics.py),
а на запрос отдавать статикой. Функция build_ics() вынесена сюда, чтобы её
могли переиспользовать и скрипт, и тесты.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

from app import config


def build_ics() -> bytes:
    """Собирает .ics-файл события свадьбы. Возвращает байты (UTF-8)."""
    tz = ZoneInfo(config.WEDDING_TZID)

    start = datetime(
        config.WEDDING_DATE.year,
        config.WEDDING_DATE.month,
        config.WEDDING_DATE.day,
        config.EVENT_START[0],
        config.EVENT_START[1],
        tzinfo=tz,
    )
    end = datetime(
        config.WEDDING_DATE.year,
        config.WEDDING_DATE.month,
        config.WEDDING_DATE.day,
        config.EVENT_END[0],
        config.EVENT_END[1],
        tzinfo=tz,
    )

    description = "Программа дня:\n" + "\n".join(
        f"{item.time} — {item.title}" for item in config.TIMELINE
    )

    cal = Calendar()
    cal.add("prodid", "-//Wedding Invitation//RU")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")

    event = Event()
    event.add("uid", "wedding-2026-09-26@invitation")
    event.add("summary", "Свадьба ❤")
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("dtstamp", start)
    event.add("location", f"{config.VENUE_NAME}, {config.VENUE_ADDRESS}")
    event.add("description", description)
    cal.add_component(event)

    return cal.to_ical()
