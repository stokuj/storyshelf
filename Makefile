.PHONY: dev-up dev-down dev-status dev-build dev-superuser prod-up prod-down prod-status prod-logs verify regenerate-openapi svelte-install svelte-types svelte-dev svelte-build svelte-check

ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
COMPOSE_DIR := $(ROOT_DIR)infra/compose
ENV_FILE := $(ROOT_DIR)infra/.env
DEV_COMPOSE = docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml
PROD_COMPOSE = docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml

dev-up:
	$(DEV_COMPOSE) --env-file $(ENV_FILE) up -d
	@printf '\n%s\n' 'Dev services:'
	@printf '%s\n' '  svelte: http://localhost:5174'
	@printf '%s\n' '  django api: http://localhost:8000/api/'
	@printf '%s\n' '  admin panel: http://localhost:8000/admin/'

dev-down:
	$(DEV_COMPOSE) --env-file $(ENV_FILE) down

dev-status:
	$(DEV_COMPOSE) --env-file $(ENV_FILE) ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"

dev-build:
	$(DEV_COMPOSE) --env-file $(ENV_FILE) build

dev-superuser:
	$(DEV_COMPOSE) --env-file $(ENV_FILE) exec django python manage.py createsuperuser

prod-up:
	$(PROD_COMPOSE) --env-file $(ENV_FILE) up -d

prod-down:
	$(PROD_COMPOSE) --env-file $(ENV_FILE) down

prod-status:
	$(PROD_COMPOSE) --env-file $(ENV_FILE) ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"

prod-logs:
	$(PROD_COMPOSE) --env-file $(ENV_FILE) logs -f

verify:
	cd $(ROOT_DIR)backend-django && uv run ruff check .
	cd $(ROOT_DIR)backend-django && DJANGO_ENV=dev uv run python manage.py check
	cd $(ROOT_DIR)backend-django && DJANGO_ENV=dev uv run python -m pytest
	cd $(ROOT_DIR)backend-django && DJANGO_ENV=dev uv run python manage.py test config.tests.test_openapi_schema --noinput
	cd $(ROOT_DIR)svelte-frontend && npm run types:api
	cd $(ROOT_DIR)svelte-frontend && npm run check
	cd $(ROOT_DIR)svelte-frontend && npm run lint

regenerate-openapi:
	$(ROOT_DIR)infra/scripts/regenerate-openapi.sh

svelte-install:
	cd $(ROOT_DIR)svelte-frontend && npm install

svelte-types:
	cd $(ROOT_DIR)svelte-frontend && npm run types:api

svelte-dev:
	cd $(ROOT_DIR)svelte-frontend && npm run dev

svelte-build:
	cd $(ROOT_DIR)svelte-frontend && npm run build

svelte-check:
	cd $(ROOT_DIR)svelte-frontend && npm run check && npm run lint
