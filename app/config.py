"""Настройки приложения и статический контент приглашения.

Всё, что заказчик может захотеть поменять без правки шаблонов
(дата, адрес, программа дня, тексты), собрано здесь в одном месте.
Секреты и переключатели поведения читаются из переменных окружения / .env.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта (каталог, содержащий app/). Нужен, чтобы путь к БД по умолчанию
# был абсолютным и не зависел от текущего рабочего каталога при запуске.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = _PROJECT_ROOT / "data" / "invitation.db"


@dataclass(frozen=True)
class TimelineItem:
    """Пункт программы дня."""

    time: str
    title: str


# --- Статический контент приглашения (единый источник правды) -------------

# Дата и время начала торжественной регистрации (для .ics и отображения).
WEDDING_DATE = date(2026, 9, 26)
WEDDING_TZID = "Asia/Barnaul"  # рп. Тальменка, Алтайский край (UTC+7)

# Программа дня. Время в формате HH:MM локального времени WEDDING_TZID.
TIMELINE: tuple[TimelineItem, ...] = (
    TimelineItem("15:30", "Сбор гостей"),
    TimelineItem("16:00", "Торжественная регистрация брака"),
    TimelineItem("17:00", "Начало банкета"),
    TimelineItem("22:00", "Официальное завершение праздничного дня"),
)

# Событие в календаре охватывает весь праздничный день: с 15:30 до 22:00.
EVENT_START = (15, 30)
EVENT_END = (22, 0)

VENUE_NAME = "Центральное кафе"
VENUE_ADDRESS = "рп. Тальменка, Банковский переулок 2"

INVITATION_GREETING = "Дорогие родные и друзья!"
INVITATION_MESSAGE = "Мы женимся! И мечтаем разделить этот день с вами!"

DRESSCODE_TEXT = (
    "Праздничная вечерняя одежда. Свадьба в красно-белых тонах — "
    "придерживаться этих цветов необязательно, выбирайте наряд по желанию."
)


class Settings(BaseSettings):
    """Переменные окружения / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"

    # Путь к SQLite. По умолчанию — <корень проекта>/data/invitation.db.
    # В контейнере корень проекта = /app, а ./data монтируется как volume,
    # поэтому дефолт корректно работает и локально, и в Docker без переопределения.
    database_url: str = f"sqlite:///{_DEFAULT_DB_PATH}"

    # Показывать ли поле "количество гостей" (+1/+2). Отключаемая фича.
    enable_guests_count_field: bool = True

    # Токен для защиты выгрузки списка гостей (xlsx). Пока не задан — выгрузка
    # недоступна (404), чтобы список гостей не был открыт всем.
    export_token: str = ""

    # Разрешённые Host-заголовки (защита от Host-header атак).
    # Пустая строка => middleware не ограничивает (удобно для dev).
    allowed_hosts: str = ""

    @property
    def allowed_hosts_list(self) -> list[str]:
        hosts = [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]
        if not hosts:
            return ["*"]
        # Всегда разрешаем локальные адреса — по ним ходит healthcheck контейнера
        # (внутри сети, не снаружи), иначе TrustedHostMiddleware вернёт им 400.
        for local in ("localhost", "127.0.0.1"):
            if local not in hosts:
                hosts.append(local)
        return hosts


@lru_cache
def get_settings() -> Settings:
    return Settings()
