#!/bin/bash
# Deploy script for storyshelf production. Run from the repo root.
# Usage: ./infra/scripts/deploy.sh [service...]
#   ./infra/scripts/deploy.sh                  → deploy all
#   ./infra/scripts/deploy.sh django svelte    → deploy specific services
# Services: django, svelte, caddy, db

set -e

COMPOSE_FILE="infra/compose/docker-compose.prod.yml"
ENV_FILE="infra/.env"
SERVICES="${@:-}"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE missing. Copy infra/.env.example to infra/.env and fill in secrets."
    exit 1
fi

COMPOSE="docker compose -f $COMPOSE_FILE --env-file $ENV_FILE"

if [ -z "$SERVICES" ]; then
    echo "Pulling all images..."
    $COMPOSE pull
    $COMPOSE up -d --force-recreate
else
    echo "Deploying services: $SERVICES"
    $COMPOSE pull $SERVICES
    $COMPOSE up -d --force-recreate $SERVICES
fi

echo "---"
$COMPOSE ps
