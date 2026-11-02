from fastapi import FastAPI

from app.api.middleware import RequestLoggingMiddleware
from app.api.routes import router
from app.lifespan import lifespan

app = FastAPI(title="KVINT test", lifespan=lifespan)
app.include_router(router)
app.add_middleware(RequestLoggingMiddleware)
