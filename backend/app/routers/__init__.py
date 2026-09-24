from fastapi import APIRouter
from app.routers import dashboard, estimate, history, rooms, runs, settings
api = APIRouter(prefix="/api")
for r in (dashboard, rooms, estimate, history, runs, settings): api.include_router(r.router)
