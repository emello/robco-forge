#!/bin/bash

# RobCo Forge - Stop Local Development Environment

set -e

echo "🛑 Stopping RobCo Forge Local Development Environment"
echo ""

# Stop API server
echo "Stopping API server..."
pkill -f "uvicorn src.main:app" || echo "API server not running"

# Stop Docker services
echo "Stopping Docker services..."
docker-compose -f docker-compose.dev.yml down

echo ""
echo "✅ All services stopped"
