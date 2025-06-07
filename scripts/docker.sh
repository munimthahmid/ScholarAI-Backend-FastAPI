#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

###############################################################################
# Pretty colours
###############################################################################
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

###############################################################################
# Paths & constants
###############################################################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"
COMPOSE_FILE="$DOCKER_DIR/docker-compose.yml"
IMAGE_NAME="scholar-ai-fastapi-app"
CONTAINER_NAME="scholarai-fastapi"
NETWORK_NAME="docker_scholar-network"
ENV_FILE="$PROJECT_ROOT/.env"

###############################################################################
# Detect docker-compose command
###############################################################################
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    COMPOSE_CMD=("docker" "compose")
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD=("docker-compose")
else
    echo -e "${RED}✖ Neither 'docker compose' nor 'docker-compose' is available.${NC}"
    exit 1
fi

###############################################################################
# Ensure the Docker network exists
###############################################################################
ensure_network() {
    if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
        echo -e "${YELLOW}⚠ Network '$NETWORK_NAME' not found. Creating...${NC}"
        docker network create "$NETWORK_NAME"
    fi
}

###############################################################################
# Load environment variables
###############################################################################
load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        echo -e "${CYAN}ℹ Loading environment from $ENV_FILE${NC}"
        set -a
        # shellcheck disable=SC1090
        source "$ENV_FILE"
        set +a
    else
        echo -e "${YELLOW}⚠ $ENV_FILE not found; proceeding without it.${NC}"
    fi
}

###############################################################################
# Build the FastAPI image
###############################################################################
build_docker() {
    echo -e "${BLUE}▶ Building Docker image '${IMAGE_NAME}'...${NC}"
    load_env

    docker build \
        -t "$IMAGE_NAME" \
        -f "$DOCKER_DIR/Dockerfile" \
        "$PROJECT_ROOT"

    echo -e "${GREEN}✔ Docker image '${IMAGE_NAME}' built successfully.${NC}"
}

###############################################################################
# Start / stop helpers
###############################################################################
start_app() {
    echo -e "${CYAN}▶ Starting FastAPI container '${CONTAINER_NAME}'...${NC}"
    echo -e "${YELLOW}ℹ Ensure core services (RabbitMQ) are running on network '$NETWORK_NAME'.${NC}"
    load_env
    ensure_network

    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

    echo -e "${GREEN}✔ FastAPI is up → http://localhost:8000/health${NC}"
}

stop_app() {
    echo -e "${CYAN}▶ Stopping FastAPI container '${CONTAINER_NAME}'...${NC}"
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✔ FastAPI stopped.${NC}"
}

###############################################################################
# Rebuild logic
###############################################################################
rebuild_app() {
    echo -e "${YELLOW}⚡ Rebuilding and restarting FastAPI...${NC}"
    stop_app
    build_docker
    start_app
    echo -e "${GREEN}✔ Rebuild complete.${NC}"
}

rebuild_nocache() {
    echo -e "${YELLOW}⚡ Rebuilding (no cache) and restarting FastAPI...${NC}"
    stop_app
    load_env
    ensure_network

    docker build --no-cache \
        -t "$IMAGE_NAME" \
        -f "$DOCKER_DIR/Dockerfile" \
        "$PROJECT_ROOT"

    start_app
    echo -e "${GREEN}✔ No-cache rebuild complete.${NC}"
}

###############################################################################
# Status & Logs
###############################################################################
status() {
    echo -e "${CYAN}▶ FastAPI container status:${NC}"
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps
}

logs() {
    echo -e "${CYAN}▶ Streaming FastAPI logs (Ctrl+C to exit):${NC}"
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" logs -f --tail=100
}

###############################################################################
# Combined Build & Run
###############################################################################
up_command() {
    echo -e "${BLUE}▶ Build & start FastAPI...${NC}"
    build_docker
    start_app
}

###############################################################################
# CLI entrypoint
###############################################################################
usage() {
    echo -e "${YELLOW}Usage:${NC} $(basename "$0") {build|start|stop|restart|up|rebuild|rebuild-nocache|status|logs}${NC}"
    exit 1
}

case "${1:-}" in
    build)           build_docker    ;;
    start)           start_app       ;;
    stop)            stop_app        ;;
    restart)         stop_app && start_app ;;
    up)              up_command      ;;
    rebuild)         rebuild_app     ;;
    rebuild-nocache) rebuild_nocache ;;
    status)          status          ;;
    logs)            logs            ;;
    *)               usage           ;;
esac
