import asyncio
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

import structlog
from fastapi import FastAPI

from app.config import Settings
from app.database import create_mongo_client
from app.logging import configure_logging
from app.messaging.connection import connect_rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Initialize dependencies before serving requests and release them in reverse order."""
    configure_logging()
    logger = structlog.get_logger().bind(component="app")
    logger.info("application_starting")

    try:
        async with AsyncExitStack() as resources:
            try:
                settings = Settings()
                mongo_client = create_mongo_client(settings)
                resources.push_async_callback(mongo_client.close)
                async with asyncio.timeout(settings.mongo_connect_timeout_seconds):
                    await mongo_client.admin.command("ping")
                logger.info("dependency_connected", dependency="mongo")

                async with asyncio.timeout(settings.rabbitmq_connect_timeout_seconds):
                    rabbitmq_connection = await connect_rabbitmq(settings)
                    resources.push_async_callback(rabbitmq_connection.close)
                    rabbitmq_channel = await rabbitmq_connection.channel()
                    resources.push_async_callback(rabbitmq_channel.close)
                logger.info("dependency_connected", dependency="rabbitmq")
            except Exception:
                logger.exception("application_startup_failed")
                raise

            # обычно использую синглтон, а не пробрасываю так
            app.state.settings = settings
            app.state.mongo_client = mongo_client
            app.state.database = mongo_client[settings.mongo_database]
            app.state.rabbitmq_connection = rabbitmq_connection
            app.state.rabbitmq_channel = rabbitmq_channel

            logger.info("application_started")
            try:
                yield
            finally:
                logger.info("application_stopping")
        logger.info("application_resources_released")
    finally:
        logger.info("application_lifespan_finished")
