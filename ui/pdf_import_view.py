"""
PDF 导入页面
支持文件选择和拖拽导入
"""

import os
import tkinter as tk
from tkinter import filedialog
from typing import Callable, List, Optional, Dict

import customtkinter as ctk

from utils.config import COLORS, MESSAGES, SUPPORTED_PDF_EXTS
from core.pdf_extractor import PDFInvoiceExtractor, InvoiceData


class DragDropFrame(ctk.CTkFrame):
    """
    拖拽区域组件
    支持文件拖拽
    """
    
    def __init__(
        self,
        master,
        on_files_dropped: Callable[[List[str]], None],
        **kwargs
    ):
        """
        初始化拖拽区域
        
        Args:
            master: 父组件
            on_files_dropped: 文件拖入回调
        """
        super().__init__(
            master,
            fg_color=COLORS["background"],
            corner_radius=10,
            border_width=2,
            border_color=COLORS["border"],
            **kwargs
        )
        
        self.on_files_dropped = on_files_dropped
        
        # 创建内容
        self._create_content()
        
        # 绑定拖拽事件（如果支持）
        self._bind_drag_events()
    
    def _create_content(self):
        """
        创建拖拽区域内容
        """
        # 图标/文字
        self.icon_label = ctk.CTkLabel(
            self,
            text="📁",
            font=("Microsoft YaHei", 48)
        )
        self.icon_label.pack(pady=(40, 10))
        
        self.text_label = ctk.CTkLabel(
            self,
            text="拖拽 PDF 文件到此处",
            font=("Microsoft YaHei", 14),
            text_color=COLORS["text"]
        )
        self.text_label.pack(pady=5)
        
        self.sub_text_label = ctk.CTkLabel(
            self,
            text="或点击选择文件",
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text_secondary"]
        )
        self.sub_text_label.pack(pady=5)
        
        # 选择文件按钮
        self.select_btn = ctk.CTkButton(
            self,
            text="选择文件",
            command=self._on_select_click,
            width=120,
            height=32,
            font=("Microsoft YaHei", 12)
        )
        self.select_btn.pack(pady=(10, 40))
    
    def _bind_drag_events(self):
        """
        绑定拖拽事件
        """
        # 尝试绑定 Tkinter DND（如果可用）
        try:
            # 进入区域
            self.bind('<Enter>', self._on_drag_enter)
            # 离开区域
            self.bind('<Leave>', self._on_drag_leave)
            # 释放
            self.bind('<ButtonRelease-1>', self._on_drop)
        except Exception:
            pass
        
        # 点击整个区域也可以选择文件
        self.bind('<Button-1>', lambda e: self._on_select_click())
        self.icon_label.bind('<Button-1>', lambda e: self._on_select_click())
        self.text_label.bind('<Button-1>', lambda e: self._on_select_click())
        self.sub_text_label.bind('<Button-1>', lambda e: self._on_select_click())
    
    def _on_drag_enter(self, event):
        """
        拖拽进入
        """
        self.configure(border_color=COLORS["primary"])
    
    def _on_drag_leave(self, event):
        """
        拖拽离开
        """
        self.configure(border_color=COLORS["border"])
    
    def _on_drop(self, event):
        """
        文件释放
        """
        self.configure(border_color=COLORS["border"])
        # 实际拖拽处理需要 tkinterdnd2 库支持
        # 这里仅作占位
    
    def _on_select_click(self):
        """
        选择文件按钮点击
        """
        file_paths = filedialog.askopenfilenames(
            title="选择 PDF 发票文件",
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if file_paths:
            self.on_files_dropped(list(file_paths))


class FileListFrame(ctk.CTkFrame):
    """
    文件列表组件
    显示已选择的文件
    """
    
    def __init__(self, master, on_remove: Optional[Callable[[int], None]] = None, **kwargs):
        """
        初始化文件列表
        
        Args:
            master: 父组件
            on_remove: 移除文件回调，参数为索引
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.on_remove = on_remove
        self.files: List[str] = []
        self.file_frames: List[ctk.CTkFrame] = []
        
        # 标题
        self.header_label = ctk.CTkLabel(
            self,
            text="已选择文件",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=COLORS["text"]
        )
        self.header_label.pack(anchor="w", pady=(0, 10))
        
        # 列表容器（带滚动条）
        self.list_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=200
        )
        self.list_container.pack(fill="both", expand=True)
        
        # 统计标签
        self.stats_label = ctk.CTkLabel(
            self,
            text="共 0 个文件",
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text_secondary"]
        )
        self.stats_label.pack(anchor="e", pady=(10, 0))
    
    def add_files(self, file_paths: List[str]):
        """
        添加文件到列表
        
        Args:
            file_paths: 文件路径列表
        """
        for path in file_paths:
            if path not in self.files:
                self.files.append(path)
                self._create_file_item(path, len(self.files) - 1)
        
        self._update_stats()
    
    def remove_file(self, index: int):
        """
        移除文件
        
        Args:
            index: 文件索引
        """
        if 0 <= index < len(self.files):
            self.files.pop(index)
            self._refresh_list()
            self._update_stats()
            
            if self.on_remove:
                self.on_remove(index)
    
    def clear(self):
        """
        清空列表
        """
        self.files.clear()
        self._refresh_list()
        self._update_stats()
    
    def get_files(self) -> List[str]:
        """
        获取所有文件路径
        
        Returns:
            文件路径列表
        """
        return self.files.copy()
    
    def _create_file_item(self, file_path: str, index: int):
        """
        创建文件项
        
        Args:
            file_path: 文件路径
            index: 索引
        """
        frame = ctk.CTkFrame(self.list_container, fg_color=COLORS["background"], height=40)
        frame.pack(fill="x", pady=2)
        frame.pack_propagate(False)
        
        # 文件名
        file_name = os.path.basename(file_path)
        name_label = ctk.CTkLabel(
            frame,
            text=file_name,
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text"]
        )
        name_label.pack(side="left", padx=10)
        
        # 移除按钮
        remove_btn = ctk.CTkButton(
            frame,
            text="✕",
            width=28,
            height=28,
            font=("Microsoft YaHei", 11),
            fg_color="transparent",
            text_color=COLORS["danger"],
            hover_color=COLORS["border"],
            command=lambda idx=index: self.remove_file(idx)
        )
        remove_btn.pack(side="right", padx=5)
    
    def _refresh_list(self):
        """
        刷新列表显示
        """
        # 清空容器
        for widget in self.list_container.winfo_children():
            widget.destroy()
        
        # 重新创建
        for i, path in enumerate(self.files):
            self._create_file_item(path, i)
    
    def _update_stats(self):
        """
        更新统计信息
        """
        self.stats_label.configure(text=f"共 {len(self.files)} 个文件")


class PDFImportView(ctk.CTkFrame):
    """
    PDF 导入页面
    """
    
    def __init__(
        self,
        master,
        on_extract: Optional[Callable[[List[InvoiceData]], None]] = None,
        **kwargs
    ):
        """
        初始化导入页面
        
        Args:
            master: 父组件
            on_extract: 提取完成回调
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.on_extract = on_extract
        self.extractor = PDFInvoiceExtractor()
        self.extracted_data: List[InvoiceData] = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        """
        创建页面组件
        """
        # 标题
        title = ctk.CTkLabel(
            self,
            text="导入 PDF 发票",
            font=("Microsoft YaHei", 20, "bold"),
            text_color=COLORS["text"]
        )
        title.pack(anchor="w", pady=(20, 20), padx=20)
        
        # 拖拽区域
        self.drag_drop = DragDropFrame(
            self,
            on_files_dropped=self._on_files_added,
            height=200
        )
        self.drag_drop.pack(fill="x", padx=20, pady=10)
        
        # 文件列表
        self.file_list = FileListFrame(
            self,
            on_remove=self._on_file_removed
        )
        self.file_list.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 进度条（默认隐藏）
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        self.progress_frame.pack_forget()  # 隐藏
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="正在解析...",
            font=("Microsoft YaHei", 11)
        )
        self.progress_label.pack(anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            mode="determinate",
            height=8
        )
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.set(0)
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="清空列表",
            command=self._on_clear,
            width=100,
            height=32,
            font=("Microsoft YaHei", 12),
            fg_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color="#CCCCCC"
        )
        self.clear_btn.pack(side="left", padx=5)
        
        self.extract_btn = ctk.CTkButton(
            btn_frame,
            text="开始解析",
            command=self._on_extract,
            width=120,
            height=32,
            font=("Microsoft YaHei", 12, "bold")
        )
        self.extract_btn.pack(side="right", padx=5)
    
    def _on_files_added(self, file_paths: List[str]):
        """
        文件添加处理
        
        Args:
            file_paths: 文件路径列表
        """
        # 过滤非 PDF 文件
        pdf_files = [f for f in file_paths if f.lower().endswith('.pdf')]
        
        if len(pdf_files) < len(file_paths):
            skipped = len(file_paths) - len(pdf_files)
            # 可以在这里显示提示
        
        self.file_list.add_files(pdf_files)
    
    def _on_file_removed(self, index: int):
        """
        文件移除处理
        
        Args:
            index: 移除的文件索引
        """
        pass  # 已在 FileListFrame 中处理
    
    def _on_clear(self):
        """
        清空列表
        """
        self.file_list.clear()
        self.extracted_data.clear()
        self._hide_progress()
    
    def _on_extract(self):
        """
        开始解析
        """
        files = self.file_list.get_files()
        
        if not files:
            # 显示提示
            return
        
        # 显示进度条
        self._show_progress()
        
        # 在后台线程执行解析
        import threading
        thread = threading.Thread(target=self._do_extract, args=(files,), daemon=True)
        thread.start()
    
    def _do_extract(self, files: List[str]):
        """
        执行解析（在后台线程）
        
        Args:
            files: 文件列表
        """
        total = len(files)
        results = []
        
        for i, file_path in enumerate(files):
            result = self.extractor.extract_from_file(file_path)
            results.append(result)
            
            # 更新进度
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self._update_progress(p))
        
        self.extracted_data = results
        
        # 完成回调
        self.after(0, self._on_extract_complete)
    
    def _update_progress(self, progress: float):
        """
        更新进度条
        
        Args:
            progress: 进度值 (0-1)
        """
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"正在解析... {int(progress * 100)}%")
    
    def _on_extract_complete(self):
        """
        解析完成处理
        """
        self._hide_progress()
        
        if self.on_extract:
            self.on_extract(self.extracted_data)
    
    def _show_progress(self):
        """
        显示进度条
        """
        self.progress_frame.pack(fill="x", padx=20, pady=10, before=self.winfo_children()[-1])
        self.progress_bar.set(0)
        self.extract_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
    
    def _hide_progress(self):
        """
        隐藏进度条
        """
        self.progress_frame.pack_forget()
        self.extract_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
    
    def get_extracted_data(self) -> List[InvoiceData]:
        """
        获取提取的数据
        
        Returns:
            InvoiceData 列表
        """
        return self.extracted_data
    
    def clear(self):
        """
        清空页面
        """
        self._on_clear()
