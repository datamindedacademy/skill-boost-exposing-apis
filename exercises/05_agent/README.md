# Exercise 5: Enable an agent with data from your API

See how spec quality and scope guards play out when an LLM agent is the consumer.

## Setup

```sh
make solve-4     # if you haven't done Ex 1-4
make up          # Postgres + Keycloak
make api         # FastAPI server (leave running)
```

In a second terminal, get a token and put it in your environment:

```sh
export CHECKUP_API_TOKEN=$(make token-all)
```

## Two skills are committed in this repo

`.claude/skills/checkup-api/SKILL.md`
:   The "good" skill. Points at the live `/openapi.json` (which after
    Ex 3 is the rich, enriched spec).

`.claude/skills/checkup-api-sparse/SKILL.md`
:   The "bad" skill. Points at the snapshot in
    `exercises/05_agent/openapi_sparse.json`, captured *before* Ex 3
    enrichments.

The agent itself (curl + bash) is the same. The only thing that changes
is which spec it reads.

## What to do

For each prompt in [`prompts.md`](./prompts.md):

1. Ask Claude Code with **`checkup-api-sparse`** — "I'd like you to use
   the `checkup-api-sparse` skill to answer: …"
2. Ask the same prompt with **`checkup-api`** (rich).
3. Compare:
   - How many requests did it make?
   - Did it have to retry with different param values?
   - Did it parse responses correctly, or guess at field meanings?
   - Did it sort/filter client-side because the spec didn't tell it
     about server-side options?

You should see fewer calls, fewer guesses, and faster, more accurate
answers from the rich-spec run.

## The auth scenario

Switch to a scoped token:

```sh
export CHECKUP_API_TOKEN=$(make token-stellar)
```

Now ask: *"How does cosmic_inventory's test coverage look?"*

The agent gets a 404. A well-instructed agent reports "I don't have
access to cosmic_inventory under this token" rather than hallucinating a
result. Same blast-radius story applies in production: a runaway agent
with a scoped token can't escape its lane.

## Re-capturing the sparse spec

If you tweak the schema or routes and want a fresh sparse snapshot:

```sh
make solve-2                    # roll back to pre-Ex3 state
make export-sparse-spec         # writes openapi_sparse.json
make solve-4                    # back to fully-solved state
```

## What you should walk away with

- The OpenAPI spec is for *consumers* — humans, agents, code-gen — not
  for FastAPI. Agents are uniquely punishing of bad specs.
- Scoped tokens are how you make API access safe to hand to an agent.
