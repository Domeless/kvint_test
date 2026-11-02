import asyncio

import structlog
from aio_pika.abc import AbstractIncomingMessage, AbstractQueueIterator, AbstractRobustChannel
from aio_pika.exceptions import AMQPConnectionError, ChannelInvalidStateError
from pydantic import ValidationError
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import ConnectionFailure, PyMongoError

from app.config import Settings
from app.schemas.events import CallEvent
from app.services.calls import handle_call

TRANSPORT_ERRORS = (AMQPConnectionError, ChannelInvalidStateError, ConnectionError, TimeoutError)
logger = structlog.get_logger(__name__, component="consumer")


async def validate_message(message: AbstractIncomingMessage) -> CallEvent | None:
    """Reject malformed events without exposing their contents in logs."""
    try:
        return CallEvent.model_validate_json(message.body)
    except ValidationError as error:
        logger.warning(
            "message_invalid",
            errors=[
                {"field": item["loc"], "type": item["type"]}
                for item in error.errors(include_input=False, include_context=False, include_url=False)
            ],
        )
        structlog.contextvars.bind_contextvars(operation="reject")
        await message.reject(requeue=False)
        return None


async def save_or_requeue(
    event: CallEvent, message: AbstractIncomingMessage, database: AsyncDatabase, settings: Settings
) -> bool:
    """Try saving once and return temporary failures to RabbitMQ after a delay."""
    # An IncomingMessage belongs to its original channel, even after reconnect.
    if message.channel.is_closed:
        raise ChannelInvalidStateError("Delivery channel is closed")
    try:
        await handle_call(database, event)
    except PyMongoError as error:
        if not (isinstance(error, ConnectionFailure) or error.timeout or error.has_error_label("RetryableWriteError")):
            raise
        logger.warning(
            "call_processing_deferred",
            error_type=type(error).__name__,
            retry_delay_seconds=settings.consumer_retry_delay_seconds,
        )
        await asyncio.sleep(settings.consumer_retry_delay_seconds)
        structlog.contextvars.bind_contextvars(operation="nack")
        await message.nack(requeue=True)
        logger.info("call_requeued")
        return False
    return True


async def process_message(message: AbstractIncomingMessage, database: AsyncDatabase, settings: Settings) -> None:
    """Validate, save and acknowledge one delivery with isolated log context."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(redelivered=message.redelivered)
    try:
        event = await validate_message(message)
        if event is None:
            return
        structlog.contextvars.bind_contextvars(call_id=event.call_id, campaign_id=event.campaign_id)
        if not await save_or_requeue(event, message, database, settings):
            return
        structlog.contextvars.bind_contextvars(operation="ack")
        await message.ack()
        logger.info("call_processed")
    except TRANSPORT_ERRORS:
        logger.exception("delivery_interrupted", include_error_message=False)
        raise
    except Exception:
        logger.exception("message_processing_failed", include_error_message=False)
        raise
    finally:
        structlog.contextvars.clear_contextvars()


async def consume_calls(
    channel: AbstractRobustChannel,
    iterator: AbstractQueueIterator,
    database: AsyncDatabase,
    settings: Settings,
) -> None:
    """Consume sequentially and release unacknowledged deliveries on failure."""
    async with channel, iterator:
        async for message in iterator:
            await process_message(message, database, settings)


def on_consumer_done(task: asyncio.Task[None]) -> None:
    """Retrieve background failures so a stopped consumer remains observable."""
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        logger.error("consumer_stopped", error_type=type(error).__name__)


async def stop_consumer(task: asyncio.Task[None], iterator: AbstractQueueIterator, timeout_seconds: float) -> None:
    """Stop deliveries and give the current operation a bounded grace period."""
    try:
        if not task.done():
            async with asyncio.timeout(timeout_seconds):
                await iterator.close()
                await asyncio.shield(asyncio.gather(task, return_exceptions=True))
    except TimeoutError:
        logger.warning("consumer_shutdown_timeout")
    except TRANSPORT_ERRORS:
        pass
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
