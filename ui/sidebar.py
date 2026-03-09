"""
左侧导航栏组件
提供功能导航切换
"""

import customtkinter as ctk
from typing import Callable, Dict, List, Optional

from utils.config import THEME_MODE, COLOR_THEME, COLORS


class SidebarButton(ctk.CTkButton):
    """
    自定义导航按钮
    支持选中状态样式
    """
    
    def __init__(self, master, text: str, command: Callable, **kwargs):
        """
        初始化导航按钮
        
        Args:
            master: 父组件
            text: 按钮文本
            command: 点击回调
        """
        super().__init__(
            master,
            text=text,
            command=command,
            width=180,
            height=40,
            corner_radius=8,
            font=("Microsoft YaHei", 13),
            fg_color="transparent",
            text_color=COLORS["text"],
            hover_color=COLORS["border"],
            anchor="w",
            **kwargs
        )
        self.is_selected = False
        self.normal_text_color = COLORS["text"]
        self.selected_text_color = "white"
        self.normal_fg = "transparent"
        self.selected_fg = COLORS["primary"]
    
    def set_selected(self, selected: bool):
        """
        设置选中状态
        
        Args:
            selected: 是否选中
        """
        self.is_selected = selected
        if selected:
            self.configure(
                fg_color=self.selected_fg,
                text_color=self.selected_text_color,
                hover_color=self.selected_fg
            )
        else:
            self.configure(
                fg_color=self.normal_fg,
                text_color=self.normal_text_color,
                hover_color=COLORS["border"]
            )


class Sidebar(ctk.CTkFrame):
    """
    左侧导航栏
    包含功能导航按钮
    """
    
    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None],
        width: int = 200,
        **kwargs
    ):
        """
        初始化导航栏
        
        Args:
            master: 父组件
            on_navigate: 导航回调函数，参数为页面标识
            width: 导航栏宽度
        """
        super().__init__(
            master,
            width=width,
            fg_color=COLORS["background"],
            corner_radius=0,
            **kwargs
        )
        
        self.on_navigate = on_navigate
        self.width = width
        self.buttons: Dict[str, SidebarButton] = {}
        self.current_page: Optional[str] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """
        创建导航栏组件
        """
        # 标题区域
        title_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        title_frame.pack(fill="x", padx=15, pady=(20, 10))
        title_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="发票查重工具",
            font=("Microsoft YaHei", 18, "bold"),
            text_color=COLORS["primary"]
        )
        title_label.pack(expand=True)
        
        # 分隔线
        separator = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        separator.pack(fill="x", padx=15, pady=10)
        
        # 导航按钮
        nav_items = [
            ("import_pdf", "📄 导入 PDF"),
            ("database", "💾 设置数据库"),
            ("task", "🔍 查重任务"),
            ("result", "📊 结果查看"),
        ]
        
        for page_id, text in nav_items:
            btn = SidebarButton(
                self,
                text=text,
                command=lambda pid=page_id: self._on_button_click(pid)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.buttons[page_id] = btn
        
        # 底部信息
        self._create_footer()
    
    def _create_footer(self):
        """
        创建底部信息区域
        """
        # 占据剩余空间
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        
        # 分隔线
        separator = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        separator.pack(fill="x", padx=15, pady=10)
        
        # 版本信息
        footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        footer_frame.pack(fill="x", padx=15, pady=(0, 10))
        footer_frame.pack_propagate(False)
        
        version_label = ctk.CTkLabel(
            footer_frame,
            text="v1.0.0",
            font=("Microsoft YaHei", 10),
            text_color=COLORS["text_secondary"]
        )
        version_label.pack(side="right")
    
    def _on_button_click(self, page_id: str):
        """
        导航按钮点击处理
        
        Args:
            page_id: 页面标识
        """
        self.set_active_page(page_id)
        if self.on_navigate:
            self.on_navigate(page_id)
    
    def set_active_page(self, page_id: str):
        """
        设置当前活动页面
        
        Args:
            page_id: 页面标识
        """
        # 取消之前的选中状态
        if self.current_page and self.current_page in self.buttons:
            self.buttons[self.current_page].set_selected(False)
        
        # 设置新的选中状态
        if page_id in self.buttons:
            self.buttons[page_id].set_selected(True)
            self.current_page = page_id
    
    def get_current_page(self) -> Optional[str]:
        """
        获取当前页面标识
        
        Returns:
            当前页面标识
        """
        return self.current_page
    
    def update_button_state(self, page_id: str, enabled: bool):
        """
        更新按钮状态
        
        Args:
            page_id: 页面标识
            enabled: 是否启用
        """
        if page_id in self.buttons:
            self.buttons[page_id].configure(
                state="normal" if enabled else "disabled"
            )
