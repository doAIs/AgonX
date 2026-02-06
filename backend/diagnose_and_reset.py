import pymysql
from passlib.context import CryptContext
import sys

# 1. 初始化加密上下文 (与 app/core/security.py 保持一致)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'agonx',
    'password': 'agonx_password',
    'database': 'agonx',
    'charset': 'utf8mb4'
}

def diagnose():
    print("=== AgonX 登录诊断与重置 ===")
    
    # 检查环境
    try:
        import bcrypt
        print(f"[*] bcrypt 版本: {getattr(bcrypt, '__version__', '未知')}")
    except ImportError:
        print("[!] 错误: 未安装 bcrypt 库")
        return

    # 生成当前环境下的哈希
    password = "admin123"
    new_hash = pwd_context.hash(password)
    print(f"[*] 为 '{password}' 生成的新哈希: {new_hash}")
    
    # 验证生成的哈希
    if pwd_context.verify(password, new_hash):
        print("[*] 自检验证: 成功")
    else:
        print("[!] 自检验证: 失败 (加密逻辑异常)")
        return

    # 写入数据库
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 先查一下当前的
            cursor.execute("SELECT hashed_password FROM users WHERE username = 'admin'")
            row = cursor.fetchone()
            if row:
                print(f"[*] 数据库当前哈希: {row[0][:20]}...")
            else:
                print("[!] 警告: 数据库中不存在 admin 用户，将尝试创建")
                cursor.execute(
                    "INSERT INTO users (username, email, hashed_password, is_superuser) VALUES (%s, %s, %s, %s)",
                    ('admin', 'admin@agonx.com', new_hash, True)
                )
                conn.commit()
                print("[*] 默认管理员创建成功")
                return

            # 更新哈希
            cursor.execute(
                "UPDATE users SET hashed_password = %s WHERE username = 'admin'",
                (new_hash,)
            )
            conn.commit()
            print("[*] 数据库哈希已强制重置")
            
        conn.close()
        print("\n✅ 重置完成！请重启后端并尝试登录。")
        print("   用户名: admin")
        print("   密  码: admin123")
        
    except Exception as e:
        print(f"[!] 数据库操作失败: {e}")

if __name__ == "__main__":
    diagnose()
