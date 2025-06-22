# ScholarAI Backend

Backend for the ScholarAI research assistant. This project uses FastAPI and Poetry.

## Prerequisites

- Python (version 3.10 or higher recommended, as per `pyproject.toml`)
- Poetry (Python dependency manager)

## Getting Started

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd ScholarAI-Backend-FastAPI
    ```

2.  **Install dependencies:**
    Poetry will create a virtual environment and install all necessary packages.

    ```bash
    poetry install
    ```

3.  **Environment Configuration:**
    Copy the example environment file and configure it:

    ```bash
    cp env.example .env
    ```

    The `.env` file should include (at minimum):
    ```bash
    UNPAYWALL_EMAIL=your.email@example.com
    ```

4.  **Run the application:**
    This command starts the FastAPI development server using Uvicorn. The `--reload` flag enables auto-reloading on code changes.

    ```bash
    poetry run uvicorn app.main:app --reload --port 8000
    ```

    You should see output indicating the server is running, typically on `http://127.0.0.1:8000`.

## Academic API Configuration

### Unpaywall
The Unpaywall API provides open-access status for academic papers. Set up:

```bash
# Add to your .env file
UNPAYWALL_EMAIL=your.email@example.com
```

**Features:**
- DOI-based paper lookup
- Open-access status detection
- PDF URL retrieval
- Full-text search capabilities
- Bulk DOI checking

**Test the client:**
```bash
poetry run python test_unpaywall.py
```

## Project Structure

For details on the project structure, please refer to `docs/3_Code_Structure.md`.
