"""
RabbitMQ connection management
"""
import logging
from typing import Optional
import aio_pika
from aio_pika import Connection, Channel, Exchange, Queue

from ..websearch import RabbitMQConfig

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """
    Manages RabbitMQ connection, exchanges, and queues.
    
    Provides a clean interface for connection management with automatic
    reconnection and proper resource cleanup.
    """
    
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None
        self.websearch_queue: Optional[Queue] = None
    
    async def connect(self) -> bool:
        """
        Establish connection to RabbitMQ.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.config.host,
                port=self.config.port,
                login=self.config.username,
                password=self.config.password,
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.config.prefetch_count)
            
            logger.info(f"🔗 Connected to RabbitMQ ({self.config.host}:{self.config.port})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            return False
    
    async def setup_queues(self) -> bool:
        """
        Setup exchanges and queues.
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            if not self.channel:
                raise RuntimeError("Channel not available. Call connect() first.")
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.config.exchange_name, 
                aio_pika.ExchangeType.TOPIC, 
                durable=self.config.durable_queues
            )
            
            # Declare websearch queue
            self.websearch_queue = await self.channel.declare_queue(
                self.config.websearch_queue, 
                durable=self.config.durable_queues
            )
            
            # Bind queue to exchange
            await self.websearch_queue.bind(
                self.exchange, 
                self.config.routing_key_request
            )
            
            logger.info("📋 RabbitMQ queues configured")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup queues: {e}")
            return False
    
    async def publish_message(
        self, 
        message_body: bytes, 
        routing_key: str, 
        content_type: str = "application/json"
    ) -> bool:
        """
        Publish a message to the exchange.
        
        Args:
            message_body: Message content as bytes
            routing_key: Routing key for message
            content_type: Content type of the message
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            if not self.exchange:
                raise RuntimeError("Exchange not available. Call setup_queues() first.")
            
            message = aio_pika.Message(
                message_body,
                content_type=content_type,
            )
            
            await self.exchange.publish(message, routing_key=routing_key)
            logger.debug(f"📤 Published message to {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish message: {e}")
            return False
    
    def get_websearch_queue(self) -> Optional[Queue]:
        """Get the websearch queue for consuming"""
        return self.websearch_queue
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        return (
            self.connection is not None 
            and not self.connection.is_closed
            and self.channel is not None
        )
    
    async def close(self):
        """Close RabbitMQ connection and clean up resources"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("✅ RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing RabbitMQ connection: {e}")
        finally:
            self.connection = None
            self.channel = None
            self.exchange = None
            self.websearch_queue = None 