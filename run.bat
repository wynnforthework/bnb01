@echo off
chcp 65001 >nul
echo 🚀 启动加密货币量化交易系统
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查是否存在.env文件
if not exist .env (
    echo ⚠️  未找到配置文件，启动配置向导...
    python setup_wizard.py
    if errorlevel 1 (
        echo ❌ 配置失败
        pause
        exit /b 1
    )
)

REM 安装依赖
echo 📦 安装依赖包...
python fix_pip_and_install.py

REM 运行测试
echo 🧪 运行系统测试...
python test_connection.py
if errorlevel 1 (
    echo ❌ 系统测试失败，请检查配置
    pause
    exit /b 1
)

REM 启动系统
echo.
echo 🎉 启动交易系统...
python start.py

pause