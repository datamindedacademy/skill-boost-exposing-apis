---
name: checkup-api
description: Query data product health metrics via the Checkup API
---

# Checkup API

You have access to the Checkup API at `http://localhost:8000` for querying
data product health metrics.

## How to use this API

1. Fetch the OpenAPI spec first to understand available routes, parameters,
   examples, and response models:

   ```bash
   curl -s http://localhost:8000/openapi.json
   ```

2. The spec is the source of truth. Read filter descriptions, default sort
   orders, pagination defaults, and enum values from it before calling.
   Don't re-derive things the spec already tells you.

3. Make requests with `curl`. Auth is via Bearer token in
   `$CHECKUP_API_TOKEN`:

   ```bash
   curl -s -H "Authorization: Bearer $CHECKUP_API_TOKEN" \
     "http://localhost:8000/v2/products"
   ```

## Versioning

- `/v2/*` is the consumer-facing API. Use this for any new query.
- `/v1/*` is a legacy DB-mirroring API. Avoid it.

## Authorization model

The token may be scoped to a subset of products via the `products` claim.
If you ask for a product outside scope, you'll get 404 (not 403) — by design,
so out-of-scope products aren't enumerable. If a result list is empty or
smaller than expected, that may be the cause.
