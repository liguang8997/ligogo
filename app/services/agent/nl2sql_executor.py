"""
NL2SQL 执行器
Schema Linking + Few-Shot + SQL 生成与执行
"""
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BusinessException
from app.services.agent.deepseek_client import DeepSeekClient
from app.services.agent.prompt_templates import NL2SQL_SCHEMA, NL2SQL_FEWSHOT, SQL_SAFETY_RULES


class NL2SQLExecutor:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.llm = DeepSeekClient(model="pro")

    def get_schema(self, question: str) -> str:
        """根据问题关键词做简单的 Schema Linking，返回相关表结构"""
        schema_parts = []
        q = question.lower()

        if any(w in q for w in ["老师", "教师", "teacher", "姓名", "部门", "职称", "手机", "邮箱"]):
            schema_parts.append(NL2SQL_SCHEMA["teacher_info"])
        if any(w in q for w in ["课", "课程", "course", "排课", "上课", "教室", "学期"]):
            schema_parts.append(NL2SQL_SCHEMA["teacher_course"])
        if any(w in q for w in ["假", "请假", "审批", "事务", "出差", "报销", "调课", "反馈", "申请"]):
            schema_parts.append(NL2SQL_SCHEMA["teacher_affair"])
        if any(w in q for w in ["打卡", "考勤", "签到", "签退", "迟到", "早退"]):
            schema_parts.append(NL2SQL_SCHEMA["attendance_record"])
        if any(w in q for w in ["通知", "消息", "提醒"]):
            schema_parts.append(NL2SQL_SCHEMA["system_notification"])

        if not schema_parts:
            schema_parts = list(NL2SQL_SCHEMA.values())

        return "\n\n".join(schema_parts)

    async def generate_sql(self, question: str, user_id: str, user_name: str, role: str) -> str:
        """生成 SQL，返回 SQL 语句"""
        schema = self.get_schema(question)
        prompt = f"""你是一个SQL专家，根据以下表结构生成正确的MySQL SQL语句。

表结构：
{schema}

{NL2SQL_FEWSHOT}

{SQL_SAFETY_RULES}

当前用户信息：
- user_id: {user_id}
- user_name: {user_name}
- role: {role} ({'管理员，可查看所有数据' if role == 'admin' else '领导，可查看所有数据' if role == 'leader' else '普通教师，只能查看自己的数据'})

用户问题：{question}

请只输出SQL语句，不要有任何其他文字。
如果用户的问题不是数据查询/操作，输出: NO_SQL
如果是修改/删除/插入操作，在SQL前加一行: -- CONFIRM_REQUIRED

SQL："""

        result = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1024,
        )
        return result.strip()

    async def execute_sql(self, sql: str, user_id: str, role: str) -> dict:
        """安全执行 SQL"""
        sql_upper = sql.strip().upper()

        forbidden = ["DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
        for word in forbidden:
            if sql_upper.startswith(word) or f" {word} " in sql_upper:
                raise BusinessException(f"禁止执行 {word} 操作")

        # 普通教师只能查自己的数据
        if role == "teacher":
            if sql_upper.startswith("SELECT"):
                if "WHERE" in sql_upper:
                    if "teacher_id" not in sql.lower():
                        raise BusinessException("权限不足：只能查询自己的数据")
                else:
                    raise BusinessException("请指定查询条件")
            else:
                raise BusinessException("普通教师无数据修改权限")

        try:
            result = await self.session.execute(text(sql))
            if sql_upper.startswith("SELECT"):
                rows = result.fetchall()
                cols = result.keys()
                data = [dict(zip(cols, row)) for row in rows]
                # 转换不可序列化的类型
                for row in data:
                    for k, v in row.items():
                        if hasattr(v, "isoformat"):
                            row[k] = v.isoformat()
                return {"type": "query", "columns": list(cols), "rows": data, "count": len(data)}
            else:
                await self.session.flush()
                return {"type": "modify", "affected": result.rowcount}
        except Exception as e:
            raise BusinessException(f"SQL执行错误: {str(e)}")

    def needs_confirmation(self, sql: str) -> bool:
        return sql.strip().startswith("-- CONFIRM_REQUIRED")

    def get_preview_description(self, sql: str) -> str:
        """生成操作预览的人类可读描述"""
        sql_clean = sql.replace("-- CONFIRM_REQUIRED", "").strip()
        sql_upper = sql_clean.upper()
        if sql_upper.startswith("INSERT"):
            return "此操作将新增一条数据记录"
        elif sql_upper.startswith("UPDATE"):
            return "此操作将修改现有数据"
        elif sql_upper.startswith("DELETE"):
            return "此操作将删除数据记录"
        return "此操作将修改数据库数据"
