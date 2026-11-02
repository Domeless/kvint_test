import asyncio
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

import structlog
from aio_pika.abc import AbstractQueueIterator
from fastapi import FastAPI

from app.config import Settings
from app.database import create_indexes, create_mongo_client
from app.logging import configure_logging
from app.messaging.connection import connect_rabbitmq
from app.messaging.consumer import consume_calls, on_consumer_done, stop_consumer
from app.messaging.queue import declare_calls_queue

logger = structlog.get_logger(__name__, component="app")


async def initialize_mongo(app: FastAPI, settings: Settings, resources: AsyncExitStack) -> None:
    """Connect to MongoDB and prepare indexes before accepting messages."""
    client = create_mongo_client(settings)
    resources.push_async_callback(client.close)
    async with asyncio.timeout(settings.mongo_connect_timeout_seconds):
        await client.admin.command("ping")
    database = client[settings.mongo_database]
    await create_indexes(database)
    app.state.mongo_client = client
    app.state.database = database
    logger.info("dependency_connected", dependency="mongo")


async def initialize_rabbitmq(
    app: FastAPI, settings: Settings, resources: AsyncExitStack
) -> AbstractQueueIterator:
    """Prepare a channel and register the consumer before reporting startup success."""
    async with asyncio.timeout(settings.rabbitmq_connect_timeout_seconds):
        connection = await connect_rabbitmq(settings)
        resources.push_async_callback(connection.close)
        channel = await connection.channel()
        resources.push_async_callback(channel.close)
        await channel.set_qos(prefetch_count=1)
        queue = await declare_calls_queue(channel, settings)
        iterator = queue.iterator()
        resources.push_async_callback(iterator.close)
        await iterator.consume()
    app.state.rabbitmq_connection = connection
    app.state.rabbitmq_channel = channel
    logger.info("dependency_connected", dependency="rabbitmq")
    return iterator


def start_consumer(
    app: FastAPI, iterator: AbstractQueueIterator, settings: Settings, resources: AsyncExitStack
) -> None:
    """Start message processing and register its graceful shutdown."""
    task = asyncio.create_task(
        consume_calls(app.state.rabbitmq_channel, iterator, app.state.database, settings), name="calls-consumer"
    )
    task.add_done_callback(on_consumer_done)
    resources.push_async_callback(stop_consumer, task, iterator, settings.consumer_shutdown_timeout_seconds)
    app.state.consumer_task = task


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Start dependencies and release them in reverse order on shutdown."""
    configure_logging()
    logger.info("application_starting")

    async with AsyncExitStack() as resources:
        try:
            settings = Settings()
            app.state.settings = settings
            await initialize_mongo(app, settings, resources)
            iterator = await initialize_rabbitmq(app, settings, resources)
            start_consumer(app, iterator, settings, resources)
        except Exception:
            logger.exception("application_startup_failed")
            raise

        logger.info("application_started")
        try:
            yield
        finally:
            logger.info("application_stopping")
    logger.info("application_resources_released")
