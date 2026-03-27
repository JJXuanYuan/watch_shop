#!/usr/bin/env bash
set -euo pipefail

BASE_IMAGES=(
  "python:3.11.15-slim-bookworm"
  "nginx:1.27.5-alpine"
  "mysql:8.0.45"
  "redis:7.4.8-alpine"
)

BUSINESS_IMAGES=(
  "mall_api:offline"
  "mall_nginx:offline"
)

EXISTING_BASE=()
MISSING_BASE=()
EXISTING_BUSINESS=()
MISSING_BUSINESS=()

check_image() {
  local image="$1"
  if docker image inspect "$image" >/dev/null 2>&1; then
    return 0
  fi

  return 1
}

for image in "${BASE_IMAGES[@]}"; do
  if check_image "$image"; then
    EXISTING_BASE+=("$image")
  else
    MISSING_BASE+=("$image")
  fi
done

for image in "${BUSINESS_IMAGES[@]}"; do
  if check_image "$image"; then
    EXISTING_BUSINESS+=("$image")
  else
    MISSING_BUSINESS+=("$image")
  fi
done

print_group() {
  local title="$1"
  shift
  echo "$title"
  if [ "$#" -eq 0 ]; then
    echo "  - none"
    return
  fi

  for image in "$@"; do
    echo "  - ${image}"
  done
}

print_group "[existing base images]" "${EXISTING_BASE[@]}"
print_group "[missing base images]" "${MISSING_BASE[@]}"
print_group "[existing business images]" "${EXISTING_BUSINESS[@]}"
print_group "[missing business images]" "${MISSING_BUSINESS[@]}"

echo
if [ "${#MISSING_BASE[@]}" -gt 0 ]; then
  echo "Base images are missing. Cannot continue build or export."
  echo "Prepare the missing base images first with docker pull on a connected machine or docker load from a tar archive."
  exit 1
fi

if [ "${#MISSING_BUSINESS[@]}" -gt 0 ]; then
  echo "Base images are ready, but business images are still missing."
  echo "You can continue build after the base images are ready, but export cannot continue until mall_api:offline and mall_nginx:offline exist."
  exit 2
fi

echo "All offline prerequisites are ready. You can continue build and export."
