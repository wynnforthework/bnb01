#!/usr/bin/env python3
"""
简单测试修复后的策略
"""

import asyncio
import pandas as pd
from strategies.ml_strategy import MLStrategy
from strategies.chanlun_strategy import ChanlunStrategy
from backend.backtesting import BacktestEngine
from backend.data_collector import DataCollector

async def test_fixed_strategies():
    """测试修复后的策略"""
    print("🧪 测试修复后的策略...")
    
    try:
        # 创建数据收集器
        collector = DataCollector()
        
        # 获取历史数据
        print("1️⃣ 获取历史数据...")
        data = await collector.collect_historical_data('BTCUSDT', '1h', 30)  # 减少数据量
        print(f"   获取到 {len(data)} 条数据")
        
        if data.empty:
            print("❌ 无法获取历史数据")
            return
        
        # 测试机器学习策略
        print("\n2️⃣ 测试修复后的机器学习策略...")
        ml_strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 25,
            'prediction_horizon': 1,
            'min_confidence': 0.55,
            'up_threshold': 0.008,
            'down_threshold': -0.008,
            'stop_loss': 0.025,
            'take_profit': 0.06,
            'position_size': 0.08
        })
        
        # 测试信号生成
        signals = []
        for i in range(20, len(data)):
            current_data = data.iloc[:i+1]
            signal = ml_strategy.generate_signal(current_data)
            signals.append(signal)
            if signal != 'HOLD':
                print(f"   ML信号: {signal} at {data.iloc[i]['timestamp']}")
        
        print(f"   ML生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
        
        # 测试缠论策略
        print("\n3️⃣ 测试修复后的缠论策略...")
        chanlun_strategy = ChanlunStrategy('BTCUSDT', {
            'timeframes': ['30m', '1h', '4h'],
            'min_swing_length': 2,
            'central_bank_min_bars': 2,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'ma_short': 5,
            'ma_long': 20,
            'position_size': 0.25,
            'max_position': 0.9,
            'stop_loss': 0.035,
            'take_profit': 0.07,
            'trend_confirmation': 0.015,
            'divergence_threshold': 0.08
        })
        
        # 测试信号生成
        signals = []
        for i in range(20, len(data)):
            current_data = data.iloc[:i+1]
            signal = chanlun_strategy.generate_signal(current_data)
            signals.append(signal)
            if signal != 'HOLD':
                print(f"   缠论信号: {signal} at {data.iloc[i]['timestamp']}")
        
        print(f"   缠论生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
        
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_fixed_strategies())
