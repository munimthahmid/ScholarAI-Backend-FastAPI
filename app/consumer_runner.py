#!/usr/bin/env python3
"""
RabbitMQ Consumer Runner for ScholarAI

This script runs the RabbitMQ consumer to process messages from Spring Boot.
It simulates the AI processing pipeline with artificial delays.

Usage:
    python consumer_runner.py

Environment Variables:
    RABBITMQ_HOST: RabbitMQ host (default: localhost)
    RABBITMQ_PORT: RabbitMQ port (default: 5672)
    RABBITMQ_USER: RabbitMQ username (default: scholar)
    RABBITMQ_PASSWORD: RabbitMQ password (default: scholar123)
"""

import asyncio
import signal
import sys
from services.rabbitmq_consumer import consumer


async def main():
    """Main function to run the consumer"""
    print("🚀 Starting ScholarAI FastAPI RabbitMQ Consumer...")
    print("=" * 60)

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Received shutdown signal. Closing consumer...")
        asyncio.create_task(consumer.close())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start consuming messages
        await consumer.start_consuming()
    except KeyboardInterrupt:
        print("\n🛑 Consumer stopped by user")
    except Exception as e:
        print(f"❌ Consumer error: {e}")
    finally:
        await consumer.close()


if __name__ == "__main__":
    asyncio.run(main())
