#!/bin/bash
# CortexOS — First-time setup script
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No colour

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}       CortexOS Setup                   ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check required tools
check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo -e "${RED}ERROR: $1 is not installed.${NC}"
    echo "  Install it first, then re-run this script."
    exit 1
  fi
}

echo "Checking prerequisites..."
check_command docker
check_command git
echo -e "${GREEN}All prerequisites met.${NC}"
echo ""

# Check Docker is running
if ! docker info &> /dev/null; then
  echo -e "${RED}ERROR: Docker daemon is not running.${NC}"
  echo "  Start Docker Desktop (macOS/Windows) or run: sudo systemctl start docker"
  exit 1
fi

# Create .env from example
if [ -f .env ]; then
  echo -e "${YELLOW}WARNING: .env already exists. Skipping copy to avoid overwriting your config.${NC}"
else
  cp .env.example .env
  echo -e "${GREEN}.env created from .env.example${NC}"
fi

# Create backups directory
mkdir -p backups
echo -e "${GREEN}backups/ directory created${NC}"

# Create docs/screenshots directory
mkdir -p docs/screenshots
echo -e "${GREEN}docs/screenshots/ directory created${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}       Next Steps                       ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "1. Edit .env with your API keys and passwords:"
echo "   nano .env"
echo ""
echo "   Required fields:"
echo "   - POSTGRES_PASSWORD  (generate: openssl rand -base64 24)"
echo "   - NEO4J_PASSWORD     (generate: openssl rand -base64 24)"
echo "   - SECRET_KEY         (generate: openssl rand -hex 32)"
echo "   - ANTHROPIC_API_KEY  (from console.anthropic.com)"
echo "   - LANGFUSE_NEXTAUTH_SECRET  (generate: openssl rand -hex 32)"
echo "   - LANGFUSE_SALT             (generate: openssl rand -hex 32)"
echo ""
echo "2. Start all services:"
echo "   make up"
echo ""
echo "3. Run database migrations:"
echo "   make migrate"
echo ""
echo "4. Open CortexOS:"
echo "   http://localhost:3000"
echo "   Default login: admin@cortexos.ai / admin"
echo ""
echo -e "${YELLOW}Remember to change the default admin password immediately.${NC}"
echo ""
