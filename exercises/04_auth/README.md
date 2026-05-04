# Exercise 4: Authorization with scoped read access

Gate `/v2/products*` with OAuth scopes so different agents see only the products they're allowed to.

## Why scoped access matters for agents

When you hand an API to an LLM agent, you can't fully trust what it'll
ask for. Scoped tokens are how you bound the blast radius:

- The `agent-stellar` token has `products: ["stellar_sales"]`. Even if
  the agent gets clever and asks about `cosmic_inventory`, the API
  returns nothing.
- The `agent-all` token has `products: ["*"]` for trusted internal use.

Same API, different views, controlled by the token.

## Setup

```sh
make solve-3     # if you haven't done Ex 1-3
make up          # Keycloak must be running for live tokens
```

## What's pre-implemented

Open `src/checkup_api/auth.py`. The JWT plumbing — fetching JWKS,
validating signatures, decoding claims — is already done in
`get_current_user`. JWT verification is boring infrastructure that varies
by IDP and is usually handled by an SDK; the *interesting* part is what
you do with the claims.

## What to implement (15 min)

### Step 1 — Extract scopes (`auth.py`)

Implement `get_allowed_products`. The token's claims dict has a
`products` key, which is either:

- a list of slugs (e.g. `["stellar_sales", "cosmic_inventory"]`), or
- the wildcard `["*"]` meaning all products allowed.

Behavior:

- Missing or empty `products` claim → 403 Forbidden.
- Wildcard → return `[]` (the convention: empty list = no filter).
- Otherwise → return the list of slugs.

### Step 2 — Apply scopes (`routers/v2.py`)

For each `/v2/products*` route, add `Depends(get_allowed_products)` and
filter results:

```python
def list_products(
    db: Annotated[Session, Depends(get_db)],
    allowed: Annotated[list[str], Depends(get_allowed_products)],
    ...,
):
    stmt = select(Product)
    if allowed:                 # empty list = wildcard, no filter
        stmt = stmt.where(Product.slug.in_(allowed))
```

For single-resource endpoints (`/v2/products/{slug}`,
`/v2/products/{slug}/metrics`, `/v2/products/{slug}/metrics/{name}/history`),
return **404** (not 403) when the slug is outside the caller's scope.
Returning 403 leaks the existence of out-of-scope products; 404 makes
them indistinguishable from non-existent.

The catalog endpoints (`/v2/metrics*`) describe metric *definitions* and
don't need to be scoped.

## Try it live

```sh
make api          # FastAPI server (in another terminal)
make token-stellar > /tmp/token.txt
TOKEN=$(cat /tmp/token.txt)

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/v2/products | jq
# only stellar_sales

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/v2/products/cosmic_inventory
# 404, not 403

make token-all > /tmp/token.txt
TOKEN=$(cat /tmp/token.txt)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/v2/products | jq
# all 4 products
```

## Verify

```sh
make test-4
```

Tests cover: no-token rejection, wildcard scope returning all,
restricted scope returning only the allowed slug, and 404 for
out-of-scope drill-down.

```sh
make solve-4     # canonical Ex 4 solution
```

## What you should walk away with

- The intuition that JWT validation is plumbing; *what to do with the
  claims* is the interesting part.
- A pattern for translating token claims into FastAPI dependencies.
- The 404-vs-403 nuance for read-only APIs.
