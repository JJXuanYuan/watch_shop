#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_IMAGE="${API_IMAGE:-mall_api:offline}"
NGINX_IMAGE="${NGINX_IMAGE:-mall_nginx:offline}"

cd "$ROOT_DIR"

echo "Building ${API_IMAGE} from services/api/Dockerfile..."
docker build -f services/api/Dockerfile -t "${API_IMAGE}" .

echo "Building ${NGINX_IMAGE} from deploy/docker/nginx/Dockerfile..."
docker build -f deploy/docker/nginx/Dockerfile -t "${NGINX_IMAGE}" .

echo "Offline business images built successfully."
echo "Next: bash deploy/scripts/export_images.sh"
