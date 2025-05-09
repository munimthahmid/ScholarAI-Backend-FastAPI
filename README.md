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

3.  **Run the application:**
    This command starts the FastAPI development server using Uvicorn. The `--reload` flag enables auto-reloading on code changes.

    ```bash
    poetry run uvicorn app.main:app --reload --port 8000
    ```

    You should see output indicating the server is running, typically on `http://127.0.0.1:8000`.

## Project Structure

For details on the project structure, please refer to `docs/3_Code_Structure.md`.
