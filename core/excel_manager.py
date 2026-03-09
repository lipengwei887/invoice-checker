"""
Excel 管理模块
处理历史发票数据库的读写操作
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.config import (
    REQUIRED_COLUMNS, 
    OPTIONAL_COLUMNS, 
    COLUMN_MAPPING,
    SUPPORTED_EXCEL_EXTS,
    DEFAULT_DB_FILENAME,
    DEFAULT_RESULT_FILENAME
)


class ExcelManager:
    """
    Excel 数据库管理器
    负责历史发票数据的加载、查询、更新和导出
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化 Excel 管理器
        
        Args:
            db_path: 历史数据库文件路径，None 表示未设置
        """
        self.db_path: Optional[str] = db_path
        self.df: Optional[pd.DataFrame] = None
        self.column_mapping: Dict[str, str] = {}  # 实际列名到标准列名的映射
        self.is_loaded: bool = False
        
    def load_database(self, db_path: str) -> Tuple[bool, str]:
        """
        加载历史发票数据库
        
        Args:
            db_path: Excel 文件路径
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(db_path):
                return False, f"文件不存在: {db_path}"
            
            # 检查文件扩展名
            ext = Path(db_path).suffix.lower()
            if ext not in SUPPORTED_EXCEL_EXTS:
                return False, f"不支持的文件格式: {ext}"
            
            # 尝试读取文件
            try:
                df = pd.read_excel(db_path, engine='openpyxl')
            except Exception as e1:
                try:
                    df = pd.read_excel(db_path)
                except Exception as e2:
                    return False, f"无法读取 Excel 文件: {str(e1)}"
            
            if df.empty:
                # 空文件，创建带标准列名的空 DataFrame
                df = pd.DataFrame(columns=REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
            
            # 建立列名映射
            self._build_column_mapping(df.columns.tolist())
            
            # 标准化列名
            self.df = self._standardize_columns(df)
            
            # 确保所有必需列都存在
            for col in REQUIRED_COLUMNS:
                if col not in self.df.columns:
                    self.df[col] = ""
            
            self.db_path = db_path
            self.is_loaded = True
            
            return True, f"成功加载 {len(self.df)} 条记录"
            
        except PermissionError:
            return False, "文件被占用，请关闭 Excel 后重试"
        except Exception as e:
            return False, f"加载失败: {str(e)}"
    
    def create_new_database(self, db_path: str) -> Tuple[bool, str]:
        """
        创建新的历史数据库文件
        
        Args:
            db_path: 新数据库文件路径
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 创建目录
            os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
            
            # 创建带标准列名的空 DataFrame
            df = pd.DataFrame(columns=REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
            
            # 保存文件
            df.to_excel(db_path, index=False, engine='openpyxl')
            
            self.db_path = db_path
            self.df = df
            self.is_loaded = True
            
            return True, f"成功创建数据库: {db_path}"
            
        except Exception as e:
            return False, f"创建失败: {str(e)}"
    
    def check_duplicate(self, invoice_code: str, invoice_number: str) -> Tuple[bool, Optional[Dict]]:
        """
        检查发票是否重复
        
        Args:
            invoice_code: 发票代码
            invoice_number: 发票号码
            
        Returns:
            (是否重复, 重复记录的详细信息)
        """
        if not self.is_loaded or self.df is None:
            return False, None
        
        if not invoice_code or not invoice_number:
            return False, None
        
        # 查询匹配的记录
        mask = (self.df['发票代码'].astype(str) == str(invoice_code)) & \
               (self.df['发票号码'].astype(str) == str(invoice_number))
        
        matches = self.df[mask]
        
        if not matches.empty:
            # 返回第一条匹配记录
            record = matches.iloc[0].to_dict()
            return True, record
        
        return False, None
    
    def check_duplicates_batch(self, invoices: List[Dict]) -> List[Dict]:
        """
        批量检查发票是否重复
        
        Args:
            invoices: 发票数据列表
            
        Returns:
            带查重状态的发票列表
        """
        results = []
        
        for inv in invoices:
            code = str(inv.get('发票代码', ''))
            number = str(inv.get('发票号码', ''))
            
            is_dup, record = self.check_duplicate(code, number)
            
            if is_dup and record:
                inv['查重状态'] = '重复'
                inv['首次出现日期'] = record.get('开票日期', '')
            else:
                inv['查重状态'] = inv.get('查重状态', '正常')
                inv['首次出现日期'] = ''
            
            results.append(inv)
        
        return results
    
    def append_invoices(self, invoices: List[Dict], auto_save: bool = True) -> Tuple[bool, str]:
        """
        追加新发票到数据库
        
        Args:
            invoices: 要追加的发票列表
            auto_save: 是否自动保存到文件
            
        Returns:
            (是否成功, 信息)
        """
        if not self.is_loaded or self.df is None:
            return False, "数据库未加载"
        
        if not invoices:
            return True, "没有要追加的数据"
        
        try:
            # 创建新 DataFrame
            new_df = pd.DataFrame(invoices)
            
            # 确保列名一致
            for col in self.df.columns:
                if col not in new_df.columns:
                    new_df[col] = ""
            
            # 只保留数据库中存在的列
            new_df = new_df[self.df.columns]
            
            # 追加数据
            self.df = pd.concat([self.df, new_df], ignore_index=True)
            
            # 去重（基于发票代码+号码）
            self.df = self.df.drop_duplicates(
                subset=['发票代码', '发票号码'], 
                keep='first'
            )
            
            # 自动保存
            if auto_save and self.db_path:
                return self.save_database()
            
            return True, f"成功追加 {len(invoices)} 条记录"
            
        except Exception as e:
            return False, f"追加失败: {str(e)}"
    
    def save_database(self) -> Tuple[bool, str]:
        """
        保存数据库到文件
        
        Returns:
            (是否成功, 信息)
        """
        if not self.is_loaded or self.df is None:
            return False, "数据库未加载"
        
        if not self.db_path:
            return False, "未设置数据库路径"
        
        try:
            self.df.to_excel(self.db_path, index=False, engine='openpyxl')
            return True, f"成功保存 {len(self.df)} 条记录"
            
        except PermissionError:
            return False, "文件被占用，请关闭 Excel 后重试"
        except Exception as e:
            return False, f"保存失败: {str(e)}"
    
    def export_results(self, results: List[Dict], output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        导出查重结果到 Excel
        
        Args:
            results: 查重结果列表
            output_path: 输出路径，None 则自动生成
            
        Returns:
            (是否成功, 信息)
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = DEFAULT_RESULT_FILENAME.format(timestamp=timestamp)
            
            # 创建目录
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # 创建 DataFrame
            df = pd.DataFrame(results)
            
            # 保存
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            return True, f"成功导出到: {output_path}"
            
        except Exception as e:
            return False, f"导出失败: {str(e)}"
    
    def get_preview(self, n_rows: int = 5) -> Optional[pd.DataFrame]:
        """
        获取数据库预览（前 n 行）
        
        Args:
            n_rows: 行数
            
        Returns:
            DataFrame 或 None
        """
        if not self.is_loaded or self.df is None:
            return None
        
        return self.df.head(n_rows)
    
    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息
        """
        if not self.is_loaded or self.df is None:
            return {
                "total_records": 0,
                "is_loaded": False,
                "db_path": None,
            }
        
        return {
            "total_records": len(self.df),
            "is_loaded": True,
            "db_path": self.db_path,
            "columns": self.df.columns.tolist(),
        }
    
    def _build_column_mapping(self, actual_columns: List[str]):
        """
        建立实际列名到标准列名的映射
        """
        self.column_mapping = {}
        
        for actual_col in actual_columns:
            actual_col_clean = str(actual_col).strip()
            
            for standard_col, variants in COLUMN_MAPPING.items():
                if actual_col_clean in variants or actual_col_clean == standard_col:
                    self.column_mapping[actual_col] = standard_col
                    break
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化列名
        """
        df = df.copy()
        
        # 重命名列
        rename_dict = {}
        for old_col, new_col in self.column_mapping.items():
            if old_col in df.columns and old_col != new_col:
                rename_dict[old_col] = new_col
        
        if rename_dict:
            df = df.rename(columns=rename_dict)
        
        return df
    
    def get_column_names(self) -> List[str]:
        """
        获取当前数据库的列名
        """
        if not self.is_loaded or self.df is None:
            return []
        
        return self.df.columns.tolist()


# ==================== 便捷函数 ====================

def load_invoice_database(db_path: str) -> Tuple[ExcelManager, str]:
    """
    便捷函数：加载发票数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        (ExcelManager 实例, 状态信息)
    """
    manager = ExcelManager()
    success, msg = manager.load_database(db_path)
    return manager, msg


def create_invoice_database(db_path: str) -> Tuple[ExcelManager, str]:
    """
    便捷函数：创建新数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        (ExcelManager 实例, 状态信息)
    """
    manager = ExcelManager()
    success, msg = manager.create_new_database(db_path)
    return manager, msg
