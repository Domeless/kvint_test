from typing import Any

from pymongo import AsyncMongoClient

from app.config import Settings


def create_mongo_client(settings: Settings) -> AsyncMongoClient[dict[str, Any]]:
    """Create a client with timezone-aware dates and default driver timeouts."""
    return AsyncMongoClient(
        host=settings.mongo_host,
        port=settings.mongo_port,
        username=settings.mongo_user,
        password=settings.mongo_password.get_secret_value(),
        authSource=settings.mongo_auth_source,
        tz_aware=True,
    )
