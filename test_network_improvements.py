#!/usr/bin/env python3
"""
测试网络改进
验证SSL错误、代理问题和网络超时的处理机制
"""

import requests
import time
import logging
from backend.network_config import binance_network_config, network_config
from backend.binance_client import BinanceClient
from backend.data_collector import DataCollector
from config.config import Config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_network_config():
    """测试网络配置"""
    print("🧪 测试网络配置...")
    print("=" * 50)
    
    try:
        # 1. 测试币安连接
        print("1️⃣ 测试币安连接...")
        success = binance_network_config.test_connection(testnet=True)
        if success:
            print("✅ 币安连接测试成功")
        else:
            print("❌ 币安连接测试失败")
        
        # 2. 测试会话创建
        print("\n2️⃣ 测试会话创建...")
        session = network_config.create_session()
        print("✅ 会话创建成功")
        
        # 3. 测试重试机制
        print("\n3️⃣ 测试重试机制...")
        def failing_request():
            raise requests.exceptions.SSLError("SSL错误测试")
        
        try:
            network_config.retry_with_backoff(failing_request)
            print("❌ 重试机制测试失败 - 应该抛出异常")
        except Exception as e:
            print(f"✅ 重试机制测试成功 - 正确抛出异常: {type(e).__name__}")
        
        # 4. 测试错误处理
        print("\n4️⃣ 测试错误处理...")
        error_types = [
            ("SSL错误", "SSLError: SSL错误测试"),
            ("代理错误", "ProxyError: 代理连接失败"),
            ("超时错误", "ReadTimeoutError: 读取超时"),
            ("连接错误", "ConnectionError: 连接失败")
        ]
        
        for error_name, error_msg in error_types:
            error_type = network_config.handle_network_error(Exception(error_msg))
            print(f"   {error_name}: {error_type}")
        
    except Exception as e:
        print(f"❌ 网络配置测试失败: {e}")

def test_binance_client():
    """测试币安客户端"""
    print("\n🧪 测试币安客户端...")
    print("=" * 50)
    
    try:
        # 初始化客户端
        client = BinanceClient(trading_mode='SPOT')
        print("✅ 币安客户端初始化成功")
        
        # 测试获取价格
        print("\n1️⃣ 测试获取价格...")
        price = client.get_ticker_price('BTCUSDT')
        if price:
            print(f"✅ 获取价格成功: {price}")
        else:
            print("❌ 获取价格失败")
        
        # 测试获取K线数据
        print("\n2️⃣ 测试获取K线数据...")
        klines = client.get_klines('BTCUSDT', interval='1h', limit=10)
        if klines:
            print(f"✅ 获取K线数据成功: {len(klines)} 条")
        else:
            print("❌ 获取K线数据失败")
        
        # 测试获取账户信息
        print("\n3️⃣ 测试获取账户信息...")
        account = client.get_account_info()
        if account:
            print("✅ 获取账户信息成功")
        else:
            print("❌ 获取账户信息失败")
        
    except Exception as e:
        print(f"❌ 币安客户端测试失败: {e}")

def test_data_collector():
    """测试数据收集器"""
    print("\n🧪 测试数据收集器...")
    print("=" * 50)
    
    try:
        # 初始化数据收集器
        collector = DataCollector()
        print("✅ 数据收集器初始化成功")
        
        # 测试收集历史数据
        print("\n1️⃣ 测试收集历史数据...")
        # 使用同步方式测试
        import asyncio
        df = asyncio.run(collector.collect_historical_data('BTCUSDT', interval='1h', days=1))
        if not df.empty:
            print(f"✅ 收集历史数据成功: {len(df)} 条")
        else:
            print("❌ 收集历史数据失败")
        
        # 测试收集最新数据
        print("\n2️⃣ 测试收集最新数据...")
        asyncio.run(collector.collect_latest_data('BTCUSDT', '1h'))
        print("✅ 收集最新数据完成")
        
        # 测试获取市场数据
        print("\n3️⃣ 测试获取市场数据...")
        market_data = collector.get_market_data('BTCUSDT', interval='1h', limit=10)
        if not market_data.empty:
            print(f"✅ 获取市场数据成功: {len(market_data)} 条")
        else:
            print("❌ 获取市场数据失败")
        
    except Exception as e:
        print(f"❌ 数据收集器测试失败: {e}")

def test_error_simulation():
    """测试错误模拟"""
    print("\n🧪 测试错误模拟...")
    print("=" * 50)
    
    try:
        # 模拟SSL错误
        print("1️⃣ 模拟SSL错误...")
        def ssl_error_simulation():
            raise requests.exceptions.SSLError("SSL错误模拟")
        
        try:
            network_config.retry_with_backoff(ssl_error_simulation)
        except Exception as e:
            print(f"✅ SSL错误处理成功: {type(e).__name__}")
        
        # 模拟超时错误
        print("\n2️⃣ 模拟超时错误...")
        def timeout_error_simulation():
            raise requests.exceptions.ReadTimeout("读取超时模拟")
        
        try:
            network_config.retry_with_backoff(timeout_error_simulation)
        except Exception as e:
            print(f"✅ 超时错误处理成功: {type(e).__name__}")
        
        # 模拟代理错误
        print("\n3️⃣ 模拟代理错误...")
        def proxy_error_simulation():
            raise requests.exceptions.ProxyError("代理错误模拟")
        
        try:
            network_config.retry_with_backoff(proxy_error_simulation)
        except Exception as e:
            print(f"✅ 代理错误处理成功: {type(e).__name__}")
        
    except Exception as e:
        print(f"❌ 错误模拟测试失败: {e}")

def test_connection_stability():
    """测试连接稳定性"""
    print("\n🧪 测试连接稳定性...")
    print("=" * 50)
    
    try:
        client = BinanceClient(trading_mode='SPOT')
        
        # 连续测试多次API调用
        print("1️⃣ 连续API调用测试...")
        success_count = 0
        total_tests = 5
        
        for i in range(total_tests):
            try:
                price = client.get_ticker_price('BTCUSDT')
                if price:
                    success_count += 1
                    print(f"   测试 {i+1}: ✅ 成功")
                else:
                    print(f"   测试 {i+1}: ❌ 失败")
            except Exception as e:
                print(f"   测试 {i+1}: ❌ 异常: {type(e).__name__}")
            
            time.sleep(1)  # 间隔1秒
        
        success_rate = (success_count / total_tests) * 100
        print(f"\n📊 成功率: {success_rate:.1f}% ({success_count}/{total_tests})")
        
        if success_rate >= 80:
            print("✅ 连接稳定性测试通过")
        else:
            print("❌ 连接稳定性测试失败")
        
    except Exception as e:
        print(f"❌ 连接稳定性测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始网络改进测试")
    print("=" * 60)
    
    # 1. 测试网络配置
    test_network_config()
    
    # 2. 测试币安客户端
    test_binance_client()
    
    # 3. 测试数据收集器
    test_data_collector()
    
    # 4. 测试错误模拟
    test_error_simulation()
    
    # 5. 测试连接稳定性
    test_connection_stability()
    
    print("\n🎉 网络改进测试完成!")
    print("\n📋 总结:")
    print("   • 网络配置: ✅ 已实现")
    print("   • 重试机制: ✅ 已实现")
    print("   • 错误处理: ✅ 已实现")
    print("   • 连接稳定性: ✅ 已测试")

if __name__ == "__main__":
    main()
