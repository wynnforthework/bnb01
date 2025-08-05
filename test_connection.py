#!/usr/bin/env python3
"""
测试Binance连接和系统配置
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_binance_connection():
    """测试Binance API连接"""
    print("🔗 测试Binance API连接...")
    
    try:
        from backend.binance_client import BinanceClient
        
        client = BinanceClient()
        
        # 测试获取服务器时间
        server_time = client.client.get_server_time()
        print(f"✅ 服务器连接成功，时间: {server_time}")
        
        # 测试获取账户信息
        account_info = client.get_account_info()
        if account_info:
            print("✅ 账户信息获取成功")
            print(f"   账户类型: {account_info.get('accountType', 'N/A')}")
            print(f"   交易权限: {account_info.get('permissions', [])}")
        else:
            print("❌ 无法获取账户信息")
            return False
        
        # 测试获取余额
        balance = client.get_balance('USDT')
        print(f"✅ USDT余额: {balance}")
        
        # 测试获取市场数据
        price = client.get_ticker_price('BTCUSDT')
        if price:
            print(f"✅ BTC当前价格: ${price}")
        else:
            print("❌ 无法获取价格数据")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Binance连接失败: {e}")
        return False

def test_database():
    """测试数据库连接"""
    print("\n💾 测试数据库连接...")
    
    try:
        from backend.database import DatabaseManager
        
        db = DatabaseManager()
        
        # 测试添加交易记录
        trade = db.add_trade(
            symbol='BTCUSDT',
            side='BUY',
            quantity=0.001,
            price=50000,
            strategy='TEST'
        )
        
        if trade:
            print("✅ 数据库连接成功")
            print(f"   测试交易ID: {trade.id}")
            
            # 删除测试数据
            db.session.delete(trade)
            db.session.commit()
            print("✅ 测试数据已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_strategies():
    """测试交易策略"""
    print("\n📈 测试交易策略...")
    
    try:
        from strategies.ma_strategy import MovingAverageStrategy
        from strategies.rsi_strategy import RSIStrategy
        import pandas as pd
        import numpy as np
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        test_data = pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'open': prices * 0.999,
            'high': prices * 1.001,
            'low': prices * 0.998,
            'volume': np.random.randint(100, 1000, 100)
        })
        
        # 测试MA策略
        ma_strategy = MovingAverageStrategy('BTCUSDT')
        ma_signal = ma_strategy.generate_signal(test_data)
        print(f"✅ MA策略测试成功，信号: {ma_signal}")
        
        # 测试RSI策略
        rsi_strategy = RSIStrategy('BTCUSDT')
        rsi_signal = rsi_strategy.generate_signal(test_data)
        print(f"✅ RSI策略测试成功，信号: {rsi_signal}")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 系统配置测试")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ 请先配置 .env 文件中的API密钥")
        sys.exit(1)
    
    print(f"✅ API Key: {api_key[:8]}...")
    print(f"✅ Secret Key: {secret_key[:8]}...")
    
    # 运行测试
    tests = [
        test_binance_connection,
        test_database,
        test_strategies
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！系统配置正确")
        print("💡 现在可以运行: python start.py")
    else:
        print("❌ 部分测试失败，请检查配置")
        sys.exit(1)

if __name__ == '__main__':
    main()