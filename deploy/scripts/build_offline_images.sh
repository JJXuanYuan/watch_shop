#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_IMAGE="${API_IMAGE:-mall_api:offline}"
NGINX_IMAGE="${NGINX_IMAGE:-mall_nginx:offline}"
BASE_IMAGES=(
  "python:3.11.15-slim-bookworm"
  "nginx:1.27.5-alpine"
  "mysql:8.0.45"
  "redis:7.4.8-alpine"
)
MISSING_BASE=()

cd "$ROOT_DIR"

for image in "${BASE_IMAGES[@]}"; do
  if ! docker image inspect "${image}" >/dev/null 2>&1; then
    MISSING_BASE+=("${image}")
  fi
done

if [ "${#MISSING_BASE[@]}" -gt 0 ]; then
  echo "Missing base images required before local offline build:"
  for image in "${MISSING_BASE[@]}"; do
    echo "  - ${image}"
  done
  echo "Cannot continue build."
  echo "Prepare these images first with docker pull on a connected machine or docker load from a tar archive."
  echo "You can inspect the current state with: bash deploy/scripts/check_offline_prereqs.sh"
  exit 1
fi

echo "Building ${API_IMAGE} from services/api/Dockerfile..."
if ! docker build -f services/api/Dockerfile -t "${API_IMAGE}" .; then
  echo "Failed to build ${API_IMAGE}."
  exit 1
fi

echo "Building ${NGINX_IMAGE} from deploy/docker/nginx/Dockerfile..."
if ! docker build -f deploy/docker/nginx/Dockerfile -t "${NGINX_IMAGE}" .; then
  echo "Failed to build ${NGINX_IMAGE}."
  exit 1
fi

echo "Offline business images built successfully."
echo "Next: bash deploy/scripts/export_images.sh"
