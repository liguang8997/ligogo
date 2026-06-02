from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.db.repositories.base import BaseRepository
from app.db.models.teacher import TeacherInfo
from app.db.models.course import TeacherCourse
from app.db.models.notification import SystemNotification
from loguru import logger


async def check_course_reminders():
    """检查明天的课程，向相关教师发送提醒"""
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = f"周{tomorrow.weekday() + 1}"
    try:
        async with async_session() as session:
            repo = BaseRepository[TeacherCourse](session)
            repo.model = TeacherCourse
            courses = await repo.find_all()
            count = 0
            for course in courses:
                schedule = course.schedule_info or ""
                if tomorrow_str in schedule:
                    notif = SystemNotification(
                        receiver_id=course.teacher_id,
                        title="课程提醒",
                        content=f"明天({tomorrow})有课程: {course.course_name}，地点: {course.location or '待定'}，时间: {schedule}",
                        type=1,
                        related_id=course.id,
                    )
                    session.add(notif)
                    count += 1
            await session.commit()
            if count > 0:
                logger.info(f"发送了 {count} 条课程提醒")
    except Exception as e:
        logger.error(f"课程提醒任务失败: {e}")


async def check_birthday_greetings():
    """检查今天生日的教师，发送生日祝福"""
    today = date.today()
    try:
        async with async_session() as session:
            repo = BaseRepository[TeacherInfo](session)
            repo.model = TeacherInfo
            teachers = await repo.find_all()
            count = 0
            for teacher in teachers:
                if teacher.birth_date and teacher.birth_date.month == today.month and teacher.birth_date.day == today.day:
                    notif = SystemNotification(
                        receiver_id=teacher.teacher_id,
                        title="生日祝福",
                        content=f"祝 {teacher.name} 老师生日快乐！愿您工作顺利，桃李满天下！",
                        type=3,
                    )
                    session.add(notif)
                    count += 1
            await session.commit()
            if count > 0:
                logger.info(f"发送了 {count} 条生日祝福")
    except Exception as e:
        logger.error(f"生日祝福任务失败: {e}")
