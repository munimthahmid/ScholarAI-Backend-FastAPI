"""
Main RabbitMQ consumer for ScholarAI
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aio_pika import IncomingMessage

from .connection import RabbitMQConnection
from .handlers import WebSearchMessageHandler, MessageHandlerFactory
from .handlers_dir.extraction_handler import ExtractionMessageHandler
from .handlers_dir.summarization_handler import SummarizationMessageHandler
from ..websearch import AppConfig

logger = logging.getLogger(__name__)


class ScholarAIConsumer:
    """
    Main RabbitMQ consumer for ScholarAI services.

    Orchestrates connection management, message routing, and result publishing
    with a clean, modular architecture.
    """

    def __init__(self, config: AppConfig = None):
        # Initialize configuration
        self.config = config or AppConfig.from_env()

        # Initialize connection manager
        self.connection_manager = RabbitMQConnection(self.config.rabbitmq)

        # Initialize message handler factory
        self.handler_factory = MessageHandlerFactory()
        self._setup_handlers()

        # State tracking
        self.is_running = False

    def _setup_handlers(self):
        """Setup message handlers for different message types"""
        # Register websearch handler
        websearch_handler = WebSearchMessageHandler()
        self.handler_factory.register_handler("websearch", websearch_handler)
        self.handler_factory.set_default_handler(websearch_handler)

        # Register extraction handler
        extraction_handler = ExtractionMessageHandler()
        self.handler_factory.register_handler("extraction", extraction_handler)

        # Register summarization handler
        summarization_handler = SummarizationMessageHandler()
        self.handler_factory.register_handler("summarization", summarization_handler)

        logger.info("📝 Message handlers ready")

    async def start(self):
        """
        Start the consumer and begin processing messages.
        """
        try:
            logger.info("🚀 Starting ScholarAI Consumer...")

            # Connect to RabbitMQ
            connected = await self.connection_manager.connect()
            if not connected:
                raise RuntimeError("Failed to connect to RabbitMQ")

            # Setup queues and exchanges
            setup_success = await self.connection_manager.setup_queues()
            if not setup_success:
                raise RuntimeError("Failed to setup RabbitMQ queues")

            # Start consuming messages
            await self._start_consuming()

        except Exception as e:
            logger.error(f"❌ Failed to start consumer: {e}")
            await self.stop()
            raise

    async def _start_consuming(self):
        """Start consuming messages from both websearch and extraction queues"""
        websearch_queue = self.connection_manager.get_websearch_queue()
        extraction_queue = self.connection_manager.get_extraction_queue()

        if not websearch_queue:
            raise RuntimeError("Websearch queue not available")
        if not extraction_queue:
            raise RuntimeError("Extraction queue not available")

        # Start consuming from both queues
        await websearch_queue.consume(self._process_message)
        await extraction_queue.consume(self._process_message)

        logger.info("📥 Ready to process messages from websearch and extraction queues")

        self.is_running = True

        # Keep the consumer running
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("🛑 Consumer task cancelled")
        finally:
            self.is_running = False

    async def _process_message(self, message: IncomingMessage):
        """
        Process an incoming message with automatic ack/nack.

        Args:
            message: Incoming RabbitMQ message
        """
        async with message.process():
            try:
                # Determine message type (could be from routing key or message properties)
                message_type = self._determine_message_type(message)

                # Get appropriate handler
                handler = self.handler_factory.get_handler(message_type)

                # Process the message
                result = await handler.handle(message)

                # Send result back if successful
                if result.get("status") != "ERROR":
                    await self._send_result(result)
                else:
                    logger.error(f"Message processing failed: {result.get('error')}")

            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                # Message will be nacked and potentially requeued

    def _determine_message_type(self, message: IncomingMessage) -> str:
        """
        Determine message type from message properties or content.

        Args:
            message: Incoming message

        Returns:
            Message type string
        """
        # Determine message type from routing key
        routing_key = message.routing_key or ""

        if "extraction" in routing_key:
            return "extraction"
        elif "websearch" in routing_key:
            return "websearch"
        else:
            # Default to websearch for backward compatibility
            return "websearch"

    async def _send_result(self, result: Dict[str, Any]):
        """
        Send processing result back to the exchange.

        Args:
            result: Processing result to send
        """
        try:
            # Serialize result
            result_json = json.dumps(result).encode()

            # Determine routing key based on result type
            routing_key = self._get_response_routing_key(result)

            # Publish to response routing key
            success = await self.connection_manager.publish_message(
                message_body=result_json, routing_key=routing_key
            )

            if success:
                # Log appropriately based on result type
                if "paperId" in result:  # Extraction result
                    logger.info(
                        f"📤 Sent extraction result: {result.get('paperId')} (status: {result.get('status')})"
                    )
                else:  # WebSearch result
                    project_id = result.get("projectId", "unknown")
                    paper_count = len(result.get("papers", []))
                    logger.info(
                        f"📤 Sent websearch results: {project_id} ({paper_count} papers)"
                    )
            else:
                logger.error("Failed to send result message")

        except Exception as e:
            logger.error(f"❌ Failed to send result: {e}")

    def _get_response_routing_key(self, result: Dict[str, Any]) -> str:
        """
        Determine the appropriate response routing key based on result type.

        Args:
            result: Processing result

        Returns:
            Appropriate routing key for the response
        """
        # Check if it's an extraction result
        if "paperId" in result and "extractedText" in result:
            return "scholarai.extraction.completed"
        else:
            # Default to websearch response routing key
            return self.config.rabbitmq.routing_key_response

    async def stop(self):
        """Stop the consumer and clean up resources"""
        logger.info("🛑 Stopping ScholarAI Consumer...")

        self.is_running = False

        # Close all handlers
        await self.handler_factory.close_all_handlers()

        # Close connection
        await self.connection_manager.close()

        logger.info("✅ Consumer stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get current consumer status"""
        return {
            "running": self.is_running,
            "connected": self.connection_manager.is_connected(),
            "registered_handlers": self.handler_factory.get_registered_types(),
            "config": {
                "rabbitmq_host": self.config.rabbitmq.host,
                "rabbitmq_port": self.config.rabbitmq.port,
                "websearch_queue": self.config.rabbitmq.websearch_queue,
                "exchange_name": self.config.rabbitmq.exchange_name,
            },
        }


# Legacy consumer class for backward compatibility
class RabbitMQConsumer(ScholarAIConsumer):
    """
    🔄 Backward compatibility alias for the old consumer class
    """

    def __init__(self):
        super().__init__()
        self.websearch_agent = self.handler_factory._handlers.get(
            "websearch"
        ).websearch_agent

    async def start_consuming(self):
        """Legacy method name for starting consumer"""
        await self.start()

    async def close(self):
        """Legacy method name for stopping consumer"""
        await self.stop()


# Global consumer instance for backward compatibility
consumer = ScholarAIConsumer()
