"""
知识库完整流程测试脚本
测试：文档上传 → 向量化 → 检索

使用方法：
1. 确保后端服务已启动
2. 准备测试文档（PDF/TXT/DOCX）
3. 运行：python test/test_knowledge_pipeline.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import requests
import json
from typing import Optional

# 配置
BASE_URL = "http://localhost:8080/api/v1"
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class KnowledgePipelineTester:
    """知识库流程测试器"""
    
    def __init__(self):
        self.token: Optional[str] = None
        self.kb_id: Optional[str] = None
        self.doc_id: Optional[str] = None
        
    def print_step(self, step: str, message: str):
        """打印步骤信息"""
        print(f"\n{'='*60}")
        print(f"【{step}】{message}")
        print('='*60)
    
    def print_success(self, message: str):
        """打印成功信息"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误信息"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """打印一般信息"""
        print(f"ℹ️  {message}")
    
    def login(self) -> bool:
        """登录并获取Token"""
        self.print_step("步骤1", "用户登录")
        
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["access_token"]
                self.print_success(f"登录成功！Token: {self.token[:20]}...")
                return True
            else:
                self.print_error(f"登录失败：{response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"登录异常：{str(e)}")
            return False
    
    def create_knowledge_base(self, name: str = "测试知识库") -> bool:
        """创建知识库"""
        self.print_step("步骤2", "创建知识库")
        
        try:
            response = requests.post(
                f"{BASE_URL}/knowledge/collections",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "name": name,
                    "description": "自动化测试创建的知识库",
                    "chunk_size": 512,
                    "chunk_overlap": 50,
                    "top_k": 5,
                    "top_n": 3,
                    "similarity_threshold": 0.7,
                    "search_mode": "vector",
                    "rerank_enabled": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.kb_id = data["data"]["id"]
                collection_name = data["data"]["collection_name"]
                self.print_success(f"知识库创建成功！")
                self.print_info(f"ID: {self.kb_id}")
                self.print_info(f"Collection: {collection_name}")
                return True
            else:
                self.print_error(f"创建失败：{response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"创建异常：{str(e)}")
            return False
    
    def upload_document(self, file_path: str) -> bool:
        """上传文档"""
        self.print_step("步骤3", "上传文档")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            self.print_error(f"文件不存在：{file_path}")
            return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path_obj.name, f, 'application/octet-stream'),
                    'collection_id': (None, self.kb_id)
                }
                
                self.print_info(f"正在上传：{file_path_obj.name} ({file_path_obj.stat().st_size} bytes)")
                
                response = requests.post(
                    f"{BASE_URL}/knowledge/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                self.doc_id = data["data"]["document_id"]
                status = data["data"]["status"]
                self.print_success(f"文档上传成功！")
                self.print_info(f"Document ID: {self.doc_id}")
                self.print_info(f"状态: {status}")
                
                if status == "processing":
                    self.print_info("文档正在向量化处理中...")
                elif status == "completed":
                    self.print_success("文档已完成向量化！")
                
                return True
            else:
                self.print_error(f"上传失败：{response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"上传异常：{str(e)}")
            return False
    
    def check_document_status(self) -> Optional[dict]:
        """检查文档处理状态"""
        self.print_step("步骤4", "检查文档状态")
        
        try:
            response = requests.get(
                f"{BASE_URL}/knowledge/collections/{self.kb_id}/documents",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"page": 1, "page_size": 20}
            )
            
            if response.status_code == 200:
                data = response.json()
                docs = data["data"]["items"]
                
                if docs:
                    doc = docs[0]
                    self.print_success(f"找到文档记录")
                    self.print_info(f"文件名: {doc['filename']}")
                    self.print_info(f"状态: {doc['status']}")
                    self.print_info(f"分块数: {doc.get('chunk_count', 'N/A')}")
                    self.print_info(f"文件大小: {doc['file_size']} bytes")
                    
                    if doc['status'] == 'failed':
                        self.print_error(f"处理失败原因: {doc.get('error_message', '未知')}")
                    
                    return doc
                else:
                    self.print_error("未找到文档记录")
                    return None
            else:
                self.print_error(f"查询失败：{response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.print_error(f"查询异常：{str(e)}")
            return None
    
    def search_knowledge(self, query: str, search_mode: str = "vector") -> bool:
        """检索知识库"""
        self.print_step("步骤5", f"检索测试（模式：{search_mode}）")
        
        try:
            self.print_info(f"查询语句：{query}")
            
            response = requests.post(
                f"{BASE_URL}/knowledge/search",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "collection_id": self.kb_id,
                    "query": query,
                    "search_mode": search_mode,
                    "top_k": 5,
                    "similarity_threshold": 0.3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data["data"]
                
                self.print_success(f"检索成功！找到 {len(results)} 条结果")
                
                for i, result in enumerate(results, 1):
                    print(f"\n--- 结果 {i} ---")
                    print(f"相似度分数: {result['score']:.4f}")
                    print(f"内容片段: {result['content'][:200]}...")
                    print(f"来源: {result.get('source', 'N/A')}")
                    if result.get('metadata'):
                        print(f"元数据: {json.dumps(result['metadata'], ensure_ascii=False, indent=2)}")
                
                return len(results) > 0
            else:
                self.print_error(f"检索失败：{response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"检索异常：{str(e)}")
            return False
    
    def check_milvus_collection(self):
        """检查Milvus集合状态"""
        self.print_step("额外检查", "Milvus集合状态")
        
        try:
            from pymilvus import connections, Collection, utility
            from app.core.config import settings
            
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            
            collections = utility.list_collections()
            self.print_info(f"现有集合: {collections}")
            
            if self.kb_id:
                # 查找对应的collection
                for coll_name in collections:
                    if self.kb_id in coll_name or "kb_" in coll_name:
                        collection = Collection(coll_name)
                        collection.load()
                        count = collection.num_entities
                        self.print_success(f"集合 {coll_name} 包含 {count} 条向量")
            
            connections.disconnect("default")
        except Exception as e:
            self.print_error(f"Milvus检查失败：{str(e)}")
    
    def cleanup(self):
        """清理测试数据"""
        self.print_step("清理", "删除测试知识库")
        
        if not self.kb_id:
            self.print_info("没有需要清理的知识库")
            return
        
        try:
            response = requests.delete(
                f"{BASE_URL}/knowledge/collections/{self.kb_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                self.print_success("测试知识库已删除")
            else:
                self.print_error(f"删除失败：{response.status_code} - {response.text}")
        except Exception as e:
            self.print_error(f"删除异常：{str(e)}")
    
    def run_full_test(self, test_file: str, test_query: str, cleanup_after: bool = False):
        """运行完整测试流程"""
        print("\n" + "="*60)
        print("🚀 知识库完整流程测试")
        print("="*60)
        
        # 1. 登录
        if not self.login():
            return False
        
        # 2. 创建知识库
        if not self.create_knowledge_base():
            return False
        
        # 3. 上传文档
        if not self.upload_document(test_file):
            return False
        
        # 4. 等待处理完成
        import time
        self.print_info("等待5秒让向量化完成...")
        time.sleep(5)
        
        # 5. 检查文档状态
        doc_status = self.check_document_status()
        if not doc_status or doc_status['status'] != 'completed':
            self.print_error("文档处理未完成，检索测试可能失败")
        
        # 6. 检索测试
        search_success = self.search_knowledge(test_query, "vector")
        
        # 7. 检查Milvus
        self.check_milvus_collection()
        
        # 8. 清理（可选）
        if cleanup_after:
            self.cleanup()
        else:
            self.print_info(f"\n💡 提示：测试知识库保留，ID: {self.kb_id}")
            self.print_info("如需删除，请运行：")
            self.print_info(f"  python test/test_knowledge_pipeline.py --cleanup {self.kb_id}")
        
        # 总结
        print("\n" + "="*60)
        if search_success:
            print("✅ 测试完成：所有功能正常！")
        else:
            print("⚠️  测试完成：部分功能异常，请检查日志")
        print("="*60)
        
        return search_success


def create_test_document(file_path: str = "test_document.txt"):
    """创建测试文档"""
    content = """AgonX 多智能体协作平台

AgonX 是一个基于 LangGraph 和 LangChain 的多智能体协作平台。

核心功能：
1. 多智能体编排：支持创建和管理多个AI智能体
2. 知识库管理：支持文档上传、向量化存储和语义检索
3. 模型配置：支持多种LLM模型的接入和测试
4. MCP协议：支持Model Context Protocol工具调用

技术栈：
- 前端：Vue3 + TypeScript + Vite
- 后端：FastAPI + Python + SQLAlchemy
- 向量数据库：Milvus
- 对象存储：MinIO
- 嵌入模型：BGE-M3

检索能力：
- 向量检索：基于语义相似度的检索
- 关键词检索：基于BM25算法的检索
- 混合检索：结合向量和关键词的混合检索
- 重排序：使用BGE-Reranker进行结果优化
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 测试文档已创建：{file_path}")
    return file_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="知识库完整流程测试")
    parser.add_argument("--file", default=None, help="测试文档路径")
    parser.add_argument("--query", default="AgonX的核心功能有哪些？", help="测试查询语句")
    parser.add_argument("--cleanup", action="store_true", help="测试后清理数据")
    parser.add_argument("--delete-kb", help="删除指定的知识库ID")
    
    args = parser.parse_args()
    
    tester = KnowledgePipelineTester()
    
    # 如果是删除模式
    if args.delete_kb:
        if tester.login():
            tester.kb_id = args.delete_kb
            tester.cleanup()
        sys.exit(0)
    
    # 准备测试文件
    if args.file and Path(args.file).exists():
        test_file = args.file
    else:
        print("📝 未指定测试文件，将创建默认测试文档...")
        test_file = create_test_document("test_document.txt")
    
    # 运行测试
    tester.run_full_test(test_file, args.query, args.cleanup)
