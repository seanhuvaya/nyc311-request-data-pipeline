from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import settings
from routers.agency import router as agency_router
from routers.backlog import router as backlog_router
from routers.borough import router as borough_router
from routers.complaints import router as complaints_router
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
app.include_router(router=borough_router, prefix="/api/v1")
app.include_router(router=complaints_router, prefix="/api/v1")
app.include_router(router=agency_router, prefix="/api/v1")
app.include_router(router=backlog_router, prefix="/api/v1")
