from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import settings
from routers.health import router as health_router
from routers.overview import router as overview_router

app = FastAPI(
    title="NYC311 Data Pipeline API",
    description="Backend API for NYC 311 Service Requests",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=health_router)
app.include_router(router=overview_router, prefix="/api/v1")
