# Prompts for Ex 5

Run each of these against both skills (`checkup-api-sparse`, then
`checkup-api`) and watch how the agent's behavior changes.

## 1. Filtering by status

> Which products have at least one critical metric right now?

**Watch for**: with the sparse spec, the agent likely fetches all
products and filters client-side because it doesn't know the server
supports `?status=critical`. With the rich spec, it should make one call.

## 2. Sorting

> Show me the three products with the worst test coverage on dbt.

**Watch for**: with the sparse spec, the agent may pull every product's
metrics one by one and sort in Python. With the rich spec, it should use
the documented `sort=health` and `limit=` parameters.

## 3. Categorical drill-down

> Tell me about quantum_marketing's freshness metrics.

**Watch for**: does the agent know there's a `category` filter on
`/v2/products/{slug}/metrics`? With the rich spec, the enum
(`data_quality | freshness | infrastructure | dbt`) is documented and
it should pick `freshness` directly.

## 4. Trend analysis

> What's the trend on stellar_sales' test coverage over the last few weeks?

**Watch for**: does the agent find `/v2/products/{slug}/metrics/{name}/history`
quickly, or does it stumble through other endpoints first? With the rich
spec the route description should make the use case obvious.

## 5. Auth scenario

Switch to a scoped token:

```sh
export CHECKUP_API_TOKEN=$(make token-stellar)
```

Then ask:

> Compare cosmic_inventory's health to nebula_customers'.

**Expected**: the agent gets 404 on both products (scope is
`stellar_sales` only). A good agent will report the scope mismatch.
A naive one might hallucinate a comparison.
