# app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.analyse import router as analyse_router
from api.routers.find_pairs import router as find_pairs_router
from api.routers.ner import router as ner_router
from api.routers.relations import router as relations_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyse_router)
app.include_router(find_pairs_router)
app.include_router(ner_router)
app.include_router(relations_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
def health():
    """
    Endpoint for health check
    """
    return {"status": "ok", "version": "1.0.0", "timestamp": "2024-01-01T00:00:00Z"}
