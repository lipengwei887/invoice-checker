"""
PDF 发票解析模块
使用 pdfplumber 提取发票关键字段
针对中国增值税电子发票格式优化
"""

import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from utils.config import PDF_KEYWORDS, REGEX_PATTERNS, DUPLICATE_STATUS


@dataclass
class InvoiceData:
    """发票数据结构"""
    invoice_code: str = ""           # 发票代码
    invoice_number: str = ""         # 发票号码
    date: str = ""                   # 开票日期
    amount: str = ""                 # 金额
    verify_code: str = ""            # 校验码
    seller_name: str = ""            # 销售方名称
    file_path: str = ""              # 文件路径
    file_name: str = ""              # 文件名
    status: str = DUPLICATE_STATUS["NORMAL"]  # 查重状态
    error_msg: str = ""              # 错误信息
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "发票代码": self.invoice_code,
            "发票号码": self.invoice_number,
            "开票日期": self.date,
            "金额": self.amount,
            "校验码": self.verify_code,
            "销售方名称": self.seller_name,
            "查重状态": self.status,
            "文件名": self.file_name,
            "文件路径": self.file_path,
            "错误信息": self.error_msg,
        }


class PDFInvoiceExtractor:
    """
    PDF 发票提取器
    支持批量提取和关键词定位
    """
    
    def __init__(self):
        self.keywords = PDF_KEYWORDS
        self.patterns = REGEX_PATTERNS
        self.extracted_data: List[InvoiceData] = []
    
    def extract_from_file(self, file_path: str) -> InvoiceData:
        """
        从单个 PDF 文件提取发票信息
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            InvoiceData 对象
        """
        invoice = InvoiceData()
        invoice.file_path = file_path
        invoice.file_name = os.path.basename(file_path)
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                invoice.status = DUPLICATE_STATUS["ERROR"]
                invoice.error_msg = "文件不存在"
                return invoice
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.pdf'):
                invoice.status = DUPLICATE_STATUS["ERROR"]
                invoice.error_msg = "非 PDF 文件"
                return invoice
            
            # 打开 PDF 文件
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    invoice.status = DUPLICATE_STATUS["ERROR"]
                    invoice.error_msg = "PDF 页面为空"
                    return invoice
                
                # 提取所有页面的文本
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                
                if not all_text.strip():
                    invoice.status = DUPLICATE_STATUS["PENDING"]
                    invoice.error_msg = "无法提取文本（可能是扫描件）"
                    return invoice
                
                # 提取各个字段
                invoice.invoice_code = self._extract_invoice_code(all_text)
                invoice.invoice_number = self._extract_invoice_number(all_text)
                invoice.date = self._extract_date(all_text)
                invoice.amount = self._extract_amount(all_text)
                invoice.verify_code = self._extract_verify_code(all_text)
                invoice.seller_name = self._extract_seller(all_text)
                
                # 检查是否提取到关键字段
                if not invoice.invoice_code and not invoice.invoice_number:
                    invoice.status = DUPLICATE_STATUS["PENDING"]
                    invoice.error_msg = "未能识别发票代码和号码，请手动核对"
                
        except Exception as e:
            invoice.status = DUPLICATE_STATUS["ERROR"]
            invoice.error_msg = f"解析异常: {str(e)}"
        
        return invoice
    
    def extract_from_files(self, file_paths: List[str]) -> List[InvoiceData]:
        """
        批量提取多个 PDF 文件
        
        Args:
            file_paths: PDF 文件路径列表
            
        Returns:
            InvoiceData 列表
        """
        results = []
        for file_path in file_paths:
            invoice = self.extract_from_file(file_path)
            results.append(invoice)
        self.extracted_data = results
        return results
    
    def _extract_invoice_code(self, text: str) -> str:
        """
        提取发票代码
        中国增值税发票代码通常为 10-12 位数字
        """
        # 先通过关键词定位
        code = self._extract_by_keywords(text, self.keywords["invoice_code"])
        if code:
            # 提取数字
            match = re.search(r'(\d{10,12})', code)
            if match:
                return match.group(1)
        
        # 全局搜索发票代码模式
        # 通常格式：发票代码: 011001900211
        patterns = [
            r'发票代码[：:]\s*(\d{10,12})',
            r'电子发票代码[：:]\s*(\d{10,12})',
            r'代码[：:]\s*(\d{10,12})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_invoice_number(self, text: str) -> str:
        """
        提取发票号码
        中国增值税发票号码通常为 8-20 位数字
        """
        # 先通过关键词定位
        number = self._extract_by_keywords(text, self.keywords["invoice_number"])
        if number:
            match = re.search(r'(\d{8,20})', number)
            if match:
                return match.group(1)
        
        # 全局搜索发票号码模式
        patterns = [
            r'发票号码[：:]\s*(\d{8,20})',
            r'电子发票号码[：:]\s*(\d{8,20})',
            r'号码[：:]\s*(\d{8,20})',
            r'发票号码\s*(\d{8,20})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_date(self, text: str) -> str:
        """
        提取开票日期
        支持多种格式：2024年01月15日、2024-01-15、2024/01/15
        """
        # 先通过关键词定位
        date_str = self._extract_by_keywords(text, self.keywords["date"])
        if date_str:
            # 尝试提取日期
            match = re.search(r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)', date_str)
            if match:
                return self._normalize_date(match.group(1))
        
        # 全局搜索日期模式
        patterns = [
            r'开票日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)',
            r'日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._normalize_date(match.group(1))
        
        return ""
    
    def _extract_amount(self, text: str) -> str:
        """
        提取金额（价税合计）
        """
        # 查找价税合计附近的内容
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '价税合计' in line or '合计金额' in line:
                # 在当前行或下一行查找金额
                for j in range(i, min(i + 3, len(lines))):
                    match = re.search(r'[¥￥]\s*([\d,]+\.\d{2})', lines[j])
                    if match:
                        return match.group(1).replace(',', '')
        
        # 全局搜索金额模式
        patterns = [
            r'价税合计.*?[¥￥]\s*([\d,]+\.\d{2})',
            r'价税合计[（(]大写[)）].*?([\d,]+\.\d{2})',
            r'合\s*计.*?[¥￥]\s*([\d,]+\.\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).replace(',', '')
        
        return ""
    
    def _extract_verify_code(self, text: str) -> str:
        """
        提取校验码（后 6 位）
        """
        # 查找校验码
        verify = self._extract_by_keywords(text, self.keywords["verify_code"])
        if verify:
            match = re.search(r'(\d{6,20})', verify)
            if match:
                code = match.group(1)
                # 返回后 6 位
                return code[-6:] if len(code) >= 6 else code
        
        # 全局搜索
        patterns = [
            r'校验码[：:]\s*(\d{6,20})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                code = match.group(1)
                return code[-6:] if len(code) >= 6 else code
        
        return ""
    
    def _extract_seller(self, text: str) -> str:
        """
        提取销售方名称
        """
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '销售方' in line and '名称' in line:
                # 尝试在当前行提取
                match = re.search(r'名称[：:]\s*([^\n]+)', line)
                if match:
                    return match.group(1).strip()
                # 或者下一行
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        
        # 全局搜索
        patterns = [
            r'销售方[\s\S]*?名\s*称[：:]\s*([^\n]+)',
            r'销\s*售\s*方.*?名\s*称[：:]\s*([^\n]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_by_keywords(self, text: str, keywords: List[str]) -> str:
        """
        通过关键词定位提取内容
        在关键词所在行及其后几行中查找
        """
        lines = text.split('\n')
        for i, line in enumerate(lines):
            for keyword in keywords:
                if keyword in line:
                    # 返回当前行和下一行（防止内容换行）
                    content = line
                    if i + 1 < len(lines):
                        content += " " + lines[i + 1]
                    return content
        return ""
    
    def _normalize_date(self, date_str: str) -> str:
        """
        标准化日期格式为 YYYY-MM-DD
        """
        # 替换中文年月日
        date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
        # 替换斜杠
        date_str = date_str.replace('/', '-')
        
        # 确保月份和日期是两位数
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            month = month.zfill(2)
            day = day.zfill(2)
            return f"{year}-{month}-{day}"
        
        return date_str
    
    def get_statistics(self) -> Dict:
        """
        获取提取统计信息
        """
        total = len(self.extracted_data)
        success = sum(1 for inv in self.extracted_data 
                     if inv.status == DUPLICATE_STATUS["NORMAL"])
        duplicate = sum(1 for inv in self.extracted_data 
                       if inv.status == DUPLICATE_STATUS["DUPLICATE"])
        pending = sum(1 for inv in self.extracted_data 
                     if inv.status == DUPLICATE_STATUS["PENDING"])
        error = sum(1 for inv in self.extracted_data 
                   if inv.status == DUPLICATE_STATUS["ERROR"])
        
        return {
            "total": total,
            "success": success,
            "duplicate": duplicate,
            "pending": pending,
            "error": error,
        }


def extract_invoice_from_pdf(file_path: str) -> InvoiceData:
    """
    便捷函数：从 PDF 提取发票信息
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        InvoiceData 对象
    """
    extractor = PDFInvoiceExtractor()
    return extractor.extract_from_file(file_path)


def extract_invoices_from_pdfs(file_paths: List[str]) -> List[InvoiceData]:
    """
    便捷函数：批量从 PDF 提取发票信息
    
    Args:
        file_paths: PDF 文件路径列表
        
    Returns:
        InvoiceData 列表
    """
    extractor = PDFInvoiceExtractor()
    return extractor.extract_from_files(file_paths)
