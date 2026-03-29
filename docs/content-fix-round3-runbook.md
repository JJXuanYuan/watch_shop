# Round 3 Execution Runbook

## Purpose

This runbook explains how to execute the Round 3 rich-fields patch safely through the admin API.

Use this together with:

- [`docs/content-fix-round3-rich-fields.md`](./content-fix-round3-rich-fields.md)
- [`docs/content-fix-round3-payload-examples.md`](./content-fix-round3-payload-examples.md)
- [`scripts/content_patch_round3_payloads.json`](../scripts/content_patch_round3_payloads.json)
- [`scripts/content_patch_round3.py`](../scripts/content_patch_round3.py)

## Preconditions

- admin login is already restored
- product media chain is already healthy for products `1..5`
- no production SQL is needed for this round
- Python 3 is available in the execution environment

## Step 1: Get An Admin Token

If you already have a valid Bearer token, use it directly.

Otherwise call admin login:

```bash
curl -sS -X POST http://127.0.0.1/api/v1/admin/auth/login \
  -H 'Content-Type: application/json' \
  --data '{"username":"admin","password":"Admin@123456"}'
```

Expected result:

- response contains `access_token`

Export it for later commands:

```bash
export ADMIN_TOKEN="your_access_token_here"
```

## Step 2: Dry-Run The Patch Script

Token mode:

```bash
python3 /opt/mall/scripts/content_patch_round3.py \
  --base-url http://127.0.0.1 \
  --token "$ADMIN_TOKEN" \
  --dry-run
```

Username/password mode:

```bash
python3 /opt/mall/scripts/content_patch_round3.py \
  --base-url http://127.0.0.1 \
  --username "admin" \
  --password "Admin@123456" \
  --dry-run
```

What to review in dry-run output:

- all 5 products appear
- the payload shape matches the admin API `PUT` contract
- `selling_points` is non-empty
- spec fields are non-empty
- `story_blocks` has 2 blocks per product
- unrelated fields are preserved rather than blanked out

## Step 3: Execute The Patch

```bash
python3 /opt/mall/scripts/content_patch_round3.py \
  --base-url http://127.0.0.1 \
  --token "$ADMIN_TOKEN"
```

The script prints per-product results:

- `[OK] Product <id>: ...`
- `[FAIL] Product <id>: ...`

If any product fails, stop and keep the error output.

## Step 4: Verify Admin API Results

Check current public product payloads:

```bash
curl -sS http://127.0.0.1/api/v1/products/1
curl -sS http://127.0.0.1/api/v1/products/2
curl -sS http://127.0.0.1/api/v1/products/3
curl -sS http://127.0.0.1/api/v1/products/4
curl -sS http://127.0.0.1/api/v1/products/5
```

Confirm for each product:

- `selling_points` exists and is non-empty
- `material` exists
- `crystal` exists
- `movement_or_function` exists
- `power_reserve` exists
- `water_resistance` exists
- `strap_material` exists
- `story_blocks` exists and contains usable copy

## Step 5: Verify Miniprogram Detail Pages

Check the detail pages for products `1..5`.

Verify:

- selling-point chips now show real content
- spec cards now show real values instead of inferred fallback
- story sections render block title, subtitle/content, and images
- no empty block leaves a visual gap

## Optional Single-Product Testing

Dry-run one product only:

```bash
python3 /opt/mall/scripts/content_patch_round3.py \
  --base-url http://127.0.0.1 \
  --token "$ADMIN_TOKEN" \
  --product-ids 1 \
  --dry-run
```

Execute one product only:

```bash
python3 /opt/mall/scripts/content_patch_round3.py \
  --base-url http://127.0.0.1 \
  --token "$ADMIN_TOKEN" \
  --product-ids 1
```

## Curl Template For Manual Comparison

If manual review is needed, fetch current admin product detail before patching:

```bash
curl -sS http://127.0.0.1/api/v1/admin/products/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

This helps compare the live product payload with the reviewed payload examples and dry-run output.

## Failure Handling

Stop and report if:

- login fails
- `PUT` returns schema validation errors
- one product payload differs too much from current live data
- story block fields are rejected by the backend

When reporting, include:

- failing product id
- full error output
- the matching dry-run payload for that product
