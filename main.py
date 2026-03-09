#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票查重工具 - 主入口

功能：从 PDF 发票文件中提取关键信息，并与本地历史发票数据库进行比对，识别重复发票。

作者：AI Assistant
版本：1.0.0
"""

import sys
import os

# 确保能正确导入项目模块
if getattr(sys, 'frozen', False):
    # 打包后的环境
    application_path = sys._MEIPASS
else:
    # 开发环境
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from ui.main_window import MainWindow


def check_dependencies():
    """
    检查必要的依赖是否已安装
    
    Returns:
        (是否通过, 错误信息)
    """
    missing = []
    
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")
    
    try:
        import pdfplumber
    except ImportError:
        missing.append("pdfplumber")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import openpyxl
    except ImportError:
        missing.append("openpyxl")
    
    try:
        import PIL
    except ImportError:
        missing.append("Pillow")
    
    if missing:
        return False, f"缺少必要的依赖包: {', '.join(missing)}\n\n请运行: pip install -r requirements.txt"
    
    return True, ""


def main():
    """
    主函数
    """
    # 检查依赖
    ok, msg = check_dependencies()
    if not ok:
        print(f"错误: {msg}")
        try:
            import tkinter.messagebox as msgbox
            msgbox.showerror("依赖错误", msg)
        except:
            pass
        sys.exit(1)
    
    # 启动应用
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
