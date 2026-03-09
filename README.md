# 发票查重工具

一个基于 Python + CustomTkinter 开发的 Windows 桌面应用，用于财务场景中的发票查重管理。

## 功能特性

- **PDF 发票解析**：自动提取发票代码、发票号码、开票日期、金额、校验码、销售方名称
- **历史数据库管理**：支持加载和更新 Excel 格式的历史发票数据库
- **智能查重**：以"发票代码 + 发票号码"为唯一主键进行重复检测
- **批量处理**：支持同时处理多张发票，多线程保证界面流畅
- **结果导出**：支持将查重结果导出为 Excel 文件
- **现代化 UI**：使用 CustomTkinter 构建，支持浅色/深色主题

## 环境要求

- Python 3.9+
- Windows 10/11

## 安装步骤

### 1. 克隆或下载项目

```bash
cd invoice_checker
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# 或 macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行程序

```bash
python main.py
```

### 基本流程

1. **导入 PDF**：点击"导入 PDF"页面，选择或拖拽 PDF 发票文件
2. **设置数据库**：在"设置数据库"页面，选择历史发票 Excel 文件
3. **执行查重**：在"查重任务"页面，点击"开始查重"按钮
4. **查看结果**：在"结果查看"页面，查看查重结果并导出

## 历史数据库 Excel 模板格式

历史数据库 Excel 文件应包含以下列：

| 列名 | 说明 | 示例 |
|------|------|------|
| 发票代码 | 10-12 位数字 | 011001900211 |
| 发票号码 | 8-20 位数字 | 12345678 |
| 开票日期 | 日期格式 | 2024-01-15 |
| 金额 | 数字 | 1000.00 |
| 销售方名称 | 文本 | 某某科技有限公司 |
| 校验码 | 可选，后 6 位 | 123456 |

**注意**：
- 列名可以略有不同（如"发票代码"也可以是"代码"），程序会自动识别
- 如果数据库不存在，可以在"设置数据库"页面创建新的数据库文件

## 打包为可执行文件

### 方法一：使用 spec 文件（推荐）

```bash
pyinstaller invoice_checker.spec
```

### 方法二：命令行直接打包

```bash
pyinstaller --onefile --windowed --name "发票查重工具" main.py
```

打包完成后，可执行文件位于 `dist/` 目录下。

### 打包参数说明

- `--onefile`：打包为单个可执行文件
- `--windowed`：不显示控制台窗口
- `--name`：指定输出文件名
- `--icon`：指定图标文件（可选）

## 项目结构

```
invoice_checker/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖列表
├── invoice_checker.spec    # PyInstaller 打包配置
├── README.md               # 使用说明
├── core/                   # 核心逻辑模块
│   ├── pdf_extractor.py    # PDF 解析
│   ├── excel_manager.py    # Excel 数据库操作
│   └── duplicate_checker.py # 查重逻辑
├── ui/                     # UI 模块
│   ├── main_window.py      # 主窗口
│   ├── sidebar.py          # 导航栏
│   ├── pdf_import_view.py  # PDF 导入页面
│   ├── database_view.py    # 数据库设置页面
│   ├── task_view.py        # 查重任务页面
│   └── result_view.py      # 结果查看页面
└── utils/                  # 工具模块
    ├── config.py           # 配置常量
    └── thread_pool.py      # 多线程管理
```

## 常见问题

### 1. PDF 解析失败

- 确保 PDF 文件包含可提取的文本层（非扫描件）
- 对于扫描件，建议先使用 OCR 工具转换为可搜索 PDF

### 2. Excel 文件被占用

- 关闭正在使用该 Excel 文件的程序（如 Microsoft Excel）
- 然后重试加载或保存操作

### 3. 打包后的程序无法运行

- 确保所有依赖已正确安装
- 检查 `invoice_checker.spec` 中的路径配置
- 尝试使用 `--onedir` 模式代替 `--onefile`

## 技术栈

- **GUI 框架**：CustomTkinter
- **PDF 解析**：pdfplumber
- **数据处理**：pandas, openpyxl
- **打包工具**：PyInstaller

## 许可证

MIT License

## 更新日志

### v1.0.0 (2024-XX-XX)
- 初始版本发布
- 支持 PDF 发票解析
- 支持 Excel 历史数据库查重
- 支持结果导出
