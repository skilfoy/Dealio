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

# Create public tunnels for cloud access
if command -v bdy &> /dev/null; then
  echo "🌐 Creating public tunnels..."

  # Create tunnels in background and capture output files
  bdy tunnel http localhost:5173 --auth public > /tmp/frontend_tunnel.txt 2>&1 &
  FRONTEND_PID=$!

  bdy tunnel http localhost:8000 --auth public > /tmp/api_tunnel.txt 2>&1 &
  API_PID=$!

  # Wait a moment for tunnels to initialize
  sleep 3

  # Extract URLs from output
  FRONTEND_URL=$(grep -oP 'https://[^\s]+' /tmp/frontend_tunnel.txt 2>/dev/null | head -1)
  API_URL=$(grep -oP 'https://[^\s]+' /tmp/api_tunnel.txt 2>/dev/null | head -1)

  if [ -n "$FRONTEND_URL" ] && [ -n "$API_URL" ]; then
    echo "✅ Public tunnels created!"
    echo ""
    echo "🎉 DealRadar is accessible from your browser:"
    echo "   Frontend: $FRONTEND_URL"
    echo "   API:      $API_URL"
    echo "   Docs:     $API_URL/docs"
    echo ""
  else
    echo "⚠️  Buddy CLI available but tunnel creation had issues"
    echo "   Frontend (localhost): http://localhost:5173"
    echo "   API (localhost):      http://localhost:8000"
  fi
else
  echo "📝 DealRadar is running locally:"
  echo "   Frontend: http://localhost:5173"
  echo "   API:      http://localhost:8000"
  echo ""
  echo "💡 For cloud access, install Buddy CLI:"
  echo "   https://buddy.works"
fi
echo ""
