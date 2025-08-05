#!/usr/bin/env python3
"""
系统诊断脚本
快速检查系统状态和常见问题
"""

import os
import sys
import importlib
from datetime import datetime

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    print(f"   Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("   ❌ Python版本过低，需要3.8或更高版本")
        return False
    else:
        print("   ✅ Python版本符合要求")
        return True

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    required_packages = [
        'flask',
        'binance',
        'pandas',
        'numpy',
        'sqlalchemy',
        'python_dotenv',
        'psutil'
    ]
    
    optional_packages = [
        'sklearn',
        'matplotlib',
        'tensorflow',
        'talib'
    ]
    
    missing_required = []
    missing_optional = []
    
    # 检查必需包
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (必需)")
            missing_required.append(package)
    
    # 检查可选包
    for package in optional_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {package} (可选)")
        except ImportError:
            print(f"   ⚠️  {package} (可选，用于高级功能)")
            missing_optional.append(package)
    
    return missing_required, missing_optional

def check_config_files():
    """检查配置文件"""
    print("\n📝 检查配置文件...")
    
    files_to_check = [
        ('.env', '环境变量配置'),
        ('config/config.py', '系统配置'),
        ('requirements.txt', '依赖列表')
    ]
    
    all_exist = True
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} - {description}")
        else:
            print(f"   ❌ {file_path} - {description} (缺失)")
            all_exist = False
    
    return all_exist

def check_env_variables():
    """检查环境变量"""
    print("\n🔑 检查环境变量...")
    
    if not os.path.exists('.env'):
        print("   ❌ .env文件不存在")
        return False
    
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY'
    ]
    
    from dotenv import load_dotenv
    load_dotenv()
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == 'your_api_key_here' or value == 'your_secret_key_here':
            print(f"   ❌ {var} (未配置或使用默认值)")
            missing_vars.append(var)
        else:
            print(f"   ✅ {var} (已配置)")
    
    return len(missing_vars) == 0

def check_database():
    """检查数据库"""
    print("\n💾 检查数据库...")
    
    try:
        from backend.database import DatabaseManager
        db_manager = DatabaseManager()
        
        # 尝试查询
        trades = db_manager.get_trades(limit=1)
        print("   ✅ 数据库连接正常")
        print(f"   📊 交易记录数量: {len(trades)}")
        return True
        
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        return False

def check_api_connection():
    """检查API连接"""
    print("\n🌐 检查Binance API连接...")
    
    try:
        from backend.binance_client import BinanceClient
        client = BinanceClient()
        
        # 测试服务器时间
        server_time = client.client.get_server_time()
        print("   ✅ Binance服务器连接正常")
        
        # 测试账户信息
        account_info = client.get_account_info()
        if account_info:
            print("   ✅ API密钥验证成功")
            print(f"   📊 账户类型: {account_info.get('accountType', 'N/A')}")
            return True
        else:
            print("   ❌ API密钥验证失败")
            return False
            
    except Exception as e:
        print(f"   ❌ API连接失败: {e}")
        return False

def check_system_resources():
    """检查系统资源"""
    print("\n💻 检查系统资源...")
    
    try:
        import psutil
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"   💻 CPU使用率: {cpu_percent}%")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        print(f"   🧠 内存使用率: {memory.percent}%")
        print(f"   🧠 可用内存: {memory.available / 1024 / 1024 / 1024:.1f} GB")
        
        # 磁盘空间
        disk = psutil.disk_usage('.')
        print(f"   💾 磁盘使用率: {disk.percent}%")
        print(f"   💾 可用空间: {disk.free / 1024 / 1024 / 1024:.1f} GB")
        
        # 检查资源是否充足
        if memory.percent > 90:
            print("   ⚠️  内存使用率过高")
        if disk.percent > 90:
            print("   ⚠️  磁盘空间不足")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 系统资源检查失败: {e}")
        return False

def generate_report(results):
    """生成诊断报告"""
    print("\n" + "="*60)
    print("📋 诊断报告")
    print("="*60)
    
    total_checks = len(results)
    passed_checks = sum(1 for result in results.values() if result)
    
    print(f"总检查项: {total_checks}")
    print(f"通过检查: {passed_checks}")
    print(f"成功率: {passed_checks/total_checks*100:.1f}%")
    
    print("\n详细结果:")
    for check_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {check_name}: {status}")
    
    if passed_checks == total_checks:
        print("\n🎉 所有检查都通过！系统状态良好")
        print("💡 现在可以运行: python start.py")
    else:
        print("\n⚠️  部分检查失败，请根据上述信息修复问题")
        print("\n🔧 常见解决方案:")
        
        if not results.get('依赖包检查', True):
            print("  - 运行: python install_simple.py")
        
        if not results.get('环境变量检查', True):
            print("  - 运行: python setup_wizard.py")
            print("  - 或手动编辑 .env 文件")
        
        if not results.get('API连接检查', True):
            print("  - 检查API密钥是否正确")
            print("  - 检查网络连接")
            print("  - 确认API权限设置")

def main():
    """主函数"""
    print("🔍 系统诊断工具")
    print(f"⏰ 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 执行各项检查
    results = {}
    
    results['Python版本检查'] = check_python_version()
    
    missing_required, missing_optional = check_dependencies()
    results['依赖包检查'] = len(missing_required) == 0
    
    results['配置文件检查'] = check_config_files()
    results['环境变量检查'] = check_env_variables()
    results['数据库检查'] = check_database()
    results['API连接检查'] = check_api_connection()
    results['系统资源检查'] = check_system_resources()
    
    # 生成报告
    generate_report(results)
    
    # 保存诊断日志
    try:
        log_file = f"logs/diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs('logs', exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"系统诊断报告 - {datetime.now()}\n")
            f.write("="*60 + "\n")
            for check_name, result in results.items():
                status = "通过" if result else "失败"
                f.write(f"{check_name}: {status}\n")
        
        print(f"\n📄 诊断日志已保存到: {log_file}")
        
    except Exception as e:
        print(f"\n⚠️  保存诊断日志失败: {e}")

if __name__ == '__main__':
    main()