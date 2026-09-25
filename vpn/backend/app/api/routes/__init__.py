from fastapi import APIRouter

from app.api.routes import keys, payments, downloads

api_router = APIRouter()

api_router.include_router(keys.router)
api_router.include_router(payments.router)
api_router.include_router(downloads.router)