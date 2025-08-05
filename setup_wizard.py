#!/usr/bin/env python3
"""
系统配置向导
"""

import os
import getpass

def create_env_file():
    """创建环境配置文件"""
    print("🔧 配置向导")
    print("=" * 50)
    
    # 检查是否已存在.env文件
    if os.path.exists('.env'):
        overwrite = input("⚠️  .env文件已存在，是否覆盖？(y/N): ").lower()
        if overwrite != 'y':
            print("配置取消")
            return
    
    print("\n请输入Binance API配置:")
    print("💡 提示: 可以在 https://www.binance.com/zh-CN/my/settings/api-management 获取")
    
    # 获取API配置
    api_key = input("🔑 API Key: ").strip()
    if not api_key:
        print("❌ API Key不能为空")
        return
    
    secret_key = getpass.getpass("🔐 Secret Key: ").strip()
    if not secret_key:
        print("❌ Secret Key不能为空")
        return
    
    # 选择环境
    print("\n选择交易环境:")
    print("1. 测试网络 (推荐新手)")
    print("2. 实盘交易 (谨慎使用)")
    
    env_choice = input("请选择 (1/2): ").strip()
    testnet = "True" if env_choice == "1" else "False"
    
    # 其他配置
    debug = input("\n是否启用调试模式？(Y/n): ").lower()
    debug_mode = "False" if debug == 'n' else "True"
    
    # 生成随机密钥
    import secrets
    secret_key_flask = secrets.token_hex(32)
    
    # 创建.env文件内容
    env_content = f"""# Binance API配置
BINANCE_API_KEY={api_key}
BINANCE_SECRET_KEY={secret_key}
BINANCE_TESTNET={testnet}

# 数据库配置
DATABASE_URL=sqlite:///trading.db

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379/0

# Flask配置
SECRET_KEY={secret_key_flask}
DEBUG={debug_mode}
"""
    
    # 写入文件
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("\n✅ 配置文件创建成功!")
        print("📁 文件位置: .env")
        
        if testnet == "True":
            print("\n⚠️  当前使用测试网络")
            print("💡 测试网络地址: https://testnet.binance.vision/")
            print("💡 可以在测试网络申请测试资金")
        else:
            print("\n⚠️  当前使用实盘交易")
            print("🚨 请谨慎操作，确保充分测试后再使用")
        
        print("\n下一步:")
        print("1. 运行测试: python test_connection.py")
        print("2. 启动系统: python start.py")
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")

def main():
    """主函数"""
    print("🚀 加密货币量化交易系统")
    print("📋 配置向导")
    print()
    
    create_env_file()

if __name__ == '__main__':
    main()