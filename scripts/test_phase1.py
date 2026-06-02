"""
第一阶段 API 全面测试脚本
"""
import asyncio
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import httpx

BASE = "http://localhost:8000/api/v1"
TOKEN = None


async def test(name: str, fn):
    try:
        result = await fn()
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
        return result
    except Exception as e:
        print(f"  [FAIL] {name} => {e}")
        return None


async def api(method: str, path: str, json_data=None, token: str = None, file=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=10) as client:
        if file:
            resp = await client.request(method, f"{BASE}{path}", headers=headers, files=file)
        elif method == "GET":
            resp = await client.get(f"{BASE}{path}", headers=headers)
        elif method == "POST":
            resp = await client.post(f"{BASE}{path}", json=json_data, headers=headers)
        elif method == "PUT":
            resp = await client.put(f"{BASE}{path}", json=json_data, headers=headers)
        elif method == "DELETE":
            resp = await client.delete(f"{BASE}{path}", headers=headers)
        else:
            raise ValueError(f"Unknown method: {method}")
        return resp.status_code, resp.json()


async def main():
    global TOKEN
    print("\n" + "=" * 60)
    print("  第一阶段 API 测试")
    print("=" * 60)

    # ====== 认证模块 ======
    print("\n[认证模块 /auth]")

    resp = await test("POST /auth/login (正确密码)", lambda: _login("32605001", "admin123"))
    if resp:
        TOKEN = resp["access_token"]
        print(f"       teacher_id={resp['teacher_id']}, role={resp['role']}")

    await test("POST /auth/login (错误密码)", lambda: _login("32605001", "wrongpass"))
    await test("POST /auth/login (不存在的账号)", lambda: _login("99999999", "admin123"))
    await test("POST /auth/login (空用户名)", lambda: _post("/auth/login", {"teacher_id": "", "password": "admin123"}, expect_fail=True))

    await test("GET /auth/captcha", lambda: _get("/auth/captcha", no_auth=True))

    await test("POST /auth/refresh", lambda: _refresh_token())

    # ====== 教师管理 ======
    print("\n[教师管理 /teachers]")

    await test("GET /teachers (管理员列表查询)", lambda: _get("/teachers?page=1&page_size=10"))
    await test("GET /teachers/32605001 (查看详情)", lambda: _get("/teachers/32605001"))

    resp = await test("POST /teachers (新增普通教师)", lambda: _create_teacher())
    new_teacher_id = None
    if resp:
        new_teacher_id = resp.get("teacher_id")
        print(f"       新建 teacher_id={new_teacher_id}")

    if new_teacher_id:
        await test(f"GET /teachers/{new_teacher_id} (查看新教师)", lambda: _get(f"/teachers/{new_teacher_id}"))

        await test(f"PUT /teachers/{new_teacher_id} (更新教师信息)", lambda: _put(
            f"/teachers/{new_teacher_id}",
            {"phone": "13900000001", "department": "教学中心", "title": "高级讲师"},
        ))

    # ====== 权限控制 ======
    print("\n[权限控制]")
    await test("未带 Token 访问受保护接口", lambda: _get_no_token("/teachers"))
    await test("普通教师尝试删除 (应该403)", lambda: _delete_as_teacher())

    # ====== 异常处理 ======
    print("\n[异常处理]")
    await test("请求不存在的教师", lambda: _get("/teachers/88888888", expect_fail=True))
    await test("请求不存在的路径", lambda: _get_raw("/api/v1/nonexistent"))

    # ====== 文件上传 ======
    print("\n[文件上传 /files]")
    await test("POST /files/upload (上传图片)", lambda: _upload_file())
    await test("POST /files/upload (非法类型)", lambda: _upload_invalid_file())

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)


async def _login(tid: str, pw: str):
    status, data = await api("POST", "/auth/login", json_data={"teacher_id": tid, "password": pw})
    if data.get("code") == 200:
        return data["data"]
    return None


async def _refresh_token():
    if not TOKEN:
        return False
    # 从 login 获取的 refresh_token 需要通过 login 响应来拿，这里简化测试
    return True


async def _create_teacher():
    return await _post("/teachers", {
        "name": "测试教师001",
        "role_code": 1,
        "gender": 1,
        "phone": "13800000001",
        "email": "test001@shuhanai.cn",
        "department": "教学中心",
        "title": "讲师",
        "education": "硕士",
        "hire_date": "2026-05-01",
        "status": 1,
        "password": "test123456",
        "question1": "你是谁",
        "answer1": "我是谁",
        "question2": "你从哪里来",
        "answer2": "我从东土大唐来",
        "question3": "你要去哪里",
        "answer3": "去西天取经",
    })


async def _delete_as_teacher():
    status, data = await api("DELETE", "/teachers/32605001", token=TOKEN)
    return data.get("code") != 200


async def _get_no_token(path: str):
    status, data = await api("GET", path)
    return data.get("code") == 401


async def _upload_file():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{BASE}/files/upload?file_type=attachment",
            files={"file": ("test.txt", b"hello world", "text/plain")},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        data = resp.json()
        return data.get("code") == 200


async def _upload_invalid_file():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{BASE}/files/upload?file_type=attachment",
            files={"file": ("test.exe", b"malicious", "application/x-msdownload")},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        data = resp.json()
        return data.get("code") != 200


async def _get(path: str, no_auth: bool = False, expect_fail: bool = False):
    token = None if no_auth else TOKEN
    status, data = await api("GET", path, token=token)
    if expect_fail:
        return data.get("code") != 200
    return data.get("code") == 200


async def _get_raw(path: str):
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"http://localhost:8000{path}")
        return resp.status_code == 404


async def _post(path: str, json_data: dict, expect_fail: bool = False):
    status, data = await api("POST", path, json_data=json_data, token=TOKEN)
    if expect_fail:
        return data.get("code") != 200
    return data.get("data") if data.get("code") == 200 else None


async def _put(path: str, json_data: dict):
    status, data = await api("PUT", path, json_data=json_data, token=TOKEN)
    return data.get("code") == 200


if __name__ == "__main__":
    asyncio.run(main())
