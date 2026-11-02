from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, field_validator


class CallResponse(BaseModel):
    call_id: str
    campaign_id: str
    phone: str
    status: str
    created_at: AwareDatetime

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)
