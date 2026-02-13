"""检查知识库文档状态"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import select
from app.core.database import async_engine
from app.models.knowledge import Document
from sqlalchemy.ext.asyncio import AsyncSession

async def check_documents(kb_id: str = "0081f74c-135e-4d1c-b352-493cf2eca4c5"):
    """检查文档状态"""
    async with AsyncSession(async_engine) as db:
        result = await db.execute(
            select(Document).where(Document.knowledge_base_id == kb_id)
        )
        docs = result.scalars().all()
        
        if not docs:
            print(f"❌ 知识库 {kb_id} 中没有任何文档")
            return
        
        print(f"\n找到 {len(docs)} 个文档：\n")
        for i, doc in enumerate(docs, 1):
            print(f"{'='*60}")
            print(f"文档 {i}:")
            print(f"  文件名: {doc.filename}")
            print(f"  文档ID: {doc.id}")
            print(f"  状态: {doc.status}")
            print(f"  分块数: {doc.chunk_count}")
            print(f"  文件大小: {doc.file_size} bytes")
            print(f"  文件路径: {doc.file_path}")
            if doc.error_message:
                print(f"  ❌ 错误信息: {doc.error_message}")
            print(f"  创建时间: {doc.created_at}")
            print(f"  更新时间: {doc.updated_at}")

if __name__ == "__main__":
    import sys
    kb_id = sys.argv[1] if len(sys.argv) > 1 else "0081f74c-135e-4d1c-b352-493cf2eca4c5"
    asyncio.run(check_documents(kb_id))
