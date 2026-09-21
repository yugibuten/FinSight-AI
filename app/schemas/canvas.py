from datetime import datetime

from pydantic import BaseModel

from app.models import FinSightResponse


class CanvasDetail(BaseModel):
    id: str
    conversation_id: str
    revision: int
    response: FinSightResponse
    created_at: datetime
    updated_at: datetime
