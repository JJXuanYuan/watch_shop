# Round 3 Rich Fields Runbook

## Overview

After the image-chain repairs in Round 1 and Round 2, the remaining storefront gap is no longer media availability. The main issue is that rich product fields are still empty or incomplete in production:

- `selling_points`
- `material`
- `crystal`
- `movement_or_function`
- `power_reserve`
- `water_resistance`
- `strap_material`
- `story_blocks`

These fields directly affect detail-page quality. When they are empty, the miniprogram falls back to generic copy and inferred specs, which keeps the UI usable but lowers trust and product specificity.

## Goal

Round 3 prepares a safe, repeatable admin API patch flow for the 5 live core products:

- product `id=1` Chronos S1 智能腕表
- product `id=2` Pulse Mini 轻量智能表
- product `id=3` Voyager M 自动机械表
- product `id=4` Navigator Pro GMT
- product `id=5` Saffiano 真皮表带

This round does not execute production changes. It only prepares the reviewable payloads and the execution script.

## Product Positioning

- Product `1` Chronos S1: smart flagship, emphasizes health tracking, dual-band GPS, and fast daily interaction.
- Product `2` Pulse Mini: lightweight daily smartwatch, emphasizes comfort, endurance, and entry-level monitoring.
- Product `3` Voyager M: formal mechanical core model, emphasizes long power reserve and material finish.
- Product `4` Navigator Pro GMT: travel-focused mechanical model, emphasizes dual time zone readability and night-time legibility.
- Product `5` Saffiano strap: accessory SKU, emphasizes quick-change structure and styling flexibility.

## Why Admin API Patch Instead Of SQL

Round 3 should go through admin API, not ad hoc SQL, for three reasons:

1. the backend update route already validates and normalizes these fields
2. `story_blocks` is structured JSON and is safer to write through schema validation
3. the current admin product endpoint expects a full validated payload, so the patch script must fetch current product detail first, merge the rich fields, then `PUT` the result

Relevant backend files:

- [`services/api/app/api/routes/admin_products.py`](../services/api/app/api/routes/admin_products.py)
- [`services/api/app/schemas/product.py`](../services/api/app/schemas/product.py)

## Target Field Structure

### `selling_points`

- type: `list[str]`
- target shape: 3 concise selling points per product
- use short, user-facing labels suitable for detail chips

### Spec fields

- `material`
- `crystal`
- `movement_or_function`
- `power_reserve`
- `water_resistance`
- `strap_material`

Target shape:

- one concise factual value per field
- no generic marketing filler
- consistent wording across the catalog

### `story_blocks`

- type: `list[object]`
- per block keys:
  - `label`
  - `title`
  - `subtitle`
  - `content`
  - `image`

Target shape:

- 2 blocks per product
- keep labels short
- keep titles readable on mobile
- story block images intentionally reuse existing `cover_image` or `hero_image` assets in this round, so Round 3 does not expand the media scope

## Canonical Payload Source

The reviewable payload source for Round 3 is:

- [`scripts/content_patch_round3_payloads.json`](../scripts/content_patch_round3_payloads.json)

Human-readable examples are also documented in:

- [`docs/content-fix-round3-payload-examples.md`](./content-fix-round3-payload-examples.md)
- [`docs/content-fix-round3-runbook.md`](./content-fix-round3-runbook.md)

## Execution Order

1. review [`scripts/content_patch_round3_payloads.json`](../scripts/content_patch_round3_payloads.json)
2. run the patch script in dry-run mode
3. patch products in this order:
   - `1`
   - `2`
   - `3`
   - `4`
   - `5`
4. verify API responses
5. verify detail-page rendering in the miniprogram
6. only after production review passes, decide whether to reconcile the same values back into seed data

## Script

Patch script:

- [`scripts/content_patch_round3.py`](../scripts/content_patch_round3.py)

The script:

- supports Bearer token auth
- can log in through `/api/v1/admin/auth/login` if username/password are provided
- fetches current admin product detail first
- merges only the target rich fields
- preserves unrelated fields
- supports `--dry-run`
- prints per-product success or failure

## Verification Plan

After Round 3 execution, verify:

1. `/api/v1/products/{id}` returns non-empty rich fields for `1..5`
2. miniprogram detail pages show:
   - real selling-point chips
   - real spec values instead of fallback specs
   - visible story blocks with readable titles and content
3. no empty detail modules remain visible because of partially filled rich fields

Suggested checks:

```bash
curl -s http://127.0.0.1/api/v1/products/1
curl -s http://127.0.0.1/api/v1/products/2
curl -s http://127.0.0.1/api/v1/products/3
curl -s http://127.0.0.1/api/v1/products/4
curl -s http://127.0.0.1/api/v1/products/5
```

## Risks

- the admin update endpoint is `PUT`, not partial `PATCH`; sending an incomplete payload would overwrite unrelated fields
- malformed `story_blocks` JSON can be rejected by schema validation
- if production product content has changed since payload drafting, review current admin product detail before applying

## Low-Priority Follow-ups

### Category 1 `cover_image` path migration

Recommendation: leave it for later.

Reason:

- current storefront flow does not rely on category cover image in the main purchase path
- it is data hygiene work, not a rich-fields blocker

### Product 4 `banner_images` cleanup

Recommendation: only fold it into Round 3 if the real gallery assets are already prepared.

Reason:

- the admin API script in this round intentionally leaves unrelated fields untouched
- cleaning `banner_images` without the real gallery asset plan would create unnecessary scope expansion
