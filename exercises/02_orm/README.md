# Exercise 2: ORM

Rewrite Ex 1's queries with SQLAlchemy ORM and learn that the
"obvious" code path silently fans out into N+1 queries.

## Why bother with ORM at all?

Raw SQL is fine for simple queries. The wins from ORM show up when:

- Joins get repeated across many endpoints (DRY).
- You want type-safe filter composition.
- Schemas evolve and you want a single source of truth.
- You need to share query fragments across different request types.

The cost: you have to think about things like *loading strategies*, deal with the ORM api which can be unintuitive for joins if you're used to SQL, ...

## Setup

If you haven't already done Ex 1:

```sh
make solve-1     # use the canonical Ex 1 solution
```

## Part A — Define ORM relationships (5 min)

Open `src/checkup_api/models.py`. The columns are there but **no
relationships are defined**. Add them.

The wrinkle: our fact table (`measurements`) joins to dim tables by
**natural key**, not surrogate FK. There's no `metric_id` column on
`measurements` — there's a `name` column that matches `metrics.name`.

For natural-key relationships in SQLAlchemy you tell it (a) the join
condition and (b) which side to treat as the FK:

```python
class Measurement(Base):
    ...
    metric: Mapped["Metric"] = relationship(
        "Metric",
        primaryjoin="Measurement.name == foreign(Metric.name)",
        viewonly=True,    # no FK constraint = no cascade behavior
    )
```

You'll need:

- `Product.entity` — straightforward FK relationship on `entity_id`.
- `Product.measurements` — natural-key one-to-many, joined on
  `Product.slug == Measurement.tag_product`.
- `Measurement.metric` — natural-key many-to-one as shown above.

## Part B — Rewrite the v2 endpoints (10 min)

Rewrite the same endpoints from Ex 1 — same URLs, same response shapes —
using the ORM models and `select(...)` instead of raw `text(sql)`.

The "obvious" code looks like this:

```python
products = db.execute(select(Product)).scalars().all()
for p in products:
    rollup = compute(p)         # walks p.measurements, m.metric.threshold_warn
```

That's beautiful. It's also wrong. By default, `relationship()` uses
`lazy="select"`, meaning each access to `p.measurements` issues a fresh
query, and each `m.metric` does too. With 4 products and 4 measurements
each you've already issued 21+ queries to render a 4-item list.

## Part C — See the explosion, then fix it (5 min)

Run the budget tests:

```sh
make test-2
```

When the budget fails, the assertion message lists every SQL statement
that was issued — read it. With naive lazy loading you'll see dozens of
small `SELECT` statements (one per product to load measurements, one per
measurement to load metrics). The shape of the explosion *is* the lesson.

Now apply the right loader strategy to your endpoints:

```python
from sqlalchemy.orm import contains_eager, selectinload

stmt = (
    select(Product)
    .join(Entity, Product.entity_id == Entity.id)
    .options(
        contains_eager(Product.entity),
        selectinload(Product.measurements).selectinload(Measurement.metric),
    )
)
```

`contains_eager` says "the JOIN already loaded this; don't issue a
separate query." `selectinload` issues one extra `WHERE pk IN (...)`
query per relationship, which is the right move for collections (the
joinedload alternative would cartesian-product blow up the row count).

## Verify

```sh
make test-2
```

The Ex 2 tests assert both **functional behavior** (same as Ex 1) and a
**query budget** of ≤ 3 queries per list endpoint. If your code passes
Ex 1 tests but fails Ex 2 budgets, you've got N+1 — fix the loader
options, not the assertion.

```sh
make solve-2     # canonical Ex 2 solution
```

## What you should walk away with

- ORM defaults to lazy loading; lazy + relationship traversal in a list
  endpoint = N+1.
- Always pick a loading strategy for any relationship you actually
  traverse. `selectinload` for collections, `joinedload`/`contains_eager`
  for FK-backed many-to-one.
- Natural-key joins work in SQLAlchemy with `foreign()` and `viewonly=True`.
