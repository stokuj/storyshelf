import json
import logging

from fastapi import APIRouter

from api.models.model import RelationsDirectRequest
from api.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relations", tags=["relations"])


@router.post("/")
async def relations(payload: RelationsDirectRequest):
    pair = [payload.name_1, payload.name_2]

    relations_raw = await llm_service.extract_relations(pair, payload.sentences)

    try:
        relations_data = json.loads(relations_raw)
    except (json.JSONDecodeError, TypeError):
        relations_data = {"raw": relations_raw}

    logger.info("Relations for %s: %s", pair, relations_data)
    return {
        "pair": pair,
        "sentences_count": len(payload.sentences),
        "relations": relations_data,
    }
