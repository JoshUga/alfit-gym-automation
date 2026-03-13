"""RabbitMQ messaging helpers."""

import json
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class MessagePublisher:
    """Publishes messages to RabbitMQ exchanges."""
    
    def __init__(self, connection_url: str = ""):
        self.connection_url = connection_url
        self._connection = None
        self._channel = None
    
    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            import aio_pika
            self._connection = await aio_pika.connect_robust(self.connection_url)
            self._channel = await self._connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.warning(f"Could not connect to RabbitMQ: {e}")
    
    async def publish(self, exchange: str, routing_key: str, message: dict):
        """Publish a message to an exchange."""
        if not self._channel:
            logger.warning("Not connected to RabbitMQ, skipping publish")
            return
        try:
            import aio_pika
            exchange_obj = await self._channel.declare_exchange(
                exchange, aio_pika.ExchangeType.TOPIC, durable=True
            )
            await exchange_obj.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    content_type="application/json",
                ),
                routing_key=routing_key,
            )
            logger.info(f"Published message to {exchange}/{routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
    
    async def close(self):
        """Close the connection."""
        if self._connection:
            await self._connection.close()


class MessageConsumer:
    """Consumes messages from RabbitMQ queues."""
    
    def __init__(self, connection_url: str = ""):
        self.connection_url = connection_url
        self._connection = None
        self._channel = None
    
    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            import aio_pika
            self._connection = await aio_pika.connect_robust(self.connection_url)
            self._channel = await self._connection.channel()
            logger.info("Connected to RabbitMQ for consuming")
        except Exception as e:
            logger.warning(f"Could not connect to RabbitMQ: {e}")
    
    async def consume(
        self, queue_name: str, exchange: str, routing_key: str, callback: Callable
    ):
        """Start consuming messages from a queue."""
        if not self._channel:
            logger.warning("Not connected to RabbitMQ, skipping consume")
            return
        try:
            import aio_pika
            exchange_obj = await self._channel.declare_exchange(
                exchange, aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await self._channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange_obj, routing_key)
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        data = json.loads(message.body.decode())
                        await callback(data)
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
    
    async def close(self):
        """Close the connection."""
        if self._connection:
            await self._connection.close()
