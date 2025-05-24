# Setup Instructions for ScholarAI Backend

This guide will walk you through setting up the ScholarAI Backend project on your local machine for development and testing.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Python**: This project requires Python. It's recommended to use a version compatible with the one specified in `pyproject.toml` (e.g., >=3.10, <4.0). You can download Python from [python.org](https://www.python.org/).
2.  **Poetry**: Poetry is used for dependency management and packaging. If you don't have Poetry installed, follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
3.  **Git**: You'll need Git to clone the repository. Download it from [git-scm.com](https://git-scm.com/).

## Installation Steps

1.  **Clone the Repository**:
    Open your terminal or command prompt and navigate to the directory where you want to store the project. Then, clone the repository using Git:

    ```bash
    git clone <your-repository-url> # Replace <your-repository-url> with the actual URL
    cd ScholarAI-Backend-FastAPI    # Navigate into the project directory
    ```

2.  **Install Dependencies**:
    This project uses Poetry to manage its dependencies. Poetry will also create and manage a virtual environment for the project to isolate its dependencies.
    Run the following command in the project's root directory (where `pyproject.toml` is located):

    ```bash
    poetry install
    ```

    This command will read the `pyproject.toml` file, resolve the dependencies listed in `poetry.lock` (or create it if it doesn't exist), and install them into a dedicated virtual environment.

3.  **Environment Variables**:
    The application might require environment variables for configuration (e.g., Firebase credentials, API keys, database URLs).

    - Create a `.env` file in the project root directory by copying the template from `.env.local` (if it exists) or by creating it from scratch.
    - Populate the `.env` file with the necessary configuration values.
      _Example `.env` structure (refer to `.env.local` or specific requirements):_

    ```env
    # Firebase
    FIREBASE_API_KEY="your_api_key"
    FIREBASE_AUTH_DOMAIN="your_auth_domain"
    # ... other Firebase credentials

    # Application settings
    ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
    ```

    **Note**: The `.env` file should be added to your `.gitignore` file to prevent committing sensitive credentials to version control.

## Running the Application

Once the dependencies are installed and environment variables are configured, you can run the FastAPI application using Uvicorn, a lightning-fast ASGI server.

To start the development server, execute the following command from the project's root directory:

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

Let's break down this command:

- `poetry run`: Executes the command within the Poetry-managed virtual environment.
- `uvicorn`: The ASGI server.
- `app.main:app`: Tells Uvicorn where to find the FastAPI application instance.
  - `app.main`: Refers to the `main.py` file inside the `app` directory.
  - `app`: Refers to the FastAPI instance created in `app/main.py` (e.g., `app = FastAPI()`).
- `--reload`: Enables auto-reload. The server will automatically restart when code changes are detected. This is very useful for development.
- `--port 8000`: Specifies the port on which the server will listen. You can change this if port 8000 is already in use.

After running the command, you should see output similar to this:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

You can now access the application by navigating to `http://127.0.0.1:8000` in your web browser.
API documentation (Swagger UI) is typically available at `http://127.0.0.1:8000/docs` and ReDoc at `http://127.0.0.1:8000/redoc`.

## Next Steps

- Familiarize yourself with the API endpoints by visiting the `/docs` URL.
- Explore the codebase, starting with `app/main.py` and the routers in `app/api/`.
- Refer to `docs/3_Code_Structure.md` for an overview of how the project is organized.
