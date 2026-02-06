"""
简单的密码更新脚本（不需要虚拟环境）
使用 pymysql 直接连接数据库
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'agonx',
    'password': 'agonx_password',
    'database': 'agonx',
    'charset': 'utf8mb4'
}

# 正确的 admin123 的 bcrypt 哈希
NEW_HASH = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

try:
    # 连接数据库
    print("正在连接数据库...")
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 更新密码
    print("正在更新 admin 用户密码...")
    cursor.execute(
        "UPDATE users SET hashed_password = %s WHERE username = 'admin'",
        (NEW_HASH,)
    )
    
    # 提交更改
    conn.commit()
    
    # 验证更新
    cursor.execute(
        "SELECT username, SUBSTRING(hashed_password, 1, 30) FROM users WHERE username = 'admin'"
    )
    result = cursor.fetchone()
    
    if result:
        print(f"\n✅ 密码更新成功！")
        print(f"用户名: {result[0]}")
        print(f"哈希预览: {result[1]}...")
        print(f"\n现在可以使用以下凭证登录：")
        print(f"  用户名: admin")
        print(f"  密码: admin123")
    else:
        print("❌ 未找到 admin 用户")
    
    # 关闭连接
    cursor.close()
    conn.close()
    print("\n✅ 完成！")
    
except pymysql.Error as e:
    print(f"❌ 数据库错误: {e}")
except Exception as e:
    print(f"❌ 错误: {e}")
