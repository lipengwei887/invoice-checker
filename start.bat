@echo off
chcp 65001 >nul
echo 正在安装依赖...
pip install -r requirements.txt
echo.
echo 正在启动发票查重工具...
python main.py
pause
