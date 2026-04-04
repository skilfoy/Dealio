#!/bin/bash
set -euo pipefail

# Async mode: allow session to start while Docker services initialize
echo '{"async": true, "asyncTimeout": 120000}'

# Only run in remote Claude Code cloud environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

echo "🚀 Starting DealRadar services..."

# Start all Docker services in background mode
docker compose up --build -d

echo "⏳ Waiting for services to become healthy..."

# Wait for Postgres to be healthy (max 30 seconds)
for i in {1..30}; do
  if docker compose exec postgres pg_isready -U dealradar &>/dev/null; then
    echo "✅ Postgres is healthy"
    break
  fi
  echo "  Waiting for Postgres... ($i/30)"
  sleep 1
done

# Wait for Redis to be healthy (max 30 seconds)
for i in {1..30}; do
  if docker compose exec redis redis-cli ping &>/dev/null; then
    echo "✅ Redis is healthy"
    break
  fi
  echo "  Waiting for Redis... ($i/30)"
  sleep 1
done

echo "✅ All services started successfully!"
echo ""
echo "📝 DealRadar is running on:"
echo "   Frontend: http://localhost:5173"
echo "   API: http://localhost:8000"
echo ""
