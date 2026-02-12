"""
知识库功能诊断脚本
检查文档上传和向量化功能是否正常
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

async def check_dependencies():
    """检查必要的依赖"""
    print("=" * 60)
    print("1. 检查依赖")
    print("=" * 60)
    
    deps = {
        "sentence_transformers": False,
        "pymilvus": False,
        "minio": False,
        "langchain": False,
        "langchain_community": False,
    }
    
    for dep in deps:
        try:
            __import__(dep)
            deps[dep] = True
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} - 未安装")
    
    return all(deps.values())

async def check_embedding_model():
    """检查 Embedding 模型"""
    print("\n" + "=" * 60)
    print("2. 检查 Embedding 模型")
    print("=" * 60)
    
    try:
        from sentence_transformers import SentenceTransformer
        from app.core.config import settings
        
        model_name = settings.EMBEDDING_MODEL or 'BAAI/bge-m3'
        print(f"  模型名称: {model_name}")
        print(f"  正在加载模型...")
        
        model = SentenceTransformer(model_name, device='cpu')
        
        # 测试编码
        test_text = "这是一个测试句子"
        vector = model.encode(test_text, normalize_embeddings=True)
        
        print(f"  ✓ 模型加载成功")
        print(f"  ✓ 向量维度: {len(vector)}")
        print(f"  ✓ 测试编码成功")
        return True
        
    except Exception as e:
        print(f"  ✗ 模型加载失败: {str(e)}")
        return False

async def check_milvus():
    """检查 Milvus 连接"""
    print("\n" + "=" * 60)
    print("3. 检查 Milvus 连接")
    print("=" * 60)
    
    try:
        from pymilvus import connections, utility
        from app.core.config import settings
        
        print(f"  主机: {settings.MILVUS_HOST}")
        print(f"  端口: {settings.MILVUS_PORT}")
        
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            user=settings.MILVUS_USER or None,
            password=settings.MILVUS_PASSWORD or None
        )
        
        # 获取集合列表
        collections = utility.list_collections()
        print(f"  ✓ 连接成功")
        print(f"  ✓ 现有集合数: {len(collections)}")
        
        if collections:
            print(f"  集合列表: {', '.join(collections[:5])}")
        
        connections.disconnect("default")
        return True
        
    except Exception as e:
        print(f"  ✗ 连接失败: {str(e)}")
        return False

async def check_minio():
    """检查 MinIO 连接"""
    print("\n" + "=" * 60)
    print("4. 检查 MinIO 连接")
    print("=" * 60)
    
    try:
        from minio import Minio
        from app.core.config import settings
        
        endpoint = settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', '')
        print(f"  端点: {endpoint}")
        
        client = Minio(
            endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        # 检查 bucket
        bucket_name = "agonx-documents"
        if not client.bucket_exists(bucket_name):
            print(f"  ! Bucket '{bucket_name}' 不存在，将自动创建")
        else:
            print(f"  ✓ Bucket '{bucket_name}' 存在")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 连接失败: {str(e)}")
        return False

async def test_document_processing():
    """测试文档处理流程"""
    print("\n" + "=" * 60)
    print("5. 测试文档处理流程")
    print("=" * 60)
    
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from app.knowledge.retrieval import retrieval_service
        
        # 测试文本分块
        test_text = """
        这是一个测试文档。它包含多个句子。
        我们需要测试文档分块功能是否正常工作。
        这是第三段文字。
        """
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            length_function=len
        )
        
        chunks = text_splitter.split_text(test_text)
        print(f"  ✓ 文档分块成功: {len(chunks)} 个分块")
        
        # 测试向量化
        print(f"  正在测试向量化...")
        await retrieval_service.connect()
        
        texts = ["这是测试文本", "这是另一个测试"]
        metadatas = [{"test": "data"}, {"test": "data2"}]
        
        # 检查集合是否存在
        from pymilvus import utility
        test_collection = "test_collection"
        
        if utility.has_collection(test_collection):
            utility.drop_collection(test_collection)
        
        # 创建测试集合
        from pymilvus import FieldSchema, CollectionSchema, DataType
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512)
        ]
        
        schema = CollectionSchema(fields, "Test collection")
        collection = Collection(test_collection, schema)
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index("embedding", index_params)
        
        # 插入数据
        await retrieval_service.add_texts(test_collection, texts, metadatas)
        
        print(f"  ✓ 向量化和存储成功")
        
        # 清理
        utility.drop_collection(test_collection)
        
        return True
        
    except Exception as e:
        print(f"  ✗ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AgonX 知识库功能诊断")
    print("=" * 60)
    
    results = []
    
    # 检查依赖
    results.append(("依赖检查", await check_dependencies()))
    
    # 检查 Embedding 模型
    results.append(("Embedding 模型", await check_embedding_model()))
    
    # 检查 Milvus
    results.append(("Milvus 连接", await check_milvus()))
    
    # 检查 MinIO
    results.append(("MinIO 连接", await check_minio()))
    
    # 测试文档处理
    results.append(("文档处理流程", await test_document_processing()))
    
    # 总结
    print("\n" + "=" * 60)
    print("6. 诊断总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n✨ 所有检查通过！知识库功能应该正常工作。")
    else:
        print("\n⚠️ 部分检查失败，请根据上述信息修复问题。")
        print("\n常见解决方案：")
        print("  1. 安装缺失的依赖: pip install sentence-transformers")
        print("  2. 确保 Milvus 服务启动: docker-compose ps")
        print("  3. 确保 MinIO 服务启动: docker-compose ps")
        print("  4. 检查配置文件: backend/config.yaml")

if __name__ == "__main__":
    asyncio.run(main())
