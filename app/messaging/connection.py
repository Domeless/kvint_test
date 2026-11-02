from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection

from app.config import RabbitMQSettings


async def connect_rabbitmq(settings: RabbitMQSettings) -> AbstractRobustConnection:
    """Connect to RabbitMQ and fail promptly if the initial connection fails."""
    return await connect_robust(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        login=settings.rabbitmq_user,
        password=settings.rabbitmq_password.get_secret_value(),
        virtualhost=settings.rabbitmq_vhost,
        timeout=settings.rabbitmq_connect_timeout_seconds,
        fail_fast="1",
    )
