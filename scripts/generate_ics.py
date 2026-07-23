"""Генерирует статический app/static/files/wedding.ics.

Запуск: python scripts/generate_ics.py
Перегенерировать нужно только если изменились дата/время/место в app/config.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ics_service import build_ics  # noqa: E402

OUT = (
    Path(__file__).resolve().parent.parent
    / "app" / "static" / "files" / "wedding.ics"
)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(build_ics())
    print(f"Записано: {OUT} ({OUT.stat().st_size} байт)")


if __name__ == "__main__":
    main()
