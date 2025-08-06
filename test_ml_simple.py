#!/usr/bin/env python3
"""
简单测试机器学习策略修复
"""

import asyncio
import pandas as pd
import numpy as np
from backend.data_collector import DataCollector
from strategies.ml_strategy import MLStrategy

async def test_ml_simple():
    """简单测试机器学习策略"""
    print("🧪 简单测试机器学习策略...")
    
    try:
        # 1. 获取数据
        print("\n1️⃣ 获取数据...")
        collector = DataCollector()
        api_data = await collector.collect_historical_data('BTCUSDT', '1h', 5)
        
        if api_data.empty:
            print("❌ 无法获取数据")
            return
        
        print(f"   数据形状: {api_data.shape}")
        print(f"   数据列: {list(api_data.columns)}")
        
        # 2. 创建策略
        print("\n2️⃣ 创建策略...")
        strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 10,
            'prediction_horizon': 1,
            'min_confidence': 0.3,
            'up_threshold': 0.002,
            'down_threshold': -0.002,
            'min_training_samples': 20
        })
        
        # 3. 测试数据验证
        print("\n3️⃣ 测试数据验证...")
        cleaned_data = strategy._validate_and_clean_data(api_data)
        print(f"   清理后数据形状: {cleaned_data.shape}")
        
        if cleaned_data.empty:
            print("❌ 数据清理后为空")
            return
        
        # 4. 测试特征准备
        print("\n4️⃣ 测试特征准备...")
        feature_data = strategy.prepare_features(cleaned_data)
        print(f"   特征数据形状: {feature_data.shape}")
        print(f"   特征列数量: {len(feature_data.columns)}")
        
        if feature_data.empty:
            print("❌ 特征准备后为空")
            return
        
        # 5. 测试模型训练
        print("\n5️⃣ 测试模型训练...")
        success = strategy.train_model(cleaned_data)
        print(f"   训练结果: {success}")
        
        if success:
            print("✅ 模型训练成功")
            
            # 6. 测试预测
            print("\n6️⃣ 测试预测...")
            prediction, confidence = strategy.predict(cleaned_data)
            print(f"   预测结果: {prediction}, 信心度: {confidence:.3f}")
            
            # 7. 测试信号生成
            print("\n7️⃣ 测试信号生成...")
            signal = strategy.generate_signal(cleaned_data)
            print(f"   生成信号: {signal}")
            
        else:
            print("❌ 模型训练失败")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_ml_simple()) 