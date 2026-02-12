import asyncio
from sqlalchemy import text

from backend.app.core.database import async_engine


async def check():
    try:
        async with async_engine.begin() as conn:
            res = await conn.execute(text('SELECT id, name, user_id FROM knowledge_bases'))
            rows = res.fetchall()
            print(f"找到 {len(rows)} 个知识库:")
            for row in rows:
                print(f"ID: {row[0]}, Name: {row[1]}, UserID: {row[2]}")
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    asyncio.run(check())
