from fastapi import FastAPI

from routers.overview import router as overview_router

app = FastAPI(
    title="NYC311 Data Pipeline API",
    description="Backend API for NYC 311 Service Requests",
    version="1.0.0"
)

app.include_router(router=overview_router, prefix="/api/v1")
