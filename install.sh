#!/bin/bash
#
# MyAIAssistant Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/jbcodeforce/MyAIAssistant/main/install.sh | bash
#
# This script:
# - Checks for Docker and Docker Compose
# - Downloads docker-compose.yml and config.yaml
# - Creates necessary directories
# - Provides instructions to get started

set -e

REPO_URL="https://raw.githubusercontent.com/jbcodeforce/MyAIAssistant/main"
INSTALL_DIR="${MYAIASSISTANT_DIR:-$HOME/myaiassistant}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  MyAIAssistant Installer${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

check_docker() {
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | tr -d ',')
        print_success "Docker found: $DOCKER_VERSION"
        return 0
    else
        return 1
    fi
}

check_docker_compose() {
    # Check for docker compose (v2) first, then docker-compose (v1)
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || docker compose version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        print_success "Docker Compose found: $COMPOSE_VERSION"
        COMPOSE_CMD="docker compose"
        return 0
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        print_success "Docker Compose found: $COMPOSE_VERSION"
        COMPOSE_CMD="docker-compose"
        return 0
    else
        return 1
    fi
}

install_docker_linux() {
    print_info "Installing Docker on Linux..."
    
    # Detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        print_error "Cannot detect Linux distribution"
        return 1
    fi

    case $DISTRO in
        ubuntu|debian)
            print_info "Detected $DISTRO, using apt..."
            sudo apt-get update
            sudo apt-get install -y ca-certificates curl gnupg
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$DISTRO \
              $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
              sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        fedora)
            print_info "Detected Fedora, using dnf..."
            sudo dnf -y install dnf-plugins-core
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
        centos|rhel)
            print_info "Detected $DISTRO, using yum..."
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
        *)
            print_error "Unsupported distribution: $DISTRO"
            print_info "Please install Docker manually: https://docs.docker.com/engine/install/"
            return 1
            ;;
    esac

    # Add current user to docker group
    if [ "$(id -u)" -ne 0 ]; then
        sudo usermod -aG docker $USER
        print_warning "Added $USER to docker group. You may need to log out and back in for this to take effect."
    fi
}

install_docker_macos() {
    print_info "Installing Docker on macOS..."
    
    if command -v brew &> /dev/null; then
        print_info "Using Homebrew to install Docker..."
        brew install --cask docker
        print_warning "Docker Desktop installed. Please start Docker Desktop from Applications."
        print_warning "After starting Docker Desktop, run this installer again."
        exit 0
    else
        print_error "Homebrew not found."
        print_info "Please install Docker Desktop manually: https://docs.docker.com/desktop/install/mac-install/"
        print_info "Or install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
}

install_docker() {
    OS="$(uname -s)"
    case "$OS" in
        Linux)
            install_docker_linux
            ;;
        Darwin)
            install_docker_macos
            ;;
        *)
            print_error "Unsupported OS: $OS"
            print_info "Please install Docker manually: https://docs.docker.com/get-docker/"
            exit 1
            ;;
    esac
}

download_file() {
    local url="$1"
    local dest="$2"
    
    if command -v curl &> /dev/null; then
        curl -fsSL "$url" -o "$dest"
    elif command -v wget &> /dev/null; then
        wget -q "$url" -O "$dest"
    else
        print_error "Neither curl nor wget found. Cannot download files."
        exit 1
    fi
}

create_config() {
    cat > "$INSTALL_DIR/config.yaml" << 'EOF'
# MyAIAssistant Configuration
# Modify these settings as needed for your environment

# Database settings (PostgreSQL)
# Uses Docker Compose service name as host
database_url: "postgresql+asyncpg://postgres:postgres@postgres:5432/myaiassistant"

# Knowledge base / Vector store settings
chroma_persist_directory: "/app/data/chroma"
chroma_collection_name: "km-db"

# CORS settings (list of allowed origins)
cors_origins:
  - "http://localhost:5173"
  - "http://localhost:3000"
  - "http://localhost:80"
  - "http://localhost"

# LLM settings
# Supported providers: ollama, openai, anthropic
llm_provider: "ollama"
llm_model: "gpt-oss:20b"
llm_api_key: null
llm_base_url: "http://host.docker.internal:11434"
llm_max_tokens: 2048
llm_temperature: 0.1
EOF
}

# Main installation process
main() {
    print_header

    # Check for Docker
    print_info "Checking prerequisites..."
    echo ""

    if ! check_docker; then
        print_warning "Docker not found."
        echo ""
        read -p "Would you like to install Docker? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_docker
            # Re-check after installation
            if ! check_docker; then
                print_error "Docker installation may have failed or requires restart."
                exit 1
            fi
        else
            print_error "Docker is required. Please install Docker and run this script again."
            print_info "Install Docker: https://docs.docker.com/get-docker/"
            exit 1
        fi
    fi

    if ! check_docker_compose; then
        print_error "Docker Compose not found."
        print_info "Docker Compose is usually included with Docker Desktop."
        print_info "For Linux, install docker-compose-plugin package."
        exit 1
    fi

    echo ""
    print_info "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/data"
    cd "$INSTALL_DIR"

    # Download docker-compose.yml
    print_info "Downloading docker-compose.yml..."
    download_file "$REPO_URL/docker-compose.yml" "$INSTALL_DIR/docker-compose.yml"
    print_success "docker-compose.yml downloaded"

    # Create config.yaml if it doesn't exist
    if [ -f "$INSTALL_DIR/config.yaml" ]; then
        print_warning "config.yaml already exists, skipping..."
    else
        print_info "Creating config.yaml..."
        create_config
        print_success "config.yaml created"
    fi

    if [ -d "$INSTALL_DIR/scripts" ]; then
        print_warning "scripts directory already exists, skipping..."
    else
        print_info "Creating scripts directory..."
        mkdir -p "$INSTALL_DIR/scripts"
        download_file "$REPO_URL/data/backup_ps_db.sh" "$INSTALL_DIR/scripts/backup_ps_db.sh"
        chmod +x "$INSTALL_DIR/scripts/backup_ps_db.sh"
        download_file "$REPO_URL/data/restore_pd_db.sh" "$INSTALL_DIR/scripts/restore_pd_db.sh"
        chmod +x "$INSTALL_DIR/scripts/restore_pd_db.sh"
        print_success "scripts directory created"
    fi

    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Installation Complete${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo ""
    echo "Files created:"
    echo "  - docker-compose.yml"
    echo "  - config.yaml"
    echo "  - data/ (for persistent storage)"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo ""
    echo "1. Review and customize config.yaml:"
    echo -e "   ${YELLOW}code $INSTALL_DIR/config.yaml${NC}"
    echo ""
    echo "2. Configure your LLM provider in config.yaml:"
    echo "   - For Ollama (default): Ensure Ollama is running on port 11434"
    echo "   - For OpenAI: Set llm_provider, llm_model, and llm_api_key"
    echo ""
    echo "3. Start MyAIAssistant:"
    echo -e "   ${YELLOW}cd $INSTALL_DIR && $COMPOSE_CMD up -d${NC}"
    echo ""
    echo "4. Access the application:"
    echo "   - Web UI: http://localhost:80"
    echo "   - API Docs: http://localhost:8000/docs"
    echo ""
    echo "5. Stop MyAIAssistant:"
    echo -e "   ${YELLOW}cd $INSTALL_DIR && $COMPOSE_CMD down${NC}"
    echo ""
    echo "For more information, visit:"`echo -e "${YELLOW}https://jbcodeforce.github.io/MyAIAssistant/user_guide/${NC}"`
    echo ""
}

# Run main function
main

