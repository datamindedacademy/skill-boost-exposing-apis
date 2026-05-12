# Exercise 1: REST API design

Redesign the existing API using RESTful design principles.

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
The data model (often optimized for storage) and the API contract serve different audiences and often shouldn't match 1-on-1. RESTful design principles are one common toolkit for shaping that consumer-facing contract.

## RESTful design principles

The notes below are a condensed summary of REST design principles. For the full references, see restfulapi.net's pages on [architectural constraints](https://restfulapi.net/rest-architectural-constraints/) and [resource naming](https://restfulapi.net/resource-naming/).

### Architectural constraints

- **Uniform interface**: one logical URI per resource, accessed and modified through a consistent approach (HTTP verbs, naming conventions, shared data format).
- **Client-server**: client and server evolve independently as long as the interface stays stable.
- **Stateless**: the server keeps no client context between requests. Every request carries everything needed to service it.
- **Cacheable**: responses declare whether they can be cached, cutting round trips and easing server load.
- **Layered system**: a client can't tell whether it's talking to the origin server or an intermediary (gateway, cache, auth proxy).

### REST Resources and URIs

A **resource** is the key abstraction in REST. Anything that can be named (a document, an image, an object, a service, a collection of other resources) can be a resource. The API exposes resources, not actions on them.

Resources come in two shapes:

- **Singleton**: one specific thing, e.g. `/customers/{id}`.
- **Collection**: a set of things, e.g. `/customers`. Collections can contain sub-collections, e.g. `/customers/{id}/accounts`.

Each resource is addressed by a **URI** (Uniform Resource Identifier). Well-chosen URIs make the resource model obvious to consumers and are part of how REST honors the uniform-interface constraint.

In practice, the resources you expose don't have to (and often shouldn't) match your DB tables 1-to-1: the storage model is optimized for normalization and joins, the API model for the consumer, so the API layer ends up doing the mapping.

Responses can also include [**HATEOAS**](https://restfulapi.net/hateoas) links pointing to related resources, so consumers navigate the API from the response itself instead of hard-coding URI structure.

### Resource naming and URI design

- **Use nouns, not verbs**. URIs name resources; HTTP methods carry the actions. Each resource fits one of three archetypes, and you should stick with one per resource:
  - *Document*: a singular concept, like one record. Singular name, e.g. `/products/{slug}`.
  - *Collection*: a server-managed set where the server assigns URIs to new items. Plural name, e.g. `/products`.
  - *Store*: a client-managed set where the client picks the URIs. Plural name, e.g. `/users/{id}/playlists`.
- **Stay consistent**. Use `/` for hierarchy, drop any trailing `/`, separate words with hyphens, keep everything lowercase.
- **No file extensions**. Use the `Content-Type` header for media type instead of `.json` or `.xml` suffixes.
- **No CRUD function names in URIs**. `GET /products`, not `/getProducts`. `DELETE /products/{id}`, not `/products/{id}/delete`.
- **Filter, sort, and paginate collections via query parameters**, not separate endpoints. E.g. `?entity=marketing&status=critical&sort=name&limit=25&offset=0`. Pick sensible defaults and a hard max for pagination.

## Part B: Design and build the `/v2/*` API

Open `src/checkup_api/routers/v2.py`. You're going to design the consumer-facing API
yourself, using the principles above as your toolkit.

### Consumer scenarios your API has to support

1. Browse products, optionally filtered by entity or by health status,
   with a quick health rollup so the UI doesn't need to fan out.
2. Drill into a specific product to see its metadata and current health.
3. See the latest measurement per metric for a product, with each
   measurement labeled `healthy`/`warn`/`critical` — derived **server-side**
   from `metrics.threshold_warn`, `metrics.threshold_critical`, and
   `metrics.higher_is_better`. (Clients shouldn't need to know your
   threshold scheme.)
4. View the recent history of a single metric on a single product.
5. Browse the metric catalog (definitions, thresholds).

Translate those into URLs, query params, and response shapes. The
Pydantic models in `src/checkup_api/schemas.py` describe the response
shapes you're aiming for — read them.

### Implementation

Use **raw SQL** via `db.execute(text(sql), params)`. See `routers/v1.py` for reference.

### Test

```sh
make test-1
```

The tests pin down the URL shape, query params, and response details.
Treat them as the contract: if your first design doesn't match, the
failures tell you what to adjust. Iterate.

If you get really stuck:

```sh
make solve-1
```

<details>
<summary>Reference design (peek only if stuck)</summary>

| Method & Path | What it returns |
|---|---|
| `GET /v2/products` | List with entity name + `{healthy, warn, critical}` rollup, filterable by `?entity=`, `?status=`, paginated |
| `GET /v2/products/{slug}` | Detail (list item + `created_at`) |
| `GET /v2/products/{slug}/metrics` | Latest measurement per metric, each with derived `status` |
| `GET /v2/products/{slug}/metrics/{name}/history` | Time series, most recent first |
| `GET /v2/metrics` | Catalog of metric definitions |
| `GET /v2/metrics/{name}` | One catalog entry |

</details>
