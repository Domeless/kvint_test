from aio_pika.abc import AbstractChannel, AbstractQueue

from app.config import RabbitMQSettings


async def declare_calls_queue(channel: AbstractChannel, settings: RabbitMQSettings) -> AbstractQueue:
    return await channel.declare_queue(settings.rabbitmq_queue, durable=True)
