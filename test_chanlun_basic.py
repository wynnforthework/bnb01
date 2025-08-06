#!/usr/bin/env python3
"""
缠论策略基础测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from strategies.chanlun_strategy import ChanlunStrategy
    print("✅ 成功导入缠论策略")
except Exception as e:
    print(f"❌ 导入缠论策略失败: {e}")
    sys.exit(1)

import pandas as pd
import numpy as np

def test_basic_functionality():
    """测试基础功能"""
    print("\n🧪 测试缠论策略基础功能...")
    
    try:
        # 1. 创建简单测试数据
        print("1️⃣ 创建测试数据...")
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='1H')
        n = len(dates)
        
        np.random.seed(42)
        base_price = 50000
        prices = base_price * (1 + np.cumsum(np.random.randn(n) * 0.01))
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n)
        })
        
        print(f"✅ 创建了 {len(data)} 条测试数据")
        
        # 2. 初始化策略
        print("\n2️⃣ 初始化策略...")
        parameters = {
            'timeframes': ['30m', '1h'],
            'min_swing_length': 3,
            'central_bank_min_bars': 3,
            'position_size': 0.3,
            'max_position': 1.0,
            'stop_loss': 0.03,
            'take_profit': 0.05
        }
        
        strategy = ChanlunStrategy('BTCUSDT', parameters)
        print("✅ 策略初始化成功")
        
        # 3. 测试特征准备
        print("\n3️⃣ 测试特征准备...")
        feature_data = strategy.prepare_features(data)
        print(f"✅ 特征数据形状: {feature_data.shape}")
        
        # 4. 测试信号生成
        print("\n4️⃣ 测试信号生成...")
        signal = strategy.generate_signal(data)
        print(f"✅ 生成信号: {signal}")
        
        # 5. 测试仓位管理
        print("\n5️⃣ 测试仓位管理...")
        position_size = strategy.calculate_position_size(50000, 10000)
        print(f"✅ 建议仓位: {position_size:.6f}")
        
        stop_loss = strategy.should_stop_loss(50000)
        take_profit = strategy.should_take_profit(50000)
        print(f"✅ 止损检查: {stop_loss}")
        print(f"✅ 止盈检查: {take_profit}")
        
        print("\n🎉 基础功能测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    test_basic_functionality() 