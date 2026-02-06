from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from surr.app.api.main import router as api_router
from surr.app.core.config import settings

app = FastAPI()


app.add_middleware(
    CORSMiddleware,  # ty:ignore[invalid-argument-type]
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_METHODS,
)


app.include_router(api_router, prefix="/api")
