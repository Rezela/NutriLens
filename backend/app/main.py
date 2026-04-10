from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import init_db
from app.routers.health import router as health_router
from app.routers.meals import router as meals_router
from app.routers.memories import router as memories_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(meals_router, prefix=settings.api_v1_prefix)
app.include_router(memories_router, prefix=settings.api_v1_prefix)
