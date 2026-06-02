import asyncio
import io
import sys

# Windows 控制台 UTF-8 编码修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import get_settings
from app.core.security import hash_password
from app.utils.crypto import encrypt_sensitive_data
from app.db.models.teacher import TeacherInfo, UserAuth
from app.db.models.riddle import LanternRiddle
from app.db.session import Base

settings = get_settings()

RIDDLES = [
    {"riddle": "一口咬掉牛尾巴", "answer": "告", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "上边毛，下边毛，中间一颗黑葡萄", "answer": "眼睛", "hint": "打一器官", "source": "传统谜语"},
    {"riddle": "千条线，万条线，掉到水里看不见", "answer": "雨", "hint": "打一自然现象", "source": "传统谜语"},
    {"riddle": "有面没有口，有脚没有手，虽有四只脚，自己不会走", "answer": "桌子", "hint": "打一物品", "source": "传统谜语"},
    {"riddle": "一个小姑娘，坐在水中央，身穿粉红衫，坐在绿船上", "answer": "荷花", "hint": "打一植物", "source": "传统谜语"},
    {"riddle": "兄弟七八个，围着柱子坐，大家一分手，衣服就扯破", "answer": "蒜", "hint": "打一食物", "source": "传统谜语"},
    {"riddle": "白嫩小宝宝，洗澡吹泡泡，洗洗身体小，再洗不见了", "answer": "肥皂", "hint": "打一生活用品", "source": "传统谜语"},
    {"riddle": "身穿绿衣裳，肚里水汪汪，生的子儿多，个个黑脸膛", "answer": "西瓜", "hint": "打一水果", "source": "传统谜语"},
    {"riddle": "七十二小时", "answer": "晶", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "一家分两院，两院子孙多，多的倒比少的少，少的倒比多的多", "answer": "算盘", "hint": "打一工具", "source": "传统谜语"},
    {"riddle": "左看两点水，右看水两点，细看不是水，敲敲硬邦邦", "answer": "冰", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "一点一横长，一撇到南洋，南洋有个人，只有一寸长", "answer": "府", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "有心走不快，见水装不完，长草难收拾，遇食就可餐", "answer": "曼", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "四面都是山，山山都相连", "answer": "田", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "一只黑狗，不叫不吼", "answer": "默", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "半青半紫", "answer": "素", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "需要一半，留下一半", "answer": "雷", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "一加一不是二", "answer": "王", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "一根木棍，吊个方箱，一把梯子，搭在中央", "answer": "面", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "久雨初晴", "answer": "昨", "hint": "打一字", "source": "传统字谜"},
    {"riddle": "麻屋子，红帐子，里面住个白胖子", "answer": "花生", "hint": "打一食物", "source": "传统谜语"},
    {"riddle": "紫色树，开紫花，紫色果里盛芝麻", "answer": "茄子", "hint": "打一蔬菜", "source": "传统谜语"},
    {"riddle": "红口袋，绿口袋，有人怕，有人爱", "answer": "辣椒", "hint": "打一蔬菜", "source": "传统谜语"},
    {"riddle": "生根不落地，有叶不开花，街上有人卖，园里不种它", "answer": "豆芽", "hint": "打一蔬菜", "source": "传统谜语"},
    {"riddle": "黄金布，包银条，中间弯弯两头翘", "answer": "香蕉", "hint": "打一水果", "source": "传统谜语"},
    {"riddle": "远看像只猫，近看是只鸟，晚上捉老鼠，天亮睡大觉", "answer": "猫头鹰", "hint": "打一动物", "source": "传统谜语"},
    {"riddle": "耳朵长，尾巴短，红眼睛，白毛衫，三瓣嘴儿胆子小", "answer": "兔子", "hint": "打一动物", "source": "传统谜语"},
    {"riddle": "尖尖牙齿大盆嘴，短短腿儿长长尾，捕捉食物流眼泪，人人知它假慈悲", "answer": "鳄鱼", "hint": "打一动物", "source": "传统谜语"},
    {"riddle": "身披花棉袄，唱歌呱呱叫，田里捉害虫，丰收立功劳", "answer": "青蛙", "hint": "打一动物", "source": "传统谜语"},
    {"riddle": "有位老师不说话，满腹学问本事大，你要有字不认识，快去请教它", "answer": "字典", "hint": "打一学习用品", "source": "传统谜语"},
    {"riddle": "小小一间房，只有一扇窗，唱歌又演戏，天天翻花样", "answer": "电视机", "hint": "打一家电", "source": "传统谜语"},
    {"riddle": "屋子方方，有门没窗，屋外热烘，屋里冰霜", "answer": "冰箱", "hint": "打一家电", "source": "传统谜语"},
    {"riddle": "有头没有颈，身上冷冰冰，有翅不能飞，无脚也能行", "answer": "鱼", "hint": "打一动物", "source": "传统谜语"},
    {"riddle": "不是葱不是蒜，一层一层裹紫缎，说葱长得矮，像蒜不分瓣", "answer": "洋葱", "hint": "打一蔬菜", "source": "传统谜语"},
    {"riddle": "独木造高楼，没瓦没砖头，人在水下走，水在人上流", "answer": "雨伞", "hint": "打一生活用品", "source": "传统谜语"},
]


async def seed():
    engine = create_async_engine(settings.mysql_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(TeacherInfo).where(TeacherInfo.teacher_id == "32605001"))
        if result.scalar_one_or_none() is None:
            admin = TeacherInfo(
                teacher_id="32605001",
                name="系统管理员",
                gender=1,
                phone="13800000000",
                department="信息中心",
                title="管理员",
                status=1,
            )
            session.add(admin)

            auth = UserAuth(
                teacher_id="32605001",
                password_hash=hash_password("admin123"),
                question1_answer=encrypt_sensitive_data("诸葛亮"),
                question2_answer=encrypt_sensitive_data("三国演义"),
                question3_answer=encrypt_sensitive_data("卧龙"),
            )
            session.add(auth)
            print("[OK] Admin account created: 32605001 / admin123")

        count = 0
        for r in RIDDLES:
            existing = await session.execute(
                select(LanternRiddle).where(LanternRiddle.riddle == r["riddle"])
            )
            if existing.scalar_one_or_none() is None:
                session.add(LanternRiddle(**r))
                count += 1

        await session.commit()
        print(f"[OK] Riddles imported: {count} records")

    await engine.dispose()
    print("Seed data initialization complete!")


if __name__ == "__main__":
    asyncio.run(seed())
