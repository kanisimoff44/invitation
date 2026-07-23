#!/usr/bin/env bash
# Первичное получение TLS-сертификата Let's Encrypt.
#
# Проблема "курицы и яйца": nginx не стартует без файла сертификата
# (в конфиге есть ssl_certificate), а certbot не может выпустить сертификат
# без работающего на порту 80 nginx для ACME-challenge.
#
# Решение: создаём временный самоподписанный "dummy" сертификат, поднимаем
# nginx, затем заменяем dummy на настоящий сертификат от Let's Encrypt.
#
# Запускать ОДИН раз на сервере после настройки .env (DOMAIN, CERTBOT_EMAIL)
# и DNS, указывающего на этот сервер:
#   bash scripts/init_letsencrypt.sh
set -euo pipefail

cd "$(dirname "$0")/.."

# Загрузить DOMAIN и CERTBOT_EMAIL из .env.
if [ -f .env ]; then
    set -a; . ./.env; set +a
fi

: "${DOMAIN:?Задайте DOMAIN в .env}"
: "${CERTBOT_EMAIL:?Задайте CERTBOT_EMAIL в .env}"

CERT_DIR="nginx/certbot/conf/live/${DOMAIN}"
WWW_DIR="nginx/certbot/www"

echo "### Домен: ${DOMAIN}"

mkdir -p "${CERT_DIR}" "${WWW_DIR}"

echo "### Создаю временный самоподписанный сертификат…"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "${CERT_DIR}/privkey.pem" \
    -out "${CERT_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN}" >/dev/null 2>&1

echo "### Поднимаю nginx с временным сертификатом…"
docker compose up -d nginx
sleep 5

echo "### Удаляю временный сертификат…"
rm -rf "${CERT_DIR}"

echo "### Запрашиваю настоящий сертификат у Let's Encrypt…"
docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    -d ${DOMAIN} \
    --email ${CERTBOT_EMAIL} \
    --agree-tos --no-eff-email \
    --non-interactive" certbot

echo "### Перезагружаю nginx с настоящим сертификатом…"
docker compose exec nginx nginx -s reload || docker compose restart nginx

echo "### Готово. Поднимаю все сервисы…"
docker compose up -d

echo "### Проверьте: https://${DOMAIN}"
