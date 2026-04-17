from fastapi import FastAPI

app = FastAPI(
    title="NYC311 Data Pipeline API",
    description="Backend API for NYC 311 Service Requests",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {"status": "healthy"}
