#!/usr/bin/env python3
"""
修复pip并安装依赖包
"""

import subprocess
import sys
import os

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}成功")
            return True
        else:
            print(f"❌ {description}失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}失败: {e}")
        return False

def fix_pip():
    """修复pip"""
    print("🛠️ 修复pip...")
    
    # 升级pip
    commands = [
        ("python -m pip install --upgrade pip", "升级pip"),
        ("python -m pip install --upgrade setuptools wheel", "升级构建工具"),
    ]
    
    for command, desc in commands:
        if not run_command(command, desc):
            print(f"⚠️ {desc}失败，继续尝试其他方法...")

def install_packages_individually():
    """逐个安装包"""
    packages = [
        "python-binance",
        "pandas",
        "numpy", 
        "flask",
        "flask-cors",
        "flask-socketio",
        "python-socketio",
        "ta",
        "plotly",
        "sqlalchemy",
        "python-dotenv",
        "websocket-client",
        "psutil"
    ]
    
    print("📦 逐个安装依赖包...")
    failed_packages = []
    
    for package in packages:
        print(f"\n安装 {package}...")
        if run_command(f"pip install {package}", f"安装{package}"):
            print(f"✅ {package} 安装成功")
        else:
            failed_packages.append(package)
            print(f"❌ {package} 安装失败")
    
    return failed_packages

def main():
    """主函数"""
    print("🚀 修复pip并安装依赖")
    print("=" * 50)
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return
    
    # 修复pip
    fix_pip()
    
    # 尝试正常安装
    print("\n📦 尝试批量安装依赖...")
    if run_command("pip install -r requirements.txt", "批量安装依赖"):
        print("🎉 所有依赖安装成功！")
        print("\n下一步:")
        print("1. 运行配置向导: python setup_wizard.py")
        print("2. 测试连接: python test_connection.py")
        print("3. 启动系统: python start.py")
        return
    
    # 如果批量安装失败，逐个安装
    print("\n⚠️ 批量安装失败，尝试逐个安装...")
    failed_packages = install_packages_individually()
    
    if failed_packages:
        print(f"\n❌ 以下包安装失败: {', '.join(failed_packages)}")
        print("💡 建议:")
        print("1. 检查网络连接")
        print("2. 尝试使用国内镜像: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        print("3. 或者手动安装失败的包")
    else:
        print("\n🎉 所有依赖安装成功！")
        print("\n下一步:")
        print("1. 运行配置向导: python setup_wizard.py")
        print("2. 测试连接: python test_connection.py")
        print("3. 启动系统: python start.py")

if __name__ == '__main__':
    main()