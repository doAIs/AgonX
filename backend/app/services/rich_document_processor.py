"""
富媒体文档处理服务
支持PDF图片提取、OCR识别、表格识别等
"""
import uuid
import json
import io
from typing import List, Dict, Tuple
from minio import Minio
from PIL import Image
from app.core.config import settings
from app.core.logger import logger
from app.services.ocr_service import ocr_service


class RichDocumentProcessor:
    """富媒体文档处理器"""
    
    def __init__(self, minio_client: Minio):
        self.minio_client = minio_client
        self.bucket_name = "agonx-documents"
    
    async def process_pdf_page(
        self,
        pdf_doc,
        page_num: int,
        doc_id: str,
        kb_id: str
    ) -> Dict:
        """
        处理PDF单个页面
        
        Returns:
            {
                "page_info": {...},
                "images": [...],
                "text": "...",
                "has_images": bool,
                "has_tables": bool
            }
        """
        page = pdf_doc[page_num]
        
        logger.info(f"  处理第 {page_num + 1} 页...")
        
        # 1. 生成页面截图
        page_image_data, page_size = await self._render_page_image(page, scale=2.0)
        page_image_path = f"{kb_id}/{doc_id}/pages/page_{page_num + 1}.png"
        await self._upload_to_minio(page_image_path, page_image_data)
        
        # 2. 生成缩略图
        thumbnail_data = await self._create_thumbnail(page_image_data, max_size=200)
        thumbnail_path = f"{kb_id}/{doc_id}/thumbnails/page_{page_num + 1}_thumb.png"
        await self._upload_to_minio(thumbnail_path, thumbnail_data)
        
        # 3. 提取页面文本
        page_text = page.get_text("text")
        
        # 4. 提取页面中的图片
        images_info = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                img_info = await self._extract_image_from_page(
                    pdf_doc, page, img, img_index, page_num, doc_id, kb_id
                )
                images_info.append(img_info)
            except Exception as e:
                logger.error(f"    图片提取失败 (img_{img_index}): {str(e)}")
        
        # 5. 检测表格（简单实现）
        has_tables = await self._detect_tables(page)
        
        return {
            "page_info": {
                "page_number": page_num + 1,
                "page_image_path": page_image_path,
                "page_thumbnail_path": thumbnail_path,
                "width": int(page_size[0]),
                "height": int(page_size[1]),
                "has_text": bool(page_text.strip()),
                "has_images": len(images_info) > 0,
                "has_tables": has_tables
            },
            "images": images_info,
            "text": page_text,
            "has_images": len(images_info) > 0,
            "has_tables": has_tables
        }
    
    async def _render_page_image(self, page, scale: float = 2.0) -> Tuple[bytes, Tuple[float, float]]:
        """渲染页面为图片"""
        import fitz  # PyMuPDF
        
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        return img_data, (page.rect.width, page.rect.height)
    
    async def _create_thumbnail(self, image_data: bytes, max_size: int = 200) -> bytes:
        """创建缩略图"""
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='PNG', optimize=True)
        return output.getvalue()
    
    async def _extract_image_from_page(
        self,
        pdf_doc,
        page,
        img_ref,
        img_index: int,
        page_num: int,
        doc_id: str,
        kb_id: str
    ) -> Dict:
        """从PDF页面提取图片"""
        xref = img_ref[0]
        base_image = pdf_doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        
        # 保存原图
        img_path = f"{kb_id}/{doc_id}/images/p{page_num + 1}_img{img_index}.{image_ext}"
        await self._upload_to_minio(img_path, image_bytes)
        
        # 创建缩略图
        thumbnail_data = await self._create_thumbnail(image_bytes, max_size=150)
        thumb_path = f"{kb_id}/{doc_id}/images/p{page_num + 1}_img{img_index}_thumb.png"
        await self._upload_to_minio(thumb_path, thumbnail_data)
        
        # OCR识别图片文字
        logger.info(f"    OCR识别图片 {img_index}...")
        ocr_result = await ocr_service.recognize_image(image_bytes, image_ext)
        
        # 获取图片在页面中的位置
        img_rects = page.get_image_rects(xref)
        position = None
        if img_rects:
            rect = img_rects[0]
            position = {
                "x": float(rect.x0),
                "y": float(rect.y0),
                "width": float(rect.width),
                "height": float(rect.height)
            }
        
        return {
            "element_id": str(uuid.uuid4()),
            "element_type": "image",
            "element_path": img_path,
            "thumbnail_path": thumb_path,
            "position": position,
            "ocr_text": ocr_result.get("text", ""),
            "ocr_confidence": ocr_result.get("confidence", 0.0),
            "metadata": {
                "format": image_ext,
                "size": len(image_bytes)
            }
        }
    
    async def _detect_tables(self, page) -> bool:
        """简单检测页面是否包含表格"""
        try:
            # 使用PyMuPDF检测表格
            tables = page.find_tables()
            return len(tables.tables) > 0 if tables else False
        except:
            return False
    
    async def _upload_to_minio(self, object_name: str, data: bytes):
        """上传数据到MinIO"""
        try:
            # 确保bucket存在
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
            
            # 上传数据
            self.minio_client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=self._get_content_type(object_name)
            )
        except Exception as e:
            logger.error(f"MinIO上传失败 ({object_name}): {str(e)}")
            raise
    
    def _get_content_type(self, filename: str) -> str:
        """根据文件名获取Content-Type"""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'pdf': 'application/pdf',
            'txt': 'text/plain'
        }
        return content_types.get(ext, 'application/octet-stream')
