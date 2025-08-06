#!/usr/bin/env python3
"""
测试机器学习策略信号生成
"""

import asyncio
from backend.data_collector import DataCollector
from strategies.ml_strategy import MLStrategy

async def test_ml_signals():
    """测试机器学习策略信号生成"""
    print("🔍 测试机器学习策略信号生成...")
    
    collector = DataCollector()
    data = await collector.collect_historical_data('BTCUSDT', '1h', 30)
    print(f"收集到 {len(data)} 条数据")
    
    strategy = MLStrategy('BTCUSDT', {
        'model_type': 'random_forest',
        'min_confidence': 0.4,
        'up_threshold': 0.002,
        'down_threshold': -0.002,
        'min_training_samples': 50,
        'retrain_frequency': 1000
    })
    
    # 测试多个数据点的信号
    signals = []
    print("\n📡 生成信号:")
    for i in range(100, len(data), 50):
        test_data = data.iloc[:i]
        signal = strategy.generate_signal(test_data)
        signals.append(signal)
        print(f'数据点 {i}: {signal}')
    
    print(f'\n📊 信号统计:')
    print(f'BUY: {signals.count("BUY")}')
    print(f'SELL: {signals.count("SELL")}')
    print(f'HOLD: {signals.count("HOLD")}')
    
    # 如果有交易信号，说明策略工作正常
    if signals.count("BUY") > 0 or signals.count("SELL") > 0:
        print("✅ 策略能够产生交易信号")
    else:
        print("❌ 策略没有产生交易信号")

if __name__ == '__main__':
    asyncio.run(test_ml_signals())