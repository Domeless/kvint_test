import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pymongo.errors import ConnectionFailure

from app.config import Settings
from app.messaging.consumer import process_message
from app.schemas.events import CallEvent
from tools.producer import SAMPLE_CALLS


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, consumer_retry_delay_seconds=0.001)


def delivery(body: bytes | None = None) -> SimpleNamespace:
    event = CallEvent.model_validate(SAMPLE_CALLS[0])
    return SimpleNamespace(
        body=event.model_dump_json().encode() if body is None else body,
        redelivered=False,
        channel=SimpleNamespace(is_closed=False),
        ack=AsyncMock(),
        nack=AsyncMock(),
        reject=AsyncMock(),
    )


async def test_campaign_then_call_then_ack(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    steps = []

    async def ensure(database: object, campaign_id: str) -> None:
        steps.append("campaign")

    async def save(database: object, event: CallEvent) -> None:
        steps.append("call")

    async def ack() -> None:
        steps.append("ack")

    monkeypatch.setattr("app.services.calls.ensure_campaign", ensure)
    monkeypatch.setattr("app.services.calls.save_call", save)
    message = delivery()
    message.ack.side_effect = ack
    await process_message(message, None, settings)
    assert steps == ["campaign", "call", "ack"]


async def test_database_error_requeues_without_ack(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    message = delivery()
    handler = AsyncMock(side_effect=ConnectionFailure("unavailable"))
    monkeypatch.setattr("app.messaging.consumer.handle_call", handler)
    await process_message(message, None, settings)
    handler.assert_awaited_once()
    message.ack.assert_not_awaited()
    message.nack.assert_awaited_once_with(requeue=True)
    message.reject.assert_not_awaited()


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        json.dumps(SAMPLE_CALLS[0] | {"created_at": "0001-01-01T00:00:00+01:00"}).encode(),
        json.dumps(SAMPLE_CALLS[0] | {"created_at": "9999-12-31T23:59:59-01:00"}).encode(),
    ],
    ids=["invalid-json", "utc-underflow", "utc-overflow"],
)
async def test_invalid_message_does_not_block_next(
    monkeypatch: pytest.MonkeyPatch, settings: Settings, body: bytes
) -> None:
    handler = AsyncMock()
    monkeypatch.setattr("app.messaging.consumer.handle_call", handler)
    invalid, valid = delivery(body), delivery()
    await process_message(invalid, None, settings)
    await process_message(valid, None, settings)
    invalid.reject.assert_awaited_once_with(requeue=False)
    invalid.ack.assert_not_awaited()
    valid.ack.assert_awaited_once()
    handler.assert_awaited_once()
