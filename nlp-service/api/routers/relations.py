import json
import logging
from fastapi import APIRouter, HTTPException, Request
from api.models.model import RelationsDirectRequest
from api.middleware.rate_limiter import limiter
from api.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relations", tags=["relations"])


@router.post("/")
@limiter.limit("10/minute")
async def relations(request: Request, payload: RelationsDirectRequest):
    if not payload.name_1.strip() or not payload.name_2.strip():
        raise HTTPException(status_code=422, detail="Character names cannot be empty")

    if payload.name_1.strip() == payload.name_2.strip():
        raise HTTPException(status_code=422, detail="Character names must be different")

    pair = [payload.name_1, payload.name_2]

    relations_raw = await llm_service.extract_relations(pair, payload.sentences)

    try:
        relations_data = json.loads(relations_raw)
    except json.JSONDecodeError:
        relations_data = {"raw": relations_raw}

    logger.info("Relations for %s: %s", pair, relations_data)
    return {
        "pair": pair,
        "sentences_count": len(payload.sentences),
        "relations": relations_data,
    }
