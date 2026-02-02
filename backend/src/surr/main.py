from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from surr.app.core.config import settings

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_METHODS,
)
