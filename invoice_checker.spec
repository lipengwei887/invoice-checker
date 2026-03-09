# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将发票查重工具打包为独立的 Windows 可执行文件

打包命令:
    pyinstaller invoice_checker.spec

或一键打包:
    pyinstaller --onefile --windowed --name "发票查重工具" main.py
"""

import sys
import os

block_cipher = None

# 项目根目录
project_root = os.path.abspath(os.path.dirname(__file__))

# 分析依赖
a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # 包含所有 Python 模块
        ('core', 'core'),
        ('ui', 'ui'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        # 确保这些模块被打包进去
        'customtkinter',
        'pdfplumber',
        'pandas',
        'openpyxl',
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的模块以减小体积
        'matplotlib',
        'numpy.random._examples',
        'scipy',
        'pytest',
        'unittest',
        'pydoc',
        'email',
        'http',
        'xml',
        'xmlrpc',
        'html',
        'lib2to3',
        'distutils',
        'setuptools',
        'pkg_resources',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 去除重复文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='发票查重工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 图标（如果有的话）
    # icon='assets/icons/app.ico',
)

# 收集所有文件（用于单文件模式）
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='发票查重工具'
)
