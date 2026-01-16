from fastapi import APIRouter 

from .endpoints.health import router as health_router
from .endpoints.search import router as search_router
from .endpoints.cluster import router as cluster_router
from .endpoints.chat import router as chat_router

router = APIRouter()
router.include_router(health_router)
router.include_router(search_router, prefix="/api")
router.include_router(cluster_router, prefix="/api")
router.include_router(chat_router, prefix="/api")
