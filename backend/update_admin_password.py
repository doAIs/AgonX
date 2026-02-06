"""
更新管理员密码的脚本
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_engine

async def update_password():
    """更新admin用户的密码哈希"""
    # 正确的 admin123 的 bcrypt 哈希
    new_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    async with async_engine.begin() as conn:
        # 更新密码
        await conn.execute(
            text("UPDATE users SET hashed_password = :hash WHERE username = 'admin'"),
            {"hash": new_hash}
        )
        
        # 验证更新
        result = await conn.execute(
            text("SELECT username, SUBSTRING(hashed_password, 1, 30) as hash_preview FROM users WHERE username = 'admin'")
        )
        row = result.fetchone()
        
        if row:
            print(f"✅ 密码更新成功！")
            print(f"用户名: {row[0]}")
            print(f"哈希预览: {row[1]}...")
        else:
            print("❌ 未找到 admin 用户")

if __name__ == "__main__":
    print("正在更新 admin 用户密码...")
    asyncio.run(update_password())
    print("\n完成！现在可以使用密码 'admin123' 登录了。")
