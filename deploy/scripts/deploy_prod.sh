#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="docker-compose.prod.yml"

cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Edit secrets for 120.53.87.191 and rerun from /opt/mall."
  exit 1
fi

set -a
. ./.env
set +a

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  git fetch --all --prune
  git pull --ff-only origin "$CURRENT_BRANCH" || git pull --ff-only
fi

docker compose -f "$COMPOSE_FILE" up -d --build

echo "Waiting for MySQL to become healthy..."
until docker compose -f "$COMPOSE_FILE" exec -T mall_mysql sh -lc 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent' >/dev/null 2>&1; do
  sleep 3
done

echo "Waiting for API container to accept commands..."
until docker compose -f "$COMPOSE_FILE" exec -T mall_api python -c "print('api-ready')" >/dev/null 2>&1; do
  sleep 2
done

docker compose -f "$COMPOSE_FILE" exec -T mall_api alembic upgrade head
docker compose -f "$COMPOSE_FILE" exec -T mall_api python -m scripts.seed_data

docker compose -f "$COMPOSE_FILE" ps
docker compose -f "$COMPOSE_FILE" logs mall_api --tail=100

BASE_URL="${PUBLIC_BASE_URL:-http://127.0.0.1:${NGINX_PORT:-80}}"

echo
echo "Deployment complete."
echo "Health check: ${BASE_URL}/health"
echo "Category list: ${BASE_URL}/api/v1/categories"
echo "Product list: ${BASE_URL}/api/v1/products"
echo "Product detail: ${BASE_URL}/api/v1/products/1"
