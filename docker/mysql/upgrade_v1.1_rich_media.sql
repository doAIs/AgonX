-- AgonX 数据库升级脚本 v1.1 - 富媒体知识库
-- 执行日期: 2025-02
-- 描述: 为知识库添加富媒体内容处理能力（PDF页面、图片、OCR、分块映射）
-- 
-- 功能：
-- 1. 为documents表添加富媒体字段
-- 2. 创建document_pages表（PDF页面管理）
-- 3. 创建document_elements表（图片、表格等元素）
-- 4. 创建document_chunks表（分块与向量映射）
-- 5. 创建ocr_tasks表（OCR任务队列）
--
-- 使用方法:
-- mysql -h localhost -u agonx -p agonx < upgrade_v1.1_rich_media.sql

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

USE agonx;

-- =============================================================================
-- 第一部分: 升级现有 documents 表
-- =============================================================================

-- 1.1 添加富媒体相关字段到 documents 表
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) DEFAULT 'text' COMMENT '内容类型: text/mixed',
ADD COLUMN IF NOT EXISTS page_count INT DEFAULT 0 COMMENT 'PDF总页数',
ADD COLUMN IF NOT EXISTS has_images TINYINT(1) DEFAULT 0 COMMENT '是否包含图片',
ADD COLUMN IF NOT EXISTS has_tables TINYINT(1) DEFAULT 0 COMMENT '是否包含表格';

-- 1.2 为新字段创建索引
CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(content_type);
CREATE INDEX IF NOT EXISTS idx_doc_status ON documents(status);

-- =============================================================================
-- 第二部分: 创建富媒体相关表
-- =============================================================================

-- 2.1 删除已存在的表（如果需要重建）
-- 注意：按照外键依赖顺序删除
DROP TABLE IF EXISTS ocr_tasks;
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS document_elements;
DROP TABLE IF EXISTS document_pages;

-- 2.2 创建文档页面表
-- 用途：存储PDF每个页面的信息
CREATE TABLE document_pages (
    id VARCHAR(36) PRIMARY KEY COMMENT '页面ID',
    document_id VARCHAR(36) NOT NULL COMMENT '所属文档ID',
    page_number INT NOT NULL COMMENT '页码',
    page_image_path VARCHAR(500) COMMENT '页面截图路径（MinIO）',
    page_thumbnail_path VARCHAR(500) COMMENT '缩略图路径（MinIO）',
    width INT COMMENT '页面宽度（像素）',
    height INT COMMENT '页面高度（像素）',
    has_text TINYINT(1) DEFAULT 1 COMMENT '是否包含文本',
    has_images TINYINT(1) DEFAULT 0 COMMENT '是否包含图片',
    has_tables TINYINT(1) DEFAULT 0 COMMENT '是否包含表格',
    ocr_text TEXT COMMENT 'OCR识别的文本内容',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_doc_page (document_id, page_number),
    
    -- 外键约束
    CONSTRAINT fk_page_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='文档页面表 - 存储PDF每个页面的元信息';

-- 2.3 创建文档元素表
-- 用途：存储页面中的图片、表格、图表等元素
CREATE TABLE document_elements (
    id VARCHAR(36) PRIMARY KEY COMMENT '元素ID',
    document_id VARCHAR(36) NOT NULL COMMENT '所属文档ID',
    page_id VARCHAR(36) NOT NULL COMMENT '所属页面ID',
    element_type ENUM('image', 'table', 'chart', 'formula', 'diagram') NOT NULL COMMENT '元素类型',
    element_path VARCHAR(500) COMMENT '元素文件路径（MinIO）',
    thumbnail_path VARCHAR(500) COMMENT '缩略图路径（MinIO）',
    position JSON COMMENT '元素在页面中的位置坐标 {x, y, width, height}',
    ocr_text TEXT COMMENT 'OCR识别的文字',
    description TEXT COMMENT '元素描述',
    metadata_info JSON COMMENT '额外元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_doc_element (document_id, element_type),
    INDEX idx_page_element (page_id, element_type),
    
    -- 外键约束
    CONSTRAINT fk_element_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_element_page FOREIGN KEY (page_id) 
        REFERENCES document_pages(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='文档元素表 - 存储图片、表格等富媒体元素';

-- 2.4 创建文档分块表
-- 用途：存储文本分块，并关联到Milvus向量ID
CREATE TABLE document_chunks (
    id VARCHAR(36) PRIMARY KEY COMMENT '分块ID',
    document_id VARCHAR(36) NOT NULL COMMENT '所属文档ID',
    page_id VARCHAR(36) COMMENT '所属页面ID（可选）',
    chunk_index INT NOT NULL COMMENT '分块序号',
    content TEXT NOT NULL COMMENT '分块文本内容',
    vector_id VARCHAR(100) COMMENT 'Milvus向量ID',
    start_position JSON COMMENT '起始位置 {page, offset}',
    end_position JSON COMMENT '结束位置 {page, offset}',
    related_elements JSON COMMENT '关联的元素ID列表',
    prev_chunk_id VARCHAR(36) COMMENT '上一个分块ID',
    next_chunk_id VARCHAR(36) COMMENT '下一个分块ID',
    token_count INT COMMENT 'Token数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_doc_chunk (document_id, chunk_index),
    INDEX idx_page_chunk (page_id),
    INDEX idx_vector (vector_id),
    
    -- 外键约束
    CONSTRAINT fk_chunk_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_chunk_page FOREIGN KEY (page_id) 
        REFERENCES document_pages(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='文档分块表 - 存储文本分块并映射到向量数据库';

-- 2.5 创建OCR任务表
-- 用途：管理异步OCR识别任务
CREATE TABLE ocr_tasks (
    id VARCHAR(36) PRIMARY KEY COMMENT '任务ID',
    element_id VARCHAR(36) NOT NULL COMMENT '关联的元素ID',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '任务状态',
    engine VARCHAR(50) DEFAULT 'paddleocr' COMMENT 'OCR引擎',
    result JSON COMMENT 'OCR识别结果',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_status (status),
    INDEX idx_element (element_id),
    
    -- 外键约束
    CONSTRAINT fk_ocr_element FOREIGN KEY (element_id) 
        REFERENCES document_elements(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='OCR任务表 - 管理图片文字识别任务队列';

-- =============================================================================
-- 第三部分: 数据验证和统计
-- =============================================================================

-- 3.1 验证表创建
SELECT 
    TABLE_NAME AS '表名',
    TABLE_ROWS AS '记录数',
    CREATE_TIME AS '创建时间',
    TABLE_COMMENT AS '说明'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'agonx' 
    AND TABLE_NAME IN ('document_pages', 'document_elements', 'document_chunks', 'ocr_tasks')
ORDER BY TABLE_NAME;

-- 3.2 显示documents表结构变化
DESCRIBE documents;

-- 3.3 显示所有外键关系
SELECT 
    TABLE_NAME AS '表名',
    CONSTRAINT_NAME AS '约束名',
    REFERENCED_TABLE_NAME AS '引用表'
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'agonx'
    AND REFERENCED_TABLE_NAME IS NOT NULL
    AND TABLE_NAME IN ('document_pages', 'document_elements', 'document_chunks', 'ocr_tasks')
ORDER BY TABLE_NAME;

-- =============================================================================
-- 升级完成提示
-- =============================================================================
SELECT '✅ 富媒体知识库升级完成！' AS '状态', 
       NOW() AS '完成时间',
       '已添加4张新表: document_pages, document_elements, document_chunks, ocr_tasks' AS '说明';
