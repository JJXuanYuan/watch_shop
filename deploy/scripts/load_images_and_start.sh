#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/opt/mall"
COMPOSE_FILE="docker-compose.offline.yml"
IMAGE_TAR="${1:-${ROOT_DIR}/mall_offline_bundle.tar}"

cd "$ROOT_DIR"

if [ ! -f "$IMAGE_TAR" ]; then
  echo "Image archive not found: $IMAGE_TAR"
  echo "Place mall_offline_bundle.tar in /opt/mall or pass a custom path as the first argument."
  exit 1
fi

echo "Loading offline image bundle: $IMAGE_TAR"
docker load -i "$IMAGE_TAR"

echo "Starting containers with docker compose..."
docker compose -f "$COMPOSE_FILE" up -d
docker compose -f "$COMPOSE_FILE" ps

echo
echo "Next commands:"
echo "  docker compose -f $COMPOSE_FILE exec -T mall_api alembic upgrade head"
echo "  docker compose -f $COMPOSE_FILE exec -T mall_api python -m scripts.seed_data"
echo "  bash deploy/scripts/offline_post_check.sh"
