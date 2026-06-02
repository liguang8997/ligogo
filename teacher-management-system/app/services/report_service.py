from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.base import BaseRepository
from app.db.models.teacher import TeacherInfo
from app.db.models.attendance import AttendanceRecord
from app.utils.excel import export_to_excel


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def export_teachers(self) -> StreamingResponse:
        repo = BaseRepository[TeacherInfo](self.session)
        repo.model = TeacherInfo
        teachers = await repo.find_all()
        headers = ["工号", "姓名", "性别", "手机号", "邮箱", "部门", "职称", "学历", "状态", "入职日期"]
        rows = []
        for t in teachers:
            gender_map = {0: "未知", 1: "男", 2: "女"}
            status_map = {1: "在职", 2: "离职", 3: "退休", 4: "外聘"}
            rows.append([
                t.teacher_id, t.name, gender_map.get(t.gender, ""),
                t.phone or "", t.email or "", t.department or "",
                t.title or "", t.education or "",
                status_map.get(t.status, ""),
                str(t.hire_date) if t.hire_date else "",
            ])
        output = export_to_excel(headers, rows, "教师名单")
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=teacher_list.xlsx"})

    async def export_attendance(self, teacher_id: str | None = None) -> StreamingResponse:
        repo = BaseRepository[AttendanceRecord](self.session)
        repo.model = AttendanceRecord
        filters = {}
        if teacher_id:
            filters["teacher_id"] = teacher_id
        records = await repo.find_all(**filters)
        headers = ["工号", "姓名", "日期", "上班时间", "下班时间", "状态", "备注"]
        status_map = {1: "正常", 2: "迟到", 3: "早退", 4: "缺卡"}
        rows = []
        for r in records:
            rows.append([
                r.teacher_id, r.teacher_name, str(r.check_date),
                str(r.check_in_time) if r.check_in_time else "",
                str(r.check_out_time) if r.check_out_time else "",
                status_map.get(r.status, ""),
                r.remark or "",
            ])
        output = export_to_excel(headers, rows, "考勤记录")
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=attendance.xlsx"})
