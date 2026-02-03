"""
PDF导出服务
将对话内容导出为PDF文件
"""
import io
from typing import List, Dict, Any
from datetime import datetime
from fpdf import FPDF


class PDFExportService:
    """PDF导出服务"""
    
    def __init__(self):
        pass
    
    def export_chat_session(
        self,
        title: str,
        messages: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> bytes:
        """
        导出对话会话为PDF
        
        Args:
            title: 会话标题
            messages: 消息列表
            metadata: 元数据
        
        Returns:
            PDF文件字节
        """
        pdf = FPDF()
        pdf.add_page()
        
        # 添加中文字体支持 (需要提供字体文件)
        # pdf.add_font('SimSun', '', 'simsun.ttf', uni=True)
        # pdf.set_font('SimSun', '', 12)
        
        # 使用内置字体 (不支持中文)
        pdf.set_font('Helvetica', '', 12)
        
        # 标题
        pdf.set_font('Helvetica', 'B', 20)
        pdf.cell(0, 20, title.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
        
        # 元数据
        if metadata:
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(128, 128, 128)
            export_time = metadata.get('export_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            pdf.cell(0, 10, f"Export Time: {export_time}", ln=True, align='C')
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(10)
        
        # 消息内容
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            # 角色标签
            pdf.set_font('Helvetica', 'B', 12)
            if role == 'user':
                pdf.set_text_color(0, 128, 0)
                pdf.cell(0, 8, 'User:', ln=True)
            else:
                pdf.set_text_color(0, 0, 128)
                agent_name = msg.get('agent_name', 'Assistant')
                pdf.cell(0, 8, f'{agent_name}:', ln=True)
            
            # 消息内容
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', '', 11)
            
            # 处理长文本
            content_safe = content.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, content_safe)
            
            # 时间戳
            if timestamp:
                pdf.set_font('Helvetica', 'I', 9)
                pdf.set_text_color(128, 128, 128)
                pdf.cell(0, 6, str(timestamp), ln=True, align='R')
                pdf.set_text_color(0, 0, 0)
            
            pdf.ln(5)
        
        # 输出PDF
        return bytes(pdf.output())
    
    def export_knowledge_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> bytes:
        """
        导出知识库检索结果为PDF
        
        Args:
            query: 查询内容
            results: 检索结果
        
        Returns:
            PDF文件字节
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', '', 12)
        
        # 标题
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 15, 'Knowledge Search Results', ln=True, align='C')
        
        # 查询
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, 'Query:', ln=True)
        pdf.set_font('Helvetica', '', 11)
        query_safe = query.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, query_safe)
        pdf.ln(10)
        
        # 结果
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, f'Results ({len(results)} items):', ln=True)
        pdf.ln(5)
        
        for i, result in enumerate(results, 1):
            pdf.set_font('Helvetica', 'B', 11)
            score = result.get('score', 0)
            pdf.cell(0, 8, f'{i}. Score: {score:.2%}', ln=True)
            
            pdf.set_font('Helvetica', '', 10)
            content = result.get('content', '')
            content_safe = content.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, content_safe)
            
            source = result.get('source', 'Unknown')
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(128, 128, 128)
            source_safe = source.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 6, f'Source: {source_safe}', ln=True)
            pdf.set_text_color(0, 0, 0)
            
            pdf.ln(5)
        
        return bytes(pdf.output())


# 全局实例
pdf_export_service = PDFExportService()
