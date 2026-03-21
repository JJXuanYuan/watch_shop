#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_TAR="${1:-mall_offline_bundle.tar}"
REQUIRED_IMAGES=(
  "mysql:8.0.45"
  "redis:7.4.8-alpine"
  "mall_api:offline"
  "mall_nginx:offline"
)
MISSING_IMAGES=()

cd "$ROOT_DIR"

for image in "${REQUIRED_IMAGES[@]}"; do
  if ! docker image inspect "${image}" >/dev/null 2>&1; then
    MISSING_IMAGES+=("${image}")
  fi
done

if [ "${#MISSING_IMAGES[@]}" -gt 0 ]; then
  echo "Cannot export an offline bundle because these images are missing:"
  for image in "${MISSING_IMAGES[@]}"; do
    echo "  - ${image}"
  done
  echo "Do not continue export until the missing images are prepared."
  echo "Use a connected machine to docker pull them, or docker load them from a tar archive first."
  echo "You can inspect the current state with: bash deploy/scripts/check_offline_prereqs.sh"
  exit 1
fi

echo "Saving images to ${OUTPUT_TAR}..."
docker save -o "${OUTPUT_TAR}" "${REQUIRED_IMAGES[@]}"

echo "Full offline image bundle exported successfully: ${OUTPUT_TAR}"
echo "The bundle already includes the prebuilt mall_api and mall_nginx image layers."
echo "Upload this file to /opt/mall on the target server before running load_images_and_start.sh."
