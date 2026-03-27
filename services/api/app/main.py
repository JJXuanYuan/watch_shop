from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.media import ensure_media_directories

settings = get_settings()
ensure_media_directories(settings)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    settings.normalized_media_url_prefix,
    StaticFiles(directory=str(settings.resolved_media_root)),
    name="media",
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
