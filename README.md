# Свадебное приглашение

Одностраничное адаптивное приглашение на свадьбу с формой подтверждения
присутствия (RSVP). Ответы сохраняются в базу данных; список гостей можно
выгрузить в Excel (xlsx).

**Стек:** FastAPI + Jinja2 (server-rendered) + SQLite. Деплой — Docker Compose
(приложение + nginx + certbot для HTTPS).

## Возможности

- Фото в начале и в конце, текст приглашения, дата с кнопкой «Добавить в
  календарь» (`.ics`), место проведения, программа дня, дресс-код.
- Форма RSVP: имя и фамилия, «придёте / не придёте», опционально «+1/+2».
- Ответы пишутся в SQLite; повторная отправка тем же именем обновляет запись.
- Выгрузка списка гостей в xlsx (защищена токеном).
- Адаптивная вёрстка (mobile-first), оптимизированные изображения (webp).

---

## Локальный запуск (для разработки)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Открыть <http://127.0.0.1:8000>. База создастся автоматически в `./data/`.

### Пересборка статических артефактов (нужно только при изменении контента)

```bash
# Пережать фото в webp/разные размеры (после замены first.jpg / second.jpg):
.venv/bin/pip install Pillow
.venv/bin/python scripts/optimize_images.py

# Перегенерировать .ics (после изменения даты/времени/места в app/config.py):
.venv/bin/python scripts/generate_ics.py
```

---

## Выгрузка списка гостей (xlsx)

Список гостей выгружается по защищённой ссылке. Токен задаётся в `.env`
(`EXPORT_TOKEN`) — пока он пуст, эндпоинт отвечает 404 (список закрыт).

```bash
# сгенерировать токен:
openssl rand -hex 16
# записать в .env: EXPORT_TOKEN=<полученное значение>, затем перезапустить app
```

Скачивание (по умолчанию — только те, кто **придёт**):

```
https://<домен>/api/guests/export.xlsx?token=<ВАШ_ТОКЕН>
```

Чтобы выгрузить всех, включая отказавшихся, добавьте `&all=true`.
В файле: имя, число доп. гостей (+N), всего человек по строке и итоговая
сумма присутствующих.

---

## Деплой на VPS (Docker Compose + HTTPS)

Предполагается, что на сервере установлены Docker и Docker Compose, а DNS домена
указывает A-записью на IP сервера. Работайте под обычным (не-root) пользователем,
от имени которого клонируете репозиторий и запускаете Docker — каталог `data/`
будет принадлежать ему, и приложение сможет писать в него базу.

> Если получаете `permission denied ... /var/run/docker.sock` — добавьте
> пользователя в группу docker: `sudo usermod -aG docker $USER`, затем
> перелогиньтесь (или `newgrp docker`).

1. Скопируйте проект на сервер (git clone или rsync).
2. Создайте `.env` из шаблона и заполните значения:
   ```bash
   cp .env.example .env
   nano .env    # DOMAIN, CERTBOT_EMAIL, ALLOWED_HOSTS, EXPORT_TOKEN
   ```
3. Выпустите сертификат и поднимите всё одной командой:
   ```bash
   bash scripts/init_letsencrypt.sh
   ```
   Скрипт создаёт временный самоподписанный сертификат, поднимает nginx,
   получает настоящий сертификат Let's Encrypt через ACME-challenge и
   перезагружает nginx. Certbot дальше продлевает сертификат автоматически
   (проверка каждые 12 часов), nginx перечитывает его каждые 6 часов.
4. Проверьте: `https://<ваш-домен>` открывается с валидным сертификатом.

Проверить автопродление:
```bash
docker compose run --rm --entrypoint "certbot renew --dry-run" certbot
```

### Предпросмотр по IP (пока домен не готов)

Если домен ещё проверяется, страницу можно посмотреть напрямую по IP сервера
через обычный HTTP, минуя nginx и сертификат:

```bash
docker build -t invitation-preview .
docker run --rm -p 80:8000 -e ALLOWED_HOSTS="" invitation-preview
```

Затем откройте `http://<IP-сервера>` в браузере (Ctrl+C — остановить).
Порт 80 должен быть свободен (если поднят nginx — сначала `docker compose down`)
и открыт в фаерволе/группе безопасности сервера.

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
  routers/             pages (/, /calendar.ics), rsvp (/api/rsvp),
                       export (/api/guests/export.xlsx)
  services/            rsvp_service (upsert), export_service (xlsx), ics_service
  templates/           Jinja2: base, index, partials/*
  static/              css, js, images (+ webp/resize), files/wedding.ics
scripts/               generate_ics, optimize_images, init_letsencrypt
nginx/templates/       конфиг nginx (шаблон с ${DOMAIN})
docker-compose.yml     app + nginx + certbot
```
