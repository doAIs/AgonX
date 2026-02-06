"""
生成密码哈希的辅助脚本
用于生成数据库初始化时需要的密码哈希值
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 生成 admin123 的哈希
password = "admin123"
hashed = pwd_context.hash(password)

print(f"密码: {password}")
print(f"哈希值: {hashed}")
print(f"\n验证测试: {pwd_context.verify(password, hashed)}")
