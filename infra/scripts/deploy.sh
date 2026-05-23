#!/bin/bash
# Deploy script for storyshelf production
# Usage: ./deploy.sh [service...]
#   ./deploy.sh              → deploy all
#   ./deploy.sh backend nlp   → deploy specific services

set -e

COMPOSE_FILE="infra/compose/docker-compose.prod.yml"
SERVICES="${@:-}"

if [ ! -f .env ]; then
    echo "ERROR: .env file missing. Copy .env.example to .env and fill in secrets."
    exit 1
fi

if [ -z "$SERVICES" ]; then
    echo "Pulling all images..."
    docker compose -f "$COMPOSE_FILE" pull
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate
else
    echo "Deploying services: $SERVICES"
    docker compose -f "$COMPOSE_FILE" pull $SERVICES
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate $SERVICES
fi

echo "---"
docker compose -f "$COMPOSE_FILE" ps
