#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib import error, request

DEFAULT_PRODUCT_IDS = [1, 2, 3, 4, 5]
PATCH_KEYS = {
    "selling_points",
    "material",
    "crystal",
    "movement_or_function",
    "power_reserve",
    "water_resistance",
    "strap_material",
    "story_blocks",
}
BASE_PAYLOAD_KEYS = [
    "name",
    "short_title",
    "subtitle",
    "category_id",
    "price",
    "original_price",
    "stock",
    "sales",
    "status",
    "cover_image",
    "hero_image",
    "banner_images",
    "detail_content",
    "sort_order",
    "is_featured",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch patch product rich fields through the admin API.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("CONTENT_PATCH_API_BASE_URL", "http://127.0.0.1"),
        help="API origin, for example http://127.0.0.1 or http://120.53.87.191",
    )
    parser.add_argument(
        "--api-prefix",
        default=os.getenv("CONTENT_PATCH_API_PREFIX", "/api/v1"),
        help="API prefix. Defaults to /api/v1.",
    )
    parser.add_argument(
        "--payload-file",
        default=str(Path(__file__).with_name("content_patch_round3_payloads.json")),
        help="Path to the reviewable rich-field patch payload JSON file.",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("CONTENT_PATCH_ADMIN_TOKEN", ""),
        help="Admin Bearer token. If omitted, the script will try admin login.",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("CONTENT_PATCH_ADMIN_USERNAME", ""),
        help="Admin username for login when token is not provided.",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("CONTENT_PATCH_ADMIN_PASSWORD", ""),
        help="Admin password for login when token is not provided.",
    )
    parser.add_argument(
        "--product-ids",
        default="1,2,3,4,5",
        help="Comma-separated product ids to patch. Defaults to 1,2,3,4,5.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print merged payloads without sending PUT requests.",
    )
    return parser.parse_args()


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def normalize_api_prefix(api_prefix: str) -> str:
    prefix = api_prefix.strip() or "/api/v1"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return prefix.rstrip("/")


def parse_product_ids(raw_value: str) -> list[int]:
    product_ids: list[int] = []
    for chunk in raw_value.split(","):
        value = chunk.strip()
        if not value:
            continue
        product_ids.append(int(value))
    return product_ids or DEFAULT_PRODUCT_IDS


def load_patch_map(payload_file: str) -> dict[int, dict[str, Any]]:
    with open(payload_file, "r", encoding="utf-8") as file:
        payload_items = json.load(file)

    patch_map: dict[int, dict[str, Any]] = {}
    for item in payload_items:
        product_id = int(item["id"])
        patch = item["patch"]
        invalid_keys = sorted(set(patch) - PATCH_KEYS)
        if invalid_keys:
            raise ValueError(
                f"Payload for product {product_id} contains unsupported keys: {', '.join(invalid_keys)}"
            )
        patch_map[product_id] = patch

    return patch_map


def request_json(
    method: str,
    url: str,
    *,
    token: str = "",
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
    }
    data: bytes | None = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = request.Request(url, data=data, method=method.upper(), headers=headers)

    try:
        with request.urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method.upper()} {url} failed: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"{method.upper()} {url} failed: {exc.reason}") from exc


def login_admin(base_url: str, api_prefix: str, username: str, password: str) -> str:
    if not username or not password:
        raise RuntimeError("Missing admin token and login credentials.")

    url = f"{base_url}{api_prefix}/admin/auth/login"
    response = request_json(
        "POST",
        url,
        body={
            "username": username,
            "password": password,
        },
    )
    token = str(response.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Admin login succeeded without returning an access token.")
    return token


def build_update_payload(current_product: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    payload = {key: current_product.get(key) for key in BASE_PAYLOAD_KEYS}
    payload.update(patch)

    if not payload.get("banner_images"):
        payload["banner_images"] = [payload["cover_image"]]

    return payload


def main() -> int:
    args = parse_args()
    base_url = normalize_base_url(args.base_url)
    api_prefix = normalize_api_prefix(args.api_prefix)
    product_ids = parse_product_ids(args.product_ids)
    patch_map = load_patch_map(args.payload_file)

    token = args.token.strip()
    if not token:
        token = login_admin(base_url, api_prefix, args.username.strip(), args.password)
        print("Logged in through admin API.")

    failures = 0

    for product_id in product_ids:
        patch = patch_map.get(product_id)
        if patch is None:
            print(f"[SKIP] Product {product_id}: no patch payload defined.")
            continue

        detail_url = f"{base_url}{api_prefix}/admin/products/{product_id}"

        try:
            current_product = request_json("GET", detail_url, token=token)
            payload = build_update_payload(current_product, patch)

            if args.dry_run:
                print(f"[DRY-RUN] Product {product_id}")
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                continue

            updated_product = request_json("PUT", detail_url, token=token, body=payload)
            print(
                f"[OK] Product {product_id}: "
                f"{updated_product.get('name') or updated_product.get('title') or 'updated'}"
            )
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[FAIL] Product {product_id}: {exc}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
