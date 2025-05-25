#!/usr/bin/env python3
"""
FastAPI Server Startup Script

This script starts the FastAPI server with the integrated RabbitMQ consumer.
The consumer will automatically start consuming messages from both:
- scholarai.summarization.queue
- scholarai.websearch.queue

Usage:
    python start_server.py
    OR
    poetry run python start_server.py

Environment Variables:
    RABBITMQ_HOST: RabbitMQ host (default: localhost)
    RABBITMQ_PORT: RabbitMQ port (default: 5672)
    RABBITMQ_USER: RabbitMQ username (default: scholar)
    RABBITMQ_PASSWORD: RabbitMQ password (default: scholar123)
"""

import subprocess
import sys
import os


def main():
    """Start the FastAPI server with integrated consumer"""
    print("🚀 Starting ScholarAI FastAPI Server with Integrated RabbitMQ Consumer")
    print("=" * 70)
    print("📋 Server will be available at: http://localhost:8001")
    print("🔄 RabbitMQ consumer will start automatically")
    print("📥 Listening for both summarization and websearch requests")
    print("=" * 70)

    # Server configuration
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = os.getenv("FASTAPI_PORT", "8001")

    # Use poetry to run uvicorn to ensure correct virtual environment
    cmd = [
        "poetry",
        "run",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        port,
        "--reload",
        "--log-level",
        "info",
    ]

    print(f"🔧 Running command: {' '.join(cmd)}")
    print("=" * 70)

    try:
        # Run the command
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
