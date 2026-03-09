"""
配置常量模块
定义应用的全局配置参数
"""

from typing import Dict, List

# ==================== 应用配置 ====================
APP_NAME: str = "发票查重工具"
APP_VERSION: str = "1.0.0"
APP_DESCRIPTION: str = "智能发票查重与管理系统"

# 窗口配置
DEFAULT_WINDOW_SIZE: tuple = (1200, 800)
MIN_WINDOW_SIZE: tuple = (900, 600)
WINDOW_TITLE: str = f"{APP_NAME} v{APP_VERSION}"

# ==================== UI 主题配置 ====================
# 外观模式: "light", "dark", "system"
THEME_MODE: str = "light"
# 颜色主题: "blue", "green", "dark-blue"
COLOR_THEME: str = "blue"

# 颜色定义（用于自定义组件）
COLORS = {
    "primary": "#3B8ED0",
    "success": "#2CC985",
    "warning": "#FFCC00",
    "danger": "#E74C3C",
    "info": "#3498DB",
    "text": "#333333",
    "text_secondary": "#666666",
    "background": "#F0F0F0",
    "border": "#CCCCCC",
}

# ==================== PDF 提取配置 ====================
# 关键词映射（用于定位发票字段）
PDF_KEYWORDS: Dict[str, List[str]] = {
    "invoice_code": ["发票代码", "电子发票代码", "发票代码:"],
    "invoice_number": ["发票号码", "电子发票号码", "发票号码:", "发票号码："],
    "date": ["开票日期", "日期", "开票日期:", "开票日期："],
    "amount": ["价税合计", "合计金额", "¥", "￥", "总金额"],
    "verify_code": ["校验码", "校验码:", "校验码："],
    "seller": ["销售方", "销售方名称", "卖方", "销售方:"],
}

# 正则表达式模式（用于提取具体值）
REGEX_PATTERNS = {
    "invoice_code": r"(\d{10,12})",
    "invoice_number": r"(\d{8,20})",
    "date": r"(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
    "amount": r"([¥￥]?\s*[\d,]+\.?\d*)",
    "verify_code": r"(\d{6,20})",
}

# PDF 处理配置
MAX_WORKERS: int = 4  # 最大并发线程数
PDF_DPI: int = 300  # PDF 渲染分辨率
TIMEOUT_SECONDS: int = 30  # 单文件处理超时时间

# ==================== Excel 配置 ====================
# 必需列名（历史数据库）
REQUIRED_COLUMNS: List[str] = [
    "发票代码",
    "发票号码",
    "开票日期",
    "金额",
    "销售方名称",
]

# 可选列名
OPTIONAL_COLUMNS: List[str] = [
    "校验码",
    "查重状态",
    "首次出现日期",
    "文件名",
]

# 支持的文件扩展名
SUPPORTED_EXCEL_EXTS: List[str] = [".xlsx", ".xls"]
SUPPORTED_PDF_EXTS: List[str] = [".pdf"]

# 默认列名映射（用于自动识别）
COLUMN_MAPPING: Dict[str, List[str]] = {
    "发票代码": ["发票代码", "代码", "发票代码:", "电子发票代码"],
    "发票号码": ["发票号码", "号码", "发票号码:", "电子发票号码", "发票号码："],
    "开票日期": ["开票日期", "日期", "开票日期:", "开票日期："],
    "金额": ["金额", "价税合计", "合计金额", "总金额", "含税金额"],
    "销售方名称": ["销售方名称", "销售方", "卖方", "销售方:"],
    "校验码": ["校验码", "校验码:", "校验码："],
}

# ==================== 查重配置 ====================
# 查重状态定义
DUPLICATE_STATUS = {
    "NORMAL": "正常",
    "DUPLICATE": "重复",
    "PENDING": "待修正",
    "ERROR": "解析失败",
}

# 结果文件列名
RESULT_COLUMNS: List[str] = [
    "发票代码",
    "发票号码",
    "开票日期",
    "金额",
    "校验码",
    "销售方名称",
    "查重状态",
    "首次出现日期",
    "文件名",
    "文件路径",
]

# ==================== 文件路径配置 ====================
# 默认文件名
DEFAULT_DB_FILENAME: str = "history_invoices.xlsx"
DEFAULT_RESULT_FILENAME: str = "查重结果_{timestamp}.xlsx"

# 临时目录
TEMP_DIR: str = "temp"

# ==================== 日志配置 ====================
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE: str = "invoice_checker.log"

# ==================== 消息提示 ====================
MESSAGES = {
    "select_pdf": "请选择 PDF 发票文件",
    "select_db": "请选择历史数据库 Excel 文件",
    "processing": "正在处理...",
    "completed": "处理完成",
    "no_files": "未选择任何文件",
    "db_not_set": "请先设置历史数据库",
    "db_load_error": "数据库加载失败，请检查文件格式",
    "pdf_parse_error": "PDF 解析失败",
    "export_success": "导出成功",
    "export_error": "导出失败",
}
