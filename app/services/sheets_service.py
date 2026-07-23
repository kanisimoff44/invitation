"""Best-effort отправка RSVP в Google Sheets.

Дизайн: append-only журнал. Каждый сабмит — новая строка. Актуальный статус
гостя всегда живёт в БД; таблица нужна заказчику как удобный «журнал ответов».

Ключевое требование: этот сервис НИКОГДА не должен ломать основной сценарий.
Любая ошибка (нет credentials, нет сети, квота, битый ключ) ловится внутри,
логируется и превращается в возврат False — вызывающий код это переживает.
Если интеграция не сконфигурирована (нет пути к ключу или Sheet ID) —
сервис тихо no-op'ает, что делает приложение полностью рабочим без Google.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from app.config import Settings

logger = logging.getLogger(__name__)

# Заголовок таблицы. Пишется один раз, если лист пустой.
_HEADER = ["Дата ответа (UTC)", "Имя и фамилия", "Придёт", "Доп. гостей"]


class SheetsService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._worksheet = None  # ленивое подключение при первом использовании

    @property
    def is_configured(self) -> bool:
        s = self._settings
        return bool(
            s.google_sheet_id
            and s.google_application_credentials
            and os.path.exists(s.google_application_credentials)
        )

    def _get_worksheet(self):
        """Ленивая авторизация и получение листа. Кэшируется."""
        if self._worksheet is not None:
            return self._worksheet

        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(
            self._settings.google_application_credentials, scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(self._settings.google_sheet_id)

        try:
            ws = spreadsheet.worksheet(self._settings.google_sheet_worksheet)
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(
                title=self._settings.google_sheet_worksheet, rows=100, cols=len(_HEADER)
            )

        # Проставить заголовок, если лист пустой.
        if not ws.get_all_values():
            ws.append_row(_HEADER, value_input_option="USER_ENTERED")

        self._worksheet = ws
        return ws

    def append_rsvp(
        self, full_name: str, attending: bool, guests_count: int
    ) -> bool:
        """Добавляет строку в таблицу. Возвращает True при успехе, иначе False.

        Никогда не пробрасывает исключения наружу.
        """
        if not self.is_configured:
            logger.info("Google Sheets не настроен — синхронизация пропущена")
            return False

        try:
            ws = self._get_worksheet()
            row = [
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                full_name,
                "Да" if attending else "Нет",
                str(guests_count),
            ]
            ws.append_row(row, value_input_option="USER_ENTERED")
            return True
        except Exception:  # noqa: BLE001 — сознательно глушим любые сбои Google
            logger.exception("Не удалось записать RSVP в Google Sheets")
            self._worksheet = None  # сбросить кэш, чтобы переавторизоваться позже
            return False


_service: SheetsService | None = None


def get_sheets_service(settings: Settings) -> SheetsService:
    global _service
    if _service is None:
        _service = SheetsService(settings)
    return _service
