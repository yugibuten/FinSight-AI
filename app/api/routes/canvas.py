from fastapi import APIRouter

from app.core.exceptions import CanvasNotFoundError
from app.db import repository
from app.schemas.canvas import CanvasDetail


router = APIRouter(prefix="/conversations", tags=["On-demand canvas"])


@router.get("/{conversation_id}/canvas", response_model=CanvasDetail)
def read_canvas(conversation_id: str) -> CanvasDetail:
    canvas = repository.get_canvas(conversation_id)
    if canvas is None:
        raise CanvasNotFoundError()
    return CanvasDetail(
        id=canvas.id,
        conversation_id=canvas.conversation_id,
        revision=canvas.revision,
        response=canvas.response_json,
        created_at=canvas.created_at,
        updated_at=canvas.updated_at,
    )
