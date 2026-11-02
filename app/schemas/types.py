from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime


def normalize_utc(value: datetime) -> datetime:
    """Normalize an aware datetime and reject values outside the UTC range."""
    try:
        return value.astimezone(UTC)
    except OverflowError as error:
        raise ValueError("Datetime is outside the supported UTC range") from error


UtcDatetime = Annotated[AwareDatetime, AfterValidator(normalize_utc)]
