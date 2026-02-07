#!/bin/bash

# KIRO2 Development Environment Setup Script (Linux/Mac)
# Prerequisites: Python 3.11+ installed

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}KIRO2 Development Environment Setup${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo -e "${GREEN}✓ Python version OK: Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3.11+ required. Current: Python $PYTHON_VERSION${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Install uv if not present
echo -e "\n${YELLOW}Checking for uv...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv package manager...${NC}"
    
    # Install using pip
    pip3 install --upgrade uv
    
    # Alternative: Install using curl
    # curl -LsSf https://astral.sh/uv/install.sh | sh
    
    echo -e "${GREEN}✓ uv installed successfully${NC}"
else
    echo -e "${GREEN}✓ uv already installed${NC}"
fi

# Create virtual environment with uv
echo -e "\n${YELLOW}Setting up Python virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        uv venv --python 3.11
        echo -e "${GREEN}✓ Virtual environment recreated${NC}"
    fi
else
    uv venv --python 3.11
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies with uv
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
uv pip sync pyproject.toml
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install development dependencies
echo -e "\n${YELLOW}Installing development dependencies...${NC}"
uv pip install -e ".[dev]"
echo -e "${GREEN}✓ Development dependencies installed${NC}"

# Install pre-commit hooks
echo -e "\n${YELLOW}Setting up pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    pre-commit install --hook-type commit-msg
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}⚠ pre-commit not found, skipping hook installation${NC}"
fi

# Setup PostgreSQL connection
echo -e "\n${YELLOW}Database Configuration:${NC}"
echo -e "  ${CYAN}PostgreSQL should be running on port 5434${NC}"
echo -e "  ${CYAN}Redis should be running on port 6379${NC}"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "\n${YELLOW}Creating .env file from template...${NC}"
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo -e "${GREEN}✓ .env file created (please update with your credentials)${NC}"
    else
        echo -e "${YELLOW}⚠ No .env.example found, creating minimal .env...${NC}"
        cat > backend/.env << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/kiro2

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys (add your keys)
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Environment
ENVIRONMENT=development
DEBUG=true
EOF
        echo -e "${GREEN}✓ Minimal .env file created${NC}"
    fi
fi

# Frontend setup
echo -e "\n${YELLOW}Setting up frontend...${NC}"
cd frontend
if [ -d "node_modules" ]; then
    echo -e "${YELLOW}Node modules already exist${NC}"
else
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi
cd ..

# Generate TypeScript types from OpenAPI
echo -e "\n${YELLOW}Generating TypeScript types...${NC}"
if [ -f "scripts/generate-types.sh" ]; then
    bash scripts/generate-types.sh
    echo -e "${GREEN}✓ TypeScript types generated${NC}"
else
    echo -e "${YELLOW}⚠ Type generation script not found${NC}"
fi

# Run initial tests
echo -e "\n${YELLOW}Running initial tests...${NC}"
cd backend
if pytest --tb=short --maxfail=5 -x; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed (this might be expected for first setup)${NC}"
fi
cd ..

# Final instructions
echo -e "\n${CYAN}=====================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update backend/.env with your credentials"
echo "2. Start PostgreSQL on port 5434"
echo "3. Start Redis on port 6379"
echo "4. Run database migrations: cd backend && alembic upgrade head"
echo "5. Start backend: cd backend && uvicorn main:app --reload --port 8000"
echo "6. Start frontend: cd frontend && npm run dev -- --port 3001"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  uv pip list              # List installed packages"
echo "  ruff check backend/      # Run linter"
echo "  ruff format backend/     # Format code"
echo "  pre-commit run --all     # Run all pre-commit hooks"
echo "  pytest backend/tests/    # Run tests"
echo ""