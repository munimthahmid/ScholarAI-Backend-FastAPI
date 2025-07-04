"""
Messaging module for ScholarAI

Handles all message queue operations including RabbitMQ connection management,
message processing, and result publishing.
"""

from .connection import RabbitMQConnection
from .handlers import WebSearchMessageHandler, MessageHandlerFactory
from .handlers_dir.extraction_handler import ExtractionMessageHandler
from .consumer import ScholarAIConsumer

__all__ = ["RabbitMQConnection", "WebSearchMessageHandler", "MessageHandlerFactory", "ExtractionMessageHandler", "ScholarAIConsumer"]
