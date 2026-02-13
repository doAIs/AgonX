# AgonX MySQL 数据库脚本

本目录包含 AgonX 项目的数据库初始化和升级脚本。

## 📁 文件说明

### 初始化脚本

- **`init.sql`** - 数据库初始化脚本
  - 创建基础表：users, chat_sessions, chat_messages, knowledge_bases, documents, model_configs, long_term_memories
  - 创建默认管理员账户
  - 用途：首次部署时自动执行（由 docker-compose 调用）

### 升级脚本

- **`upgrade_v1.1_rich_media.sql`** - v1.1 富媒体知识库升级脚本
  - 为 documents 表添加富媒体字段
  - 创建 4 张新表：document_pages, document_elements, document_chunks, ocr_tasks
  - 支持 PDF 页面管理、图片提取、OCR 识别、分块映射
  - 执行时间：约 1-2 秒
  - 前置条件：已执行 init.sql

## 🚀 使用方法

### 1. 初始化数据库（首次部署）

```bash
# 方法1: 使用 docker-compose（推荐）
docker-compose up -d mysql
# init.sql 会自动执行

# 方法2: 手动执行
mysql -h localhost -P 3306 -u root -p < init.sql
```

### 2. 升级到 v1.1（富媒体知识库）

#### Docker 环境

```bash
# 进入 MySQL 容器
docker exec -i agonx-mysql mysql -u agonx -pagonx_password agonx < docker/mysql/upgrade_v1.1_rich_media.sql

# 或者使用 docker cp + 容器内执行
docker cp docker/mysql/upgrade_v1.1_rich_media.sql agonx-mysql:/tmp/
docker exec -it agonx-mysql mysql -u agonx -pagonx_password agonx < /tmp/upgrade_v1.1_rich_media.sql
```

#### 本地环境

```bash
# 使用 MySQL 客户端
mysql -h localhost -P 3306 -u agonx -pagonx_password agonx < docker/mysql/upgrade_v1.1_rich_media.sql

# 或使用 Python 脚本（backend 目录）
cd backend
python run_migration.py
```

### 3. 验证升级结果

```bash
# 检查新增的表
mysql -h localhost -P 3306 -u agonx -pagonx_password agonx -e "SHOW TABLES LIKE 'document_%';"

# 使用验证脚本
cd backend
python verify_migration.py
```

## 📊 数据库版本历史

| 版本 | 日期 | 脚本文件 | 主要变更 |
|------|------|----------|----------|
| v1.0 | 2025-01 | init.sql | 初始版本，基础表结构 |
| v1.1 | 2025-02 | upgrade_v1.1_rich_media.sql | 富媒体知识库支持 |

## 🔧 升级脚本详细说明

### upgrade_v1.1_rich_media.sql

**新增功能：**

1. **documents 表扩展**
   - `content_type`: 内容类型（text/mixed）
   - `page_count`: PDF 总页数
   - `has_images`: 是否包含图片
   - `has_tables`: 是否包含表格

2. **document_pages 表**（PDF 页面管理）
   - 存储每个 PDF 页面的截图、缩略图、尺寸
   - 支持 OCR 文本存储
   - 标记页面是否包含图片/表格

3. **document_elements 表**（富媒体元素）
   - 存储图片、表格、图表、公式等元素
   - 记录元素在页面中的位置坐标
   - 支持 OCR 文字识别
   - 存储元素缩略图

4. **document_chunks 表**（分块映射）
   - 文本分块与 Milvus 向量 ID 映射
   - 关联到页面和元素
   - 支持上下文导航（prev/next chunk）
   - 记录分块位置信息

5. **ocr_tasks 表**（OCR 任务队列）
   - 异步 OCR 任务管理
   - 支持多种 OCR 引擎
   - 任务状态追踪
   - 结果缓存

**外键关系：**
```
documents (主表)
    ├─→ document_pages (1:N, CASCADE)
    │       ├─→ document_elements (1:N, CASCADE)
    │       │       └─→ ocr_tasks (1:N, CASCADE)
    │       └─→ document_chunks (1:N, SET NULL)
    ├─→ document_elements (1:N, CASCADE)
    └─→ document_chunks (1:N, CASCADE)
```

**性能优化：**
- 复合索引：`(document_id, page_number)`, `(document_id, chunk_index)`
- 外键索引自动创建
- JSON 字段用于灵活存储元数据

## ⚠️ 注意事项

1. **备份数据库**
   ```bash
   # 升级前务必备份
   mysqldump -h localhost -u agonx -pagonx_password agonx > backup_$(date +%Y%m%d).sql
   ```

2. **检查权限**
   - 确保用户有 CREATE/ALTER TABLE 权限
   - 检查磁盘空间（新表初始约占用 1MB）

3. **版本要求**
   - MySQL 5.7+ 或 MariaDB 10.2+（JSON 字段支持）
   - 字符集：utf8mb4

4. **回滚方案**
   ```sql
   -- 如需回滚，执行：
   DROP TABLE IF EXISTS ocr_tasks;
   DROP TABLE IF EXISTS document_chunks;
   DROP TABLE IF EXISTS document_elements;
   DROP TABLE IF EXISTS document_pages;
   
   ALTER TABLE documents 
     DROP COLUMN IF EXISTS content_type,
     DROP COLUMN IF EXISTS page_count,
     DROP COLUMN IF EXISTS has_images,
     DROP COLUMN IF EXISTS has_tables;
   ```

5. **执行时机**
   - 建议在业务低峰期执行
   - 预计执行时间：1-2 秒（空表）
   - 不影响现有数据和功能

## 🔍 常见问题

**Q: 升级会影响现有知识库吗？**
A: 不会。升级只添加新表和字段，不修改现有数据。

**Q: 如何验证升级成功？**
A: 执行 `python backend/verify_migration.py` 查看详细验证报告。

**Q: 已有文档需要重新处理吗？**
A: 不需要。新上传的 PDF 会自动使用富媒体功能，旧文档保持不变。

**Q: 升级失败如何处理？**
A: 查看 MySQL 错误日志，通常是权限或版本问题。可使用备份恢复。

## 📞 技术支持

- 查看升级日志：`docker logs agonx-mysql`
- 问题排查：运行 `python backend/check_db_structure.py`
- 完整验证：运行 `python backend/verify_migration.py`
