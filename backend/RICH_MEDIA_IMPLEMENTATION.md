# 知识库富媒体架构升级实施指南

## ✅ 已完成的工作

### 1. 依赖添加
- ✅ PyMuPDF (fitz) - PDF处理和图片提取
- ✅ pdfplumber - 表格识别
- ✅ Pillow - 图片处理
- ✅ PaddleOCR - OCR识别
- ✅ paddlepaddle - OCR引擎

### 2. 数据库架构
- ✅ 创建迁移SQL: `migrations/upgrade_knowledge_rich_media.sql`
- ✅ 新增表：
  - `document_pages` - 文档页面表
  - `document_elements` - 文档元素表（图片、表格等）
  - `document_chunks` - 文档分块表
  - `ocr_tasks` - OCR任务表
- ✅ 优化 `documents` 表，新增字段：
  - `content_type` - 内容类型
  - `page_count` - 总页数
  - `has_images` - 是否包含图片
  - `has_tables` - 是否包含表格

### 3. 数据模型
- ✅ `app/models/document_rich.py` - 富媒体数据模型
- ✅ 更新 `app/models/knowledge.py` - 添加关系映射

### 4. 核心服务
- ✅ `app/services/ocr_service.py` - OCR识别服务
- ✅ `app/services/rich_document_processor.py` - 富媒体文档处理器

---

## 🚧 待完成的工作

### 步骤5：重构向量化流程
需要修改 `app/api/v1/knowledge.py` 中的 `_process_document_vectorization` 函数

主要改动：
```python
# 使用PyMuPDF代替原有的loader
import fitz
doc = fitz.open(stream=file_content, filetype="pdf")

# 逐页处理
for page_num in range(len(doc)):
    page_data = await processor.process_pdf_page(doc, page_num, doc_id, kb_id)
    
    # 创建页面记录
    # 创建元素记录
    # 创建分块记录
```

### 步骤6：创建增强检索接口
在 `app/api/v1/knowledge.py` 添加新接口：
```python
@router.post("/search/enhanced")
async def enhanced_search(...):
    # 1. 向量检索
    # 2. 查询chunk记录（包含页面、元素信息）
    # 3. 获取上下文chunk
    # 4. 获取关联图片
    # 5. 返回增强结果
```

### 步骤7：前端界面优化
修改 `frontend/src/views/Knowledge.vue`：

添加增强检索结果展示：
- 显示页面预览图
- 显示关联图片
- 显示上下文
- 提供跳转到原文功能

### 步骤8：执行数据库迁移
```bash
# 连接到MySQL
mysql -h localhost -u root -p agonx

# 执行迁移脚本
source backend/migrations/upgrade_knowledge_rich_media.sql;
```

### 步骤9：安装依赖
```bash
cd backend
pip install PyMuPDF==1.24.0 pdfplumber==0.11.0 Pillow==10.3.0
pip install paddleocr==2.7.3 paddlepaddle==2.6.1
```

### 步骤10：测试验证
1. 上传包含图片的PDF文档
2. 查看页面截图是否生成
3. 测试OCR识别
4. 测试增强检索
5. 测试图片下载

---

## 📋 快速实施命令

```bash
# 1. 安装依赖
cd e:\GIT_AI\AgonX\backend
pip install -r requirements.txt

# 2. 执行数据库迁移
mysql -h localhost -u root -p agonx < migrations/upgrade_knowledge_rich_media.sql

# 3. 重启后端
python main.py

# 4. 测试上传
# 使用前端界面上传一个包含图片的PDF文档
```

---

## 🔄 回滚方案

如需回滚到旧版本：

```sql
DROP TABLE IF EXISTS ocr_tasks;
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS document_elements;
DROP TABLE IF EXISTS document_pages;

ALTER TABLE documents 
DROP COLUMN content_type,
DROP COLUMN page_count,
DROP COLUMN has_images,
DROP COLUMN has_tables;
```

---

## 📊 性能优化建议

1. **异步OCR**：大量图片时，使用异步任务队列
2. **缓存优化**：页面截图可以设置CDN缓存
3. **懒加载**：前端分页加载图片
4. **压缩优化**：对大图片进行压缩
5. **批量处理**：多个页面并行处理

---

## 🐛 常见问题

### Q1: PaddleOCR安装失败？
A: 使用CPU版本：`pip install paddlepaddle==2.6.1`

### Q2: PyMuPDF导入错误？
A: 导入时使用 `import fitz` 而不是 `import PyMuPDF`

### Q3: MinIO上传图片失败？
A: 检查bucket权限和网络连接

### Q4: OCR识别速度慢？
A: 考虑使用GPU版本或异步任务队列

---

## 📝 下一步计划

1. **表格识别优化** - 使用pdfplumber提取表格结构
2. **图表理解** - 集成图表理解模型
3. **公式识别** - 支持LaTeX公式识别
4. **多语言支持** - 支持更多语言OCR
5. **批注支持** - 保留PDF批注信息

---

## 📞 技术支持

如遇问题，请查看：
- 后端日志：`backend/logs/agonx.log`
- OCR日志：查找 "OCR" 关键词
- 向量化日志：查找 "向量化" 关键词
