-- 修复数据库表结构
-- 删除已存在的表（如果迁移失败）
DROP TABLE IF EXISTS ocr_tasks;
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS document_elements;
DROP TABLE IF EXISTS document_pages;

-- 创建文档页面表
CREATE TABLE IF NOT EXISTS document_pages (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    page_number INT NOT NULL,
    page_image_path VARCHAR(500),
    page_thumbnail_path VARCHAR(500),
    width INT,
    height INT,
    has_text BOOLEAN DEFAULT TRUE,
    has_images BOOLEAN DEFAULT FALSE,
    has_tables BOOLEAN DEFAULT FALSE,
    ocr_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_doc_page (document_id, page_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建文档元素表（图片、表格等）
CREATE TABLE IF NOT EXISTS document_elements (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    page_id VARCHAR(36) NOT NULL,
    element_type ENUM('image', 'table', 'chart', 'formula', 'diagram') NOT NULL,
    element_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    position JSON,
    ocr_text TEXT,
    description TEXT,
    metadata_info JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES document_pages(id) ON DELETE CASCADE,
    INDEX idx_doc_element (document_id, element_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建文档分块表
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    page_id VARCHAR(36),
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    vector_id VARCHAR(100),
    start_position JSON,
    end_position JSON,
    related_elements JSON,
    prev_chunk_id VARCHAR(36),
    next_chunk_id VARCHAR(36),
    token_count INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (page_id) REFERENCES document_pages(id) ON DELETE SET NULL,
    INDEX idx_doc_chunk (document_id, chunk_index),
    INDEX idx_vector (vector_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建OCR任务表
CREATE TABLE IF NOT EXISTS ocr_tasks (
    id VARCHAR(36) PRIMARY KEY,
    element_id VARCHAR(36) NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    engine VARCHAR(50) DEFAULT 'paddleocr',
    result JSON,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (element_id) REFERENCES document_elements(id) ON DELETE CASCADE,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 检查是否需要添加新字段到documents表
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) DEFAULT 'text';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS page_count INT DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_images BOOLEAN DEFAULT FALSE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_tables BOOLEAN DEFAULT FALSE;
