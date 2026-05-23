#!/usr/bin/env bash
# Regeneruje snapshot OpenAPI dla testu kontraktu.
#
# Wywolanie:
#     make regenerate-openapi
# lub bezposrednio:
#     ./infra/scripts/regenerate-openapi.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUT_FILE="${REPO_ROOT}/docs/api/openapi.yml"

mkdir -p "$(dirname "${OUT_FILE}")"
cd "${REPO_ROOT}/backend-django"
DJANGO_ENV=dev uv run python manage.py spectacular \
    --file "${OUT_FILE}" \
    --format openapi

echo "OpenAPI snapshot updated: ${OUT_FILE}"
