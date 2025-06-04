"""
Message handlers for different types of messages
"""
import json
import logging
from typing import Dict, Any, Protocol
from abc import ABC, abstractmethod
from aio_pika import IncomingMessage

from ..websearch_agent import WebSearchAgent

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
            project_id = body.get('projectId', 'unknown')
            logger.info(f"📥 Processing {self.handler_name} request: {project_id}")
            
            # Process the message
            result = await self._process_message(body)
            
            logger.info(f"✅ {self.handler_name} completed: {project_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ {self.handler_name} error: {str(e)}")
            # Return error result
            return {
                "status": "ERROR",
                "error": str(e),
                "handler": self.handler_name
            }
    
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


class WebSearchMessageHandler(BaseMessageHandler):
    """
    Handler for websearch request messages.
    
    Processes academic paper search requests using the WebSearchAgent.
    """
    
    def __init__(self, websearch_agent: WebSearchAgent = None):
        super().__init__()
        self.websearch_agent = websearch_agent or WebSearchAgent()
    
    async def _process_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process websearch request message.
        
        Args:
            body: Request body containing search parameters
            
        Returns:
            Search results with papers and metadata
        """
        # Validate required fields
        self._validate_websearch_request(body)
        
        # Process the search request
        result = await self.websearch_agent.process_request(body)
        
        # Add handler metadata
        result["handler"] = self.handler_name
        result["processing_time"] = self._get_processing_time()
        
        return result
    
    def _validate_websearch_request(self, body: Dict[str, Any]):
        """
        Validate websearch request body.
        
        Args:
            body: Request body to validate
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ["projectId", "queryTerms"]
        
        for field in required_fields:
            if field not in body:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate queryTerms is a list
        if not isinstance(body["queryTerms"], list) or not body["queryTerms"]:
            raise ValueError("queryTerms must be a non-empty list")
        
        # Validate optional fields
        if "batchSize" in body:
            batch_size = body["batchSize"]
            if not isinstance(batch_size, int) or batch_size <= 0:
                raise ValueError("batchSize must be a positive integer")
    
    def _get_processing_time(self) -> str:
        """Get current timestamp for processing time tracking"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def close(self):
        """Clean up handler resources"""
        if self.websearch_agent:
            await self.websearch_agent.close()


class MessageHandlerFactory:
    """
    Factory for creating message handlers based on message type or routing key.
    """
    
    def __init__(self):
        self._handlers = {}
        self._default_handler = None
    
    def register_handler(self, message_type: str, handler: MessageHandler):
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message or routing key
            handler: Handler instance
        """
        self._handlers[message_type] = handler
        logger.info(f"📝 Registered handler {handler.__class__.__name__} for '{message_type}'")
    
    def set_default_handler(self, handler: MessageHandler):
        """Set default handler for unrecognized message types"""
        self._default_handler = handler
        logger.info(f"📝 Set default handler: {handler.__class__.__name__}")
    
    def get_handler(self, message_type: str) -> MessageHandler:
        """
        Get handler for a message type.
        
        Args:
            message_type: Type of message
            
        Returns:
            Appropriate handler instance
            
        Raises:
            ValueError: If no handler found for message type
        """
        handler = self._handlers.get(message_type, self._default_handler)
        
        if not handler:
            raise ValueError(f"No handler registered for message type: {message_type}")
        
        return handler
    
    def get_registered_types(self) -> list:
        """Get list of registered message types"""
        return list(self._handlers.keys())
    
    async def close_all_handlers(self):
        """Close all registered handlers"""
        for handler in self._handlers.values():
            if hasattr(handler, 'close'):
                await handler.close()
        
        if self._default_handler and hasattr(self._default_handler, 'close'):
            await self._default_handler.close() 