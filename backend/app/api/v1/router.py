from fastapi import APIRouter

from app.api.v1.endpoints import integrations, uploads

api_router = APIRouter()

api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])

