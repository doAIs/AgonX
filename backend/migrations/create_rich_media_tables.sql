-- 完整的富媒体表创建脚本（修复版）
-- 删除已存在的表（如果有）
DROP TABLE IF EXISTS ocr_tasks;
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS document_elements;
DROP TABLE IF EXISTS document_pages;

-- 1. 创建文档页面表
CREATE TABLE document_pages (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    page_number INT NOT NULL,
    page_image_path VARCHAR(500),
    page_thumbnail_path VARCHAR(500),
    width INT,
    height INT,
    has_text TINYINT(1) DEFAULT 1,
    has_images TINYINT(1) DEFAULT 0,
    has_tables TINYINT(1) DEFAULT 0,
    ocr_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc_page (document_id, page_number),
    CONSTRAINT fk_page_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 创建文档元素表（图片、表格等）
CREATE TABLE document_elements (
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
    INDEX idx_doc_element (document_id, element_type),
    CONSTRAINT fk_element_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_element_page FOREIGN KEY (page_id) 
        REFERENCES document_pages(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 创建文档分块表
CREATE TABLE document_chunks (
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
    INDEX idx_doc_chunk (document_id, chunk_index),
    INDEX idx_vector (vector_id),
    CONSTRAINT fk_chunk_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_chunk_page FOREIGN KEY (page_id) 
        REFERENCES document_pages(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 创建OCR任务表
CREATE TABLE ocr_tasks (
    id VARCHAR(36) PRIMARY KEY,
    element_id VARCHAR(36) NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    engine VARCHAR(50) DEFAULT 'paddleocr',
    result JSON,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    CONSTRAINT fk_ocr_element FOREIGN KEY (element_id) 
        REFERENCES document_elements(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 验证表创建
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'agonx' 
    AND TABLE_NAME IN ('document_pages', 'document_elements', 'document_chunks', 'ocr_tasks')
ORDER BY TABLE_NAME;
