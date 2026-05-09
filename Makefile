.PHONY: dev-up dev-down dev-status dev-build prod-up prod-down prod-status prod-logs

COMPOSE_DIR = infra/compose

dev-up:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml up -d

dev-down:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml down

dev-status:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml ps

dev-build:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml build

prod-up:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml up -d

prod-down:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml down

prod-status:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml ps

prod-logs:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml logs -f
