#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_TAR="${1:-mall_offline_bundle.tar}"

IMAGES=(
  "mysql:8.0.45"
  "redis:7.4.8-alpine"
  "mall_api:offline"
  "mall_nginx:offline"
)

cd "$ROOT_DIR"

BASE_IMAGES=(
  "mysql:8.0.45"
  "redis:7.4.8-alpine"
)

LOCAL_IMAGES=(
  "mall_api:offline"
  "mall_nginx:offline"
)

echo "Pulling base images required by docker-compose.offline.yml..."
for image in "${BASE_IMAGES[@]}"; do
  echo "-> docker pull ${image}"
  docker pull "${image}"
done

for image in "${LOCAL_IMAGES[@]}"; do
  if ! docker image inspect "${image}" >/dev/null 2>&1; then
    echo "Missing local image: ${image}"
    echo "Run bash deploy/scripts/build_offline_images.sh first."
    exit 1
  fi
done

echo "Saving images to ${OUTPUT_TAR}..."
docker save -o "${OUTPUT_TAR}" "${IMAGES[@]}"

echo "Full offline image bundle exported successfully: ${OUTPUT_TAR}"
echo "The bundle already includes the prebuilt mall_api and mall_nginx image layers."
echo "Upload this file to /opt/mall on the target server before running load_images_and_start.sh."
