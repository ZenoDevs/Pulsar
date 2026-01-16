from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 

from .core.config import CORS_ALLOW_ORIGINS
from .api.router import api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Pulsar API",
        description="News narrative intelligence backend for Italian news sources.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app
