@echo off
chcp 65001 >nul
echo Steam游戏数据处理工具
echo ======================
echo.
echo 请选择要运行的工具:
echo 1. Steam数据提取器
echo 2. 数据清理工具  
echo 3. 评论分析工具
echo 4. 退出
echo.
set /p choice="请输入选择 (1-4): "

cd /d "%~dp0src"

if "%choice%"=="1" (
    echo.
    echo 正在启动Steam数据提取器...
    python steam_data_extractor.py
) else if "%choice%"=="2" (
    echo.
    echo 正在启动数据清理工具...
    python data_cleaner.py
) else if "%choice%"=="3" (
    echo.
    echo 正在启动评论分析工具...
    cd comments
    python simple_steam_crawler_easy.py
) else if "%choice%"=="4" (
    echo 感谢使用，再见！
    exit /b 0
) else (
    echo 无效选择，请重新运行！
)

echo.
pause