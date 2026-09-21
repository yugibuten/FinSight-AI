from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import FinSightResponse


class ResearchListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str | None
    turn_index: int | None
    question: str
    response_type: str | None
    status: str
    response_cache_hit: bool
    duration_ms: float | None
    error_code: str | None
    created_at: datetime
    completed_at: datetime | None


class ToolExecutionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tool_name: str
    arguments_json: dict[str, Any]
    success: bool
    cache_hit: bool
    duration_ms: float
    created_at: datetime


class ResearchDetail(ResearchListItem):
    result: FinSightResponse | None
    tool_executions: list[ToolExecutionItem]
