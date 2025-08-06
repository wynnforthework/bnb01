#!/usr/bin/env python3
"""
诊断API权限和配置问题
"""

import logging
from backend.binance_client import BinanceClient

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def diagnose_api_permissions():
    """诊断API权限问题"""
    print("🔍 诊断API权限和配置...")
    
    print("\n" + "="*50)
    print("📊 现货API测试")
    print("="*50)
    
    try:
        # 测试现货API
        spot_client = BinanceClient(trading_mode='SPOT')
        
        # 测试现货账户信息
        try:
            account = spot_client.get_account_info()
            if account:
                print("✅ 现货账户信息获取成功")
                print(f"  账户类型: {account.get('accountType', 'N/A')}")
                print(f"  交易权限: {account.get('canTrade', False)}")
                print(f"  提现权限: {account.get('canWithdraw', False)}")
                print(f"  存款权限: {account.get('canDeposit', False)}")
            else:
                print("❌ 现货账户信息获取失败")
        except Exception as e:
            print(f"❌ 现货账户信息获取失败: {e}")
        
        # 测试现货余额
        try:
            usdt_balance = spot_client.get_balance('USDT')
            print(f"✅ USDT余额: ${usdt_balance:.2f}")
        except Exception as e:
            print(f"❌ 获取USDT余额失败: {e}")
        
        # 测试现货市场数据
        try:
            price = spot_client.get_ticker_price('BTCUSDT')
            print(f"✅ BTC现货价格: ${price:.2f}")
        except Exception as e:
            print(f"❌ 获取现货价格失败: {e}")
            
    except Exception as e:
        print(f"❌ 现货客户端初始化失败: {e}")
    
    print("\n" + "="*50)
    print("🚀 合约API测试")
    print("="*50)
    
    try:
        # 测试合约API
        futures_client = BinanceClient(trading_mode='FUTURES')
        
        # 测试合约账户信息
        try:
            account = futures_client.get_account_balance()
            if account:
                print("✅ 合约账户信息获取成功")
                print(f"  总钱包余额: ${account['totalWalletBalance']:.2f}")
                print(f"  可用余额: ${account['availableBalance']:.2f}")
                print(f"  未实现盈亏: ${account['totalUnrealizedProfit']:.2f}")
            else:
                print("❌ 合约账户信息获取失败")
        except Exception as e:
            print(f"❌ 合约账户信息获取失败: {e}")
            if "Invalid API-key" in str(e):
                print("  💡 可能原因: API密钥没有合约交易权限")
            elif "IP" in str(e):
                print("  💡 可能原因: IP地址未加入白名单")
        
        # 测试合约持仓
        try:
            positions = futures_client.get_positions()
            print(f"✅ 合约持仓查询成功，持仓数量: {len(positions)}")
        except Exception as e:
            print(f"❌ 合约持仓查询失败: {e}")
        
        # 测试合约市场数据（这个通常不需要特殊权限）
        try:
            price = futures_client.get_ticker_price('BTCUSDT')
            print(f"✅ BTC合约价格: ${price:.2f}")
        except Exception as e:
            print(f"❌ 获取合约价格失败: {e}")
        
        # 测试标记价格
        try:
            mark_price = futures_client.get_mark_price('BTCUSDT')
            if mark_price:
                print(f"✅ BTC标记价格: ${mark_price['markPrice']:.2f}")
                print(f"✅ 资金费率: {mark_price['lastFundingRate']:.6f}")
        except Exception as e:
            print(f"❌ 获取标记价格失败: {e}")
        
        # 测试杠杆设置（需要交易权限）
        try:
            result = futures_client.set_leverage('BTCUSDT', 5)
            if result:
                print("✅ 杠杆设置测试成功")
            else:
                print("❌ 杠杆设置测试失败")
        except Exception as e:
            print(f"❌ 杠杆设置测试失败: {e}")
            if "Invalid API-key" in str(e):
                print("  💡 确认: API密钥没有合约交易权限")
                
    except Exception as e:
        print(f"❌ 合约客户端初始化失败: {e}")
    
    print("\n" + "="*50)
    print("📋 诊断总结")
    print("="*50)
    
    print("\n🔧 API权限要求:")
    print("  现货交易需要的权限:")
    print("    ✅ 读取权限 (Read)")
    print("    ✅ 现货交易权限 (Spot Trading)")
    print("")
    print("  合约交易需要的权限:")
    print("    ✅ 读取权限 (Read)")
    print("    ✅ 期货交易权限 (Futures Trading)")
    print("    ✅ 可能需要保证金交易权限 (Margin Trading)")
    
    print("\n💡 解决方案:")
    print("  1. 登录币安账户")
    print("  2. 进入 API 管理页面")
    print("  3. 编辑现有API密钥")
    print("  4. 启用 '期货交易' 权限")
    print("  5. 确认IP白名单设置")
    print("  6. 保存并重新测试")
    
    print("\n⚠️ 注意事项:")
    print("  - 测试网络和主网需要不同的API密钥")
    print("  - 合约交易权限需要单独申请")
    print("  - 确保账户已完成KYC认证")
    print("  - 检查API密钥的IP白名单设置")
    
    print("\n🔗 相关链接:")
    print("  - 币安API管理: https://www.binance.com/cn/my/settings/api-management")
    print("  - 测试网络: https://testnet.binance.vision/")
    print("  - API文档: https://binance-docs.github.io/apidocs/")

def check_api_configuration():
    """检查API配置"""
    print("\n" + "="*50)
    print("⚙️ API配置检查")
    print("="*50)
    
    from config.config import Config
    config = Config()
    
    print(f"API密钥: {config.BINANCE_API_KEY[:10]}...{config.BINANCE_API_KEY[-10:]}")
    print(f"密钥长度: {len(config.BINANCE_API_KEY)} 字符")
    print(f"测试网络: {'是' if config.BINANCE_TESTNET else '否'}")
    
    if len(config.BINANCE_API_KEY) != 64:
        print("⚠️ API密钥长度异常，标准长度应为64字符")
    
    if len(config.BINANCE_SECRET_KEY) != 64:
        print("⚠️ 密钥长度异常，标准长度应为64字符")
    
    if not config.BINANCE_API_KEY or not config.BINANCE_SECRET_KEY:
        print("❌ API密钥或密钥为空，请检查.env文件")

if __name__ == '__main__':
    check_api_configuration()
    diagnose_api_permissions()