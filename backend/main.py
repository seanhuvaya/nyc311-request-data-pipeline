from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from routers.overview import router as overview_router

app = FastAPI(
    title="NYC311 Data Pipeline API",
    description="Backend API for NYC 311 Service Requests",
    version="1.0.0"
)

origins = [
    "http://localhost:5173"
]  # Will change to read from environment variable

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=overview_router, prefix="/api/v1")
