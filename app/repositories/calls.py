from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.schemas.events import CallEvent


async def save_call(database: AsyncDatabase, event: CallEvent) -> None:
    """Persist the first result for a call identifier."""
    await database.calls.update_one(
        {"call_id": event.call_id},
        {"$setOnInsert": event.model_dump()},
        upsert=True,
    )


async def get_campaign_calls(database: AsyncDatabase, campaign_id: str) -> list[dict[str, Any]]:
    cursor = database.calls.find({"campaign_id": campaign_id}, {"_id": 0})
    return await cursor.sort([("created_at", 1), ("call_id", 1)]).to_list(length=None)
