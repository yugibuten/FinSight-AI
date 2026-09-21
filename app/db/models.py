from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    queries: Mapped[list["ResearchQuery"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    canvas: Mapped["Canvas | None"] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", uselist=False
    )


class Canvas(Base):
    __tablename__ = "canvases"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), unique=True, index=True
    )
    revision: Mapped[int] = mapped_column(Integer, default=1)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    conversation: Mapped[Conversation] = relationship(back_populates="canvas")
    operations: Mapped[list["CanvasOperationLog"]] = relationship(
        back_populates="canvas", cascade="all, delete-orphan"
    )


class CanvasOperationLog(Base):
    __tablename__ = "canvas_operations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    canvas_id: Mapped[str] = mapped_column(
        ForeignKey("canvases.id", ondelete="CASCADE"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    command: Mapped[str] = mapped_column(Text)
    operations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    canvas: Mapped[Canvas] = relationship(back_populates="operations")


class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    turn_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str] = mapped_column(String(80), index=True)
    question: Mapped[str] = mapped_column(Text)
    response_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    response_cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    result: Mapped["ResearchResult | None"] = relationship(
        back_populates="query", cascade="all, delete-orphan", uselist=False
    )
    conversation: Mapped["Conversation | None"] = relationship(back_populates="queries")
    tool_executions: Mapped[list["ToolExecution"]] = relationship(
        back_populates="query", cascade="all, delete-orphan"
    )


class ResearchResult(Base):
    __tablename__ = "research_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(
        ForeignKey("research_queries.id", ondelete="CASCADE"), unique=True, index=True
    )
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    query: Mapped[ResearchQuery] = relationship(back_populates="result")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(
        ForeignKey("research_queries.id", ondelete="CASCADE"), index=True
    )
    tool_name: Mapped[str] = mapped_column(String(80), index=True)
    arguments_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    success: Mapped[bool] = mapped_column(Boolean)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    query: Mapped[ResearchQuery] = relationship(back_populates="tool_executions")
