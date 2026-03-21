#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="docker-compose.prod.yml"

cd "$ROOT_DIR"

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

BASE_URL="${1:-${PUBLIC_BASE_URL:-http://120.53.87.191:${NGINX_PORT:-80}}}"

docker compose -f "$COMPOSE_FILE" ps
docker compose -f "$COMPOSE_FILE" logs mall_api --tail=100

echo
echo "[health]"
curl -fsS "${BASE_URL}/health"
echo
echo "[categories]"
curl -fsS "${BASE_URL}/api/v1/categories"
echo
echo "[products]"
curl -fsS "${BASE_URL}/api/v1/products"
echo
echo "[product detail]"
curl -fsS "${BASE_URL}/api/v1/products/1"
echo
