"""
OCR服务 - 支持多种OCR引擎
"""
import io
from typing import Optional, List, Dict
from PIL import Image
from app.core.logger import logger


class OCRService:
    """OCR识别服务"""
    
    def __init__(self, engine: str = "paddleocr"):
        """
        初始化OCR服务
        
        Args:
            engine: OCR引擎 (paddleocr/tesseract/azure)
        """
        self.engine = engine
        self._ocr_instance = None
    
    def _get_paddle_ocr(self):
        """获取PaddleOCR实例（懒加载）"""
        if self._ocr_instance is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr_instance = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',  # 中文+英文
                    use_gpu=False,  # 如需GPU，设置为True
                    show_log=False
                )
                logger.info("✅ PaddleOCR初始化成功")
            except Exception as e:
                logger.error(f"❌ PaddleOCR初始化失败: {str(e)}")
                raise
        return self._ocr_instance
    
    async def recognize_image(
        self,
        image_data: bytes,
        image_format: str = "png"
    ) -> Dict[str, any]:
        """
        识别图片中的文字
        
        Args:
            image_data: 图片二进制数据
            image_format: 图片格式
        
        Returns:
            {
                "text": "识别的文本",
                "confidence": 0.95,
                "lines": [{"text": "行文本", "confidence": 0.98, "bbox": [x1, y1, x2, y2]}]
            }
        """
        try:
            if self.engine == "paddleocr":
                return await self._recognize_with_paddle(image_data)
            elif self.engine == "tesseract":
                return await self._recognize_with_tesseract(image_data)
            else:
                raise ValueError(f"不支持的OCR引擎: {self.engine}")
        except Exception as e:
            logger.error(f"OCR识别失败: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "lines": [],
                "error": str(e)
            }
    
    async def _recognize_with_paddle(self, image_data: bytes) -> Dict:
        """使用PaddleOCR识别"""
        try:
            # 加载OCR实例
            ocr = self._get_paddle_ocr()
            
            # 将bytes转换为numpy array
            import numpy as np
            from PIL import Image
            image = Image.open(io.BytesIO(image_data))
            img_array = np.array(image)
            
            # OCR识别
            result = ocr.ocr(img_array, cls=True)
            
            if not result or not result[0]:
                return {"text": "", "confidence": 0.0, "lines": []}
            
            # 解析结果
            lines = []
            full_text = []
            total_confidence = 0.0
            
            for line in result[0]:
                bbox = line[0]  # 边界框 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text_info = line[1]  # (text, confidence)
                text = text_info[0]
                confidence = text_info[1]
                
                lines.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox
                })
                full_text.append(text)
                total_confidence += confidence
            
            avg_confidence = total_confidence / len(lines) if lines else 0.0
            
            return {
                "text": "\n".join(full_text),
                "confidence": avg_confidence,
                "lines": lines
            }
        except Exception as e:
            logger.error(f"PaddleOCR识别失败: {str(e)}")
            raise
    
    async def _recognize_with_tesseract(self, image_data: bytes) -> Dict:
        """使用Tesseract识别"""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(io.BytesIO(image_data))
            
            # 识别文本
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            # 获取详细信息
            data = pytesseract.image_to_data(image, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)
            
            lines = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    lines.append({
                        "text": data['text'][i],
                        "confidence": data['conf'][i] / 100.0,
                        "bbox": [
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ]
                    })
            
            avg_confidence = sum(l['confidence'] for l in lines) / len(lines) if lines else 0.0
            
            return {
                "text": text.strip(),
                "confidence": avg_confidence,
                "lines": lines
            }
        except Exception as e:
            logger.error(f"Tesseract识别失败: {str(e)}")
            raise


# 全局OCR服务实例
ocr_service = OCRService(engine="paddleocr")
