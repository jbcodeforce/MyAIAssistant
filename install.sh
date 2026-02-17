#!/bin/bash
#
# MyAIAssistant Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/jbcodeforce/MyAIAssistant/main/install.sh | bash
#
# This script:
# - Checks for Docker and Docker Compose
# - Optionally installs the ai_assist CLI tool
# - Downloads docker-compose.yml and config.yaml
# - Creates necessary directories
# - Provides instructions to get started

set -e

REPO_URL="https://raw.githubusercontent.com/jbcodeforce/MyAIAssistant/main"
INSTALL_DIR="${MYAIASSISTANT_DIR:-$HOME/myaiassistant}"
CLI_INSTALL="${AI_ASSIST_CLI:-true}"

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

check_uv() {
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version | cut -d ' ' -f2)
        print_success "uv found: $UV_VERSION"
        return 0
    else
        return 1
    fi
}

install_uv() {
    print_info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the env to get uv in path
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    fi
    export PATH="$HOME/.local/bin:$PATH"
}

install_llm() {
    # Installs OSAURIS (macOS) or Ollama (Linux/other) for LLM support.
    OS="$(uname -s)"
    if [ "$OS" = "Darwin" ]; then
        print_info "macOS detected. Installing osaurus..."
        if ! command -v brew &> /dev/null; then
            print_error "Homebrew is required to install osauris. Please install Homebrew first: https://brew.sh/"
            return 1
        fi
        brew install osaurus
        if command -v osaurus &> /dev/null; then
            print_success "osaurus installed successfully."
            return 0    
        else
            print_error "osaurus installation failed."
            return 1
        fi
    else
        print_info "Non-macOS detected. Installing Ollama..."
        if command -v ollama &> /dev/null; then
            print_success "Ollama is already installed."
            return 0
        fi
        if [ "$OS" = "Linux" ]; then
            curl -fsSL https://ollama.com/install.sh | sh
        else
            print_warning "Automatic Ollama installation is only supported on Linux. Please follow manual instructions: https://ollama.com/download"
            return 1
        fi
        if command -v ollama &> /dev/null; then
            print_success "Ollama installed successfully."
            return 0
        else
            print_error "Ollama installation failed."
            return 1
        fi
    fi

}

install_cli() {
    print_info "Installing ai_assist CLI tool..."
    
    # Check for uv
    if ! check_uv; then
        print_warning "uv not found."
        read -p "Would you like to install uv (recommended Python package manager)? [Y/n] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            install_uv
            if ! check_uv; then
                print_error "uv installation failed. Skipping CLI installation."
                return 1
            fi
        else
            print_warning "Skipping CLI installation (requires uv or pip)."
            return 1
        fi
    fi
    
    # Download CLI package
    print_info "Building agent_core..."
    cd $INSTALL_DIR/code/agent_core
    uv build
    print_info "Building ai_assist_cli..."
    cd ../ai_assist_cli
    uv build
    print_info "Installing ai_assist_cli..."
    uv tool install ./dist/ai_assist_cli-0.1.0-py3-none-any.whl \
    --with ../agent_core/dist/agent_core-0.1.0-py3-none-any.whl \
    --force

    
    if command -v ai_assist &> /dev/null; then
        print_success "ai_assist CLI installed successfully"
        return 0
    else
        print_warning "CLI installed but may require adding ~/.local/bin to PATH"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
        return 0
    fi
}


# Main installation process
main() {
    print_header

    echo ""
    print_header
    print_info "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    export MYAIASSISTANT_DIR=$(pwd)
    mkdir -p "$INSTALL_DIR/code"
    mkdir -p "$INSTALL_DIR/workspaces"
    # Clone the repository if not already present in INSTALL_DIR/code
    if [ ! -d "$INSTALL_DIR/code/.git" ]; then
        print_info "Cloning MyAIAssistant repository into $INSTALL_DIR/code..."
        git clone https://github.com/jbcodeforce/MyAIAssistant.git "$INSTALL_DIR/code"
        print_success "Repository cloned"
        cd "$INSTALL_DIR/code"
    else
        print_info "Repository already present in $INSTALL_DIR/code , skipping clone."
    fi

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

    # Install CLI tool
    echo ""
    if [ "$CLI_INSTALL" = "true" ]; then
        install_cli || print_warning "CLI installation skipped or failed."
    else
        print_info "Skipping CLI installation (AI_ASSIST_CLI=false)"
    fi
    install_llm || print_warning "LLM installation skipped or failed."

    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Installation Complete${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "Installation directory: $INSTALL_DIR"
    echo ""
    echo "Folders created:"
    echo "  - $INSTALL_DIR/code   the cloned code to access product features"
    echo "  - $INSTALL_DIR/workspaces the folder to define your own isolated workspaces"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo ""
    if command -v ai_assist &> /dev/null; then
        echo "1. Initialize a workspace:"
        echo "cd $INSTALL_DIR"
        echo -e "   ${YELLOW}ai_assist init ./workspaces/business${NC}"
    fi
    echo ""
    echo "2. Configure your LLM provider as environment variables:"
    echo "   - For Ollama (default): Ensure Ollama is running on port 11434"
    echo "   - For OpenAI: Set llm_provider, llm_model, and llm_api_key"
    echo "   - For OSAURUS: Set llm_provider, llm_model, and llm_api_key"
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
    if command -v ai_assist &> /dev/null; then
        echo -e "${BLUE}CLI Commands:${NC}"
        echo "  ai_assist init [path]        - Initialize a new workspace"
        echo "  ai_assist workspace status   - Show workspace status"
        echo "  ai_assist config show        - Display configuration"
        echo "  ai_assist --help             - Show all commands"
        echo ""
    fi
    echo "For more information, visit:"
    echo -e "  ${YELLOW}https://jbcodeforce.github.io/MyAIAssistant/user_guide/${NC}"
    echo ""
}

# Run main function
main

