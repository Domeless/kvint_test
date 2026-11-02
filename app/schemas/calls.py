from pydantic import BaseModel

from app.schemas.types import UtcDatetime


class CallResponse(BaseModel):
    call_id: str
    campaign_id: str
    phone: str
    status: str
    created_at: UtcDatetime
