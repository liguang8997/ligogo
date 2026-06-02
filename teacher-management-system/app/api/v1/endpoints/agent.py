"""
诸葛亮 Agent API (SSE 流式对话)
"""
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.services.agent.agent_manager import AgentManager
from app.services.agent.session_manager import SessionManager
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/agent", tags=["诸葛亮Agent"])

VALID_MODULES = ["business", "knowledge", "chat", "game_24", "game_riddle"]


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=2000)
    session_id: str | None = Field(None, description="会话ID")
    module: str | None = Field(None, description="模块: business/knowledge/chat/game_24/game_riddle")


@router.post("/chat")
async def chat(req: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """SSE 流式对话"""
    session_mgr = SessionManager()
    session_id = req.session_id
    module = req.module

    # 如果指定了模块且跟前一个模块不同，创建新会话
    if not session_id or (module and session_id):
        existing = await session_mgr.get_session(session_id) if session_id else None
        if existing and module and existing.get("current_module") != module:
            session_id = await session_mgr.create_session(request.state.user_id, request.state.role)
        elif not existing:
            session_id = await session_mgr.create_session(request.state.user_id, request.state.role)

    if module:
        await session_mgr.update_session(session_id, current_module=module)

    await session_mgr.add_to_history(session_id, "user", req.message)

    agent = AgentManager(db)

    async def event_stream():
        try:
            async for chunk in agent.stream_response(req.message, session_id, module):
                yield chunk
        except Exception as e:
            error_msg = json.dumps({"type": "error", "content": f"主公恕罪，亮处理中出了差错：{str(e)}"}, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
        },
    )


class RiddleAction(BaseModel):
    action: str = Field(..., pattern="^(next)$")
    session_id: str


@router.post("/riddle/next")
async def next_riddle(req: RiddleAction, request: Request, db: AsyncSession = Depends(get_db)):
    """获取下一道灯谜"""
    from app.services.agent.game_manager import GameManager
    session_mgr = SessionManager()
    session = await session_mgr.get_session(req.session_id)
    if not session:
        return ResponseModel(code=400, message="会话已过期")

    game_mgr = GameManager(db)
    used_ids = session.get("used_riddle_ids") or []
    result = await game_mgr.start_riddle(exclude_ids=used_ids)
    if result.get("riddle_id"):
        used_ids.append(result["riddle_id"])
        await session_mgr.update_session(req.session_id,
                                         current_game="riddle",
                                         game_state={"riddle_id": result["riddle_id"]},
                                         used_riddle_ids=used_ids)
    return ResponseModel(data=result)


class Game24Action(BaseModel):
    action: str = Field(..., pattern="^(next)$")
    session_id: str


@router.post("/game24/next")
async def next_24(req: Game24Action, request: Request, db: AsyncSession = Depends(get_db)):
    """获取下一道二十四点题目"""
    from app.services.agent.game_manager import GameManager
    session_mgr = SessionManager()
    session = await session_mgr.get_session(req.session_id)
    if not session:
        return ResponseModel(code=400, message="会话已过期")

    game_mgr = GameManager(db)
    result = game_mgr.start_24_points()
    await session_mgr.update_session(req.session_id,
                                     current_game="24_points",
                                     game_state={"numbers": result["numbers"]})
    return ResponseModel(data=result)


@router.get("/abilities")
async def get_abilities(db: AsyncSession = Depends(get_db)):
    agent = AgentManager(db)
    abilities = await agent.get_abilities()
    return ResponseModel(data=abilities)


@router.post("/clear-session")
async def clear_session(request: Request, session_id: str = None):
    session_mgr = SessionManager()
    if session_id:
        await session_mgr.clear_session(session_id)
    return ResponseModel(message="会话已清除")
