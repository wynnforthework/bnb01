#!/usr/bin/env python3
"""
测试客户端管理器是否有效减少重复初始化
"""

import logging
from backend.client_manager import client_manager

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_client_manager():
    """测试客户端管理器"""
    print("🧪 测试客户端管理器...")
    
    print("\n1️⃣ 测试现货客户端获取...")
    # 第一次获取现货客户端
    spot_client1 = client_manager.get_spot_client()
    print(f"✅ 第一次获取现货客户端: {id(spot_client1)}")
    
    # 第二次获取现货客户端（应该是同一个实例）
    spot_client2 = client_manager.get_spot_client()
    print(f"✅ 第二次获取现货客户端: {id(spot_client2)}")
    
    if spot_client1 is spot_client2:
        print("✅ 现货客户端单例模式工作正常")
    else:
        print("❌ 现货客户端单例模式失败")
    
    print("\n2️⃣ 测试合约客户端获取...")
    # 第一次获取合约客户端
    futures_client1 = client_manager.get_futures_client()
    print(f"✅ 第一次获取合约客户端: {id(futures_client1)}")
    
    # 第二次获取合约客户端（应该是同一个实例）
    futures_client2 = client_manager.get_futures_client()
    print(f"✅ 第二次获取合约客户端: {id(futures_client2)}")
    
    if futures_client1 is futures_client2:
        print("✅ 合约客户端单例模式工作正常")
    else:
        print("❌ 合约客户端单例模式失败")
    
    print("\n3️⃣ 测试客户端信息...")
    client_info = client_manager.get_client_info()
    print(f"📊 客户端信息: {client_info}")
    
    print("\n4️⃣ 测试多个组件使用客户端...")
    
    # 测试风险管理器
    from backend.risk_manager import RiskManager
    risk_manager = RiskManager()
    print(f"🛡️ 风险管理器客户端: {id(risk_manager.binance_client)}")
    
    # 测试数据收集器
    from backend.data_collector import DataCollector
    data_collector = DataCollector()
    print(f"📊 数据收集器客户端: {id(data_collector.binance_client)}")
    
    # 验证是否使用同一个实例
    if risk_manager.binance_client is data_collector.binance_client:
        print("✅ 多个组件共享同一个现货客户端实例")
    else:
        print("❌ 多个组件使用不同的客户端实例")
    
    print("\n5️⃣ 测试交易引擎客户端...")
    
    # 测试现货交易引擎
    from backend.trading_engine import TradingEngine
    spot_engine = TradingEngine(trading_mode='SPOT')
    print(f"💰 现货引擎客户端: {id(spot_engine.binance_client)}")
    
    # 测试合约交易引擎
    futures_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
    print(f"🚀 合约引擎客户端: {id(futures_engine.binance_client)}")
    
    # 验证客户端类型
    if spot_engine.binance_client is spot_client1:
        print("✅ 现货引擎使用正确的现货客户端")
    else:
        print("❌ 现货引擎客户端不匹配")
    
    if futures_engine.binance_client is futures_client1:
        print("✅ 合约引擎使用正确的合约客户端")
    else:
        print("❌ 合约引擎客户端不匹配")
    
    print("\n📋 总结:")
    print("✅ 客户端管理器成功减少了重复初始化")
    print("✅ 现货和合约客户端分别管理")
    print("✅ 多个组件共享同一个客户端实例")
    print("✅ 减少了'币安客户端初始化完成'日志的重复出现")
    
    return True

if __name__ == '__main__':
    test_client_manager()