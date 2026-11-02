from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI

from app.api.routes import router
from tools.producer import SAMPLE_CALLS


@pytest.fixture
def application() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.state.database = SimpleNamespace(
        campaigns=SimpleNamespace(find_one=AsyncMock(return_value={"_id": "exists"})),
        calls=SimpleNamespace(find=MagicMock()),
    )
    return app


async def test_campaign_calls(application: FastAPI) -> None:
    cursor = MagicMock()
    cursor.sort.return_value.to_list = AsyncMock(return_value=SAMPLE_CALLS[:2])
    application.state.database.calls.find.return_value = cursor
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test") as client:
        response = await client.get("/campaigns/camp_001/calls")
    assert response.status_code == 200
    assert [call["call_id"] for call in response.json()] == ["call_0001", "call_0002"]
    assert all(call["campaign_id"] == "camp_001" for call in response.json())
    application.state.database.calls.find.assert_called_once_with({"campaign_id": "camp_001"}, {"_id": 0})


async def test_missing_campaign_returns_404(application: FastAPI) -> None:
    application.state.database.campaigns.find_one.return_value = None
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://test") as client:
        response = await client.get("/campaigns/missing/calls")
    assert response.status_code == 404
    assert response.json() == {"detail": "Кампания не найдена"}
    application.state.database.calls.find.assert_not_called()
