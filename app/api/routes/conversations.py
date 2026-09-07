"""对话相关接口：会话与消息。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from db import repos
from app.api.deps import get_db, get_default_user
from app.schemas.chat import ConversationListItem, MessageItem
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ApiResponse)
def create_conversation(session=Depends(get_db),
                        user=Depends(get_default_user)) -> ApiResponse:
    conv = repos.conversation.create_conversation(session, user_id=user["id"])
    return ApiResponse.success(conv)


@router.get("", response_model=ApiResponse)
def list_conversations(session=Depends(get_db),
                       user=Depends(get_default_user)) -> ApiResponse:
    items = repos.conversation.list_conversations(session, user["id"])
    return ApiResponse.success([ConversationListItem(**c) for c in items])


@router.get("/{conversation_id}/messages", response_model=ApiResponse)
def get_messages(conversation_id: int, session=Depends(get_db),
                 user=Depends(get_default_user)) -> ApiResponse:
    conv = repos.conversation.get_conversation(session, conversation_id)
    if not conv or conv["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = repos.conversation.list_messages(session, conversation_id)
    return ApiResponse.success([MessageItem(**m) for m in msgs])
