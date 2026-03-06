# app.py

from fastapi import FastAPI
from api.routers.direct import router as direct_router

app = FastAPI()
app.include_router(direct_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
def health():
    """
    Endpoint for health check
    """
    return {"status": "ok", "version": "1.0.0", "timestamp": "2024-01-01T00:00:00Z"}
