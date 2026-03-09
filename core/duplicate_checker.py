"""
查重逻辑模块
实现发票查重的核心算法
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

from utils.config import DUPLICATE_STATUS


@dataclass
class CheckResult:
    """查重结果数据结构"""
    invoice_code: str
    invoice_number: str
    is_duplicate: bool
    status: str
    first_seen_date: Optional[str] = None
    duplicate_source: Optional[str] = None  # 重复来源：database 或 current_batch
    message: str = ""


class DuplicateChecker:
    """
    发票查重器
    支持与历史数据库比对和批次内查重
    """
    
    def __init__(self):
        self.checked_keys: Set[str] = set()  # 已检查的主键集合
        self.duplicate_keys: Set[str] = set()  # 重复的主键集合
        self.current_batch: Dict[str, Dict] = {}  # 当前批次的发票（用于批次内查重）
    
    def check_single(
        self, 
        invoice_code: str, 
        invoice_number: str,
        db_checker=None
    ) -> CheckResult:
        """
        检查单张发票是否重复
        
        Args:
            invoice_code: 发票代码
            invoice_number: 发票号码
            db_checker: 数据库检查函数 (code, number) -> (is_dup, record)
            
        Returns:
            CheckResult 对象
        """
        result = CheckResult(
            invoice_code=invoice_code,
            invoice_number=invoice_number,
            is_duplicate=False,
            status=DUPLICATE_STATUS["NORMAL"]
        )
        
        # 生成唯一主键
        key = self._generate_key(invoice_code, invoice_number)
        
        if not key:
            result.status = DUPLICATE_STATUS["PENDING"]
            result.message = "发票代码或号码为空，无法查重"
            return result
        
        # 检查是否在历史数据库中重复
        if db_checker:
            is_dup, record = db_checker(invoice_code, invoice_number)
            if is_dup:
                result.is_duplicate = True
                result.status = DUPLICATE_STATUS["DUPLICATE"]
                result.duplicate_source = "database"
                result.first_seen_date = record.get('开票日期') if record else None
                result.message = f"与历史数据库重复（首次出现: {result.first_seen_date}）"
                self.duplicate_keys.add(key)
                return result
        
        # 检查是否在批次内重复
        if key in self.current_batch:
            result.is_duplicate = True
            result.status = DUPLICATE_STATUS["DUPLICATE"]
            result.duplicate_source = "current_batch"
            first_inv = self.current_batch[key]
            result.first_seen_date = first_inv.get('开票日期')
            result.message = f"与当前批次重复（文件: {first_inv.get('文件名', '未知')}）"
            self.duplicate_keys.add(key)
            return result
        
        # 添加到当前批次
        self.current_batch[key] = {
            '发票代码': invoice_code,
            '发票号码': invoice_number,
        }
        self.checked_keys.add(key)
        
        result.message = "未重复"
        return result
    
    def check_batch(
        self, 
        invoices: List[Dict],
        db_checker=None
    ) -> List[Dict]:
        """
        批量检查发票
        
        Args:
            invoices: 发票数据列表
            db_checker: 数据库检查函数
            
        Returns:
            带查重状态的发票列表
        """
        results = []
        
        # 重置批次状态
        self.reset_batch()
        
        for inv in invoices:
            code = str(inv.get('发票代码', '')).strip()
            number = str(inv.get('发票号码', '')).strip()
            
            result = self.check_single(code, number, db_checker)
            
            # 更新发票数据
            inv['查重状态'] = result.status
            inv['首次出现日期'] = result.first_seen_date or ''
            inv['查重信息'] = result.message
            inv['是否重复'] = result.is_duplicate
            
            results.append(inv)
        
        return results
    
    def check_with_excel_manager(
        self,
        invoices: List[Dict],
        excel_manager
    ) -> List[Dict]:
        """
        使用 ExcelManager 进行查重
        
        Args:
            invoices: 发票数据列表
            excel_manager: ExcelManager 实例
            
        Returns:
            带查重状态的发票列表
        """
        def db_checker(code, number):
            if excel_manager and excel_manager.is_loaded:
                return excel_manager.check_duplicate(code, number)
            return False, None
        
        return self.check_batch(invoices, db_checker)
    
    def get_statistics(self) -> Dict:
        """
        获取查重统计信息
        """
        total = len(self.checked_keys) + len(self.duplicate_keys)
        duplicates = len(self.duplicate_keys)
        normal = len(self.checked_keys)
        
        return {
            "total_checked": total,
            "duplicates": duplicates,
            "normal": normal,
            "duplicate_rate": f"{(duplicates/total*100):.1f}%" if total > 0 else "0%"
        }
    
    def reset_batch(self):
        """
        重置批次状态
        """
        self.checked_keys.clear()
        self.duplicate_keys.clear()
        self.current_batch.clear()
    
    def _generate_key(self, invoice_code: str, invoice_number: str) -> str:
        """
        生成唯一主键
        """
        if not invoice_code or not invoice_number:
            return ""
        return f"{invoice_code}_{invoice_number}"


class DuplicateReportGenerator:
    """
    查重报告生成器
    生成详细的查重报告
    """
    
    def __init__(self):
        self.duplicates: List[Dict] = []
        self.normals: List[Dict] = []
        self.pendings: List[Dict] = []
        self.errors: List[Dict] = []
    
    def categorize(self, results: List[Dict]):
        """
        分类结果
        """
        self.duplicates.clear()
        self.normals.clear()
        self.pendings.clear()
        self.errors.clear()
        
        for inv in results:
            status = inv.get('查重状态', '')
            
            if status == DUPLICATE_STATUS["DUPLICATE"]:
                self.duplicates.append(inv)
            elif status == DUPLICATE_STATUS["NORMAL"]:
                self.normals.append(inv)
            elif status == DUPLICATE_STATUS["PENDING"]:
                self.pendings.append(inv)
            elif status == DUPLICATE_STATUS["ERROR"]:
                self.errors.append(inv)
    
    def generate_summary(self) -> Dict:
        """
        生成汇总报告
        """
        total = len(self.duplicates) + len(self.normals) + len(self.pendings) + len(self.errors)
        
        return {
            "total": total,
            "duplicates": len(self.duplicates),
            "normals": len(self.normals),
            "pendings": len(self.pendings),
            "errors": len(self.errors),
            "summary_text": self._format_summary(total)
        }
    
    def _format_summary(self, total: int) -> str:
        """
        格式化汇总文本
        """
        if total == 0:
            return "未处理任何发票"
        
        lines = [
            f"处理完成！共处理 {total} 张发票：",
            f"  - 正常（未重复）: {len(self.normals)} 张",
            f"  - 重复: {len(self.duplicates)} 张",
        ]
        
        if self.pendings:
            lines.append(f"  - 待修正: {len(self.pendings)} 张")
        
        if self.errors:
            lines.append(f"  - 解析失败: {len(self.errors)} 张")
        
        return "\n".join(lines)
    
    def get_duplicates_detail(self) -> List[Dict]:
        """
        获取重复发票详情
        """
        return self.duplicates
    
    def get_normals_for_append(self) -> List[Dict]:
        """
        获取可追加到数据库的正常发票
        """
        return [inv for inv in self.normals 
                if inv.get('查重状态') == DUPLICATE_STATUS["NORMAL"]]


# ==================== 便捷函数 ====================

def check_duplicates(
    invoices: List[Dict],
    excel_manager=None
) -> List[Dict]:
    """
    便捷函数：检查发票重复
    
    Args:
        invoices: 发票数据列表
        excel_manager: ExcelManager 实例（可选）
        
    Returns:
        带查重状态的发票列表
    """
    checker = DuplicateChecker()
    
    if excel_manager:
        return checker.check_with_excel_manager(invoices, excel_manager)
    else:
        return checker.check_batch(invoices)


def generate_report(results: List[Dict]) -> Dict:
    """
    便捷函数：生成查重报告
    
    Args:
        results: 查重结果列表
        
    Returns:
        报告字典
    """
    generator = DuplicateReportGenerator()
    generator.categorize(results)
    return generator.generate_summary()
