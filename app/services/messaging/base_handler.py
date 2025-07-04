"""
Base message handler class
"""

import json
import logging
from typing import Dict, Any, Protocol
from abc import ABC, abstractmethod
from aio_pika import IncomingMessage

logger = logging.getLogger(__name__)


class MessageHandler(Protocol):
    """Protocol for message handlers"""

    async def handle(self, message: IncomingMessage) -> Dict[str, Any]:
        """Handle an incoming message and return result"""
        ...


class BaseMessageHandler(ABC):
    """
    Base class for message handlers with common functionality
    """

    def __init__(self):
        self.handler_name = self.__class__.__name__

    async def handle(self, message: IncomingMessage) -> Dict[str, Any]:
        """
        Handle an incoming message with error handling and logging.

        Args:
            message: Incoming RabbitMQ message

        Returns:
            Dictionary with processing result
        """
        try:
            # Parse message body
            body = self._parse_message_body(message)
            # Use correlationId for extraction messages, projectId for websearch messages
            request_id = body.get("correlationId") or body.get("projectId", "unknown")
            logger.info(f"📥 Processing {self.handler_name} request: {request_id}")

            # Process the message
            result = await self._process_message(body)

            logger.info(f"✅ {self.handler_name} completed: {request_id}")
            return result

        except Exception as e:
            logger.error(f"❌ {self.handler_name} error: {str(e)}")
            # Return error result
            return {"status": "ERROR", "error": str(e), "handler": self.handler_name}

    def _parse_message_body(self, message: IncomingMessage) -> Dict[str, Any]:
        """
        Parse message body from JSON.

        Args:
            message: Incoming message

        Returns:
            Parsed message body

        Raises:
            ValueError: If message body is invalid JSON
        """
        try:
            body = json.loads(message.body.decode())
            return body
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in message body: {e}")

    @abstractmethod
    async def _process_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the parsed message body.

        Args:
            body: Parsed message body

        Returns:
            Processing result
        """
        pass