# 发票查重工具 - 项目上下文

## 项目概述

这是一个基于 Python + CustomTkinter 开发的桌面应用程序，专门用于财务场景中的发票查重管理。该工具能够从 PDF 发票中自动提取关键信息，并与历史发票数据库进行比对，识别重复发票。

### 核心功能
- **PDF 发票解析**：自动提取发票代码、发票号码、开票日期、金额、校验码、销售方名称
- **历史数据库管理**：支持加载和更新 Excel 格式的历史发票数据库
- **智能查重**：以"发票代码 + 发票号码"为唯一主键进行重复检测
- **批量处理**：支持同时处理多张发票，多线程保证界面流畅
- **结果导出**：支持将查重结果导出为 Excel 文件

### 技术栈
- **GUI 框架**：CustomTkinter (基于 Tkinter)
- **PDF 解析**：pdfplumber
- **数据处理**：pandas, openpyxl
- **打包工具**：PyInstaller

### 目标平台
- **主要**：Windows 10/11
- **Python 版本**：3.9+

---

## 项目结构

```
invoice_checker/
├── main.py                    # 程序入口，包含依赖检查和应用启动逻辑
├── requirements.txt           # 项目依赖
├── invoice_checker.spec       # PyInstaller 打包配置
├── README.md                  # 项目文档
│
├── core/                      # 核心业务逻辑
│   ├── __init__.py
│   ├── pdf_extractor.py       # PDF 解析模块，提取发票字段
│   ├── excel_manager.py       # Excel 数据库管理，读写查重
│   └── duplicate_checker.py   # 查重算法实现
│
├── ui/                        # 用户界面
│   ├── __init__.py
│   ├── main_window.py         # 主窗口，页面路由和状态管理
│   ├── sidebar.py             # 左侧导航栏
│   ├── pdf_import_view.py     # PDF 导入页面
│   ├── database_view.py       # 数据库设置页面
│   ├── task_view.py           # 查重任务页面
│   └── result_view.py         # 结果查看页面
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── config.py              # 全局配置常量（关键词、正则、颜色等）
│   └── thread_pool.py         # 多线程管理
│
└── assets/                    # 静态资源
    └── icons/                 # 图标文件
```

---

## 构建与运行

### 开发环境设置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

### 打包为可执行文件

```bash
# 使用 spec 文件打包（推荐）
pyinstaller invoice_checker.spec

# 或命令行直接打包
pyinstaller --onefile --windowed --name "发票查重工具" main.py
```

打包后的可执行文件位于 `dist/` 目录。

---

## 核心模块说明

### 1. PDF 解析模块 (`core/pdf_extractor.py`)

**主要类**：
- `InvoiceData`：发票数据结构（dataclass），包含发票代码、号码、日期、金额等字段
- `PDFInvoiceExtractor`：PDF 解析器，支持单个和批量提取

**提取逻辑**：
1. 使用 pdfplumber 打开 PDF 并提取文本
2. 通过关键词定位（如"发票代码"、"发票号码"）
3. 使用正则表达式提取具体值
4. 标准化日期格式为 YYYY-MM-DD

**关键词配置**：在 `utils/config.py` 的 `PDF_KEYWORDS` 中定义

### 2. Excel 管理模块 (`core/excel_manager.py`)

**主要类**：
- `ExcelManager`：Excel 数据库管理器

**核心方法**：
- `load_database(path)`：加载历史数据库
- `check_duplicate(code, number)`：检查单张发票是否重复
- `append_invoices(invoices)`：追加新发票到数据库
- `export_results(results)`：导出查重结果

**列名映射**：支持自动识别不同格式的列名（如"代码"映射到"发票代码"）

### 3. 查重模块 (`core/duplicate_checker.py`)

**主要类**：
- `DuplicateChecker`：查重器，支持数据库比对和批次内查重
- `DuplicateReportGenerator`：报告生成器

**查重逻辑**：
- 唯一主键：`发票代码_发票号码`
- 支持两类重复检测：
  1. 与历史数据库重复
  2. 当前批次内重复

### 4. UI 模块 (`ui/`)

**页面流转**：
```
导入 PDF → 设置数据库 → 执行查重 → 查看结果
```

**状态管理**（在 `main_window.py` 中）：
- `excel_manager`：Excel 管理器实例
- `extracted_invoices`：提取的发票数据
- `check_results`：查重结果

---

## 配置文件 (`utils/config.py`)

### 重要配置项

| 配置项 | 说明 |
|--------|------|
| `PDF_KEYWORDS` | PDF 字段提取关键词映射 |
| `REGEX_PATTERNS` | 正则表达式模式 |
| `REQUIRED_COLUMNS` | 历史数据库必需列 |
| `COLUMN_MAPPING` | 列名自动映射规则 |
| `DUPLICATE_STATUS` | 查重状态枚举（正常/重复/待修正/解析失败） |
| `COLORS` | UI 颜色定义 |
| `MAX_WORKERS` | 最大并发线程数（默认 4） |

### 查重状态说明

| 状态 | 含义 |
|------|------|
| `正常` | 未检测到重复 |
| `重复` | 与历史数据库或当前批次重复 |
| `待修正` | PDF 文本提取失败或关键字段缺失 |
| `解析失败` | PDF 解析异常 |

---

## 数据格式

### 历史数据库 Excel 格式

| 列名 | 必需 | 说明 | 示例 |
|------|------|------|------|
| 发票代码 | 是 | 10-12 位数字 | 011001900211 |
| 发票号码 | 是 | 8-20 位数字 | 12345678 |
| 开票日期 | 是 | 日期格式 | 2024-01-15 |
| 金额 | 是 | 数字 | 1000.00 |
| 销售方名称 | 是 | 文本 | 某某科技有限公司 |
| 校验码 | 否 | 后 6 位 | 123456 |

**注意**：列名可以略有不同，程序会自动识别映射。

---

## CI/CD

项目使用 GitHub Actions 自动构建 Windows 可执行文件。

**触发条件**：
- 推送到 `main` 或 `master` 分支
- Pull Request 到 `main` 或 `master`
- 手动触发

**构建产物**：`dist/发票查重工具.exe`

**工作流文件**：`.github/workflows/build.yml`

---

## 开发规范

### 代码风格
- 使用 UTF-8 编码
- 模块顶部包含 docstring 说明
- 类型注解：使用 `typing` 模块
- 数据类：使用 `dataclass`

### 命名约定
- 文件名：小写 + 下划线（如 `pdf_extractor.py`）
- 类名：大驼峰（如 `PDFInvoiceExtractor`）
- 函数/变量：小写 + 下划线（如 `extract_from_file`）
- 常量：大写 + 下划线（如 `REQUIRED_COLUMNS`）

### 模块依赖
- `ui/` 依赖 `core/` 和 `utils/`
- `core/` 仅依赖 `utils/config.py`
- `utils/` 为纯工具模块，无外部依赖

---

## 常见问题排查

### PDF 解析失败
- 确认 PDF 包含可提取的文本层（非扫描件）
- 扫描件需先 OCR 转换

### Excel 文件被占用
- 关闭 Excel 后重试

### 打包后程序无法运行
- 检查 `invoice_checker.spec` 中的 `hiddenimports` 是否完整
- 尝试 `--onedir` 模式调试

### Tkinter 依赖问题
- macOS：确保 Python 使用系统 Tkinter（`brew install python-tk`）
- Windows：通常内置 Tkinter

---

## 扩展建议

### 支持新发票格式
1. 在 `utils/config.py` 中添加新的关键词映射
2. 在 `pdf_extractor.py` 中添加对应的提取方法

### 添加新字段
1. 更新 `InvoiceData` dataclass
2. 更新 `REQUIRED_COLUMNS` 或 `OPTIONAL_COLUMNS`
3. 更新 UI 显示列

### 多语言支持
1. 将 `config.py` 中的文本抽取为语言文件
2. 使用 Python 的 `gettext` 模块

---

## 关键文件参考

- 入口：`main.py`
- 主窗口：`ui/main_window.py`
- PDF 解析：`core/pdf_extractor.py`
- 查重逻辑：`core/duplicate_checker.py`
- 配置：`utils/config.py`
