"""
Agent 管理器
模块路由 → 工具执行 → 结果润色 → SSE 流式输出
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent.tool_manager import ToolManager
from app.services.agent.session_manager import SessionManager
from app.services.agent.game_manager import GameManager
from app.services.agent.prompt_templates import SYSTEM_PROMPT
from app.services.agent.deepseek_client import DeepSeekClient
from app.core.config import get_settings
from app.db.repositories.teacher_repo import TeacherInfoRepository

settings = get_settings()


class AgentManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.sessions = SessionManager()
        self.llm = DeepSeekClient(model="pro")
        self.llm_fast = DeepSeekClient(model="flash")

    async def process_message(self, message: str, session_id: str, module: str = None) -> str:
        """处理消息，支持模块路由"""
        session = await self.sessions.get_session(session_id)
        if not session:
            return "会话已过期，请重新开始对话。"

        tools = ToolManager(self.session, session["user_id"], "", session["role"])
        user_name = await self._get_user_name(session["user_id"])
        tools.user_name = user_name

        # 检查待确认操作
        pending = session.get("pending_operation")
        if pending:
            if message.strip() in ("是", "确认", "好的", "可以", "yes", "ok", "执行", "同意"):
                return await self._execute_pending(session, session_id, pending, tools)
            elif message.strip() in ("否", "取消", "不", "no", "cancel", "算了"):
                await self.sessions.update_session(session_id, pending_operation=None)
                return "好的主公，此操作已取消。"

        # 游戏状态检查
        game = session.get("current_game")
        game_state = session.get("game_state")
        game_mgr = GameManager(self.session)

        if game == "24_points" and game_state:
            return await self._handle_24_answer(message, game_state, session_id, game_mgr)

        if game == "riddle" and game_state:
            return await self._handle_riddle_answer(message, game_state, session_id, game_mgr)

        # 模块路由（优先于意图分类）
        if module:
            return await self._route_module(module, message, session, session_id, tools, game_mgr, user_name)

        # 意图分类（无模块时的 fallback）
        intent = await tools.classify_intent(message)
        await self.sessions.update_session(session_id, last_intent=intent)
        return await self._route_intent(intent, message, session, session_id, tools, game_mgr, user_name)

    async def stream_response(self, message: str, session_id: str, module: str = None):
        """SSE 流式响应生成器"""
        full_response = await self.process_message(message, session_id, module)

        # 发送额外标记（游戏状态、按钮等）
        session = await self.sessions.get_session(session_id)
        extra = {}
        if session:
            if session.get("current_game") == "riddle" and session.get("game_state"):
                pass
            extra["game_active"] = session.get("current_game")
            extra["module"] = session.get("current_module")
            if session.get("show_next_24"):
                extra["show_next_24"] = True
                await self.sessions.update_session(session_id, show_next_24=None)

        yield f"data: {self._sse_msg('start', '')}\n\n"

        chunk_size = 3
        for i in range(0, len(full_response), chunk_size):
            chunk = full_response[i:i + chunk_size]
            yield f"data: {self._sse_msg('text', chunk)}\n\n"
            await asyncio.sleep(0.02)

        if extra.get("game_active") or extra.get("module"):
            yield f"data: {self._sse_msg('meta', json.dumps(extra, ensure_ascii=False))}\n\n"

        yield f"data: {self._sse_msg('end', '')}\n\n"
        yield "data: [DONE]\n\n"

    # ========== 模块路由 ==========

    async def _route_module(self, module: str, message: str, session: dict, session_id: str,
                            tools: ToolManager, game_mgr: GameManager, user_name: str) -> str:
        await self.sessions.update_session(session_id, current_module=module)

        if module == "game_24":
            # 检查是否已有活跃游戏
            if session.get("current_game") == "24_points":
                return await self._handle_24_answer(message, session.get("game_state"), session_id, game_mgr)
            result = game_mgr.start_24_points()
            await self.sessions.update_session(session_id, current_game="24_points",
                                               game_state={"numbers": result["numbers"]})
            return result["message"]

        elif module == "game_riddle":
            if session.get("current_game") == "riddle":
                return await self._handle_riddle_answer(message, session.get("game_state"), session_id, game_mgr)
            used_ids = session.get("used_riddle_ids") or []
            result = await game_mgr.start_riddle(exclude_ids=used_ids)
            if result.get("riddle_id"):
                used_ids.append(result["riddle_id"])
                await self.sessions.update_session(session_id, current_game="riddle",
                                                   game_state={"riddle_id": result["riddle_id"]},
                                                   used_riddle_ids=used_ids)
            return result["message"]

        elif module == "business":
            intent = await tools.classify_intent(message)
            if intent in ("query", "modify"):
                return await self._route_intent(intent, message, session, session_id, tools, game_mgr, user_name)
            # Fallback: 直接尝试 NL2SQL
            result = await tools.handle_query(message, [])
            if "未找到" in result.content or "未能理解" in result.content:
                result = await tools.handle_modify(message)
            return result.content

        elif module == "knowledge":
            return (await tools.handle_knowledge(message)).content

        elif module == "chat":
            return (await tools.handle_greet(message)).content

        return await self._route_intent("unknown", message, session, session_id, tools, game_mgr, user_name)

    # ========== 意图路由 ==========

    async def _route_intent(self, intent: str, message: str, session: dict, session_id: str,
                            tools: ToolManager, game_mgr: GameManager, user_name: str) -> str:
        if intent == "game_24":
            result = game_mgr.start_24_points()
            await self.sessions.update_session(session_id, current_game="24_points",
                                               game_state={"numbers": result["numbers"]}, current_module="game_24")
            return result["message"]

        elif intent == "game_riddle":
            used_ids = session.get("used_riddle_ids") or []
            result = await game_mgr.start_riddle(exclude_ids=used_ids)
            if result.get("riddle_id"):
                used_ids.append(result["riddle_id"])
                await self.sessions.update_session(session_id, current_game="riddle",
                                                   game_state={"riddle_id": result["riddle_id"]},
                                                   current_module="game_riddle",
                                                   used_riddle_ids=used_ids)
            return result["message"]

        elif intent == "query":
            result = await tools.handle_query(message, [])
            return result.content

        elif intent == "modify":
            result = await tools.handle_modify(message)
            if result.type == "confirm_required":
                await self.sessions.update_session(session_id, pending_operation=result.data)
            return result.content

        elif intent == "knowledge":
            return (await tools.handle_knowledge(message)).content

        elif intent == "greet":
            return (await tools.handle_greet(message)).content

        else:
            return await self._general_chat(message, session_id, session["user_id"])

    # ========== 游戏处理 ==========

    async def _handle_24_answer(self, message: str, game_state: dict, session_id: str, game_mgr: GameManager) -> str:
        """使用 LLM 解析用户的自然语言输入，转换为算式后再验证"""
        numbers = game_state.get("numbers", [])

        # 检测跳过意图
        skip_keywords = ["算不出来", "不知道", "不会", "跳过", "skip", "pass", "过", "太难", "不会算", "下一题", "换一题"]
        if any(kw in message.strip().lower() for kw in skip_keywords):
            await self.sessions.update_session(session_id, current_game=None, game_state=None,
                                               show_next_24=True)
            return f"主公不必介怀，此题已过。点击下方「下一题」可继续挑战。"

        # 用 LLM 将自然语言转为数学表达式
        expression = await self._parse_24_expression(message, numbers)
        if expression is None:
            return f"主公，亮未能从您的回答中识别出有效的算式。请用这四个数字 {numbers} 通过加减乘除得出24。例如：(3+3)×(8-4)"

        result = game_mgr.check_24_points(expression, numbers)
        if result["correct"]:
            await self.sessions.update_session(session_id, current_game=None, game_state=None,
                                               show_next_24=True)
            return result["message"]
        return result["message"]

    async def _handle_riddle_answer(self, message: str, game_state: dict, session_id: str, game_mgr: GameManager) -> str:
        # 检测跳过意图
        skip_keywords = ["不知道", "不会", "猜不到", "猜不出", "算不出来", "跳过", "skip", "pass", "过", "太难", "下一题", "换一题", "告诉我答案", "答案是什么"]
        if any(kw in message.strip().lower() for kw in skip_keywords):
            riddle_id = game_state.get("riddle_id")
            answer = await game_mgr.get_riddle_answer(riddle_id) if riddle_id else None
            answer_text = f"，谜底是「{answer}」" if answer else ""
            await self.sessions.update_session(session_id, current_game=None, game_state=None)
            return f"主公不必介怀{answer_text}。此题已过，点击「下一题」可继续猜谜。"

        result = await game_mgr.check_riddle(game_state.get("riddle_id"), message)
        if result["correct"]:
            await self.sessions.update_session(session_id, current_game=None, game_state=None)
            return result["message"] + "\n\n主公，点击「下一题」可继续猜谜。"
        return result["message"]

    async def _parse_24_expression(self, user_input: str, numbers: list[int]) -> str | None:
        """使用 LLM 将自然语言解析为标准算式"""
        prompt = f"""将用户的输入转换为标准数学表达式（仅使用数字和+-*/()运算符）。

可用数字（各用一次）：{numbers}
用户输入：{user_input}

规则：
1. 必须恰好使用每个数字一次
2. 只能使用加减乘除和括号
3. 只输出表达式，不要任何其他文字
4. 如果无法解析，输出：INVALID

表达式："""
        try:
            result = await self.llm_fast.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1,
            )
            expr = result.strip()
            if expr == "INVALID" or not expr:
                return None
            # 清理表达式
            expr = expr.replace(" ", "").replace("（", "(").replace("）", ")").replace("×", "*").replace("÷", "/").replace("X", "*").replace("x", "*")
            return expr
        except Exception:
            return None

    # ========== 辅助方法 ==========

    async def _execute_pending(self, session: dict, session_id: str, pending: dict, tools: ToolManager) -> str:
        sql = pending.get("pending_sql", "")
        if not sql:
            return "主公，待确认操作已失效。"
        result = await tools.execute_confirmed_sql(sql)
        await self.sessions.update_session(session_id, pending_operation=None)
        return result.content

    async def _general_chat(self, message: str, session_id: str, user_id: str) -> str:
        history = await self.sessions.get_history(session_id) if session_id else []
        msgs = history[-10:] + [{"role": "user", "content": message}]
        reply = await self.llm.chat(messages=msgs, system=SYSTEM_PROMPT, max_tokens=300)
        return reply

    async def _get_user_name(self, user_id: str) -> str:
        try:
            teacher_repo = TeacherInfoRepository(self.session)
            teacher = await teacher_repo.get_by_teacher_id(user_id)
            return teacher.name if teacher else ""
        except Exception:
            return ""

    async def get_abilities(self) -> dict:
        return {
            "name": "诸葛亮 (孔明)",
            "description": "蜀汉丞相，智能助手",
            "modules": [
                {"key": "business", "name": "业务处理", "desc": "查询课表、请假、查考勤等", "icon": "Document"},
                {"key": "knowledge", "name": "知识问答", "desc": "学校规章制度、FAQ", "icon": "Collection"},
                {"key": "chat", "name": "闲聊", "desc": "与丞相畅谈古今", "icon": "ChatDotRound"},
                {"key": "game_24", "name": "二十四点", "desc": "4个数字算24", "icon": "Odometer"},
                {"key": "game_riddle", "name": "猜灯谜", "desc": "传统文字游戏", "icon": "Sunrise"},
            ],
            "greeting": "主公在上，臣诸葛亮拜见。亮在此恭候差遣，为您分忧解难。请选择上方模块开始。",
        }

    def _sse_msg(self, msg_type: str, content: str) -> str:
        return json.dumps({"type": msg_type, "content": content}, ensure_ascii=False)
