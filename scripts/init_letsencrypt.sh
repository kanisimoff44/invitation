#!/usr/bin/env bash
# Первичное получение TLS-сертификата Let's Encrypt.
#
# Схема без "курицы и яйца": nginx сначала поднимается ТОЛЬКО с HTTP-конфигом
# (nginx/templates/http.conf.template) — он не требует сертификата и потому
# гарантированно стартует, обслуживая ACME-challenge на порту 80. После выпуска
# сертификата подключается HTTPS-конфиг (nginx/https.conf.template копируется
# в nginx/templates/), и nginx перезапускается уже с настоящим сертификатом.
#
# Запускать ОДИН раз на сервере после настройки .env (DOMAIN, CERTBOT_EMAIL)
# и DNS, указывающего A-записью на этот сервер:
#   bash scripts/init_letsencrypt.sh
set -euo pipefail

cd "$(dirname "$0")/.."

# Загрузить DOMAIN и CERTBOT_EMAIL из .env.
if [ -f .env ]; then
    set -a; . ./.env; set +a
fi

: "${DOMAIN:?Задайте DOMAIN в .env}"
: "${CERTBOT_EMAIL:?Задайте CERTBOT_EMAIL в .env}"

echo "### Домен: ${DOMAIN}"

mkdir -p nginx/certbot/www nginx/certbot/conf

# 1. Бутстрап: только HTTP-конфиг. Убираем возможный HTTPS-конфиг от прошлого
#    запуска, чтобы nginx точно стартовал без сертификата.
rm -f nginx/templates/https.conf.template

echo "### Поднимаю app и nginx (только HTTP)…"
docker compose up -d --build app
docker compose up -d nginx
sleep 5

# Проверим, что nginx действительно слушает 80 внутри контейнера.
echo "### Проверка nginx на порту 80…"
if docker compose exec -T nginx wget -q -O /dev/null \
        "http://localhost/.well-known/acme-challenge/ping" 2>/dev/null; then
    echo "    nginx отвечает."
else
    # 404 на несуществующий файл — это нормально (значит nginx жив).
    echo "    (проверка завершена)"
fi

echo "### Запрашиваю сертификат Let's Encrypt…"
docker compose run --rm --entrypoint certbot certbot \
    certonly --webroot -w /var/www/certbot \
    -d "${DOMAIN}" \
    --email "${CERTBOT_EMAIL}" \
    --agree-tos --no-eff-email --non-interactive

# 2. Сертификат получен — подключаем HTTPS-конфиг и перезапускаем nginx.
echo "### Включаю HTTPS…"
cp nginx/https.conf.template nginx/templates/https.conf.template
docker compose restart nginx

echo "### Поднимаю все сервисы (включая автопродление certbot)…"
docker compose up -d

echo "### Готово. Проверьте: https://${DOMAIN}"
