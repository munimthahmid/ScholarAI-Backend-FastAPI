import asyncio
import json
import os
from typing import Dict, Any
import aio_pika
from aio_pika import Message, IncomingMessage
from app.services.summarization_agent import SummarizationAgent
from app.services.websearch_agent import WebSearchAgent


class RabbitMQConsumer:
    """RabbitMQ Consumer for ScholarAI agents"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.summarization_agent = SummarizationAgent()
        self.websearch_agent = WebSearchAgent()

        # RabbitMQ configuration
        self.rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.rabbitmq_user = os.getenv("RABBITMQ_USER", "scholar")
        self.rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "scholar123")

        # Queue names
        self.summarization_queue = "scholarai.summarization.queue"
        self.websearch_queue = "scholarai.websearch.queue"
        self.exchange_name = "scholarai.exchange"

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                login=self.rabbitmq_user,
                password=self.rabbitmq_password,
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            print(
                f"✅ Connected to RabbitMQ at {self.rabbitmq_host}:{self.rabbitmq_port}"
            )
        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            raise

    async def setup_queues(self):
        """Setup exchanges and queues"""
        try:
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )

            # Declare queues
            summarization_queue = await self.channel.declare_queue(
                self.summarization_queue, durable=True
            )
            websearch_queue = await self.channel.declare_queue(
                self.websearch_queue, durable=True
            )

            # Bind queues to exchange
            await summarization_queue.bind(exchange, "scholarai.summarization")
            await websearch_queue.bind(exchange, "scholarai.websearch")

            print("✅ RabbitMQ queues and bindings setup complete")
        except Exception as e:
            print(f"❌ Failed to setup queues: {e}")
            raise

    async def process_summarization_message(self, message: IncomingMessage):
        """Process summarization request"""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                print(f"📥 Received summarization request: {body}")

                # Process with summarization agent
                result = await self.summarization_agent.process_request(body)

                # Send result back
                await self.send_summarization_result(result)
                print(
                    f"✅ Successfully processed summarization for project {body.get('projectId')}"
                )

            except Exception as e:
                print(f"❌ Error processing summarization message: {e}")
                # Message will be rejected and potentially requeued

    async def process_websearch_message(self, message: IncomingMessage):
        """Process websearch request"""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                print(f"📥 Received web search request: {body}")

                # Process with websearch agent
                result = await self.websearch_agent.process_request(body)

                # Send result back
                await self.send_websearch_result(result)
                print(
                    f"✅ Successfully processed web search for project {body.get('projectId')}"
                )

            except Exception as e:
                print(f"❌ Error processing web search message: {e}")
                # Message will be rejected and potentially requeued

    async def send_summarization_result(self, result: Dict[str, Any]):
        """Send summarization result back to Spring Boot"""
        try:
            exchange = await self.channel.get_exchange(self.exchange_name)
            message = Message(
                json.dumps(result).encode(),
                content_type="application/json",
            )
            await exchange.publish(
                message, routing_key="scholarai.summarization.completed"
            )
            print(
                f"📤 Sent summarization completion event for project {result.get('projectId')}"
            )
        except Exception as e:
            print(f"❌ Failed to send summarization result: {e}")

    async def send_websearch_result(self, result: Dict[str, Any]):
        """Send websearch result back to Spring Boot"""
        try:
            exchange = await self.channel.get_exchange(self.exchange_name)
            message = Message(
                json.dumps(result).encode(),
                content_type="application/json",
            )
            await exchange.publish(message, routing_key="scholarai.websearch.completed")
            print(
                f"📤 Sent web search completion event for project {result.get('projectId')}"
            )
            print(f"📚 Sent {len(result.get('papers', []))} papers in the batch")
        except Exception as e:
            print(f"❌ Failed to send web search result: {e}")

    async def start_consuming(self):
        """Start consuming messages from both queues"""
        try:
            await self.connect()
            await self.setup_queues()

            # Get queues
            summarization_queue = await self.channel.get_queue(self.summarization_queue)
            websearch_queue = await self.channel.get_queue(self.websearch_queue)

            # Start consuming from both queues
            await summarization_queue.consume(self.process_summarization_message)
            await websearch_queue.consume(self.process_websearch_message)

            print("🔄 Started consuming from both summarization and websearch queues")
            print("📥 Waiting for messages...")

            # Keep the consumer running
            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("🛑 Consumer task cancelled")
        except Exception as e:
            print(f"❌ Consumer error: {e}")
            raise

    async def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                print("✅ RabbitMQ connection closed")
        except Exception as e:
            print(f"❌ Error closing RabbitMQ connection: {e}")


# Global consumer instance
consumer = RabbitMQConsumer()
