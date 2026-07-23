"""Одноразовая офлайн-оптимизация фото приглашения.

Из app/static/images/{first,second}.jpg генерирует адаптивные варианты:
  {name}-600.jpg / .webp
  {name}-900.jpg / .webp
  {name}-1200.jpg / .webp

Запуск: python scripts/optimize_images.py
Результат коммитится в репозиторий (ресайз не делается на каждый запрос).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

IMAGES_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "images"
SOURCES = ["first", "second"]
WIDTHS = [600, 900, 1200]
JPEG_QUALITY = 82
WEBP_QUALITY = 80

# Необязательная вертикальная подрезка исходника (доли высоты, которые убрать
# сверху и снизу) — оригинальный файл не меняется, режутся только производные.
# Для hero-фото (first) убираем пустой фон сверху и ноги снизу, чтобы пара
# была выше в кадре и фото не «висело низко».
CROPS = {
    "first": {"top": 0.05, "bottom": 0.20},
}


def process(name: str) -> None:
    src = IMAGES_DIR / f"{name}.jpg"
    if not src.exists():
        print(f"! пропуск: нет файла {src}")
        return

    with Image.open(src) as img:
        img = img.convert("RGB")

        crop = CROPS.get(name)
        if crop:
            top_px = round(img.height * crop.get("top", 0))
            bottom_px = round(img.height * (1 - crop.get("bottom", 0)))
            img = img.crop((0, top_px, img.width, bottom_px))
            print(f"  подрезка: {img.width}x{img.height}")

        for width in WIDTHS:
            if width >= img.width:
                resized = img.copy()
            else:
                height = round(img.height * width / img.width)
                resized = img.resize((width, height), Image.LANCZOS)

            jpg_out = IMAGES_DIR / f"{name}-{width}.jpg"
            webp_out = IMAGES_DIR / f"{name}-{width}.webp"
            resized.save(jpg_out, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
            resized.save(webp_out, "WEBP", quality=WEBP_QUALITY, method=6)
            print(f"  {jpg_out.name} ({jpg_out.stat().st_size // 1024} KB)")
            print(f"  {webp_out.name} ({webp_out.stat().st_size // 1024} KB)")


def main() -> None:
    for name in SOURCES:
        print(f"Обработка {name}.jpg…")
        process(name)
    print("Готово.")


if __name__ == "__main__":
    main()
