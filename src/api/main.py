from fastapi import FastAPI

from src.api.routers.requests import router as requests_router

app = FastAPI()

app.include_router(requests_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Hello World"}
