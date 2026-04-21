#!/bin/bash
# Development mode startup script for agent_service

set -e

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

AGENT_SERVICE_DIR="$SCRIPT_DIR"


# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${YELLOW}Configuration:${NC}"
echo -e "  Project Root:  $PROJECT_ROOT"
echo -e "  Database:      $AGENT_SERVICE_DIR/test_wksp/content.db"
echo -e "  LanceDB:       $AGENT_SERVICE_DIR/test_wksp/vs.db"

# Export config for backend and agent service URL when running agent_service in this script
export AI_DB_FILE="$AGENT_SERVICE_DIR/test_wksp/memory.db"
export VS_DB_URL="$AGENT_SERVICE_DIR/test_wksp/vs.db"
export AGENT_SERVICE_URL="http://localhost:8100"
export AGNO_DEBUG=1
export TRACE_LLM_PROMPT=1


# Function to cleanup on exit (only kills processes we started)
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ -n "$AGENT_SERVICE_PID" ]; then
        kill $AGENT_SERVICE_PID 2>/dev/null && echo -e "${GREEN}Agent service stopped${NC}"
    fi
    if [ -n "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null && echo -e "${GREEN}Ollama stopped${NC}"
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
    
    if [ $missing -eq 1 ]; then
        exit 1
    fi
}

# Start Ollama if not already running (agent_service needs it for chat and RAG embeddings)
ensure_ollama() {
    local url="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
    if curl -s -f "$url/api/tags" > /dev/null 2>&1; then
        echo -e "\n${GREEN}Ollama already running${NC} ($url)"
        return
    fi
    if ! command -v ollama &> /dev/null; then
        echo -e "\n${YELLOW}Ollama not installed or not in PATH; agent_service chat/RAG may fail.${NC}"
        echo -e "  Install: https://ollama.com or run \`ollama serve\` in another terminal."
        return
    fi
    echo -e "\n${GREEN}Starting Ollama...${NC}"
    echo -e "  URL: $url"
    ollama serve &
    OLLAMA_PID=$!
    echo -e "  PID: $OLLAMA_PID"
    echo -e "  ${YELLOW}Waiting for Ollama to start...${NC}"
    for i in {1..30}; do
        if curl -s -f "$url/api/tags" > /dev/null 2>&1; then
            echo -e "  ${GREEN}Ollama is ready!${NC}"
            return
        fi
        sleep 1
    done
    echo -e "  ${YELLOW}Ollama may still be starting; continuing.${NC}"
}

# Start agent_service only if not already running (Ollama-backed chat, RAG, extract, tag)
ensure_agent_service() {
    if curl -s http://localhost:8100/health > /dev/null 2>&1; then
        echo -e "\n${GREEN}Agent service already running${NC} (http://localhost:8100)"
        return
    fi
    echo -e "\n${GREEN}Starting Agent Service...${NC}"
    echo -e "  Port: 8100"
    echo -e "  Project: $AGENT_SERVICE_DIR"
    
    cd "$AGENT_SERVICE_DIR"
    
    uv run  python  agent_service/main.py
    
    AGENT_SERVICE_PID=$!
    echo -e "  PID: $AGENT_SERVICE_PID"
    
    echo -e "  ${YELLOW}Waiting for agent service to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8100/health > /dev/null 2>&1; then
            echo -e "  ${GREEN}Agent service is ready!${NC}"
            break
        fi
        sleep 1
    done
}


# Main execution
check_requirements
ensure_ollama
ensure_agent_service


echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Development environment is running!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e ""
echo -e "  ${YELLOW}Agent Service:${NC}  http://localhost:8100 (backend proxies chat/RAG to it)"
echo -e "  ${YELLOW}Ollama:${NC}         ${OLLAMA_BASE_URL:-http://127.0.0.1:11434} (chat + embeddings; started by script if not running)"
echo -e ""
echo -e "  Press ${RED}Ctrl+C${NC} to stop all services"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Wait for processes
wait

