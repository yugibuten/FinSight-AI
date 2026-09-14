from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db.database import SessionLocal
from app.db.models import ResearchQuery, ResearchResult, ToolExecution


def create_research(request_id: str, question: str) -> str:
    research_id = f"res_{uuid4().hex}"
    with SessionLocal.begin() as session:
        session.add(
            ResearchQuery(
                id=research_id,
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
