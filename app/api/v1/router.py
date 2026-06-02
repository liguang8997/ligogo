from fastapi import APIRouter
from app.api.v1.endpoints import auth, teachers, files, courses, affairs, attendance, notifications, logs, reports, agent

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(teachers.router)
api_router.include_router(files.router)
api_router.include_router(courses.router)
api_router.include_router(affairs.router)
api_router.include_router(attendance.router)
api_router.include_router(notifications.router)
api_router.include_router(logs.router)
api_router.include_router(reports.router)
api_router.include_router(agent.router)
