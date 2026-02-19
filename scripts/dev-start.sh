#!/bin/bash

# RobCo Forge - Local Development Startup Script
# This script sets up and starts all services for local development

set -e

echo "🚀 Starting RobCo Forge Local Development Environment"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ Python 3 is required but not installed.${NC}" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}❌ Node.js is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ Docker is required but not installed.${NC}" >&2; exit 1; }

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Start Docker services
echo "🐳 Starting Docker services (PostgreSQL, Redis)..."

docker-compose -f docker-compose.dev.yml up -d

echo -e "${GREEN}✓ Docker services started${NC}"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec forge-postgres pg_isready -U forge > /dev/null 2>&1; do
  sleep 1
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
echo ""

# Set up Python API
echo "🐍 Setting up Python API..."

cd api

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
  echo "Creating .env file from template..."
  cp .env.example .env
  echo -e "${YELLOW}⚠️  Please edit api/.env with your configuration${NC}"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo -e "${GREEN}✓ API setup complete${NC}"
echo ""

# Set up CLI
echo "📦 Setting up CLI..."

cd ../cli

# Install dependencies
echo "Installing Node.js dependencies..."
npm install --silent

# Build CLI
echo "Building CLI..."
npm run build

echo -e "${GREEN}✓ CLI setup complete${NC}"
echo ""

# Start API server in background
echo "🚀 Starting API server..."

cd ../api
source venv/bin/activate

# Start API in background
nohup uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/api.log 2>&1 &
API_PID=$!

echo "API server started (PID: $API_PID)"
echo "Logs: logs/api.log"
echo ""

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is ready${NC}"
    break
  fi
  sleep 1
done

echo ""
echo "✅ RobCo Forge Local Development Environment is ready!"
echo ""
echo "📍 Services:"
echo "  - API:        http://localhost:8000"
echo "  - API Docs:   http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis:      localhost:6379"
echo ""
echo "🔧 CLI Commands:"
echo "  cd cli"
echo "  npm run dev -- --help"
echo "  npm run dev -- config set apiUrl http://localhost:8000"
echo "  npm run dev -- list"
echo ""
echo "📝 Logs:"
echo "  API:    tail -f logs/api.log"
echo "  Docker: docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "🛑 To stop:"
echo "  ./scripts/dev-stop.sh"
echo ""
