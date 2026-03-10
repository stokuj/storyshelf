#!/bin/bash
set -euo pipefail

APP_DIR="/opt/storyweave"
COMPOSE_FILE="docker-compose.prod.yml"

echo "=== StoryWeave Deploy ==="
echo ""

# Check if .env exists
if [ ! -f "$APP_DIR/.env" ]; then
    echo "ERROR: .env file not found in $APP_DIR"
    echo "Create it first: cp .env.example .env && nano .env"
    exit 1
fi

# Pull latest images
echo "[1/3] Pulling latest images..."
docker compose -f "$COMPOSE_FILE" pull

# Restart services
echo "[2/3] Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

# Wait and check health
echo "[3/3] Waiting for services to start..."
sleep 10

echo ""
echo "=== Service Status ==="
docker compose -f "$COMPOSE_FILE" ps
echo ""

# Check health endpoint
if curl -sf http://localhost/health/ > /dev/null 2>&1; then
    echo "Health check: OK"
    curl -s http://localhost/health/ | python3 -m json.tool 2>/dev/null || true
else
    echo "Health check: FAILED (service may still be starting)"
    echo "Check logs with: docker compose -f $COMPOSE_FILE logs"
fi

echo ""
echo "=== Deploy complete ==="
