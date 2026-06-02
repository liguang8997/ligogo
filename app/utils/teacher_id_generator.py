from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.redis_client import get_redis
from loguru import logger


async def generate_teacher_id(role_code: int, db_session: AsyncSession) -> str:
    """
    生成8位teacher_id: [身份码1位][年2位][月2位][序号3位]
    role_code: 1-普通教师,2-领导,3-管理员
    """
    now = datetime.now()
    prefix = f"{role_code}{now.strftime('%y%m')}"
    seq_key = f"teacher_id:seq:{prefix}"

    seq = None
    try:
        redis = await get_redis()
        seq = await redis.incr(seq_key)
        await redis.expire(seq_key, 86400 * 2)
    except Exception:
        logger.warning("Redis unavailable for teacher_id generation, using DB fallback")

    if seq is None:
        seq = await _db_sequence(prefix, db_session)

    teacher_id = f"{prefix}{seq:03d}"

    result = await db_session.execute(
        text("SELECT 1 FROM teacher_info WHERE teacher_id = :tid"),
        {"tid": teacher_id},
    )
    if result.first():
        return await generate_teacher_id(role_code, db_session)

    return teacher_id


async def _db_sequence(prefix: str, db_session: AsyncSession) -> int:
    await db_session.execute(
        text("""
            INSERT INTO teacher_seq (prefix, current_seq)
            VALUES (:prefix, 1)
            ON DUPLICATE KEY UPDATE current_seq = current_seq + 1
        """),
        {"prefix": prefix},
    )
    await db_session.flush()
    result = await db_session.execute(
        text("SELECT current_seq FROM teacher_seq WHERE prefix = :prefix"),
        {"prefix": prefix},
    )
    row = result.first()
    return row[0] if row else 1
