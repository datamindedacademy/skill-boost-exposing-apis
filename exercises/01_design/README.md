# Exercise 1: REST API design

Redesign the existing API design using RESTful design principles.

## Setup

```sh
make up
make api
```

Open the Swagger UI at <http://localhost:8000/docs>. You'll see two versions of the API:

- `/v1/*`: Already implemented. An inside-out, DB-mirroring API design.
- `/v2/*`: TODO.

## Part A: Test out the API

Write a short Python script or curl commands that answers the following question:

> Get every product in the **marketing** entity whose **column test coverage on dbt** is below the warning threshold.

Use the v1 api:

```bash
curl -s http://localhost:8000/v1/measurements | jq
```

Notes:
- Check out the [data model](../../README.md#data-model).
- You will notice you need multiple round trips and a client-side join.

This is a very simple inside-out API design. The URLs and payloads
mirror the data model. It's the most intuitive thing to ship, requires no transformation,
but it can fail to properly abstract the inner workings of the backend. 
The data model (often optimized for storage) and the API contract serve different audiences and often shouldn't match.
RESTful design principles are one common toolkit for shaping that consumer-facing contract — that's what you'll apply in Part B.

## Part B: Build the `/v2/*` API

Open `src/checkup_api/routers/v2.py`. The endpoints are stubbed —
each one raises 501 with a hint about what to build. Implement them using
**raw SQL** via `db.execute(text(sql), params)`.

The endpoints to implement:

| Method & Path | What it returns |
|---|---|
| `GET /v2/products` | List, with entity name + `{healthy, warn, critical}` rollup, filterable by `?entity=`, `?status=`, paginated |
| `GET /v2/products/{slug}` | Detail (same as list item + `created_at`) |
| `GET /v2/products/{slug}/metrics` | Latest measurement per metric, with **server-derived** `status` |
| `GET /v2/products/{slug}/metrics/{name}/history` | Time series (most recent first) |
| `GET /v2/metrics` | Catalog of metric definitions |
| `GET /v2/metrics/{name}` | One catalog entry |

The `status` field is the headline win: clients no longer need to know
your threshold scheme. Compute it from `metrics.threshold_warn`,
`metrics.threshold_critical`, and `metrics.higher_is_better`.

### Test

```sh
make test-1
```

If you get stuck:

```sh
make solve-1
```

## RESTful design principles

The headline principle this whole arc drills:

> **Don't mirror the database.** The API is the contract; the database is
> an implementation detail. Consumers shouldn't see your `tag_product`
> column or your numeric `entity_id`.

The principles below are the toolkit you use to honor that headline.

### URI design

- **Nouns, not verbs.** `/products`, not `/getProducts`. HTTP methods
  carry the action.
- **Plural collections; item under the collection.** `/products` and
  `/products/{slug}`.
- **Stable, meaningful identifiers.** Slugs (`stellar_sales`) are
  searchable, memorable, and don't leak DB row order. Opaque ids
  (`/products/1`) leak nothing useful.
- **Cap nesting at ~2 levels.** `/products/{slug}/metrics/{name}/history`
  is at the limit; deeper paths get brittle.

### Responses

- **Derived fields belong on the server.** A `status` of "critical" is
  more useful than the raw value + thresholds the client has to combine.
- **Embed for ergonomics; link for size.** Small, common rollups (health
  counts) belong in list responses to avoid N+1 calls. Big payloads
  (history, full measurements) deserve their own endpoint.
- **Status codes carry meaning.** 200/201/204 for success, 400/404/422
  for client errors, 401/403 for auth, 5xx for server. Don't 200-with-
  error-in-body.

### Lists

- **Filter** with query params: `?entity=marketing`, `?status=critical`.
- **Sort** with `?sort=name|health`. Default sort should be the most
  common useful ordering, and you should *document it*.
- **Paginate** with `?limit=&offset=`. Set sensible defaults and a hard max.

### Versioning

- The story you walk through (`v1` → `v2` URL prefixes) is one valid
  versioning style. Header- and media-type-versioning are alternatives;
  each has tradeoffs around caching and HATEOAS.
- More important than the *style* is the *commitment*: never break a
  version that's in active use. Add new versions instead.

### HATEOAS — mentioned, not implemented

Hypermedia as the Engine of Application State: each response carries
links to the operations available on the returned resource(s). E.g. a
`Product` response includes a `links` object with the URI of its
`/metrics` and `/metrics/{name}/history` endpoints, so a consumer can
navigate the API without prior knowledge of the URI structure.

Why it matters for agents: a well-HATEOAS'd response lets an agent
discover what to do next without re-reading the spec. We don't implement
it here (skill scope), but it's worth knowing about.
