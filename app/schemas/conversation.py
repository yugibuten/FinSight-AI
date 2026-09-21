from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import FinSightResponse


class ConversationCreate(BaseModel):
    title: str = Field(default="New research", min_length=1, max_length=160)


class ConversationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    turn_count: int = 0


class ConversationTurn(BaseModel):
    research_id: str
    turn_index: int
    question: str
    status: str
    result: FinSightResponse | None = None


class ConversationDetail(ConversationListItem):
    turns: list[ConversationTurn]
