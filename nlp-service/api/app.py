# app.py
from datetime import UTC, datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.config.celery_app import celery  # noqa: F811
from api.routers.analyse import router as analyse_router
from api.routers.find_pairs import router as find_pairs_router
from api.routers.ner import router as ner_router
from api.routers.relations import router as relations_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

#####################################################
### Include Routers
#####################################################
app.include_router(analyse_router)
app.include_router(find_pairs_router)
app.include_router(ner_router)
app.include_router(relations_router)


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/health/")
def health():
    return {
        "status": "ok",
        "version": "0.6.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }
