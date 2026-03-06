# app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.analyse import router as analyse_router
from api.routers.find_pairs import router as find_pairs_router
from api.routers.ner import router as ner_router
from api.routers.relations import router as relations_router
from api.services.transformers import (
    DEFAULT_NER_MODEL,
    is_ner_model_loaded,
    load_ner_model,
)

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


@app.on_event("startup")
def preload_models() -> None:
    load_ner_model(DEFAULT_NER_MODEL)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health/")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z",
        "models": {
            "ner": {
                "name": DEFAULT_NER_MODEL,
                "loaded": is_ner_model_loaded(DEFAULT_NER_MODEL),
            }
        },
    }
