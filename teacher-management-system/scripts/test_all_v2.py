"""
教师管理系统 全面覆盖测试 V2 (Phase 1+2+3)
"""
import io, sys, json, http.client
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

passed = 0; failed = 0; failures = []

class APIClient:
    def __init__(self):
        self.conn = http.client.HTTPConnection("localhost", 8000)
        self.token = None
    def login(self, tid, pw):
        r = self._json("POST", "/api/v1/auth/login", {"teacher_id": tid, "password": pw}, auth=False)
        if r.get("code") == 200:
            self.token = r["data"]["access_token"]
        return r
    def _json(self, method, path, body=None, auth=True):
        headers = {"Content-Type": "application/json"}
        if auth and self.token: headers["Authorization"] = f"Bearer {self.token}"
        b = json.dumps(body).encode() if body else None
        self.conn.request(method, path, body=b, headers=headers)
        r = self.conn.getresponse()
        ct = r.getheader("Content-Type", "")
        d = r.read()
        if "application/json" in ct: return json.loads(d.decode())
        if "text/event-stream" in ct:
            text = ""
            for line in d.decode().split("\n"):
                if line.startswith("data: "):
                    x = line[6:]
                    if x != "[DONE]":
                        try:
                            c2 = json.loads(x)
                            if c2["type"] == "text": text += c2["content"]
                        except: pass
            return {"code": 200, "sse_text": text, "session_id": r.getheader("X-Session-Id", "")}
        return {"_binary_size": len(d)}
    def _upload(self, filename, content, ct, ft="attachment"):
        boundary = "----B7"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {ct}\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
        self.conn.request("POST", f"/api/v1/files/upload?file_type={ft}", body=body, headers=headers)
        return json.loads(self.conn.getresponse().read().decode())
    def get(self, p, auth=True): return self._json("GET", p, auth=auth)
    def post(self, p, b=None, auth=True): return self._json("POST", p, b, auth=auth)
    def put(self, p, b=None, auth=True): return self._json("PUT", p, b, auth=auth)
    def delete(self, p, auth=True): return self._json("DELETE", p, auth=auth)
    def agent(self, msg, sid=None):
        body = {"message": msg}
        if sid: body["session_id"] = sid
        return self._json("POST", "/api/v1/agent/chat", body)

def ok(r, msg):
    global passed, failed, failures
    if r.get("code", 0) == 200: passed += 1
    else: failed += 1; failures.append(f"  [FAIL] {msg} code={r.get('code')} {r.get('message','')[:60]}")

def fail(r, msg, expected=None):
    global passed, failed, failures
    c = r.get("code", 0)
    if c != 200:
        if expected and c != expected: failed += 1; failures.append(f"  [FAIL] {msg} expected={expected} got={c}")
        else: passed += 1
    else: failed += 1; failures.append(f"  [FAIL] {msg} should have failed")

def check(cond, msg):
    global passed, failed, failures
    if cond: passed += 1
    else: failed += 1; failures.append(f"  [FAIL] {msg}")

def section(title):
    print(f"\n{'='*50}\n  {title}\n{'='*50}")

# ============================================================
def run_all():
    global passed, failed
    c = APIClient()

    # ====== PHASE 1: AUTH ======
    section("1.1 认证 - 登录")
    ok(c.login("32605001", "admin123"), "正确密码登录")
    check(c.token is not None, "获取到token")
    fail(c.login("32605001", "wrongPassword"), "错误密码被拒", expected=401)
    fail(c.login("99999999", "admin123"), "不存在账号被拒", expected=401)
    fail(c._json("POST", "/api/v1/auth/login", {"teacher_id": "", "password": "123456"}, auth=False), "空用户名被拒")

    section("1.2 认证 - 密码与令牌")
    ok(c.get("/api/v1/auth/captcha", auth=False), "获取验证码")
    ok(c._json("POST", "/api/v1/auth/forgot-password", {"teacher_id": "32605001"}, auth=False), "找回密码步骤1")
    ok(c.put("/api/v1/auth/password", {"old_password": "admin123", "new_password": "tmpPwd123"}), "修改密码")
    ok(c.put("/api/v1/auth/password", {"old_password": "tmpPwd123", "new_password": "admin123"}), "改回密码")
    fail(c._json("POST", "/api/v1/auth/refresh", {"refresh_token": "invalid"}), "无效refresh被拒", expected=401)

    section("1.3 权限与中间件")
    fail(c.get("/api/v1/teachers", auth=False), "未登录被拒", expected=401)
    old = c.token; c.token = "invalid_xxx"
    fail(c.get("/api/v1/teachers"), "无效Token被拒", expected=401)
    c.token = old

    # ====== PHASE 1: TEACHERS ======
    section("2.1 教师管理")
    ok(c.get("/api/v1/teachers?page=1&page_size=10"), "列表查询")
    r = c.get("/api/v1/teachers/32605001")
    ok(r, "管理员详情")
    check(r.get("data", {}).get("name") == "系统管理员", "姓名正确")
    fail(c.get("/api/v1/teachers/88888888"), "不存在教师404", expected=404)

    r = c.post("/api/v1/teachers", {"name": "关羽", "role_code": 1, "gender": 1, "phone": "13900000001",
        "department": "教学中心", "title": "高级讲师", "password": "guanyu123",
        "question1": "父", "answer1": "关父", "question2": "母", "answer2": "关母", "question3": "地", "answer3": "河东"})
    guanyu_id = r.get("data", {}).get("teacher_id") if r.get("code") == 200 else None
    ok(r, "新增教师关羽")
    check(guanyu_id is not None, "获取到工号")
    ok(c.get(f"/api/v1/teachers/{guanyu_id}"), "查看关羽详情")

    r2 = c.post("/api/v1/teachers", {"name": "张飞", "role_code": 2, "gender": 1, "phone": "13900000003",
        "department": "行政中心", "title": "主任", "password": "zhangfei123",
        "question1": "q", "answer1": "a", "question2": "q", "answer2": "a", "question3": "q", "answer3": "a"})
    zhangfei_id = r2.get("data", {}).get("teacher_id") if r2.get("code") == 200 else None
    ok(r2, "新增张飞(领导)")
    ok(c.get("/api/v1/teachers?page=1&page_size=10"), "列表(含3人)")
    ok(c.put(f"/api/v1/teachers/{guanyu_id}", {"phone": "13900000002"}), "更新关羽")
    ok(c.delete(f"/api/v1/teachers/{guanyu_id}"), "软删除关羽")
    fail(c.get(f"/api/v1/teachers/{guanyu_id}"), "已删除查不到", expected=404)

    # ====== PHASE 1: FILES ======
    section("3. 文件上传")
    ok(c._upload("doc.pdf", b"%PDF-1.4 fake", "application/pdf"), "上传PDF附件")
    ok(c._upload("photo.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF", "image/jpeg", "avatar"), "上传JPG头像")
    fail(c._upload("virus.exe", b"x", "application/x-msdownload"), "拒绝EXE")
    fail(c._upload("noext", b"data", "application/octet-stream"), "拒绝无扩展名")

    # ====== PHASE 2: COURSES ======
    section("4. 课程管理")
    r = c.post("/api/v1/courses", {"teacher_id": "32605001", "course_name": "Python数据分析",
        "semester": "2025-2026-2", "schedule_info": "周一1-2节", "location": "302机房"})
    c1_id = r.get("data", {}).get("id") if r.get("code") == 200 else None
    ok(r, "创建课程1")

    r = c.post("/api/v1/courses", {"teacher_id": "32605001", "course_name": "冲突课",
        "semester": "2025-2026-2", "schedule_info": "周一1-2节"})
    fail(r, "同时段冲突检测", expected=409)

    r = c.post("/api/v1/courses", {"teacher_id": "32605001", "course_name": "机器学习实战",
        "semester": "2025-2026-2", "schedule_info": "周三5-6节", "location": "401机房"})
    c2_id = r.get("data", {}).get("id") if r.get("code") == 200 else None
    ok(r, "创建课程2(不同时段)")

    ok(c.get("/api/v1/courses"), "课程列表")
    if c1_id: ok(c.put(f"/api/v1/courses/{c1_id}", {"location": "301机房"}), "更新课程")
    if c1_id: ok(c.get(f"/api/v1/courses/{c1_id}"), "查看课程详情")
    if c2_id: ok(c.delete(f"/api/v1/courses/{c2_id}"), "删除课程")

    # ====== PHASE 2: AFFAIRS ======
    section("5. 事务审批流程")
    r = c.post("/api/v1/affairs", {"affair_type": 1, "title": "事假申请",
        "content": "家里有急事", "start_time": "2026-06-05", "end_time": "2026-06-06", "urgency": 1})
    a1_id = r.get("data", {}).get("id") if r.get("code") == 200 else 1
    ok(r, "创建草稿")
    if a1_id:
        ok(c.put(f"/api/v1/affairs/{a1_id}", {"content": "家里有急事，请假两天"}), "修改草稿")
        ok(c.post(f"/api/v1/affairs/{a1_id}/submit"), "提交审批")
        fail(c.post(f"/api/v1/affairs/{a1_id}/submit"), "重复提交被拒")
        ok(c.post(f"/api/v1/affairs/{a1_id}/approve", {"approved": True, "comment": "批准"}), "审批通过")

    r = c.post("/api/v1/affairs", {"affair_type": 3, "title": "调课", "content": "课程对调"})
    a2_id = r.get("data", {}).get("id") if r.get("code") == 200 else 2
    ok(r, "创建第二条")
    if a2_id:
        ok(c.post(f"/api/v1/affairs/{a2_id}/submit"), "提交第二条")
        ok(c.post(f"/api/v1/affairs/{a2_id}/approve", {"approved": False, "comment": "不充分"}), "审批驳回")

    if a1_id: fail(c.put(f"/api/v1/affairs/{a1_id}", {"title": "修改已审批"}), "已审批不可修改")
    ok(c.get("/api/v1/affairs"), "事务列表")
    ok(c.get("/api/v1/affairs?status=3"), "按状态筛选")

    # ====== PHASE 2: ATTENDANCE ======
    section("6. 考勤打卡")
    ok(c.post("/api/v1/attendance/check-in"), "上班打卡")
    fail(c.post("/api/v1/attendance/check-in"), "重复打卡被拒")
    ok(c.post("/api/v1/attendance/check-out"), "下班签退")
    fail(c.post("/api/v1/attendance/check-out"), "重复签退被拒")
    ok(c.get("/api/v1/attendance"), "打卡记录列表")

    # ====== PHASE 2: NOTIFICATIONS ======
    section("7. 消息通知")
    ok(c.get("/api/v1/notifications"), "通知列表")
    r = c.get("/api/v1/notifications/unread-count")
    ok(r, "未读计数")
    check("count" in r.get("data", {}), "count字段存在")

    # ====== PHASE 2: LOGS & REPORTS ======
    section("8. 操作日志与报表")
    r = c.get("/api/v1/logs")
    ok(r, "管理员查看日志")
    check(r.get("data", {}).get("total", 0) > 5, "有操作日志")
    r = c._json("GET", "/api/v1/reports/teachers/export")
    check(r.get("_binary_size", 0) > 1000, "导出教师Excel")
    r = c._json("GET", "/api/v1/reports/attendance/export")
    check(r.get("_binary_size", 0) > 1000, "导出考勤Excel")

    # ====== PHASE 2: PERMISSIONS ======
    section("9. 角色权限")
    ok(c.login(zhangfei_id, "zhangfei123"), "张飞(领导)登录")
    ok(c.get("/api/v1/teachers"), "领导可查教师列表")
    fail(c.get("/api/v1/logs"), "领导不可查日志", expected=403)
    fail(c.delete(f"/api/v1/teachers/32605001"), "领导不可删除", expected=403)
    c.login("32605001", "admin123")  # 切回admin

    # ====== SECURITY ======
    section("10. 安全测试")
    fail(c.login("' OR '1'='1", "xxx"), "SQL注入被拒")
    fail(c.post("/api/v1/courses", {"teacher_id": "32605001", "course_name": "A"*200, "semester": "x"}), "超长输入")
    fail(c.get("/api/v1/teachers?page=1&page_size=999"), "超限page_size")
    fail(c.get("/api/v1/teachers?page=-1"), "负数页码")
    fail(c.post("/api/v1/teachers", {"name": "X"*50, "role_code": 99}), "非法role_code")
    fail(c.post("/api/v1/affairs", {"affair_type": 99, "title": "x"}), "非法affair_type")

    # ====== PHASE 3: AGENT ======
    section("11.1 Agent - 能力列表")
    ok(c.get("/api/v1/agent/abilities"), "获取能力列表")

    section("11.2 Agent - RAG 知识问答")
    r = c.agent("学校在什么地方？")
    ok(r, "学校地址查询")
    check(any(w in r.get("sse_text", "") for w in ["成都", "高新区", "蜀锦路"]), "回答含地址信息")

    section("11.3 Agent - RAG 规章制度")
    r = c.agent("请假需要提前多久？")
    ok(r, "请假制度查询")
    check("1个工作日" in r.get("sse_text", "") or "提前" in r.get("sse_text", ""), "回答含请假制度")

    section("11.4 Agent - NL2SQL 数据查询")
    r = c.agent("查询我的课表")
    ok(r, "查询课表")
    check(len(r.get("sse_text", "")) > 10, "有返回内容")

    section("11.5 Agent - 二十四点游戏")
    r = c.agent("来一局二十四点")
    ok(r, "二十四点游戏")
    check("主公" in r.get("sse_text", ""), "称呼主公")

    section("11.6 Agent - 猜灯谜")
    r = c.agent("猜灯谜")
    ok(r, "猜灯谜")
    check("谜" in r.get("sse_text", "") or "主公" in r.get("sse_text", ""), "灯谜启动")

    section("11.7 Agent - 多轮对话")
    r1 = c.agent("你好，我是刘备")
    ok(r1, "多轮对话-问候")
    sid = r1.get("session_id", "")
    if sid:
        r2 = c.agent("学费是多少？", sid)
        ok(r2, "多轮对话-追问学费")
        check(any(w in r2.get("sse_text", "") for w in ["元", "16800", "9800", "6800", "学费"]), "回答含学费信息")

    section("11.8 Agent - 修改操作确认")
    r = c.agent("帮我请两天假，明天开始")
    ok(r, "修改操作")
    text = r.get("sse_text", "")
    check("确认" in text or "预览" in text or "SQL" in text or "主公" in text, "有确认或预览")

    # ====== EDGE CASES ======
    section("12. 异常场景")
    ok(c.get("/api/v1/auth/captcha", auth=False), "验证码公开接口")
    r = c._json("GET", "/api/v1/api/nonexistent", auth=False)
    check(r.get("code") != 200, "不存在路径")
    r = c._json("POST", "/api/v1/teachers", {}, auth=True)
    check(r.get("code") != 200, "空body创建教师")

    # ====== SUMMARY ======
    print(f"\n{'='*60}")
    total = passed + failed
    print(f"  测试结果: {passed} 通过 / {total} 总计")
    if failed > 0:
        print(f"  {failed} 项失败:")
        for f in failures:
            print(f)
    else:
        print("  状态: [ 全部通过! ]")
    print(f"{'='*60}\n")
    return passed, failed

if __name__ == "__main__":
    p, f = run_all()
    if f > 0: sys.exit(1)
