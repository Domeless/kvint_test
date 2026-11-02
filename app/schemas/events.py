from pydantic import BaseModel, ConfigDict, Field

from app.schemas.types import UtcDatetime


class CallEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    call_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    status: str = Field(min_length=1)
    created_at: UtcDatetime
