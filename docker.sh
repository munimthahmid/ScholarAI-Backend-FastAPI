#!/bin/bash

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
ROOT_DIR="$(dirname "$0")"
# Ensure this points to the docker-compose.yml in the FastAPI project
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
IMAGE_NAME="scholar-ai-fastapi-app"
CONTAINER_NAME="scholarai-fastapi"

###############################################################################
# Build the FastAPI image
###############################################################################
build_docker() {
    echo -e "${BLUE}▶ Building Docker image '${IMAGE_NAME}'...${NC}"

    # Source the .env file from the project root to load ENV variables
    # This is important if your Dockerfile or compose file uses build-time ARGs from .env
    if [ -f "$ROOT_DIR/.env" ]; then
        echo -e "${CYAN}ℹ Sourcing environment variables from $ROOT_DIR/.env${NC}"
        set -a # Automatically export all variables defined by source
        # shellcheck source=/dev/null # Path is dynamic
        source "$ROOT_DIR/.env"
        set +a
    else
        echo -e "${YELLOW}⚠ $ROOT_DIR/.env file not found. Some environment variables might not be set for the build process if they are expected as build ARGs.${NC}"
    fi

    # Example: If your Dockerfile expected an ENV build arg like the Spring Boot one
    # Docker build command would be: docker build --build-arg ENV="${ENV:-dev}" ...
    # For now, the FastAPI Dockerfile doesn't use build-time ARGs from .env directly

    docker build -t "$IMAGE_NAME" -f "$ROOT_DIR/Dockerfile" "$ROOT_DIR" || {
        echo -e "${RED}✖ Docker build failed.${NC}"
        exit 1
    }

    echo -e "${GREEN}✔ Docker image '${IMAGE_NAME}' built successfully.${NC}"
}

###############################################################################
# Start / stop helpers
###############################################################################
start_app() {
    echo -e "${CYAN}▶ Starting FastAPI application '${CONTAINER_NAME}'...${NC}"
    echo -e "${YELLOW}ℹ Make sure the 'scholar-network' Docker network exists and core services (RabbitMQ) are running.${NC}"
    # Pass --env-file to ensure .env variables are loaded by docker-compose
    docker compose -f "$COMPOSE_FILE" --env-file "$ROOT_DIR/.env" up -d --build # --build ensures image is rebuilt if Dockerfile changed
    echo -e "${GREEN}✔ FastAPI application is starting. API → http://localhost:8001/health ${NC}"
}

stop_app() {
    echo -e "${CYAN}▶ Stopping FastAPI application '${CONTAINER_NAME}'...${NC}"
    docker compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✔ FastAPI application stopped.${NC}"
}

###############################################################################
# Rebuild logic
###############################################################################
rebuild_app() {
    echo -e "${YELLOW}⚡ Rebuilding and restarting FastAPI application...${NC}"
    stop_app
    build_docker # Build image separately first
    start_app    # Then use compose up, which will use the newly built image
    echo -e "${GREEN}✔ FastAPI application rebuild completed.${NC}"
}

rebuild_nocache() {
    echo -e "${YELLOW}⚡ Rebuilding FastAPI (no-cache) and restarting...${NC}"
    stop_app
    # Build with no-cache directly
    docker build --no-cache -t "$IMAGE_NAME" -f "$ROOT_DIR/Dockerfile" "$ROOT_DIR" || {
        echo -e "${RED}✖ Docker build (no-cache) failed.${NC}"
        exit 1
    }
    start_app
    echo -e "${GREEN}✔ FastAPI application rebuild (no-cache) completed.${NC}"
}

###############################################################################
# Status & Logs
###############################################################################
status() {
    echo -e "${CYAN}▶ Current status for FastAPI application:${NC}"
    docker compose -f "$COMPOSE_FILE" ps
}

logs() {
    echo -e "${CYAN}▶ Showing logs for FastAPI application (Ctrl+C to exit):${NC}"
    docker compose -f "$COMPOSE_FILE" logs -f --tail=100
}

###############################################################################
# Combined Build & Run
###############################################################################
up_command() {
    echo -e "${BLUE}▶ Building and starting FastAPI application...${NC}"
    build_docker
    start_app
    # start_app already prints success message, so no extra one needed here unless more specific
}

###############################################################################
# CLI entrypoint
###############################################################################
case "$1" in
"build") build_docker ;;
"start") start_app ;;
"stop") stop_app ;;
"restart") stop_app && start_app ;;
"up") up_command ;; # New command
"rebuild") rebuild_app ;;
"rebuild-nocache") rebuild_nocache ;;
"status") status ;;
"logs") logs ;;
*) # Default / Invalid command
    echo -e "${RED}Usage:${NC} $0 ${YELLOW}{build|start|stop|restart|up|rebuild|rebuild-nocache|status|logs}${NC}"
    exit 1
    ;;
esac
