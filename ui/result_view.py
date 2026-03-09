"""
结果查看页面
显示查重结果，支持筛选和导出
"""

import os
from tkinter import filedialog, messagebox
from typing import Callable, List, Optional, Dict
from datetime import datetime

import customtkinter as ctk

from utils.config import COLORS, DUPLICATE_STATUS, DEFAULT_RESULT_FILENAME
from core.excel_manager import ExcelManager


class ResultTable(ctk.CTkFrame):
    """
    结果表格组件
    使用 Treeview 实现表格显示
    """
    
    def __init__(self, master, **kwargs):
        """
        初始化结果表格
        
        Args:
            master: 父组件
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.results: List[Dict] = []
        self.filtered_results: List[Dict] = []
        
        self._create_table()
    
    def _create_table(self):
        """
        创建表格
        """
        import tkinter as tk
        from tkinter import ttk
        
        # 样式配置
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置 Treeview 样式
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground=COLORS["text"],
            fieldbackground="white",
            rowheight=28,
            font=("Microsoft YaHei", 10)
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=("Microsoft YaHei", 10, "bold")
        )
        
        # 定义列
        columns = [
            ("发票代码", 100),
            ("发票号码", 120),
            ("开票日期", 100),
            ("金额", 100),
            ("销售方名称", 200),
            ("查重状态", 80),
            ("文件名", 200),
        ]
        
        # 创建 Treeview
        self.tree = ttk.Treeview(
            self,
            columns=[c[0] for c in columns],
            show="headings",
            style="Custom.Treeview"
        )
        
        # 设置列
        for col_name, width in columns:
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor="center")
        
        # 滚动条
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self._on_double_click)
    
    def set_data(self, results: List[Dict]):
        """
        设置表格数据
        
        Args:
            results: 结果列表
        """
        self.results = results
        self.filtered_results = results.copy()
        self._refresh_table()
    
    def filter_by_status(self, status: Optional[str] = None):
        """
        按状态筛选
        
        Args:
            status: 状态值，None 表示全部
        """
        if status is None:
            self.filtered_results = self.results.copy()
        else:
            self.filtered_results = [
                r for r in self.results 
                if r.get('查重状态') == status
            ]
        
        self._refresh_table()
    
    def _refresh_table(self):
        """
        刷新表格显示
        """
        # 清空
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 填充数据
        for row in self.filtered_results:
            values = [
                row.get('发票代码', ''),
                row.get('发票号码', ''),
                row.get('开票日期', ''),
                row.get('金额', ''),
                row.get('销售方名称', ''),
                row.get('查重状态', ''),
                row.get('文件名', ''),
            ]
            
            # 根据状态设置标签（用于颜色）
            status = row.get('查重状态', '')
            tags = []
            if status == DUPLICATE_STATUS["DUPLICATE"]:
                tags.append("duplicate")
            elif status == DUPLICATE_STATUS["PENDING"]:
                tags.append("pending")
            elif status == DUPLICATE_STATUS["ERROR"]:
                tags.append("error")
            
            item_id = self.tree.insert("", "end", values=values, tags=tags)
        
        # 配置标签颜色
        self.tree.tag_configure("duplicate", background="#FFEBEE")  # 浅红
        self.tree.tag_configure("pending", background="#FFF8E1")    # 浅黄
        self.tree.tag_configure("error", background="#FFEBEE")      # 浅红
    
    def _on_double_click(self, event):
        """
        双击行处理
        """
        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        # 可以显示详细信息对话框
    
    def get_selected(self) -> Optional[Dict]:
        """
        获取选中的行数据
        
        Returns:
            选中行的数据字典
        """
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        idx = self.tree.index(item)
        
        if 0 <= idx < len(self.filtered_results):
            return self.filtered_results[idx]
        
        return None
    
    def get_all_data(self) -> List[Dict]:
        """
        获取所有数据
        
        Returns:
            所有结果数据
        """
        return self.results


class ResultView(ctk.CTkFrame):
    """
    结果查看页面
    """
    
    def __init__(
        self,
        master,
        excel_manager: Optional[ExcelManager] = None,
        **kwargs
    ):
        """
        初始化结果查看页面
        
        Args:
            master: 父组件
            excel_manager: Excel 管理器实例
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.excel_manager = excel_manager
        
        self._create_widgets()
    
    def _create_widgets(self):
        """
        创建页面组件
        """
        # 标题
        title = ctk.CTkLabel(
            self,
            text="查重结果",
            font=("Microsoft YaHei", 20, "bold"),
            text_color=COLORS["text"]
        )
        title.pack(anchor="w", pady=(20, 10), padx=20)
        
        # 统计区域
        self._create_stats_section()
        
        # 筛选区域
        self._create_filter_section()
        
        # 表格区域
        self._create_table_section()
        
        # 操作按钮
        self._create_action_section()
    
    def _create_stats_section(self):
        """
        创建统计区域
        """
        stats_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        stats_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # 统计卡片
        self.stat_cards: Dict[str, ctk.CTkLabel] = {}
        
        stats_data = [
            ("总计", "0", COLORS["text"]),
            ("正常", "0", COLORS["success"]),
            ("重复", "0", COLORS["danger"]),
            ("待修正", "0", COLORS["warning"]),
        ]
        
        for i, (name, value, color) in enumerate(stats_data):
            card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=8, width=120, height=70)
            card.pack(side="left", padx=10, pady=15)
            card.pack_propagate(False)
            
            name_label = ctk.CTkLabel(
                card,
                text=name,
                font=("Microsoft YaHei", 11),
                text_color=COLORS["text_secondary"]
            )
            name_label.pack(pady=(10, 0))
            
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=("Microsoft YaHei", 18, "bold"),
                text_color=color
            )
            value_label.pack()
            
            self.stat_cards[name] = value_label
    
    def _create_filter_section(self):
        """
        创建筛选区域
        """
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        filter_label = ctk.CTkLabel(
            filter_frame,
            text="筛选:",
            font=("Microsoft YaHei", 12),
            text_color=COLORS["text"]
        )
        filter_label.pack(side="left", padx=(0, 10))
        
        # 筛选按钮
        filters = [
            ("全部", None),
            ("正常", DUPLICATE_STATUS["NORMAL"]),
            ("重复", DUPLICATE_STATUS["DUPLICATE"]),
            ("待修正", DUPLICATE_STATUS["PENDING"]),
        ]
        
        self.filter_buttons: Dict[str, ctk.CTkButton] = {}
        
        for text, status in filters:
            btn = ctk.CTkButton(
                filter_frame,
                text=text,
                command=lambda s=status, t=text: self._on_filter(s, t),
                width=70,
                height=28,
                font=("Microsoft YaHei", 11),
                fg_color=COLORS["primary"] if status is None else "transparent",
                text_color="white" if status is None else COLORS["text"],
                hover_color=COLORS["border"]
            )
            btn.pack(side="left", padx=5)
            self.filter_buttons[text] = btn
        
        self.current_filter = "全部"
    
    def _create_table_section(self):
        """
        创建表格区域
        """
        table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 结果表格
        self.result_table = ResultTable(table_frame)
        self.result_table.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_action_section(self):
        """
        创建操作按钮区域
        """
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # 导出结果按钮
        export_result_btn = ctk.CTkButton(
            action_frame,
            text="导出查重结果",
            command=self._on_export_result,
            width=140,
            height=36,
            font=("Microsoft YaHei", 12)
        )
        export_result_btn.pack(side="left", padx=5)
        
        # 更新数据库按钮
        update_db_btn = ctk.CTkButton(
            action_frame,
            text="更新历史数据库",
            command=self._on_update_database,
            width=140,
            height=36,
            font=("Microsoft YaHei", 12),
            fg_color=COLORS["success"],
            hover_color="#25A070"
        )
        update_db_btn.pack(side="left", padx=5)
    
    def set_results(self, results: List[Dict]):
        """
        设置结果显示
        
        Args:
            results: 查重结果列表
        """
        self.result_table.set_data(results)
        self._update_stats(results)
    
    def _update_stats(self, results: List[Dict]):
        """
        更新统计数据
        
        Args:
            results: 结果列表
        """
        total = len(results)
        normal = sum(1 for r in results if r.get('查重状态') == DUPLICATE_STATUS["NORMAL"])
        duplicate = sum(1 for r in results if r.get('查重状态') == DUPLICATE_STATUS["DUPLICATE"])
        pending = sum(1 for r in results if r.get('查重状态') == DUPLICATE_STATUS["PENDING"])
        
        self.stat_cards["总计"].configure(text=str(total))
        self.stat_cards["正常"].configure(text=str(normal))
        self.stat_cards["重复"].configure(text=str(duplicate))
        self.stat_cards["待修正"].configure(text=str(pending))
    
    def _on_filter(self, status: Optional[str], filter_name: str):
        """
        筛选按钮点击
        
        Args:
            status: 状态值
            filter_name: 筛选名称
        """
        # 更新按钮样式
        for name, btn in self.filter_buttons.items():
            if name == filter_name:
                btn.configure(fg_color=COLORS["primary"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text"])
        
        self.current_filter = filter_name
        
        # 应用筛选
        self.result_table.filter_by_status(status)
    
    def _on_export_result(self):
        """
        导出结果
        """
        results = self.result_table.get_all_data()
        
        if not results:
            messagebox.showwarning("警告", "没有可导出的数据")
            return
        
        # 选择保存路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = DEFAULT_RESULT_FILENAME.format(timestamp=timestamp)
        
        file_path = filedialog.asksaveasfilename(
            title="导出查重结果",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            initialfile=default_name
        )
        
        if not file_path:
            return
        
        # 导出
        if self.excel_manager:
            success, msg = self.excel_manager.export_results(results, file_path)
        else:
            # 创建临时管理器导出
            from core.excel_manager import ExcelManager
            temp_manager = ExcelManager()
            success, msg = temp_manager.export_results(results, file_path)
        
        if success:
            messagebox.showinfo("成功", msg)
        else:
            messagebox.showerror("错误", msg)
    
    def _on_update_database(self):
        """
        更新历史数据库
        """
        if not self.excel_manager or not self.excel_manager.is_loaded:
            messagebox.showwarning("警告", "请先设置历史数据库")
            return
        
        results = self.result_table.get_all_data()
        
        # 筛选正常发票
        normals = [
            r for r in results 
            if r.get('查重状态') == DUPLICATE_STATUS["NORMAL"]
        ]
        
        if not normals:
            messagebox.showinfo("提示", "没有可追加的正常发票")
            return
        
        # 确认对话框
        if messagebox.askyesno(
            "确认",
            f"确定要将 {len(normals)} 张正常发票追加到历史数据库吗？"
        ):
            success, msg = self.excel_manager.append_invoices(normals, auto_save=True)
            
            if success:
                messagebox.showinfo("成功", msg)
            else:
                messagebox.showerror("错误", msg)
    
    def set_excel_manager(self, excel_manager: Optional[ExcelManager]):
        """
        设置 Excel 管理器
        
        Args:
            excel_manager: ExcelManager 实例
        """
        self.excel_manager = excel_manager
    
    def clear(self):
        """
        清空结果
        """
        self.result_table.set_data([])
        self._update_stats([])
