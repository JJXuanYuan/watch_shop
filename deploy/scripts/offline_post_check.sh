#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/opt/mall"
COMPOSE_FILE="docker-compose.offline.yml"

cd "$ROOT_DIR"

docker compose -f "$COMPOSE_FILE" ps
docker compose -f "$COMPOSE_FILE" logs mall_api --tail=100

echo
echo "[health]"
curl -fsS http://127.0.0.1/health
echo
echo "[categories]"
curl -fsS http://127.0.0.1/api/v1/categories
echo
echo "[products]"
curl -fsS http://127.0.0.1/api/v1/products
echo
