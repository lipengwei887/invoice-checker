"""
数据库设置页面
配置历史发票数据库
"""

import os
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk
import pandas as pd

from utils.config import COLORS, MESSAGES, DEFAULT_DB_FILENAME, REQUIRED_COLUMNS
from core.excel_manager import ExcelManager


class DatabaseView(ctk.CTkFrame):
    """
    数据库设置页面
    """
    
    def __init__(
        self,
        master,
        on_database_loaded: Optional[Callable[[ExcelManager], None]] = None,
        **kwargs
    ):
        """
        初始化数据库设置页面
        
        Args:
            master: 父组件
            on_database_loaded: 数据库加载成功回调
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.on_database_loaded = on_database_loaded
        self.excel_manager: Optional[ExcelManager] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """
        创建页面组件
        """
        # 标题
        title = ctk.CTkLabel(
            self,
            text="设置历史数据库",
            font=("Microsoft YaHei", 20, "bold"),
            text_color=COLORS["text"]
        )
        title.pack(anchor="w", pady=(20, 20), padx=20)
        
        # 说明文本
        desc = ctk.CTkLabel(
            self,
            text="选择历史发票数据库 Excel 文件，用于查重比对",
            font=("Microsoft YaHei", 12),
            text_color=COLORS["text_secondary"]
        )
        desc.pack(anchor="w", padx=20)
        
        # 文件选择区域
        self._create_file_section()
        
        # 数据库信息区域
        self._create_info_section()
        
        # 预览区域
        self._create_preview_section()
    
    def _create_file_section(self):
        """
        创建文件选择区域
        """
        file_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        file_frame.pack(fill="x", padx=20, pady=20)
        
        # 路径输入框
        path_label = ctk.CTkLabel(
            file_frame,
            text="数据库路径:",
            font=("Microsoft YaHei", 12),
            text_color=COLORS["text"]
        )
        path_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        path_input_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        path_input_frame.pack(fill="x", padx=15, pady=5)
        
        self.path_entry = ctk.CTkEntry(
            path_input_frame,
            font=("Microsoft YaHei", 11),
            height=32
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            path_input_frame,
            text="浏览...",
            command=self._on_browse,
            width=80,
            height=32,
            font=("Microsoft YaHei", 11)
        )
        browse_btn.pack(side="right")
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        self.load_btn = ctk.CTkButton(
            btn_frame,
            text="加载数据库",
            command=self._on_load,
            width=120,
            height=32,
            font=("Microsoft YaHei", 12)
        )
        self.load_btn.pack(side="left", padx=(0, 10))
        
        create_btn = ctk.CTkButton(
            btn_frame,
            text="创建新数据库",
            command=self._on_create_new,
            width=120,
            height=32,
            font=("Microsoft YaHei", 12),
            fg_color=COLORS["success"],
            hover_color="#25A070"
        )
        create_btn.pack(side="left")
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            file_frame,
            text="",
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(anchor="w", padx=15, pady=(5, 0))
    
    def _create_info_section(self):
        """
        创建数据库信息区域
        """
        info_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        info_title = ctk.CTkLabel(
            info_frame,
            text="数据库信息",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=COLORS["text"]
        )
        info_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 信息网格
        self.info_grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        self.info_grid.pack(fill="x", padx=15, pady=5)
        
        # 记录数
        self._create_info_row(self.info_grid, "记录总数:", "未加载", 0)
        # 状态
        self._create_info_row(self.info_grid, "加载状态:", "未加载", 1)
        # 文件路径
        self._create_info_row(self.info_grid, "文件路径:", "-", 2)
    
    def _create_info_row(self, parent, label: str, value: str, row: int):
        """
        创建信息行
        """
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text_secondary"],
            width=100,
            anchor="w"
        )
        label_widget.grid(row=row, column=0, sticky="w", pady=3)
        
        value_widget = ctk.CTkLabel(
            parent,
            text=value,
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text"],
            anchor="w"
        )
        value_widget.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=3)
        
        # 保存引用以便更新
        setattr(self, f"info_{row}", value_widget)
    
    def _create_preview_section(self):
        """
        创建预览区域
        """
        preview_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        preview_title = ctk.CTkLabel(
            preview_frame,
            text="数据预览（前 5 行）",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=COLORS["text"]
        )
        preview_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 预览内容（使用滚动文本框）
        self.preview_text = ctk.CTkTextbox(
            preview_frame,
            font=("Consolas", 10),
            wrap="none",
            state="disabled"
        )
        self.preview_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 默认提示
        self._update_preview("请先加载数据库文件...")
    
    def _on_browse(self):
        """
        浏览文件
        """
        file_path = filedialog.askopenfilename(
            title="选择历史数据库文件",
            filetypes=[
                ("Excel 文件", "*.xlsx *.xls"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)
    
    def _on_load(self):
        """
        加载数据库
        """
        path = self.path_entry.get().strip()
        
        if not path:
            self._set_status("请先选择数据库文件", "warning")
            return
        
        if not os.path.exists(path):
            self._set_status("文件不存在", "error")
            return
        
        # 创建管理器并加载
        self.excel_manager = ExcelManager()
        success, msg = self.excel_manager.load_database(path)
        
        if success:
            self._set_status(msg, "success")
            self._update_info()
            self._update_preview_data()
            
            if self.on_database_loaded:
                self.on_database_loaded(self.excel_manager)
        else:
            self._set_status(msg, "error")
    
    def _on_create_new(self):
        """
        创建新数据库
        """
        path = filedialog.asksaveasfilename(
            title="创建新数据库",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            initialfile=DEFAULT_DB_FILENAME
        )
        
        if path:
            self.excel_manager = ExcelManager()
            success, msg = self.excel_manager.create_new_database(path)
            
            if success:
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, path)
                self._set_status(msg, "success")
                self._update_info()
                self._update_preview_data()
                
                if self.on_database_loaded:
                    self.on_database_loaded(self.excel_manager)
            else:
                self._set_status(msg, "error")
    
    def _set_status(self, message: str, status_type: str = "info"):
        """
        设置状态信息
        
        Args:
            message: 消息文本
            status_type: 状态类型 (info/success/warning/error)
        """
        colors = {
            "info": COLORS["text_secondary"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["danger"]
        }
        
        self.status_label.configure(text=message, text_color=colors.get(status_type, COLORS["text"]))
    
    def _update_info(self):
        """
        更新数据库信息
        """
        if not self.excel_manager or not self.excel_manager.is_loaded:
            return
        
        stats = self.excel_manager.get_statistics()
        
        # 更新记录数
        self.info_0.configure(text=str(stats.get("total_records", 0)))
        # 更新状态
        self.info_1.configure(text="已加载", text_color=COLORS["success"])
        # 更新路径
        path = stats.get("db_path", "-")
        if len(path) > 50:
            path = "..." + path[-47:]
        self.info_2.configure(text=path)
    
    def _update_preview_data(self):
        """
        更新预览数据
        """
        if not self.excel_manager or not self.excel_manager.is_loaded:
            self._update_preview("数据库未加载")
            return
        
        preview_df = self.excel_manager.get_preview(5)
        
        if preview_df is None or preview_df.empty:
            self._update_preview("数据库为空")
            return
        
        # 格式化显示
        text = preview_df.to_string(index=False)
        self._update_preview(text)
    
    def _update_preview(self, text: str):
        """
        更新预览文本
        
        Args:
            text: 预览文本
        """
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")
    
    def get_excel_manager(self) -> Optional[ExcelManager]:
        """
        获取 Excel 管理器实例
        
        Returns:
            ExcelManager 实例或 None
        """
        return self.excel_manager
    
    def is_database_loaded(self) -> bool:
        """
        检查数据库是否已加载
        
        Returns:
            是否已加载
        """
        return self.excel_manager is not None and self.excel_manager.is_loaded
