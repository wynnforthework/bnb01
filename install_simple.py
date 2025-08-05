#!/usr/bin/env python3
"""
简化版依赖安装脚本
使用国内镜像源，提高安装成功率
"""

import subprocess
import sys
import os

# 国内镜像源
MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.douban.com/simple/",
]

# 核心依赖包（最小化）
CORE_PACKAGES = [
    "python-binance",
    "pandas", 
    "numpy",
    "flask",
    "flask-cors",
    "flask-socketio",
    "sqlalchemy",
    "python-dotenv",
    "psutil"
]

def install_with_mirror(package, mirror):
    """使用指定镜像安装包"""
    cmd = f"pip install -i {mirror} {package}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def install_package(package):
    """尝试使用不同镜像安装包"""
    print(f"📦 安装 {package}...")
    
    # 先尝试默认源
    try:
        result = subprocess.run(f"pip install {package}", shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ {package} 安装成功")
            return True
    except:
        pass
    
    # 尝试镜像源
    for mirror in MIRRORS:
        print(f"   尝试镜像: {mirror.split('/')[2]}")
        if install_with_mirror(package, mirror):
            print(f"✅ {package} 安装成功")
            return True
    
    print(f"❌ {package} 安装失败")
    return False

def upgrade_pip():
    """升级pip"""
    print("🔧 升级pip...")
    for mirror in MIRRORS:
        try:
            cmd = f"python -m pip install -i {mirror} --upgrade pip"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("✅ pip升级成功")
                return True
        except:
            continue
    print("⚠️ pip升级失败，继续安装...")
    return False

def main():
    """主函数"""
    print("🚀 简化版依赖安装")
    print("=" * 40)
    
    # 升级pip
    upgrade_pip()
    
    # 安装核心包
    failed_packages = []
    for package in CORE_PACKAGES:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n" + "=" * 40)
    if failed_packages:
        print(f"❌ 安装失败的包: {', '.join(failed_packages)}")
        print("\n💡 手动安装建议:")
        for pkg in failed_packages:
            print(f"pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ {pkg}")
    else:
        print("🎉 所有依赖安装成功！")
        
        # 创建简化版的.env文件（如果不存在）
        if not os.path.exists('.env'):
            print("\n📝 创建示例配置文件...")
            with open('.env', 'w', encoding='utf-8') as f:
                f.write("""# Binance API配置 - 请填入你的API密钥
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_TESTNET=True

# 系统配置
DATABASE_URL=sqlite:///trading.db
SECRET_KEY=your-secret-key-here
DEBUG=True
""")
            print("✅ 已创建 .env 配置文件")
            print("⚠️ 请编辑 .env 文件，填入你的Binance API密钥")
        
        print("\n🎯 下一步:")
        print("1. 编辑 .env 文件，填入API密钥")
        print("2. 运行测试: python test_connection.py")
        print("3. 启动系统: python start.py")

if __name__ == '__main__':
    main()