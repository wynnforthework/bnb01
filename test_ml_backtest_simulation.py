#!/usr/bin/env python3
"""
测试机器学习策略回测模拟
"""

import asyncio
import pandas as pd
import numpy as np
from backend.data_collector import DataCollector
from strategies.ml_strategy import MLStrategy

async def test_ml_backtest_simulation():
    """测试机器学习策略回测模拟"""
    print("🧪 测试机器学习策略回测模拟...")
    
    try:
        # 1. 获取更多数据用于模拟回测
        print("\n1️⃣ 获取数据...")
        collector = DataCollector()
        api_data = await collector.collect_historical_data('BTCUSDT', '1h', 20)
        
        if api_data.empty:
            print("❌ 无法获取数据")
            return
        
        print(f"   数据形状: {api_data.shape}")
        
        # 2. 创建策略
        print("\n2️⃣ 创建策略...")
        strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 10,
            'prediction_horizon': 1,
            'min_confidence': 0.3,
            'up_threshold': 0.002,
            'down_threshold': -0.002,
            'min_training_samples': 30
        })
        
        # 3. 模拟回测过程
        print("\n3️⃣ 模拟回测过程...")
        
        # 分割数据为训练和测试
        split_point = len(api_data) // 2
        training_data = api_data.iloc[:split_point]
        testing_data = api_data.iloc[split_point:]
        
        print(f"   训练数据: {len(training_data)} 条")
        print(f"   测试数据: {len(testing_data)} 条")
        
        # 4. 训练模型
        print("\n4️⃣ 训练模型...")
        success = strategy.train_model(training_data)
        print(f"   训练结果: {success}")
        
        if not success:
            print("❌ 模型训练失败")
            return
        
        print("✅ 模型训练成功")
        
        # 5. 模拟预测过程
        print("\n5️⃣ 模拟预测过程...")
        
        predictions = []
        signals = []
        
        for i in range(len(testing_data)):
            # 获取当前数据点
            current_data = testing_data.iloc[i:i+1]
            
            try:
                # 预测
                prediction, confidence = strategy.predict(current_data)
                predictions.append(prediction)
                
                # 生成信号
                signal = strategy.generate_signal(current_data)
                signals.append(signal)
                
                if i % 10 == 0:  # 每10个数据点打印一次
                    print(f"   第{i}个数据点: 预测={prediction}, 信心度={confidence:.3f}, 信号={signal}")
                    
            except Exception as e:
                print(f"   第{i}个数据点预测失败: {e}")
                predictions.append(0)
                signals.append('HOLD')
        
        # 6. 统计结果
        print("\n6️⃣ 统计结果...")
        print(f"   总预测次数: {len(predictions)}")
        print(f"   预测分布: {pd.Series(predictions).value_counts().to_dict()}")
        print(f"   信号分布: {pd.Series(signals).value_counts().to_dict()}")
        
        # 计算成功率
        buy_signals = signals.count('BUY')
        sell_signals = signals.count('SELL')
        hold_signals = signals.count('HOLD')
        
        print(f"   买入信号: {buy_signals} ({buy_signals/len(signals)*100:.1f}%)")
        print(f"   卖出信号: {sell_signals} ({sell_signals/len(signals)*100:.1f}%)")
        print(f"   持有信号: {hold_signals} ({hold_signals/len(signals)*100:.1f}%)")
        
        print("\n✅ 回测模拟完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_ml_backtest_simulation()) 