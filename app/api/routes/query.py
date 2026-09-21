import asyncio
import json
import re
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.canvas import apply_canvas_command, detect_canvas_command
from app.core.cache import cache_key, response_cache
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    CanvasRevisionConflictError,
    ConversationNotFoundError,
    ProviderUnavailableError,
    QueryTimeoutError,
)
from app.db import repository
from app.models import FinSightResponse
from app.orchestrator import (
    answer_question,
    reset_stream_event_sink,
    set_stream_event_sink,
)
from app.planner import build_query_plan
from app.schemas.error import ErrorResponse
from app.schemas.query import QueryRequest


router = APIRouter(prefix="/query", tags=["Financial intelligence"])

FOLLOW_UP_PATTERN = re.compile(
    r"^(and|then|now)\b|\b(it|its|they|them|their|that|those|these|same|also|instead|earlier|previous|"
    r"what about|how about|compare (?:it|that|them)|show (?:me )?the last)\b",
    re.IGNORECASE,
)


def _needs_conversation_context(question: str) -> bool:
    """Use history only when the new question linguistically depends on it."""
    return bool(FOLLOW_UP_PATTERN.search(question))


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
    if payload.conversation_id:
        conversation = repository.get_conversation(payload.conversation_id)
        if conversation is None:
            raise ConversationNotFoundError()
    else:
        conversation = repository.create_conversation(payload.question)
    conversation_id = conversation.id
    current_canvas = repository.get_canvas(conversation_id)
    if (
        payload.canvas_revision is not None
        and current_canvas is not None
        and payload.canvas_revision != current_canvas.revision
    ):
        raise CanvasRevisionConflictError()
    canvas_command = detect_canvas_command(payload.question, current_canvas is not None)
    context = (
        repository.conversation_context(conversation_id)
        if payload.conversation_id
        and (canvas_command is not None or _needs_conversation_context(payload.question))
        else []
    )
    query_plan = build_query_plan(
        payload.question,
        context,
        canvas_action=canvas_command.action if canvas_command else None,
        requested_blocks=canvas_command.targets if canvas_command else None,
    )
    research_id = repository.create_research(
        request.state.request_id, payload.question, conversation_id
    )
    normalized_question = " ".join(payload.question.casefold().split())
    key = cache_key("query", {"question": normalized_question, "context": context})
    cache_hit = False
    cached_result = None
    if not canvas_command or canvas_command.action != "remove":
        cache_hit, cached_result = response_cache.get(key)

    try:
        if canvas_command and canvas_command.action == "remove":
            generated_result = None
            tool_executions = []
        elif cache_hit:
            generated_result = cached_result
            tool_executions = []
        else:
            answer_args = (payload.question, context) if context else (payload.question,)
            generated_result = await asyncio.wait_for(
                asyncio.to_thread(answer_question, *answer_args),
                timeout=settings.query_timeout_seconds,
            )
            tool_executions = generated_result.pop("_tool_executions", [])
            response_cache.set(key, generated_result, settings.response_cache_seconds)

        if canvas_command and current_canvas is not None:
            result, operations = apply_canvas_command(
                current_canvas.response_json,
                generated_result,
                canvas_command.action,
                canvas_command.targets,
                canvas_command.entities,
            )
        else:
            result = generated_result
            operations = []
        if result is None:
            raise RuntimeError("Canvas command did not produce a result")

        result["research_id"] = research_id
        result["conversation_id"] = conversation_id
        result["query_plan"] = query_plan.model_dump()
        result = repository.save_canvas(
            conversation_id,
            result,
            payload.question,
            operations,
            expected_revision=payload.canvas_revision,
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
    repository.complete_research(
        research_id,
        result,
        tool_executions,
        round((time.perf_counter() - started) * 1_000, 2),
        response_cache_hit=cache_hit,
    )
    return FinSightResponse(**result)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream", summary="Ask FinSight with component streaming")
async def query_stream(payload: QueryRequest, request: Request) -> StreamingResponse:
    async def events():
        queue: asyncio.Queue[dict] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def publish(event: dict) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, event)

        async def run_query() -> FinSightResponse:
            token = set_stream_event_sink(publish)
            try:
                return await query(payload, request)
            finally:
                reset_stream_event_sink(token)

        task = asyncio.create_task(run_query())
        yield _sse("status", {"stage": "planning"})
        try:
            while not task.done() or not queue.empty():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.2)
                except TimeoutError:
                    continue
                yield _sse(event.pop("type", "status"), event)

            response = await task
            complete = response.model_dump(mode="json")
            blocks = list((complete.get("presentation") or {}).get("blocks", []))
            initial = dict(complete)
            initial["presentation"] = {
                **(complete.get("presentation") or {"layout": "explainer"}),
                "blocks": [],
            }
            yield _sse("response_start", {"response": initial})
            for block in blocks:
                yield _sse("component", {"block": block})
                await asyncio.sleep(0)
            yield _sse(
                "complete",
                {
                    "research_id": complete["research_id"],
                    "conversation_id": complete.get("conversation_id"),
                    "canvas_revision": complete.get("canvas_revision"),
                },
            )
        except AppError as exc:
            yield _sse(
                "error",
                {"code": exc.code, "message": exc.message, "retryable": exc.retryable},
            )
        except Exception:
            yield _sse(
                "error",
                {
                    "code": "STREAM_FAILED",
                    "message": "The streamed query could not be completed.",
                    "retryable": True,
                },
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
