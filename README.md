# ScholarAI Backend

Backend for the ScholarAI research assistant. This project uses FastAPI and Poetry.

## Prerequisites

- Python 3.10+ (as per `pyproject.toml`)
- Poetry (Python dependency manager)
- Docker & Docker Compose (for containerized setup)

## Quick Start

### Option 1: Local Development

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Run the application:**
   ```bash
   poetry run uvicorn app.main:app --reload --port 8000
   ```

   Server will be available at `http://localhost:8000`

### Option 2: Docker Setup

1. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

2. **Start with Docker:**
   ```bash
   # Ensure Docker network exists
   docker network create docker_scholar-network
   
   # Start the application
   ./scripts/docker.sh start
   ```

   Server will be available at `http://localhost:8000`

## Environment Configuration

Copy `env.example` to `.env` and configure:

```bash
# Required
UNPAYWALL_EMAIL=your.email@example.com

# Optional (for enhanced features)
CORE_API_KEY=your_core_api_key
RABBITMQ_USER=your_rabbitmq_user
RABBITMQ_PASSWORD=your_rabbitmq_password
B2_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET_NAME=your_b2_bucket_name
LOG_LEVEL=INFO
```

## Available Scripts

- `./scripts/docker.sh start` - Start the application with Docker
- `./scripts/docker.sh stop` - Stop the application
- `./scripts/docker.sh rebuild` - Rebuild and restart
- `./scripts/azure-setup.sh` - Set up Azure infrastructure

## Testing

```bash
# Test Unpaywall client
poetry run python test_unpaywall.py

# Run all tests
poetry run pytest
```

## Project Structure

For detailed project structure, see `docs/3_Code_Structure.md`.
