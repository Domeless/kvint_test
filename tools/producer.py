import asyncio

import structlog
from aio_pika import DeliveryMode, Message

from app.config import RabbitMQSettings
from app.logging import configure_logging
from app.messaging.connection import connect_rabbitmq
from app.messaging.queue import declare_calls_queue
from app.schemas.events import CallEvent

logger = structlog.get_logger(__name__, component="producer")

SAMPLE_CALLS = [
    {
        "call_id": "call_0001",
        "campaign_id": "camp_001",
        "phone": "79001234561",
        "status": "success",
        "created_at": "2026-10-20T10:06:00Z",
    },
    {
        "call_id": "call_0002",
        "campaign_id": "camp_001",
        "phone": "79001234562",
        "status": "failed",
        "created_at": "2026-10-20T10:07:00Z",
    },
    {
        "call_id": "call_0003",
        "campaign_id": "camp_002",
        "phone": "79001234563",
        "status": "success",
        "created_at": "2026-10-20T10:08:00Z",
    },
    {
        "call_id": "call_0004",
        "campaign_id": "camp_002",
        "phone": "79001234564",
        "status": "failed",
        "created_at": "2026-10-20T10:09:00Z",
    },
]


async def publish_calls(settings: RabbitMQSettings) -> None:
    async with asyncio.timeout(settings.rabbitmq_connect_timeout_seconds):
        connection = await connect_rabbitmq(settings)
    async with connection, connection.channel(publisher_confirms=True, on_return_raises=True) as channel:
        queue = await declare_calls_queue(channel, settings)
        for payload in SAMPLE_CALLS:
            event = CallEvent.model_validate(payload)
            message = Message(
                body=event.model_dump_json().encode("utf-8"),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=event.call_id,
            )
            await channel.default_exchange.publish(
                message,
                routing_key=queue.name,
                mandatory=True,
                timeout=settings.rabbitmq_connect_timeout_seconds,
            )
            logger.info("call_published", call_id=event.call_id, campaign_id=event.campaign_id)


def main() -> None:
    configure_logging()
    asyncio.run(publish_calls(RabbitMQSettings()))


if __name__ == "__main__":
    main()
