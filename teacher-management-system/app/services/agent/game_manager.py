"""
游戏管理器：二十四点、猜灯谜
"""
import random
import re
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.riddle import LanternRiddle


class GameManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    def start_24_points(self) -> dict:
        """开始一局二十四点，返回4个数字"""
        numbers = [random.randint(1, 10) for _ in range(4)]
        return {
            "game": "24_points",
            "numbers": numbers,
            "message": f"主公，亮出题了：【{', '.join(map(str, numbers))}】，请用加减乘除使结果为24。",
        }

    def check_24_points(self, expression: str, numbers: list[int]) -> dict:
        """验证二十四点答案"""
        # 提取表达式中的数字
        expr_nums = re.findall(r"\d+", expression)
        expr_nums_int = sorted(int(n) for n in expr_nums)
        expected = sorted(numbers)

        if expr_nums_int != expected:
            return {"correct": False, "message": "主公，所用数字与原题不符，请用给出的四个数字各一次。"}

        # 安全检查：只允许数字、运算符、括号和空格
        if not re.match(r"^[\d\s\+\-\*/\(\)\.]+$", expression):
            return {"correct": False, "message": "主公，表达式含有非法字符，亮不能接受。"}

        try:
            result = eval(expression)
            if abs(result - 24) < 0.001:
                return {"correct": True, "message": "主公英明！答案完全正确，亮佩服之至！"}
            else:
                return {"correct": False, "message": f"主公，此算式结果为{result}，并非24，请再试。"}
        except Exception:
            return {"correct": False, "message": "主公，此算式无法计算，请检查后重新输入。"}

    async def start_riddle(self, exclude_ids: list[int] | None = None) -> dict:
        """随机出一道灯谜，可排除已出过的题目"""
        query = select(LanternRiddle).where(LanternRiddle.is_deleted == 0)
        if exclude_ids:
            query = query.where(LanternRiddle.id.notin_(exclude_ids))
        result = await self.session.execute(
            query.order_by(func.rand()).limit(1)
        )
        riddle = result.scalar_one_or_none()
        # 所有题目都已出过，重置
        if not riddle and exclude_ids:
            result = await self.session.execute(
                select(LanternRiddle).where(LanternRiddle.is_deleted == 0).order_by(func.rand()).limit(1)
            )
            riddle = result.scalar_one_or_none()
        if not riddle:
            return {"game": "riddle", "message": "主公恕罪，灯谜库今日空空如也，容亮改日再备。"}

        return {
            "game": "riddle",
            "riddle_id": riddle.id,
            "riddle": riddle.riddle,
            "hint": riddle.hint,
            "message": f"主公请听谜面：【{riddle.riddle}】（{riddle.hint}）",
        }

    async def get_riddle_answer(self, riddle_id: int) -> str | None:
        """获取指定灯谜答案"""
        result = await self.session.execute(
            select(LanternRiddle).where(LanternRiddle.id == riddle_id)
        )
        riddle = result.scalar_one_or_none()
        return riddle.answer if riddle else None

    async def check_riddle(self, riddle_id: int, answer: str) -> dict:
        """验证灯谜答案"""
        result = await self.session.execute(
            select(LanternRiddle).where(LanternRiddle.id == riddle_id)
        )
        riddle = result.scalar_one_or_none()
        if not riddle:
            return {"correct": False, "message": "主公，此题已不知所踪。"}

        if answer.strip() == riddle.answer:
            src = f" 此谜出自{riddle.source}" if riddle.source else ""
            return {"correct": True, "message": f"主公英明！正是「{riddle.answer}」。{src}"}
        else:
            hint_text = f"，{riddle.hint}" if riddle.hint else ""
            return {"correct": False, "message": f"主公，答案不对{hint_text}，请再猜。"}
