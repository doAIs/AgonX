"""
Milvus 连接测试脚本
"""
import sys
from pathlib import Path

from backend.app.core.config import settings

sys.path.insert(0, str(Path(__file__).parent.parent))

# from app.core.config import settings

print("=" * 60)
print("Milvus 连接诊断")
print("=" * 60)

print(f"\n配置信息:")
print(f"  主机: {settings.MILVUS_HOST}")
print(f"  端口: {settings.MILVUS_PORT}")
print(f"  用户: {settings.MILVUS_USER}")
print(f"  密码: {'已设置' if settings.MILVUS_PASSWORD else '未设置'}")

print(f"\n尝试连接...")

try:
    from pymilvus import connections, utility

    # 尝试连接
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        user=settings.MILVUS_USER or None,
        password=settings.MILVUS_PASSWORD or None
    )
    
    print(f"  ✓ 连接成功!")
    
    # 获取服务器版本
    version = utility.get_server_version()
    print(f"  ✓ Milvus 版本: {version}")
    
    # 获取集合列表
    collections = utility.list_collections()
    print(f"  ✓ 现有集合数: {len(collections)}")
    
    if collections:
        print(f"\n  集合列表:")
        for coll in collections[:5]:
            print(f"    - {coll}")
    
    # 断开连接
    connections.disconnect("default")
    print(f"\n✅ Milvus 连接测试通过!")
    
except Exception as e:
    print(f"\n  ✗ 连接失败: {str(e)}")
    print(f"\n❌ 连接测试失败")
    
    print(f"\n可能的原因:")
    print(f"  1. Docker 容器未启动 - 运行: docker-compose ps")
    print(f"  2. 端口映射错误 - 检查 docker-compose.yml")
    print(f"  3. 防火墙阻止 - 检查 Windows 防火墙设置")
    print(f"  4. 配置错误 - 检查 config.yaml 中的 milvus 配置")
    
    import traceback
    print(f"\n详细错误:")
    traceback.print_exc()
