from fastapi import FastAPI

from app.api.routes import router
from app.lifespan import lifespan

app = FastAPI(title="KVINT test", lifespan=lifespan)
app.include_router(router)
