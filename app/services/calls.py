from pymongo.asynchronous.database import AsyncDatabase

from app.repositories.calls import save_call
from app.repositories.campaigns import ensure_campaign
from app.schemas.events import CallEvent


async def handle_call(database: AsyncDatabase, event: CallEvent) -> None:
    await ensure_campaign(database, event.campaign_id)
    await save_call(database, event)
