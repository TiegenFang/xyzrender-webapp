@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动 XYZRender Web 工作站...
python app.py
if errorlevel 1 (
  echo.
  echo 启动失败。请检查上方错误信息，或尝试 python app.py --port 5001
  pause
)
