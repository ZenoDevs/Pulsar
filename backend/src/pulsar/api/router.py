
from fastapi import APIRouter 
from .v1.router import router as v1_router 

api_router = APIRouter()

# Version 1 API routes
api_router.include_router(v1_router)
