"""
Agent 工具管理器
定义 Agent 可用的工具函数
"""
import json
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agent.nl2sql_executor import NL2SQLExecutor
from app.services.agent.rag_retriever import RAGRetriever
from app.services.agent.game_manager import GameManager
from app.services.agent.prompt_templates import RAG_PROMPT, SYSTEM_PROMPT
from app.services.agent.deepseek_client import DeepSeekClient


@dataclass
class ToolResult:
    type: str  # "text", "sql_result", "game", "confirm_required", "error"
    content: str
    data: dict = None

    def to_dict(self):
        return {"type": self.type, "content": self.content, "data": self.data}


class ToolManager:
    def __init__(self, session: AsyncSession, user_id: str, user_name: str, role: str):
        self.session = session
        self.user_id = user_id
        self.user_name = user_name
        self.role = role
        self.nl2sql = NL2SQLExecutor(session)
        self.rag = RAGRetriever()
        self.game = GameManager(session)
        self.llm_fast = DeepSeekClient(model="flash")
        self.llm_pro = DeepSeekClient(model="pro")

    async def classify_intent(self, message: str) -> str:
        """意图分类"""
        prompt = f"""分析用户意图，只返回一个单词：
- query: 查询数据（课表、教师信息、考勤等）
- modify: 修改数据（请假、修改信息等）
- knowledge: 问学校规章制度、FAQ、联系方式等
- game_24: 玩二十四点游戏
- game_riddle: 猜灯谜
- greet: 打招呼或闲聊
- unknown: 无法判断

用户：{message}
意图："""

        result = await self.llm_fast.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.1,
        )
        return result.strip().lower()

    async def handle_query(self, question: str, history: list) -> ToolResult:
        """处理数据查询"""
        sql = await self.nl2sql.generate_sql(question, self.user_id, self.user_name, self.role)
        if sql == "NO_SQL":
            return ToolResult(type="text", content="主公，亮未能理解您想查询什么数据，可否说得更具体些？")

        try:
            result = await self.nl2sql.execute_sql(sql, self.user_id, self.role)
            if result["type"] == "query":
                return await self._format_query_result(question, result)
            else:
                return ToolResult(type="text", content=f"操作完成，影响了 {result['affected']} 条记录。")
        except Exception as e:
            return ToolResult(type="error", content=f"主公恕罪，执行出错：{str(e)}")

    async def handle_modify(self, question: str) -> ToolResult:
        """处理数据修改"""
        sql = await self.nl2sql.generate_sql(question, self.user_id, self.user_name, self.role)
        if sql == "NO_SQL":
            return ToolResult(type="text", content="主公，亮未能理解您想要进行何种操作。")

        if self.nl2sql.needs_confirmation(sql):
            preview = self.nl2sql.get_preview_description(sql)
            sql_clean = sql.replace("-- CONFIRM_REQUIRED\n", "").replace("-- CONFIRM_REQUIRED", "").strip()
            return ToolResult(
                type="confirm_required",
                content=f"主公，{preview}。是否确认执行？\n\n预览SQL：{sql_clean}",
                data={"pending_sql": sql_clean, "description": preview},
            )
        else:
            try:
                result = await self.nl2sql.execute_sql(sql, self.user_id, self.role)
                return ToolResult(
                    type="sql_result",
                    content=f"操作完成，影响了 {result['affected']} 条记录。",
                )
            except Exception as e:
                return ToolResult(type="error", content=f"执行出错：{str(e)}")

    async def execute_confirmed_sql(self, sql: str) -> ToolResult:
        """执行已确认的 SQL"""
        try:
            result = await self.nl2sql.execute_sql(sql, self.user_id, self.role)
            if result["type"] == "modify":
                return ToolResult(type="text", content=f"主公，操作已完成，影响了 {result['affected']} 条记录。")
            return ToolResult(type="sql_result", content=json.dumps(result, ensure_ascii=False), data=result)
        except Exception as e:
            return ToolResult(type="error", content=f"主公恕罪：{str(e)}")

    async def handle_knowledge(self, question: str) -> ToolResult:
        """处理知识问答 (RAG)"""
        docs = await self.rag.retrieve(question, top_k=3)
        if not docs:
            return ToolResult(type="text", content="主公，亮暂未在校内资料中查得相关信息，容我另行探查。")

        context = self.rag.format_context(docs)
        prompt = RAG_PROMPT.format(context=context, question=question)

        answer = await self.llm_fast.chat(
            messages=[{"role": "user", "content": prompt}],
            system=SYSTEM_PROMPT,
            max_tokens=512,
        )

        sources = "、".join([f"《{d['title']}》" for d in docs])
        return ToolResult(
            type="text",
            content=answer + f"\n\n（参考来源：{sources}）",
        )

    async def handle_greet(self, message: str) -> ToolResult:
        """处理问候/闲聊"""
        prompt = f"""用户说：{message}
用诸葛亮的口吻简短回复（30字以内），称呼用户为"主公"。"""
        reply = await self.llm_fast.chat(messages=[{"role": "user", "content": prompt}], max_tokens=100)
        return ToolResult(type="text", content=reply)

    async def _format_query_result(self, question: str, result: dict) -> ToolResult:
        """用 LLM 格式化查询结果为自然语言"""
        if result["count"] == 0:
            return ToolResult(type="text", content="主公，据亮查询，未找到符合条件的数据。")

        data_str = json.dumps(result["rows"], ensure_ascii=False, default=str)
        prompt = f"""用诸葛亮的口吻，将以下查询结果友好地总结给主公。

主公的问题：{question}
查询结果（{result['count']}条）：{data_str}

请用表格或列表形式呈现关键信息，语气温文尔雅。"""
        reply = await self.llm_fast.chat(messages=[{"role": "user", "content": prompt}], max_tokens=512)
        return ToolResult(type="text", content=reply, data={"raw_rows": result["rows"]})
