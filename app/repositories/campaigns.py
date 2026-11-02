from datetime import UTC, datetime

from pymongo.asynchronous.database import AsyncDatabase


async def ensure_campaign(database: AsyncDatabase, campaign_id: str) -> None:
    """Create campaign metadata without overwriting manual changes."""
    await database.campaigns.update_one(
        {"campaign_id": campaign_id},
        {
            "$setOnInsert": {
                "campaign_id": campaign_id,
                "name": f"Кампания {campaign_id}",
                "created_at": datetime.now(UTC),
            }
        },
        upsert=True,
    )


async def campaign_exists(database: AsyncDatabase, campaign_id: str) -> bool:
    return await database.campaigns.find_one({"campaign_id": campaign_id}, {"_id": 1}) is not None
