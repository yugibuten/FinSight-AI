from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.db.database import SessionLocal
from app.core.exceptions import CanvasRevisionConflictError
from app.db.models import (
    Canvas,
    CanvasOperationLog,
    Conversation,
    ResearchQuery,
    ResearchResult,
    ToolExecution,
)


def create_conversation(title: str = "New research") -> Conversation:
    conversation = Conversation(
        id=f"con_{uuid4().hex}",
        title=title.strip()[:160] or "New research",
    )
    with SessionLocal.begin() as session:
        session.add(conversation)
    return conversation


def get_conversation(conversation_id: str) -> Conversation | None:
    with SessionLocal() as session:
        statement = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.queries).selectinload(ResearchQuery.result))
        )
        conversation = session.scalar(statement)
        if conversation is not None:
            conversation.queries.sort(key=lambda item: item.turn_index or 0)
        return conversation


def list_conversations(limit: int, offset: int) -> list[Conversation]:
    with SessionLocal() as session:
        statement = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .options(selectinload(Conversation.queries))
        )
        return list(session.scalars(statement).all())


def delete_conversation(conversation_id: str) -> bool:
    with SessionLocal.begin() as session:
        result = session.execute(delete(Conversation).where(Conversation.id == conversation_id))
        return bool(result.rowcount)


def get_canvas(conversation_id: str) -> Canvas | None:
    with SessionLocal() as session:
        return session.scalar(select(Canvas).where(Canvas.conversation_id == conversation_id))


def save_canvas(
    conversation_id: str,
    response: dict[str, Any],
    command: str,
    operations: list[dict[str, Any]],
    *,
    expected_revision: int | None = None,
) -> dict[str, Any]:
    """Persist one atomic canvas revision and its audit operations."""
    now = datetime.now(timezone.utc)
    with SessionLocal.begin() as session:
        canvas = session.scalar(
            select(Canvas).where(Canvas.conversation_id == conversation_id).with_for_update()
        )
        if canvas is None:
            if expected_revision is not None:
                raise CanvasRevisionConflictError()
            canvas = Canvas(
                id=f"can_{uuid4().hex}",
                conversation_id=conversation_id,
                revision=1,
                response_json={},
            )
            session.add(canvas)
        else:
            if expected_revision is not None and canvas.revision != expected_revision:
                raise CanvasRevisionConflictError()
            canvas.revision += 1
            canvas.updated_at = now

        stored = {
            **response,
            "canvas_id": canvas.id,
            "canvas_revision": canvas.revision,
            "canvas_mode": "patch" if operations else "full",
            "canvas_operations": operations,
        }
        canvas.response_json = stored
        if operations:
            session.add(
                CanvasOperationLog(
                    canvas_id=canvas.id,
                    revision=canvas.revision,
                    command=command,
                    operations_json=operations,
                )
            )
        return stored


def conversation_context(conversation_id: str, limit: int = 6) -> list[dict[str, Any]]:
    conversation = get_conversation(conversation_id)
    if conversation is None:
        return []
    completed = [item for item in conversation.queries if item.status == "completed" and item.result]
    context: list[dict[str, Any]] = []
    for item in completed[-limit:]:
        response = item.result.response_json
        context.append(
            {
                "question": item.question,
                "title": str(response.get("title") or "")[:200],
                "summary": str(response.get("summary") or "")[:1_200],
                "companies": [
                    {"ticker": company.get("ticker"), "name": company.get("name")}
                    for company in response.get("companies", [])[:5]
                    if isinstance(company, dict)
                ],
                "tool_calls": [
                    {"name": call.get("name"), "arguments": call.get("arguments", {})}
                    for call in response.get("tool_calls", [])[:8]
                    if isinstance(call, dict)
                ],
            }
        )
    return context


def create_research(request_id: str, question: str, conversation_id: str | None = None) -> str:
    research_id = f"res_{uuid4().hex}"
    with SessionLocal.begin() as session:
        turn_index = None
        if conversation_id:
            turn_index = session.scalar(
                select(func.coalesce(func.max(ResearchQuery.turn_index), 0)).where(
                    ResearchQuery.conversation_id == conversation_id
                )
            ) + 1
        session.add(
            ResearchQuery(
                id=research_id,
                conversation_id=conversation_id,
                turn_index=turn_index,
                request_id=request_id,
                question=question,
                status="pending",
            )
        )
    return research_id


def complete_research(
    research_id: str,
    response: dict[str, Any],
    tool_executions: list[dict[str, Any]],
    duration_ms: float,
    *,
    response_cache_hit: bool,
) -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal.begin() as session:
        query = session.get(ResearchQuery, research_id)
        if query is None:
            return
        query.status = "completed"
        query.response_type = response.get("response_type")
        query.duration_ms = duration_ms
        query.response_cache_hit = response_cache_hit
        query.completed_at = now
        if query.conversation is not None:
            query.conversation.updated_at = now
        query.result = ResearchResult(response_json=response, generated_at=now)
        for execution in tool_executions:
            query.tool_executions.append(
                ToolExecution(
                    tool_name=execution["name"],
                    arguments_json=execution.get("arguments", {}),
                    success=execution.get("success", False),
                    cache_hit=execution.get("cache_hit", False),
                    duration_ms=execution.get("duration_ms", 0),
                )
            )


def fail_research(
    research_id: str,
    error_code: str,
    error_message: str,
    duration_ms: float,
) -> None:
    with SessionLocal.begin() as session:
        query = session.get(ResearchQuery, research_id)
        if query is None:
            return
        query.status = "failed"
        query.error_code = error_code
        query.error_message = error_message
        query.duration_ms = duration_ms
        query.completed_at = datetime.now(timezone.utc)


def list_research(limit: int, offset: int) -> list[ResearchQuery]:
    with SessionLocal() as session:
        statement = (
            select(ResearchQuery)
            .order_by(ResearchQuery.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.scalars(statement).all())


def get_research(research_id: str) -> ResearchQuery | None:
    with SessionLocal() as session:
        statement = (
            select(ResearchQuery)
            .where(ResearchQuery.id == research_id)
            .options(
                selectinload(ResearchQuery.result),
                selectinload(ResearchQuery.tool_executions),
            )
        )
        return session.scalar(statement)


def delete_research(research_id: str) -> bool:
    with SessionLocal.begin() as session:
        result = session.execute(delete(ResearchQuery).where(ResearchQuery.id == research_id))
        return bool(result.rowcount)
