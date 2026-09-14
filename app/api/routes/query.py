import asyncio
import time

from fastapi import APIRouter, Request

from app.core.cache import cache_key, response_cache
from app.core.config import settings
from app.core.exceptions import AppError, ProviderUnavailableError, QueryTimeoutError
from app.db import repository
from app.models import FinSightResponse
from app.orchestrator import answer_question
from app.schemas.error import ErrorResponse
from app.schemas.query import QueryRequest


router = APIRouter(prefix="/query", tags=["Financial intelligence"])


@router.post(
    "",
    response_model=FinSightResponse,
    summary="Ask FinSight",
    responses={
        413: {"model": ErrorResponse, "description": "Request body too large"},
        422: {"model": ErrorResponse, "description": "Invalid request"},
        429: {"model": ErrorResponse, "description": "Rate limit reached"},
        502: {"model": ErrorResponse, "description": "Provider unavailable"},
        503: {"model": ErrorResponse, "description": "Service not configured"},
        504: {"model": ErrorResponse, "description": "Query timed out"},
    },
)
async def query(payload: QueryRequest, request: Request) -> FinSightResponse:
    started = time.perf_counter()
    research_id = repository.create_research(request.state.request_id, payload.question)
    normalized_question = " ".join(payload.question.casefold().split())
    key = cache_key("query", {"question": normalized_question})
    cache_hit, cached_result = response_cache.get(key)
    if cache_hit:
        result = {**cached_result, "research_id": research_id}
        duration_ms = round((time.perf_counter() - started) * 1_000, 2)
        repository.complete_research(
            research_id,
            result,
            [],
            duration_ms,
            response_cache_hit=True,
        )
        return FinSightResponse(**result)

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(answer_question, payload.question),
            timeout=settings.query_timeout_seconds,
        )
    except TimeoutError as exc:
        repository.fail_research(
            research_id,
            "QUERY_TIMEOUT",
            "The query exceeded its time limit.",
            round((time.perf_counter() - started) * 1_000, 2),
        )
        raise QueryTimeoutError() from exc
    except AppError as exc:
        repository.fail_research(
            research_id,
            exc.code,
            exc.message,
            round((time.perf_counter() - started) * 1_000, 2),
        )
        raise
    except Exception as exc:
        repository.fail_research(
            research_id,
            "PROVIDER_UNAVAILABLE",
            "The provider failed unexpectedly.",
            round((time.perf_counter() - started) * 1_000, 2),
        )
        raise ProviderUnavailableError() from exc
    tool_executions = result.pop("_tool_executions", [])
    response_cache.set(key, result, settings.response_cache_seconds)
    result["research_id"] = research_id
    repository.complete_research(
        research_id,
        result,
        tool_executions,
        round((time.perf_counter() - started) * 1_000, 2),
        response_cache_hit=False,
    )
    return FinSightResponse(**result)
