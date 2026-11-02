import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from app.repositories.calls import get_campaign_calls
from app.repositories.campaigns import campaign_exists
from app.schemas.calls import CallResponse

router = APIRouter()
logger = structlog.get_logger(__name__, component="api")


@router.get("/health", tags=["health"], responses={503: {"description": "Consumer stopped"}})
async def health(request: Request) -> JSONResponse:
    if request.app.state.consumer_task.done():
        return JSONResponse(status_code=503, content={"status": "error", "detail": "Consumer stopped"})
    return JSONResponse(content={"status": "ok"})


@router.get(
    "/campaigns/{campaign_id}/calls",
    response_model=list[CallResponse],
    tags=["calls"],
    responses={
        404: {
            "description": "Campaign not found",
            "content": {"application/json": {"example": {"detail": "Кампания не найдена"}}},
        },
        503: {"description": "Database unavailable"},
    },
)
async def campaign_calls(campaign_id: str, request: Request) -> list[CallResponse]:
    database = request.app.state.database
    try:
        if not await campaign_exists(database, campaign_id):
            raise HTTPException(status_code=404, detail="Кампания не найдена")
        documents = await get_campaign_calls(database, campaign_id)
    except PyMongoError:
        logger.exception("database_request_failed", include_error_message=False)
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return [CallResponse.model_validate(document) for document in documents]
