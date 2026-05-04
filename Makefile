.PHONY: help install up down logs api test test-1 test-2 test-3 test-4 \
        solve-1 solve-2 solve-3 solve-4 solve-all reset \
        export-sparse-spec token-all token-stellar clean

install:
	uv sync --all-extras

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

api:
	uv run uvicorn checkup_api.main:app --reload

test:
	uv run pytest tests -v

test-1:
	uv run pytest tests/test_01_design.py -v

test-2:
	uv run pytest tests/test_02_orm.py -v

test-3:
	uv run pytest tests/test_03_openapi.py -v

test-4:
	uv run pytest tests/test_04_auth.py -v

solve-1:
	uv run python scripts/apply_solutions.py solve 1

solve-2:
	uv run python scripts/apply_solutions.py solve 2

solve-3:
	uv run python scripts/apply_solutions.py solve 3

solve-4:
	uv run python scripts/apply_solutions.py solve 4

solve-all:
	uv run python scripts/apply_solutions.py solve all

reset:
	uv run python scripts/apply_solutions.py reset

export-sparse-spec:
	uv run python scripts/export_sparse_spec.py

token-all:
	@curl -s -X POST "http://localhost:8080/realms/checkup/protocol/openid-connect/token" \
		-d "client_id=checkup-api" \
		-d "username=agent-all" \
		-d "password=test" \
		-d "grant_type=password" | jq -r '.access_token'

token-stellar:
	@curl -s -X POST "http://localhost:8080/realms/checkup/protocol/openid-connect/token" \
		-d "client_id=checkup-api" \
		-d "username=agent-stellar" \
		-d "password=test" \
		-d "grant_type=password" | jq -r '.access_token'
