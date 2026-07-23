# Свадебное приглашение

Одностраничное адаптивное приглашение на свадьбу с формой подтверждения
присутствия (RSVP). Ответы сохраняются в базу данных и дополнительно
дублируются в Google-таблицу.

**Стек:** FastAPI + Jinja2 (server-rendered) + SQLite. Деплой — Docker Compose
(приложение + nginx + certbot для HTTPS).

## Возможности

- Фото в начале и в конце, текст приглашения, дата с кнопкой «Добавить в
  календарь» (`.ics`), место проведения, программа дня, дресс-код.
- Форма RSVP: имя и фамилия, «придёте / не придёте», опционально «+1/+2».
- Ответы пишутся в SQLite (основной источник) и в Google Sheets (best-effort).
- Адаптивная вёрстка (mobile-first), оптимизированные изображения (webp).

---

## Локальный запуск (для разработки)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Открыть <http://127.0.0.1:8000>. База создастся автоматически в `./data/`.
Google Sheets без настройки — просто отключён, приложение полностью работает.

### Пересборка статических артефактов (нужно только при изменении контента)

```bash
# Пережать фото в webp/разные размеры (после замены first.jpg / second.jpg):
.venv/bin/pip install Pillow
.venv/bin/python scripts/optimize_images.py

# Перегенерировать .ics (после изменения даты/времени/места в app/config.py):
.venv/bin/python scripts/generate_ics.py
```

---

## Настройка Google Sheets (с нуля)

Позволяет автоматически складывать ответы гостей в Google-таблицу.
Шаг необязательный — без него ответы всё равно сохраняются в БД.

1. Откройте [Google Cloud Console](https://console.cloud.google.com/) и создайте
   новый проект (например, `wedding-invitation`).
2. В «APIs & Services → Library» найдите **Google Sheets API** и нажмите
   **Enable**.
3. «APIs & Services → Credentials → Create Credentials → **Service account**».
   Задайте имя (например `invitation-rsvp-bot`), создайте. Роль на уровне проекта
   назначать не нужно — доступ дадим точечно через шаринг таблицы.
4. Откройте созданный сервис-аккаунт → вкладка **Keys** → «Add Key → Create new
   key → **JSON**». Скачается файл-ключ.
5. Создайте [Google-таблицу](https://sheets.new). Из её URL скопируйте ID:
   `https://docs.google.com/spreadsheets/d/`**`<ЭТО_ID>`**`/edit`.
6. Нажмите **Share** и расшарьте таблицу на email сервис-аккаунта (вида
   `invitation-rsvp-bot@<project>.iam.gserviceaccount.com` — он есть в JSON-ключе
   и в консоли) с правом **Editor**.
7. Положите скачанный JSON в `secrets/google-service-account.json`
   (каталог `secrets/` в `.gitignore`, ключ не попадёт в git).
8. В `.env` пропишите `GOOGLE_SHEET_ID=<ID из шага 5>` и убедитесь, что
   `GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/google-service-account.json`.

Заголовок таблицы и лист `RSVP` создаются автоматически при первом ответе.
Каждый ответ — новая строка (журнал). Актуальный статус гостя всегда есть в БД.

---

## Деплой на VPS (Docker Compose + HTTPS)

Предполагается, что на сервере установлены Docker и Docker Compose, а DNS домена
указывает A-записью на IP сервера.

1. Скопируйте проект на сервер (git clone или rsync).
2. Создайте `.env` из шаблона и заполните значения:
   ```bash
   cp .env.example .env
   nano .env    # DOMAIN, CERTBOT_EMAIL, ALLOWED_HOSTS, (опц.) GOOGLE_SHEET_ID
   ```
3. Если используете Google Sheets — положите ключ в
   `secrets/google-service-account.json` и ограничьте права: `chmod 600`.
4. Выпустите сертификат и поднимите всё одной командой:
   ```bash
   bash scripts/init_letsencrypt.sh
   ```
   Скрипт создаёт временный самоподписанный сертификат, поднимает nginx,
   получает настоящий сертификат Let's Encrypt через ACME-challenge и
   перезагружает nginx. Certbot дальше продлевает сертификат автоматически
   (проверка каждые 12 часов), nginx перечитывает его каждые 6 часов.
5. Проверьте: `https://<ваш-домен>` открывается с валидным сертификатом.

Проверить автопродление:
```bash
docker compose run --rm --entrypoint "certbot renew --dry-run" certbot
```

### Обслуживание

```bash
docker compose ps                 # статус сервисов
docker compose logs -f app        # логи приложения
docker compose up -d --build      # применить изменения кода
docker compose restart            # перезапуск (данные в data/ сохраняются)
```

Бэкап ответов: скопируйте файл `data/invitation.db`.

---

## Отключить поле «+1/+2»

В `.env` поставьте `ENABLE_GUESTS_COUNT_FIELD=false` и перезапустите:
```bash
docker compose up -d
```
Поле исчезнет со страницы (не рендерится на сервере) и будет игнорироваться на
бэкенде. Обратно — верните `true`.

---

## Структура

```
app/
  main.py              точка входа FastAPI
  config.py            контент приглашения + настройки из .env
  database.py          SQLAlchemy (SQLite, WAL)
  models.py            модель RSVP
  schemas.py           валидация формы
  routers/             pages (/, /calendar.ics), rsvp (/api/rsvp)
  services/            rsvp_service (upsert), sheets_service, ics_service
  templates/           Jinja2: base, index, partials/*
  static/              css, js, images (+ webp/resize), files/wedding.ics
scripts/               generate_ics, optimize_images, init_letsencrypt
nginx/templates/       конфиг nginx (шаблон с ${DOMAIN})
docker-compose.yml     app + nginx + certbot
```
