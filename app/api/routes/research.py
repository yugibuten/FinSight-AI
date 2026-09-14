from fastapi import APIRouter, Query, Response, status

from app.core.exceptions import ResearchNotFoundError
from app.db import repository
from app.schemas.research import ResearchDetail, ResearchListItem, ToolExecutionItem


router = APIRouter(prefix="/research", tags=["Research history"])


@router.get("", response_model=list[ResearchListItem], summary="List recent research")
def list_recent_research(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ResearchListItem]:
    return [ResearchListItem.model_validate(item) for item in repository.list_research(limit, offset)]


@router.get("/{research_id}", response_model=ResearchDetail, summary="Get saved research")
def read_research(research_id: str) -> ResearchDetail:
    item = repository.get_research(research_id)
    if item is None:
        raise ResearchNotFoundError()
    result = None
    if item.result is not None:
        result = item.result.response_json
    return ResearchDetail(
        **ResearchListItem.model_validate(item).model_dump(),
        result=result,
        tool_executions=[
            ToolExecutionItem.model_validate(execution) for execution in item.tool_executions
        ],
    )


@router.delete(
    "/{research_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete saved research",
)
def remove_research(research_id: str) -> Response:
    if not repository.delete_research(research_id):
        raise ResearchNotFoundError()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
