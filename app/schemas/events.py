from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class CallEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    call_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    status: str = Field(min_length=1)
    created_at: AwareDatetime

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)
