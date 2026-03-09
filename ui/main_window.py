"""
主窗口
整合所有 UI 组件
"""

import sys
from typing import Optional, List, Dict

import customtkinter as ctk

# 添加项目根目录到路径
sys.path.insert(0, '/Users/lipengwei/Downloads/代码/qoder/invoice_checker')

from utils.config import (
    APP_NAME, 
    APP_VERSION, 
    DEFAULT_WINDOW_SIZE,
    MIN_WINDOW_SIZE,
    THEME_MODE,
    COLOR_THEME,
    COLORS
)
from core.excel_manager import ExcelManager
from core.pdf_extractor import InvoiceData

from ui.sidebar import Sidebar
from ui.pdf_import_view import PDFImportView
from ui.database_view import DatabaseView
from ui.task_view import TaskView
from ui.result_view import ResultView


# 在类定义之前设置主题（全局设置）
ctk.set_appearance_mode(THEME_MODE)
ctk.set_default_color_theme(COLOR_THEME)


class MainWindow(ctk.CTk):
    """
    应用程序主窗口
    """
    
    def __init__(self):
        """
        初始化主窗口
        """
        super().__init__()
        
        # 窗口配置
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{DEFAULT_WINDOW_SIZE[0]}x{DEFAULT_WINDOW_SIZE[1]}")
        self.minsize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1])
        
        # 数据共享
        self.excel_manager: Optional[ExcelManager] = None
        self.extracted_invoices: List[InvoiceData] = []
        self.check_results: List[Dict] = []
        self.current_page_id: str = ""
        
        # 创建 UI
        self._create_layout()
        self._create_pages()
        
        # 显示默认页面
        self._show_page("import_pdf")
    
    def _create_layout(self):
        """
        创建布局框架
        """
        # 主容器配置
        self.grid_columnconfigure(0, weight=0)  # sidebar 列不扩展
        self.grid_columnconfigure(1, weight=1)  # 内容区列扩展
        self.grid_rowconfigure(0, weight=1)
        
        # 左侧导航栏
        self.sidebar = Sidebar(
            self,
            on_navigate=self._on_navigate,
            width=200
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 右侧内容区容器
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color="white",
            corner_radius=0
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def _create_pages(self):
        """
        创建各个页面
        """
        self.pages: Dict[str, ctk.CTkFrame] = {}
        
        # PDF 导入页面
        self.pdf_import_view = PDFImportView(
            self.content_frame,
            on_extract=self._on_extract_complete
        )
        self.pages["import_pdf"] = self.pdf_import_view
        
        # 数据库设置页面
        self.database_view = DatabaseView(
            self.content_frame,
            on_database_loaded=self._on_database_loaded
        )
        self.pages["database"] = self.database_view
        
        # 查重任务页面
        self.task_view = TaskView(
            self.content_frame,
            excel_manager=self.excel_manager,
            on_check_complete=self._on_check_complete
        )
        self.pages["task"] = self.task_view
        
        # 结果查看页面
        self.result_view = ResultView(
            self.content_frame,
            excel_manager=self.excel_manager
        )
        self.pages["result"] = self.result_view
        
        # 初始布局（全部隐藏）
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()
    
    def _show_page(self, page_id: str):
        """
        显示指定页面
        
        Args:
            page_id: 页面标识
        """
        # 隐藏所有页面
        for page in self.pages.values():
            page.grid_remove()
        
        # 显示指定页面
        if page_id in self.pages:
            self.pages[page_id].grid()
            self.sidebar.set_active_page(page_id)
    
    def _on_navigate(self, page_id: str):
        """
        导航处理
        
        Args:
            page_id: 页面标识
        """
        self._show_page(page_id)
    
    def _on_extract_complete(self, invoices: List[InvoiceData]):
        """
        PDF 提取完成回调
        
        Args:
            invoices: 提取的发票数据
        """
        self.extracted_invoices = invoices
        
        # 更新查重任务页面的数据
        self.task_view.set_invoices_data(invoices)
        
        # 自动跳转到查重任务页面
        self._show_page("task")
        
        # 显示提示
        total = len(invoices)
        success = sum(1 for inv in invoices if inv.status == "正常")
        
        import tkinter.messagebox as msgbox
        msgbox.showinfo(
            "提取完成",
            f"成功提取 {success}/{total} 张发票信息\n\n请检查提取结果后执行查重任务。"
        )
    
    def _on_database_loaded(self, excel_manager: ExcelManager):
        """
        数据库加载完成回调
        
        Args:
            excel_manager: ExcelManager 实例
        """
        self.excel_manager = excel_manager
        
        # 更新其他页面的 Excel 管理器
        self.task_view.set_excel_manager(excel_manager)
        self.result_view.set_excel_manager(excel_manager)
    
    def _on_check_complete(self, results: List[Dict]):
        """
        查重完成回调
        
        Args:
            results: 查重结果
        """
        self.check_results = results
        
        # 更新结果页面
        self.result_view.set_results(results)
        
        # 自动跳转到结果页面
        self._show_page("result")
        
        # 生成统计信息
        total = len(results)
        duplicate = sum(1 for r in results if r.get('查重状态') == "重复")
        normal = sum(1 for r in results if r.get('查重状态') == "正常")
        
        import tkinter.messagebox as msgbox
        msgbox.showinfo(
            "查重完成",
            f"查重结果统计：\n"
            f"- 总计: {total} 张\n"
            f"- 正常: {normal} 张\n"
            f"- 重复: {duplicate} 张"
        )
    
    def run(self):
        """
        运行应用程序
        """
        self.mainloop()


def main():
    """
    主函数
    """
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
