"""
教师管理系统 全面功能测试 (Phase 1 + Phase 2)
"""
import io
import sys
import json
import http.client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "localhost:8000"
passed = 0
failed = 0


class APIClient:
    def __init__(self):
        self.conn = http.client.HTTPConnection(BASE)
        self.token = None
        self.user_id = None
        self.user_role = None

    def login(self, tid: str, pw: str):
        r = self._json("POST", "/api/v1/auth/login", {"teacher_id": tid, "password": pw}, auth=False)
        if r.get("code") == 200:
            self.token = r["data"]["access_token"]
            self.user_id = r["data"]["teacher_id"]
            self.user_role = r["data"]["role"]
        return r

    def _json(self, method, path, body=None, auth=True):
        headers = {"Content-Type": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body_bytes = json.dumps(body).encode() if body else None
        self.conn.request(method, path, body=body_bytes, headers=headers)
        resp = self.conn.getresponse()
        ct = resp.getheader("Content-Type", "")
        data = resp.read()
        if "application/json" in ct:
            return json.loads(data.decode())
        return {"_binary_size": len(data), "_ct": ct}

    def _upload(self, path, filename, content, content_type, file_type="attachment"):
        boundary = "----Boundary7MA4YWxkTr"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        self.conn.request("POST", f"/api/v1/files/upload?file_type={file_type}", body=body, headers=headers)
        resp = self.conn.getresponse()
        return json.loads(resp.read().decode())

    def get(self, p, auth=True): return self._json("GET", p, auth=auth)
    def post(self, p, b=None, auth=True): return self._json("POST", p, b, auth=auth)
    def put(self, p, b=None, auth=True): return self._json("PUT", p, b, auth=auth)
    def delete(self, p, auth=True): return self._json("DELETE", p, auth=auth)


def ok(r, msg=""):
    global passed, failed
    if r.get("code") == 200:
        passed += 1
        print(f"  [PASS] {msg}")
    else:
        failed += 1
        print(f"  [FAIL] {msg} => code={r.get('code')} {r.get('message','')[:60]}")

def fail(r, msg="", expected=None):
    global passed, failed
    code = r.get("code", 0)
    if code != 200:
        if expected and code != expected:
            print(f"  [FAIL] {msg} => expected code={expected}, got {code}")
            failed += 1
        else:
            passed += 1
            print(f"  [PASS] {msg}")
    else:
        failed += 1
        print(f"  [FAIL] {msg} => should have failed")

def check(condition, msg=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {msg}")
    else:
        failed += 1
        print(f"  [FAIL] {msg}")

def binary_ok(r, msg="", min_size=100):
    global passed, failed
    sz = r.get("_binary_size", 0)
    if sz > min_size:
        passed += 1
        print(f"  [PASS] {msg} ({sz} bytes)")
    else:
        failed += 1
        print(f"  [FAIL] {msg} => size={sz}")


# ============================================================
def run_tests():
    global passed, failed
    c = APIClient()

    # ==================== 1. 认证模块 ====================
    print("\n" + "=" * 50)
    print("  1. 认证模块 /auth")
    print("=" * 50)

    r = c.login("32605001", "admin123")
    ok(r, "正确密码登录")
    check(r.get("data", {}).get("role") == "admin", "  角色为admin")
    check(r.get("data", {}).get("teacher_id") == "32605001", "  工号正确")

    fail(c.login("32605001", "wrongPassword"), "错误密码被拒", expected=401)
    fail(c.login("99999999", "admin123"), "不存在账号被拒", expected=401)
    fail(c._json("POST", "/api/v1/auth/login", {"teacher_id": "", "password": "123456"}, auth=False), "空用户名被拒")
    ok(c.get("/api/v1/auth/captcha", auth=False), "获取验证码")
    ok(c._json("POST", "/api/v1/auth/forgot-password", {"teacher_id": "32605001"}, auth=False), "找回密码第一步")

    r = c.put("/api/v1/auth/password", {"old_password": "admin123", "new_password": "newPwd123"})
    ok(r, "修改密码")
    r = c.put("/api/v1/auth/password", {"old_password": "newPwd123", "new_password": "admin123"})
    ok(r, "改回原密码")

    fail(c._json("POST", "/api/v1/auth/refresh", {"refresh_token": "invalid_token"}), "无效刷新令牌被拒", expected=401)

    # ==================== 2. 权限与异常 ====================
    print("\n" + "=" * 50)
    print("  2. 权限与异常处理")
    print("=" * 50)

    fail(c.get("/api/v1/teachers", auth=False), "未登录访问被拒", expected=401)

    old = c.token
    c.token = "invalid_token_xxxxxx"
    fail(c.get("/api/v1/teachers"), "无效Token被拒", expected=401)
    c.token = old

    # 重新登录(上面改了密码要重新登录)
    c.login("32605001", "admin123")

    fail(c.get("/api/v1/teachers/88888888"), "不存在教师返回404", expected=404)

    r = c._json("GET", "/api/v1/nonexistent", auth=False)
    check(r.get("code") != 200, "不存在路径返回错误")

    r = c._json("POST", "/api/v1/teachers", {}, auth=True)
    check(r.get("code") != 200, "空body创建教师被拒")

    # ==================== 3. 教师管理 ====================
    print("\n" + "=" * 50)
    print("  3. 教师管理 /teachers")
    print("=" * 50)

    r = c.get("/api/v1/teachers?page=1&page_size=10")
    ok(r, "教师列表查询")
    check(r.get("data", {}).get("total", 0) >= 1, "  至少1名教师")

    r = c.get("/api/v1/teachers/32605001")
    ok(r, "管理员详情")
    check(r.get("data", {}).get("name") == "系统管理员", "  姓名正确")

    r = c.post("/api/v1/teachers", {
        "name": "关羽", "role_code": 1, "gender": 1, "phone": "13900000001",
        "department": "教学中心", "title": "高级讲师",
        "password": "guanyu123",
        "question1": "父", "answer1": "关父",
        "question2": "母", "answer2": "关母",
        "question3": "地", "answer3": "河东",
    })
    ok(r, "新增教师关羽")
    guanyu_id = r.get("data", {}).get("teacher_id")

    r = c.get(f"/api/v1/teachers/{guanyu_id}")
    ok(r, "查看关羽详情")
    check(r.get("data", {}).get("name") == "关羽", "  姓名正确")

    r = c.put(f"/api/v1/teachers/{guanyu_id}", {"phone": "13900000002", "remark": "测试"})
    ok(r, "更新教师信息")

    r = c.post("/api/v1/teachers", {
        "name": "张飞", "role_code": 2, "gender": 1, "phone": "13900000003",
        "department": "行政中心", "title": "主任",
        "password": "zhangfei123",
        "question1": "q", "answer1": "a",
        "question2": "q", "answer2": "a",
        "question3": "q", "answer3": "a",
    })
    ok(r, "新增教师张飞(领导)")
    zhangfei_id = r.get("data", {}).get("teacher_id")

    r = c.get("/api/v1/teachers?page=1&page_size=10")
    ok(r, "列表含3名教师")
    check(r.get("data", {}).get("total", 0) >= 3, "  total>=3")

    r = c.delete(f"/api/v1/teachers/{guanyu_id}")
    ok(r, "软删除关羽")

    fail(c.get(f"/api/v1/teachers/{guanyu_id}"), "已删除教师查不到", expected=404)

    # ==================== 4. 文件上传 ====================
    print("\n" + "=" * 50)
    print("  4. 文件上传 /files")
    print("=" * 50)

    r = c._upload("/api/v1/files/upload", "doc.pdf", b"%PDF-1.4 fake pdf", "application/pdf", "attachment")
    ok(r, "上传PDF附件")

    r = c._upload("/api/v1/files/upload", "photo.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF", "image/jpeg", "avatar")
    ok(r, "上传JPG头像")

    r = c._upload("/api/v1/files/upload", "virus.exe", b"malware", "application/x-msdownload", "attachment")
    fail(r, "拒绝EXE文件")

    r = c._upload("/api/v1/files/upload", "noext", b"data", "application/octet-stream", "attachment")
    fail(r, "拒绝无扩展名文件")

    # ==================== 5. 课程管理 ====================
    print("\n" + "=" * 50)
    print("  5. 课程管理 /courses")
    print("=" * 50)

    r = c.post("/api/v1/courses", {
        "teacher_id": "32605001", "course_name": "Python数据分析",
        "semester": "2025-2026-2", "schedule_info": "周一1-2节", "location": "302机房",
    })
    ok(r, "创建课程1")
    course1_id = (r.get("data") or {}).get("id") if r.get("code") == 200 else None

    r = c.post("/api/v1/courses", {
        "teacher_id": "32605001", "course_name": "冲突课程",
        "semester": "2025-2026-2", "schedule_info": "周一1-2节",
    })
    fail(r, "同时段冲突检测", expected=409)

    r = c.post("/api/v1/courses", {
        "teacher_id": "32605001", "course_name": "机器学习实战",
        "semester": "2025-2026-2", "schedule_info": "周三5-6节", "location": "401机房",
    })
    ok(r, "不同时段创建成功")
    course2_id = (r.get("data") or {}).get("id") if r.get("code") == 200 else None

    r = c.get("/api/v1/courses")
    ok(r, "课程列表")
    check(len(r.get("data", {}).get("items", [])) >= 2, "  至少2门课程")

    if course1_id:
        r = c.put(f"/api/v1/courses/{course1_id}", {"location": "301机房"})
        ok(r, "更新课程")
        r = c.get(f"/api/v1/courses/{course1_id}")
        ok(r, "查看课程详情")
    else:
        check(False, "更新课程(无ID)")
        check(False, "查看课程详情(无ID)")

    if course2_id:
        r = c.delete(f"/api/v1/courses/{course2_id}")
        ok(r, "删除课程")
    else:
        check(False, "删除课程(无ID)")

    # ==================== 6. 事务管理 ====================
    print("\n" + "=" * 50)
    print("  6. 事务管理 /affairs")
    print("=" * 50)

    r = c.post("/api/v1/affairs", {
        "affair_type": 1, "title": "事假申请",
        "content": "家里有急事", "start_time": "2026-06-05", "end_time": "2026-06-06",
        "urgency": 1,
    })
    ok(r, "创建事假草稿")
    affair1_id = r.get("data", {}).get("id")

    r = c.put(f"/api/v1/affairs/{affair1_id}", {"content": "家里有急事需要处理，请假两天"})
    ok(r, "修改草稿")

    r = c.post(f"/api/v1/affairs/{affair1_id}/submit")
    ok(r, "提交审批")

    fail(c.post(f"/api/v1/affairs/{affair1_id}/submit"), "重复提交被拒")

    r = c.post(f"/api/v1/affairs/{affair1_id}/approve", {"approved": True, "comment": "批准"})
    ok(r, "审批通过")

    r = c.post("/api/v1/affairs", {
        "affair_type": 3, "title": "调课申请",
        "content": "课程对调", "start_time": "2026-06-10", "end_time": "2026-06-11",
    })
    ok(r, "创建调课草稿")
    affair2_id = r.get("data", {}).get("id")

    r = c.post(f"/api/v1/affairs/{affair2_id}/submit")
    ok(r, "提交调课")

    r = c.post(f"/api/v1/affairs/{affair2_id}/approve", {"approved": False, "comment": "理由不充分"})
    ok(r, "审批驳回")

    r = c.get("/api/v1/affairs")
    ok(r, "事务列表")
    check(len(r.get("data", {}).get("items", [])) >= 2, "  至少2条事务")

    r = c.get("/api/v1/affairs?status=3")
    ok(r, "按状态筛选(已通过)")

    fail(c.put(f"/api/v1/affairs/{affair1_id}", {"title": "修改已审批"}), "已审批不可修改")

    r = c.post("/api/v1/affairs", {"affair_type": 6, "title": "反馈", "content": "测试"})
    draft_id = r.get("data", {}).get("id")
    r = c.delete(f"/api/v1/affairs/{draft_id}")
    ok(r, "删除草稿")

    # ==================== 7. 考勤打卡 ====================
    print("\n" + "=" * 50)
    print("  7. 考勤打卡 /attendance")
    print("=" * 50)

    r = c.post("/api/v1/attendance/check-in")
    ok(r, "上班打卡")
    check(r.get("data", {}).get("status") in (1, 2), "  状态为正常或迟到")

    fail(c.post("/api/v1/attendance/check-in"), "重复打卡被拒")

    r = c.post("/api/v1/attendance/check-out")
    ok(r, "下班签退")

    fail(c.post("/api/v1/attendance/check-out"), "重复签退被拒")

    r = c.get("/api/v1/attendance")
    ok(r, "打卡记录列表")
    check(len(r.get("data", {}).get("items", [])) >= 1, "  至少1条记录")

    # ==================== 8. 消息通知 ====================
    print("\n" + "=" * 50)
    print("  8. 消息通知 /notifications")
    print("=" * 50)

    r = c.get("/api/v1/notifications")
    ok(r, "通知列表")

    r = c.get("/api/v1/notifications/unread-count")
    ok(r, "未读计数")
    check("count" in r.get("data", {}), "  包含count字段")

    # ==================== 9. 操作日志 ====================
    print("\n" + "=" * 50)
    print("  9. 操作日志 /logs")
    print("=" * 50)

    r = c.get("/api/v1/logs?page=1&page_size=100")
    ok(r, "管理员查看日志")
    total_logs = r.get("data", {}).get("total", 0)
    check(total_logs > 0, f"  有操作日志({total_logs}条)")

    # 检查日志类型覆盖
    items = r.get("data", {}).get("items", [])
    actions = " ".join(i.get("action", "") for i in items)
    check("POST" in actions, "  包含POST日志")
    check("PUT" in actions or "PUT" in actions, "  包含PUT日志")
    check("DELETE" in actions or "DELETE" in actions, "  包含DELETE日志")

    # ==================== 10. 报表导出 ====================
    print("\n" + "=" * 50)
    print("  10. 报表导出 /reports")
    print("=" * 50)

    r = c._json("GET", "/api/v1/reports/teachers/export")
    binary_ok(r, "导出教师Excel", min_size=500)

    r = c._json("GET", "/api/v1/reports/attendance/export")
    binary_ok(r, "导出考勤Excel", min_size=500)

    # ==================== 11. 边界与安全 ====================
    print("\n" + "=" * 50)
    print("  11. 边界与安全测试")
    print("=" * 50)

    r = c.login("' OR '1'='1", "admin123")
    check(r.get("code") != 200, "SQL注入登录被拒")

    r = c.post("/api/v1/courses", {"teacher_id": "32605001", "course_name": "A" * 200, "semester": "2025-2026-2"})
    fail(r, "超长课程名被拒")

    r = c.get("/api/v1/teachers?page=1&page_size=999")
    fail(r, "超限page_size被拒")

    r = c.get("/api/v1/teachers?page=-1&page_size=10")
    fail(r, "负数页码被拒")

    r = c.post("/api/v1/teachers", {"name": "X" * 50, "role_code": 99})
    fail(r, "非法role_code被拒")

    r = c.post("/api/v1/affairs", {"affair_type": 99, "title": "test"})
    fail(r, "非法affair_type被拒")

    # ==================== 12. 多角色权限验证 ====================
    print("\n" + "=" * 50)
    print("  12. 多角色权限验证")
    print("=" * 50)

    # 用张飞账号登录(role=leader)
    zhangfei = APIClient()
    r = zhangfei.login(zhangfei_id, "zhangfei123")
    ok(r, "张飞(领导)登录")
    check(r.get("data", {}).get("role") in ("leader",), "  角色为领导")

    r = zhangfei.get("/api/v1/teachers")
    ok(r, "  领导可查看教师列表")

    r = zhangfei.get("/api/v1/logs")
    fail(r, "  领导不可查看日志", expected=403)

    r = zhangfei.delete("/api/v1/teachers/32605001")
    fail(r, "  领导不可删除用户", expected=403)

    # 创建一个新事务供领导审批
    r = c.post("/api/v1/affairs", {"affair_type": 6, "title": "需要审批的反馈", "content": "测试"})
    new_affair_id = r.get("data", {}).get("id")
    c.post(f"/api/v1/affairs/{new_affair_id}/submit")
    r = zhangfei.post(f"/api/v1/affairs/{new_affair_id}/approve", {"approved": True})
    ok(r, "  领导可审批事务")

    # 创建普通教师账号测试
    r = c.post("/api/v1/teachers", {
        "name": "赵云", "role_code": 1, "gender": 1, "phone": "13900000005",
        "password": "zhaoyun123",
        "question1": "q", "answer1": "a",
        "question2": "q", "answer2": "a",
        "question3": "q", "answer3": "a",
    })
    zhaoyun_id = r.get("data", {}).get("teacher_id")

    zhaoyun = APIClient()
    r = zhaoyun.login(zhaoyun_id, "zhaoyun123")
    ok(r, "赵云(普通教师)登录")
    check(r.get("data", {}).get("role") == "teacher", "  角色为teacher")

    r = zhaoyun.get("/api/v1/teachers")
    fail(r, "  普通教师不可查看列表", expected=403)

    r = zhaoyun.get(f"/api/v1/teachers/{zhaoyun_id}")
    ok(r, "  普通教师可查看自己")

    r = zhaoyun.get("/api/v1/courses")
    ok(r, "  可查看自己的课程")

    r = zhaoyun.post("/api/v1/courses", {"teacher_id": zhaoyun_id, "course_name": "test", "semester": "2026-1"})
    fail(r, "  不可创建课程", expected=403)

    # cleanup: 软删除测试教师
    c.delete(f"/api/v1/teachers/{zhaoyun_id}")

    # ==================== 汇总 ====================
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"  结果: {passed} 通过 / {failed} 失败 / {total} 总计")
    if failed == 0:
        print("  状态: [ 全部通过! ]")
    else:
        print(f"  状态: [ {failed} 项失败 ]")
    print("=" * 60 + "\n")
    return passed, failed


if __name__ == "__main__":
    p, f = run_tests()
    if f > 0:
        sys.exit(1)
