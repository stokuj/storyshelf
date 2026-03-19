from datetime import UTC, datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging

logger = logging.getLogger(__name__)

FIELD_MISSING_MESSAGES: dict[str, str] = {
    "content": "Content cannot be empty",
    "names": "Names cannot be empty",
}
from contextlib import asynccontextmanager

from api.config import settings
from api.config.celery_app import celery
from api.middleware.rate_limiter import limiter
from api.routers.analyse import router as analyse_router
from api.routers.find_pairs import router as find_pairs_router
from api.routers.ner import router as ner_router
from api.routers.relations import router as relations_router
from api.kafka.consumer import ChapterAnalysisConsumer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Kafka Consumer
    consumer_thread = ChapterAnalysisConsumer()
    consumer_thread.start()
    
    yield
    
    # Stop Kafka Consumer
    consumer_thread.stop()
    consumer_thread.join(timeout=5.0)

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception: %s %s — %s",
        request.method,
        request.url,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for error in exc.errors():
        if error.get("type") == "missing":
            field = error["loc"][-1]
            if field in FIELD_MISSING_MESSAGES:
                return JSONResponse(
                    status_code=422,
                    content={"detail": FIELD_MISSING_MESSAGES[field]},
                )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


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
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/health/celery/")
def health_celery():
    try:
        inspector = celery.control.inspect()
        active = inspector.active() or {}
        stats = inspector.stats() or {}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": str(exc)},
        )

    workers = {}
    total_processes = 0
    for name, tasks in active.items():
        worker_stats = stats.get(name, {})
        pool_stats = worker_stats.get("pool", {})
        max_concurrency = (
            pool_stats.get("max-concurrency")
            or pool_stats.get("max_concurrency")
            or worker_stats.get("max-concurrency")
        )
        if isinstance(max_concurrency, int):
            total_processes += max_concurrency

        workers[name] = {
            "status": "online",
            "active_tasks": len(tasks),
            "concurrency": max_concurrency,
        }
    return {
        "status": "ok",
        "total_workers": len(workers),
        "total_processes": total_processes,
        "workers": workers,
    }
