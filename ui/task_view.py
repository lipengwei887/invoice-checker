"""
查重任务页面
执行查重操作
"""

import threading
from typing import Callable, List, Optional, Dict

import customtkinter as ctk

from utils.config import COLORS, DUPLICATE_STATUS
from core.pdf_extractor import InvoiceData
from core.excel_manager import ExcelManager
from core.duplicate_checker import DuplicateChecker, DuplicateReportGenerator


class TaskView(ctk.CTkFrame):
    """
    查重任务页面
    """
    
    def __init__(
        self,
        master,
        excel_manager: Optional[ExcelManager] = None,
        on_check_complete: Optional[Callable[[List[Dict]], None]] = None,
        **kwargs
    ):
        """
        初始化查重任务页面
        
        Args:
            master: 父组件
            excel_manager: Excel 管理器实例
            on_check_complete: 查重完成回调
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.excel_manager = excel_manager
        self.on_check_complete = on_check_complete
        
        self.invoices_data: List[Dict] = []
        self.check_results: List[Dict] = []
        self.is_checking = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """
        创建页面组件
        """
        # 标题
        title = ctk.CTkLabel(
            self,
            text="查重任务",
            font=("Microsoft YaHei", 20, "bold"),
            text_color=COLORS["text"]
        )
        title.pack(anchor="w", pady=(20, 10), padx=20)
        
        # 说明
        desc = ctk.CTkLabel(
            self,
            text="将导入的发票与历史数据库进行比对，识别重复发票",
            font=("Microsoft YaHei", 12),
            text_color=COLORS["text_secondary"]
        )
        desc.pack(anchor="w", padx=20)
        
        # 状态区域
        self._create_status_section()
        
        # 配置区域
        self._create_config_section()
        
        # 进度区域
        self._create_progress_section()
        
        # 操作按钮
        self._create_action_section()
    
    def _create_status_section(self):
        """
        创建状态显示区域
        """
        status_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        status_frame.pack(fill="x", padx=20, pady=20)
        
        status_title = ctk.CTkLabel(
            status_frame,
            text="任务状态",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=COLORS["text"]
        )
        status_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 状态网格
        grid = ctk.CTkFrame(status_frame, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=5)
        
        # 待查重数量
        self._create_status_row(grid, "待查重发票:", "0 张", 0)
        # 数据库状态
        self._create_status_row(grid, "数据库状态:", "未设置", 1)
        # 任务状态
        self._create_status_row(grid, "任务状态:", "等待开始", 2)
    
    def _create_status_row(self, parent, label: str, value: str, row: int):
        """
        创建状态行
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
        
        setattr(self, f"status_{row}", value_widget)
    
    def _create_config_section(self):
        """
        创建配置区域
        """
        config_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        config_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        config_title = ctk.CTkLabel(
            config_frame,
            text="任务配置",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=COLORS["text"]
        )
        config_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 自动追加选项
        self.auto_append_var = ctk.BooleanVar(value=False)
        
        auto_append_cb = ctk.CTkCheckBox(
            config_frame,
            text="查重完成后，自动将正常发票追加到历史数据库",
            variable=self.auto_append_var,
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text"]
        )
        auto_append_cb.pack(anchor="w", padx=15, pady=5)
        
        # 提示文本
        hint = ctk.CTkLabel(
            config_frame,
            text="提示：重复发票不会被追加到数据库",
            font=("Microsoft YaHei", 10),
            text_color=COLORS["text_secondary"]
        )
        hint.pack(anchor="w", padx=15, pady=(0, 15))
    
    def _create_progress_section(self):
        """
        创建进度显示区域
        """
        self.progress_frame = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=10)
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.progress_frame.pack_forget()  # 默认隐藏
        
        progress_title = ctk.CTkLabel(
            self.progress_frame,
            text="处理进度",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=COLORS["text"]
        )
        progress_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            mode="determinate",
            height=10
        )
        self.progress_bar.pack(fill="x", padx=15, pady=5)
        self.progress_bar.set(0)
        
        # 进度文本
        self.progress_text = ctk.CTkLabel(
            self.progress_frame,
            text="准备开始...",
            font=("Microsoft YaHei", 11),
            text_color=COLORS["text_secondary"]
        )
        self.progress_text.pack(anchor="w", padx=15, pady=(5, 15))
    
    def _create_action_section(self):
        """
        创建操作按钮区域
        """
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.start_btn = ctk.CTkButton(
            action_frame,
            text="开始查重",
            command=self._on_start_check,
            width=150,
            height=40,
            font=("Microsoft YaHei", 14, "bold")
        )
        self.start_btn.pack(side="right")
    
    def set_invoices_data(self, invoices: List[InvoiceData]):
        """
        设置待查重的发票数据
        
        Args:
            invoices: InvoiceData 列表
        """
        self.invoices_data = [inv.to_dict() for inv in invoices]
        self._update_status()
    
    def set_excel_manager(self, excel_manager: Optional[ExcelManager]):
        """
        设置 Excel 管理器
        
        Args:
            excel_manager: ExcelManager 实例
        """
        self.excel_manager = excel_manager
        self._update_status()
    
    def _update_status(self):
        """
        更新状态显示
        """
        # 待查重数量
        count = len(self.invoices_data)
        self.status_0.configure(text=f"{count} 张")
        
        # 数据库状态
        if self.excel_manager and self.excel_manager.is_loaded:
            db_status = f"已加载 ({self.excel_manager.get_statistics().get('total_records', 0)} 条记录)"
            db_color = COLORS["success"]
        else:
            db_status = "未设置"
            db_color = COLORS["warning"]
        
        self.status_1.configure(text=db_status, text_color=db_color)
    
    def _on_start_check(self):
        """
        开始查重
        """
        if self.is_checking:
            return
        
        # 检查数据
        if not self.invoices_data:
            self._set_task_status("请先导入 PDF 发票", "warning")
            return
        
        # 检查数据库（可选，但建议设置）
        if not self.excel_manager or not self.excel_manager.is_loaded:
            # 询问是否继续
            result = ctk.CTkInputDialog(
                text="未设置历史数据库，将只进行批次内查重。是否继续？",
                title="确认"
            )
            # 简化处理，实际应该使用确认对话框
        
        # 开始查重
        self.is_checking = True
        self._show_progress()
        self._set_task_status("正在查重...", "info")
        self.start_btn.configure(state="disabled")
        
        # 在后台线程执行
        thread = threading.Thread(target=self._do_check, daemon=True)
        thread.start()
    
    def _do_check(self):
        """
        执行查重（在后台线程）
        """
        try:
            checker = DuplicateChecker()
            
            # 分批处理并更新进度
            total = len(self.invoices_data)
            batch_size = max(1, total // 10)
            results = []
            
            for i in range(0, total, batch_size):
                batch = self.invoices_data[i:i + batch_size]
                
                # 执行查重
                batch_results = checker.check_with_excel_manager(
                    batch, 
                    self.excel_manager
                )
                results.extend(batch_results)
                
                # 更新进度
                progress = min(100, (i + batch_size) / total * 100)
                self.after(0, lambda p=progress: self._update_progress(p))
            
            self.check_results = results
            
            # 自动追加到数据库
            if self.auto_append_var.get() and self.excel_manager:
                normals = [r for r in results 
                          if r.get('查重状态') == DUPLICATE_STATUS["NORMAL"]]
                if normals:
                    self.excel_manager.append_invoices(normals, auto_save=True)
            
            # 完成
            self.after(0, self._on_check_complete)
            
        except Exception as e:
            self.after(0, lambda: self._on_check_error(str(e)))
    
    def _update_progress(self, progress: float):
        """
        更新进度
        
        Args:
            progress: 进度值 (0-100)
        """
        self.progress_bar.set(progress / 100)
        self.progress_text.configure(text=f"正在查重... {int(progress)}%")
    
    def _on_check_complete(self):
        """
        查重完成处理
        """
        self.is_checking = False
        self._hide_progress()
        self.start_btn.configure(state="normal")
        
        # 生成报告
        generator = DuplicateReportGenerator()
        generator.categorize(self.check_results)
        report = generator.generate_summary()
        
        self._set_task_status("查重完成", "success")
        
        # 回调
        if self.on_check_complete:
            self.on_check_complete(self.check_results)
    
    def _on_check_error(self, error_msg: str):
        """
        查重出错处理
        
        Args:
            error_msg: 错误信息
        """
        self.is_checking = False
        self._hide_progress()
        self.start_btn.configure(state="normal")
        self._set_task_status(f"查重失败: {error_msg}", "error")
    
    def _show_progress(self):
        """
        显示进度区域
        """
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 20), before=self.winfo_children()[-1])
        self.progress_bar.set(0)
    
    def _hide_progress(self):
        """
        隐藏进度区域
        """
        self.progress_frame.pack_forget()
    
    def _set_task_status(self, message: str, status_type: str = "info"):
        """
        设置任务状态
        
        Args:
            message: 状态消息
            status_type: 状态类型
        """
        colors = {
            "info": COLORS["text"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["danger"]
        }
        
        self.status_2.configure(text=message, text_color=colors.get(status_type, COLORS["text"]))
    
    def get_results(self) -> List[Dict]:
        """
        获取查重结果
        
        Returns:
            查重结果列表
        """
        return self.check_results
    
    def clear(self):
        """
        清空数据
        """
        self.invoices_data.clear()
        self.check_results.clear()
        self._update_status()
        self._set_task_status("等待开始", "info")
