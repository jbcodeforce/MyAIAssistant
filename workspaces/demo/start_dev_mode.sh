#!/bin/bash
# Development mode startup script for MyAIAssistant
# Uses the biz-db workspace configuration and data

set -e

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
WORKSPACE_DIR="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  MyAIAssistant Development Mode${NC}"
echo -e "${BLUE}  Workspace: biz-db${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${YELLOW}Configuration:${NC}"
echo -e "  Project Root:  $PROJECT_ROOT"
echo -e "  Workspace:     $WORKSPACE_DIR"
echo -e "  Config File:   $WORKSPACE_DIR/config.yaml"
echo -e "  Database:      $WORKSPACE_DIR/data/biz-assistant.db"
echo -e "  ChromaDB:      $WORKSPACE_DIR/data/chroma/"

# Export config file for backend
export CONFIG_FILE="$WORKSPACE_DIR/config.yaml"

# Ensure data directory exists
mkdir -p "$WORKSPACE_DIR/data"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null && echo -e "${GREEN}Backend stopped${NC}"
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null && echo -e "${GREEN}Frontend stopped${NC}"
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check for required tools
check_requirements() {
    local missing=0
    
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: 'uv' is not installed${NC}"
        echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        missing=1
    fi
    
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: 'node' is not installed${NC}"
        missing=1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}Error: 'npm' is not installed${NC}"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        exit 1
    fi
}

# Start backend
start_backend() {
    echo -e "\n${GREEN}Starting Backend...${NC}"
    echo -e "  Port: 8000"
    echo -e "  Config: $CONFIG_FILE"
    
    cd "$WORKSPACE_DIR"
    
    # Run uvicorn from workspace directory so relative paths in config.yaml work
    uv run --project "$BACKEND_DIR" \
        uvicorn app.main:app \
        --reload \
        --host 0.0.0.0 \
        --port 8000 \
        --app-dir "$BACKEND_DIR" &
    
    BACKEND_PID=$!
    echo -e "  PID: $BACKEND_PID"
    
    # Wait for backend to be ready
    echo -e "  ${YELLOW}Waiting for backend to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "  ${GREEN}Backend is ready!${NC}"
            break
        fi
        sleep 1
    done
}

# Start frontend
start_frontend() {
    echo -e "\n${GREEN}Starting Frontend...${NC}"
    echo -e "  Port: 3000"
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if node_modules is missing
    if [ ! -d "node_modules" ]; then
        echo -e "  ${YELLOW}Installing dependencies...${NC}"
        npm install
    fi
    
    npm run dev &
    FRONTEND_PID=$!
    echo -e "  PID: $FRONTEND_PID"
    
    # Wait for frontend to be ready
    echo -e "  ${YELLOW}Waiting for frontend to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "  ${GREEN}Frontend is ready!${NC}"
            break
        fi
        sleep 1
    done
}

# Main execution
check_requirements
start_backend
start_frontend

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Development environment is running!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e ""
echo -e "  ${YELLOW}Frontend:${NC}  http://localhost:3000"
echo -e "  ${YELLOW}Backend:${NC}   http://localhost:8000"
echo -e "  ${YELLOW}API Docs:${NC}  http://localhost:8000/docs"
echo -e "  ${YELLOW}Config:${NC}    http://localhost:8000/debug/config"
echo -e ""
echo -e "  Press ${RED}Ctrl+C${NC} to stop all services"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Wait for processes
wait

