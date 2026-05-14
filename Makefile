.PHONY: dev-up dev-down dev-status dev-build dev-superuser prod-up prod-down prod-status prod-logs

ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
COMPOSE_DIR := $(ROOT_DIR)infra/compose
ENV_FILE := $(ROOT_DIR).env
DEV_COMPOSE = docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml
PROD_COMPOSE = docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml

dev-up:
	$(DEV_COMPOSE) --env-file $(ENV_FILE) up -d
	@printf '\n%s\n' 'Dev services:'
	@printf '%s\n' '  frontend: http://localhost:5173'
	@printf '%s\n' '  rabbitmq UI: http://127.0.0.1:15672'
	@printf '%s\n' '  flower: http://localhost:5555'
	@printf '%s\n' '  admin panel: http://localhost:5173/admin/'

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
