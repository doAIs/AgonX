"""
测试 Embedding 模型加载
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

print("=" * 60)
print("Embedding 模型配置测试")
print("=" * 60)

print(f"\n配置信息:")
print(f"  模型路径: {settings.EMBEDDING_MODEL}")
print(f"  设备: {settings.EMBEDDING_DEVICE}")
print(f"  缓存目录: {settings.EMBEDDING_CACHE_FOLDER}")
print(f"  向量维度: {settings.EMBEDDING_DIMENSION}")

# 检查路径是否存在
import os
model_path = settings.EMBEDDING_MODEL
print(f"\n路径检查:")
print(f"  模型路径: {model_path}")
print(f"  路径存在: {os.path.exists(model_path)}")

if os.path.exists(model_path):
    print(f"  是目录: {os.path.isdir(model_path)}")
    if os.path.isdir(model_path):
        files = os.listdir(model_path)
        print(f"  目录内容: {files[:10]}...")  # 只显示前10个

# 尝试加载模型
print(f"\n模型加载测试:")
try:
    from sentence_transformers import SentenceTransformer
    
    print(f"  正在加载模型...")
    if os.path.exists(model_path):
        model = SentenceTransformer(model_path, device=settings.EMBEDDING_DEVICE)
    else:
        model = SentenceTransformer(
            model_path, 
            device=settings.EMBEDDING_DEVICE,
            cache_folder=settings.EMBEDDING_CACHE_FOLDER
        )
    
    print(f"  ✓ 模型加载成功")
    
    # 测试编码
    test_texts = [
        "这是一个测试句子",
        "This is a tests sentence",
        "AgonX is a multi-agent platform"
    ]
    
    print(f"\n编码测试:")
    for text in test_texts:
        vector = model.encode(text, normalize_embeddings=True)
        print(f"  '{text[:30]}...' -> 向量维度: {len(vector)}, 前5个值: {vector[:5]}")
    
    print(f"\n✅ 所有测试通过！模型可以正常工作。")
    
except Exception as e:
    print(f"  ✗ 模型加载失败: {str(e)}")
    import traceback
    traceback.print_exc()
    print(f"\n❌ 测试失败，请检查模型路径和依赖。")
