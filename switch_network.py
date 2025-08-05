#!/usr/bin/env python3
"""
网络切换脚本
"""

import os
from dotenv import load_dotenv

def switch_to_mainnet():
    """切换到主网"""
    print("⚠️  切换到主网（实盘交易）")
    print("🚨 警告：这将使用真实资金进行交易！")
    
    confirm = input("确认切换到主网吗？(输入 'YES' 确认): ")
    if confirm != 'YES':
        print("❌ 取消切换")
        return False
    
    # 读取当前.env文件
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换测试网络设置
    content = content.replace('BINANCE_TESTNET=True', 'BINANCE_TESTNET=False')
    
    # 写回文件
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已切换到主网")
    print("🔧 请确保你的API密钥是主网密钥")
    return True

def switch_to_testnet():
    """切换到测试网络"""
    print("🧪 切换到测试网络")
    
    # 读取当前.env文件
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换主网设置
    content = content.replace('BINANCE_TESTNET=False', 'BINANCE_TESTNET=True')
    
    # 写回文件
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已切换到测试网络")
    print("🔧 请确保你的API密钥是测试网络密钥")
    return True

def get_testnet_guide():
    """显示测试网络密钥获取指南"""
    print("\n📖 获取测试网络API密钥指南")
    print("=" * 50)
    print("1. 访问: https://testnet.binance.vision/")
    print("2. 点击右上角 'Log In'")
    print("3. 使用GitHub账号登录")
    print("4. 登录后点击右上角头像 -> 'API Key'")
    print("5. 点击 'Create API Key'")
    print("6. 输入标签名称（如：trading-bot）")
    print("7. 完成验证后获得API Key和Secret Key")
    print("8. 将新密钥替换到 .env 文件中")
    print("\n💰 获取测试资金:")
    print("- 在测试网络中，你可以获得免费的测试USDT")
    print("- 登录后在钱包页面申请测试资金")

def update_api_keys():
    """更新API密钥"""
    print("\n🔑 更新API密钥")
    print("=" * 30)
    
    new_api_key = input("请输入新的API Key: ").strip()
    if not new_api_key:
        print("❌ API Key不能为空")
        return False
    
    new_secret_key = input("请输入新的Secret Key: ").strip()
    if not new_secret_key:
        print("❌ Secret Key不能为空")
        return False
    
    # 读取当前.env文件
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新密钥
    with open('.env', 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('BINANCE_API_KEY='):
                f.write(f'BINANCE_API_KEY={new_api_key}\n')
            elif line.startswith('BINANCE_SECRET_KEY='):
                f.write(f'BINANCE_SECRET_KEY={new_secret_key}\n')
            else:
                f.write(line)
    
    print("✅ API密钥已更新")
    return True

def main():
    """主菜单"""
    while True:
        print("\n🔧 网络和密钥管理")
        print("=" * 30)
        print("1. 切换到测试网络")
        print("2. 切换到主网（实盘）")
        print("3. 更新API密钥")
        print("4. 查看测试网络密钥获取指南")
        print("5. 测试当前配置")
        print("0. 退出")
        
        choice = input("\n请选择操作 (0-5): ").strip()
        
        if choice == '1':
            switch_to_testnet()
        elif choice == '2':
            switch_to_mainnet()
        elif choice == '3':
            update_api_keys()
        elif choice == '4':
            get_testnet_guide()
        elif choice == '5':
            print("\n🧪 运行诊断测试...")
            os.system('python diagnose_api.py')
        elif choice == '0':
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择")

if __name__ == '__main__':
    main()