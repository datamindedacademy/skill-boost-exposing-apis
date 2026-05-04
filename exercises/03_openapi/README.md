# Exercise 3: OpenAPI spec

Turn the auto-generated OpenAPI spec into something an agent
(or human) can actually use.

## Why this matters

Your `/openapi.json` is what consumers — including AI agents — read to
figure out how to use your API. FastAPI emits one for free, but "free"
means *empty*: routes have method+path, fields have types, and that's it.
No descriptions, no examples, no enum values, no documented sort orders.
An agent staring at that spec has to guess.

Open <http://localhost:8000/openapi.json> and have a look at what your
v2 routes currently emit. Compare to <http://localhost:8000/docs> — the
docs UI is just a renderer over the same JSON. Notice what's missing.

## Setup

```sh
make solve-2     # if you haven't done Ex 1+2
```

## What to add (15-20 min)

The list looks long; most of it is short. Work file-by-file.

### `src/checkup_api/schemas.py` — every Pydantic model

For every v2 schema (`ProductSummary`, `ProductDetail`, `MetricStatus`,
`MetricHistoryPoint`, `MetricCatalogEntry`, `HealthRollup`):

1. Add a class docstring — becomes the schema description.
2. For each field, swap the bare type for a `Field(...)`:

   ```python
   slug: str = Field(
       description="URL-safe identifier. Use this in subsequent calls.",
       examples=["stellar_sales"],
   )
   ```

3. Where a field is one of a fixed set of values, use `Literal`:

   ```python
   status: Literal["healthy", "warn", "critical"] = Field(...)
   ```

   This emits an enum in the spec → the agent knows the valid values
   without trial and error.

### `src/checkup_api/routers/v2.py` — every endpoint

For every v2 route:

1. Real docstring (becomes the endpoint description). Mention the
   *default sort order* and any agent-relevant gotchas.
2. `summary="..."` and `tags=[...]` in the `@router.get(...)` decorator.
3. `response_model=...` so consumers know the response shape.
4. Replace bare `Query()` calls with `Annotated[..., Query(description=, examples=)]`:

   ```python
   entity: Annotated[
       str | None,
       Query(description="Filter by owning entity (slug).", examples=["analytics"]),
   ] = None
   ```

5. Use `Literal` types for params with a fixed set of values
   (`status`, `category`, `sort`).

### `src/checkup_api/main.py` — the app

Set a non-trivial `description=` on `FastAPI(...)` (Markdown is allowed)
and bump the `version=` away from the scaffold default.

## What good looks like

The agent in Ex 5 should be able to:

- Pick the right enum value for a status filter without guessing.
- Know that `/v2/products` is paginated (default 25, max 100) without
  fetching twice.
- Read default sort order in the description and not re-sort client-side.
- See concrete examples like `"stellar_sales"` and use them as templates.

## Verify

```sh
make test-3
```

The Ex 3 tests inspect `/openapi.json` and assert metadata coverage:
schema descriptions, field descriptions and examples, operation
summaries/descriptions/tags, parameter docs, `Literal` enums, and
`response_model` annotations.

```sh
make solve-3     # canonical Ex 3 solution
```

## What you should walk away with

- A FastAPI app whose `/openapi.json` is genuinely useful.
- Concrete patterns: `Field(description=, examples=)`, `Literal[...]`
  for enums, `Annotated[..., Query(...)]` for documented params,
  `response_model=...` for declared response shapes.
- The intuition that **the spec is a deliverable**, not a side effect of
  your code.
