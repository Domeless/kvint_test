from typing import Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings


def create_mongo_client(settings: Settings) -> AsyncMongoClient[dict[str, Any]]:
    """Create a client with timezone-aware dates and bounded operations."""
    return AsyncMongoClient(
        host=settings.mongo_host,
        port=settings.mongo_port,
        username=settings.mongo_user,
        password=settings.mongo_password.get_secret_value(),
        authSource=settings.mongo_auth_source,
        tz_aware=True,
        timeoutMS=int(settings.mongo_operation_timeout_seconds * 1000),
    )


async def create_indexes(database: AsyncDatabase) -> None:
    """Enforce event identity before accepting messages."""
    await database.campaigns.create_index("campaign_id", unique=True)
    await database.calls.create_index("call_id", unique=True)
    await database.calls.create_index("campaign_id")
