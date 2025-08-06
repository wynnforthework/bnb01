#!/usr/bin/env python3
"""
调试机器学习策略
"""

import asyncio
import pandas as pd
import numpy as np
from backend.data_collector import DataCollector
from strategies.ml_strategy import MLStrategy

async def debug_ml_strategy():
    """调试机器学习策略"""
    print("🔍 调试机器学习策略...")
    
    try:
        # 收集数据
        collector = DataCollector()
        data = await collector.collect_historical_data('BTCUSDT', '1h', 30)
        print(f"收集到 {len(data)} 条数据")
        
        if data.empty:
            print("❌ 没有数据")
            return
        
        # 创建策略
        strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 20,
            'prediction_horizon': 1,
            'min_confidence': 0.5,  # 降低信心阈值
            'up_threshold': 0.003,   # 0.3%
            'down_threshold': -0.003, # -0.3%
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'position_size': 0.1,
            'min_training_samples': 50  # 降低最小训练样本
        })
        
        print(f"策略参数: {strategy.parameters}")
        
        # 准备特征
        print("\n📊 准备特征...")
        feature_data = strategy.prepare_features(data)
        print(f"特征数据形状: {feature_data.shape}")
        print(f"特征列: {len([col for col in feature_data.columns if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']])}")
        
        # 创建标签
        print("\n🏷️ 创建标签...")
        labels = strategy.create_labels(feature_data)
        print(f"标签分布: {pd.Series(labels).value_counts().to_dict()}")
        
        # 训练模型
        print("\n🧠 训练模型...")
        success = strategy.train_model(data)
        print(f"训练结果: {success}")
        
        if success:
            # 测试信号生成
            print("\n📡 测试信号生成...")
            for i in range(max(0, len(data)-10), len(data)):
                test_data = data.iloc[:i+1]
                if len(test_data) >= 100:  # 确保有足够数据
                    signal = strategy.generate_signal(test_data)
                    print(f"第{i}条数据信号: {signal}")
        
        # 手动测试预测
        if strategy.is_trained:
            print("\n🔮 测试预测...")
            prediction, confidence = strategy.predict(data)
            print(f"最新预测: {prediction}, 信心度: {confidence:.3f}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    asyncio.run(debug_ml_strategy())