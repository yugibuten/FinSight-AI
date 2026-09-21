from fastapi import APIRouter, Query, Response, status

from app.core.exceptions import ConversationNotFoundError
from app.db import repository
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationListItem,
    ConversationTurn,
)


router = APIRouter(prefix="/conversations", tags=["Conversations"])


def _list_item(conversation, turn_count: int | None = None) -> ConversationListItem:
    return ConversationListItem(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        turn_count=len(conversation.queries) if turn_count is None else turn_count,
    )


@router.post("", response_model=ConversationListItem, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate) -> ConversationListItem:
    return _list_item(repository.create_conversation(payload.title), turn_count=0)


@router.get("", response_model=list[ConversationListItem])
def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ConversationListItem]:
    return [_list_item(item) for item in repository.list_conversations(limit, offset)]


@router.get("/{conversation_id}", response_model=ConversationDetail)
def read_conversation(conversation_id: str) -> ConversationDetail:
    conversation = repository.get_conversation(conversation_id)
    if conversation is None:
        raise ConversationNotFoundError()
    item = _list_item(conversation)
    turns = [
        ConversationTurn(
            research_id=query.id,
            turn_index=query.turn_index or 0,
            question=query.question,
            status=query.status,
            result=query.result.response_json if query.result else None,
        )
        for query in conversation.queries
    ]
    return ConversationDetail(**item.model_dump(), turns=turns)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_conversation(conversation_id: str) -> Response:
    if not repository.delete_conversation(conversation_id):
        raise ConversationNotFoundError()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
