-- ========================================
-- 知识库富媒体架构升级迁移脚本
-- 版本: v2.0.0
-- 日期: 2026-02-13
-- 描述: 支持图片、OCR、页面预览等富媒体内容
-- ========================================

-- 1. 优化 documents 表
ALTER TABLE documents 
ADD COLUMN content_type VARCHAR(50) DEFAULT 'text' COMMENT '内容类型: text/mixed/image-heavy',
ADD COLUMN page_count INT DEFAULT 0 COMMENT '总页数',
ADD COLUMN has_images BOOLEAN DEFAULT FALSE COMMENT '是否包含图片',
ADD COLUMN has_tables BOOLEAN DEFAULT FALSE COMMENT '是否包含表格';

-- 2. 创建文档页面表
CREATE TABLE IF NOT EXISTS document_pages (
    id VARCHAR(36) PRIMARY KEY COMMENT '页面ID',
    document_id VARCHAR(36) NOT NULL COMMENT '文档ID',
    page_number INT NOT NULL COMMENT '页码（从1开始）',
    page_image_path VARCHAR(500) COMMENT 'MinIO中页面截图路径',
    page_thumbnail_path VARCHAR(500) COMMENT '缩略图路径',
    width INT COMMENT '页面宽度',
    height INT COMMENT '页面高度',
    has_text BOOLEAN DEFAULT TRUE COMMENT '是否包含文本',
    has_images BOOLEAN DEFAULT FALSE COMMENT '是否包含图片',
    has_tables BOOLEAN DEFAULT FALSE COMMENT '是否包含表格',
    ocr_text TEXT COMMENT 'OCR识别的文本（如果是扫描件）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_doc_page (document_id, page_number),
    INDEX idx_page_content (has_text, has_images, has_tables)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档页面表';

-- 3. 创建文档元素表（图片、表格、图表等）
CREATE TABLE IF NOT EXISTS document_elements (
    id VARCHAR(36) PRIMARY KEY COMMENT '元素ID',
    document_id VARCHAR(36) NOT NULL COMMENT '文档ID',
    page_id VARCHAR(36) NOT NULL COMMENT '页面ID',
    element_type ENUM('image', 'table', 'chart', 'formula', 'diagram') NOT NULL COMMENT '元素类型',
    element_path VARCHAR(500) COMMENT 'MinIO中元素文件路径',
    thumbnail_path VARCHAR(500) COMMENT '缩略图路径',
    position JSON COMMENT '位置信息 {x, y, width, height}',
    ocr_text TEXT COMMENT 'OCR识别的文字',
    description TEXT COMMENT 'AI生成的描述（可选）',
    metadata JSON COMMENT '额外元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES document_pages(id) ON DELETE CASCADE,
    INDEX idx_doc_element (document_id, element_type),
    INDEX idx_page_element (page_id, element_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档元素表';

-- 4. 创建文档分块表（替代纯metadata方式）
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(36) PRIMARY KEY COMMENT '分块ID',
    document_id VARCHAR(36) NOT NULL COMMENT '文档ID',
    page_id VARCHAR(36) COMMENT '所属页面ID',
    chunk_index INT NOT NULL COMMENT '分块索引（从0开始）',
    content TEXT NOT NULL COMMENT '分块文本内容',
    vector_id VARCHAR(100) COMMENT 'Milvus中的向量ID',
    start_position JSON COMMENT '起始位置 {page, x, y}',
    end_position JSON COMMENT '结束位置 {page, x, y}',
    related_elements JSON COMMENT '关联的元素ID列表',
    prev_chunk_id VARCHAR(36) COMMENT '上一个分块ID',
    next_chunk_id VARCHAR(36) COMMENT '下一个分块ID',
    token_count INT COMMENT 'Token数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES document_pages(id) ON DELETE SET NULL,
    INDEX idx_doc_chunk (document_id, chunk_index),
    INDEX idx_vector_id (vector_id),
    INDEX idx_page_chunk (page_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档分块表';

-- 5. 创建OCR任务表（用于异步处理）
CREATE TABLE IF NOT EXISTS ocr_tasks (
    id VARCHAR(36) PRIMARY KEY COMMENT '任务ID',
    element_id VARCHAR(36) NOT NULL COMMENT '元素ID',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    ocr_engine VARCHAR(50) COMMENT 'OCR引擎: paddleocr/tesseract/azure',
    result_text TEXT COMMENT '识别结果',
    confidence FLOAT COMMENT '置信度',
    error_message TEXT COMMENT '错误信息',
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (element_id) REFERENCES document_elements(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_element (element_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='OCR任务表';

-- 6. 创建索引优化查询性能
CREATE INDEX idx_doc_status ON documents(status);
CREATE INDEX idx_doc_type ON documents(content_type);
CREATE INDEX idx_chunk_vector ON document_chunks(vector_id);

-- ========================================
-- 数据迁移（可选）
-- ========================================

-- 将现有文档标记为 text 类型
UPDATE documents SET content_type = 'text' WHERE content_type IS NULL;

-- ========================================
-- 回滚脚本（如需回滚，执行以下语句）
-- ========================================

-- DROP TABLE IF EXISTS ocr_tasks;
-- DROP TABLE IF EXISTS document_chunks;
-- DROP TABLE IF EXISTS document_elements;
-- DROP TABLE IF EXISTS document_pages;
-- 
-- ALTER TABLE documents 
-- DROP COLUMN content_type,
-- DROP COLUMN page_count,
-- DROP COLUMN has_images,
-- DROP COLUMN has_tables;
