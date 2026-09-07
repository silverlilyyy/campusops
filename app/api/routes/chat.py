"""聊天入口：接收用户消息，触发 Multi-Agent 规划/重规划。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from db import repos
from app.api.deps import get_db, get_default_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.common import ApiResponse
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ApiResponse)
def chat(req: ChatRequest, session=Depends(get_db),
         user=Depends(get_default_user)) -> ApiResponse:
    """发送一条消息并触发 Agent 规划。"""
    user_id = req.user_id or user["id"]
    try:
        result = chat_service.handle_chat(
            session, user_id=user_id, message=req.message,
            conversation_id=req.conversation_id,
            replan=req.replan, previous_session_id=req.previous_session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not result.get("ok"):
        return ApiResponse.fail(result.get("error", "处理失败"),
                                data={"agent_session_id": result.get("agent_session_id")})
    return ApiResponse.success(result)
