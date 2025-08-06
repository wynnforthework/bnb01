#!/usr/bin/env python3
"""
测试合约交易中的缠论策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading_engine import TradingEngine
from strategies.chanlun_strategy import ChanlunStrategy

def test_futures_chanlun():
    """测试合约交易中的缠论策略"""
    print("🧪 测试合约交易中的缠论策略...")
    print("=" * 50)
    
    try:
        # 1. 初始化合约交易引擎
        print("1️⃣ 初始化合约交易引擎...")
        futures_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
        print("✅ 合约交易引擎初始化成功")
        
        # 2. 检查策略数量
        print(f"\n2️⃣ 检查策略数量...")
        print(f"   总策略数量: {len(futures_engine.strategies)}")
        
        # 3. 列出所有策略
        print(f"\n3️⃣ 列出所有策略...")
        for name, strategy in futures_engine.strategies.items():
            strategy_type = strategy.__class__.__name__
            print(f"   {name}: {strategy_type}")
        
        # 4. 检查缠论策略
        print(f"\n4️⃣ 检查缠论策略...")
        chanlun_strategies = []
        for name, strategy in futures_engine.strategies.items():
            if isinstance(strategy, ChanlunStrategy):
                chanlun_strategies.append(name)
                print(f"   ✅ 找到缠论策略: {name}")
        
        if chanlun_strategies:
            print(f"   缠论策略数量: {len(chanlun_strategies)}")
        else:
            print("   ❌ 未找到缠论策略")
        
        # 5. 测试缠论策略功能
        if chanlun_strategies:
            print(f"\n5️⃣ 测试缠论策略功能...")
            test_strategy_name = chanlun_strategies[0]
            test_strategy = futures_engine.strategies[test_strategy_name]
            
            print(f"   测试策略: {test_strategy_name}")
            print(f"   策略类型: {test_strategy.__class__.__name__}")
            print(f"   交易对: {test_strategy.symbol}")
            print(f"   参数: {test_strategy.parameters}")
            
            # 测试信号生成
            import pandas as pd
            import numpy as np
            
            # 创建测试数据
            dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='1H')
            n = len(dates)
            np.random.seed(42)
            base_price = 50000
            prices = base_price * (1 + np.cumsum(np.random.randn(n) * 0.01))
            
            test_data = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': prices * 1.01,
                'low': prices * 0.99,
                'close': prices,
                'volume': np.random.uniform(1000, 10000, n)
            })
            
            # 测试特征准备
            feature_data = test_strategy.prepare_features(test_data)
            print(f"   特征数据形状: {feature_data.shape}")
            
            # 测试信号生成
            signal = test_strategy.generate_signal(test_data)
            print(f"   生成信号: {signal}")
            
            print("✅ 缠论策略功能测试成功")
        
        # 6. 检查策略类型分布
        print(f"\n6️⃣ 策略类型分布...")
        strategy_types = {}
        for name, strategy in futures_engine.strategies.items():
            strategy_type = strategy.__class__.__name__
            if strategy_type not in strategy_types:
                strategy_types[strategy_type] = 0
            strategy_types[strategy_type] += 1
        
        for strategy_type, count in strategy_types.items():
            print(f"   {strategy_type}: {count} 个")
        
        print("\n🎉 合约交易缠论策略测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    test_futures_chanlun() 