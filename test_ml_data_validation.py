#!/usr/bin/env python3
"""
测试ML策略数据验证
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from strategies.ml_strategy import MLStrategy
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def create_problematic_data():
    """创建有问题的数据格式"""
    # 模拟从错误日志中看到的数据格式
    problematic_data = [
        "['450776.89295' '617291.23200' '449647.44984' '574472.66766' '363.98' '521.31' '263.51' '202.36' '1057.59']",
        "['239820.47895' '117152.85840' '203523.43440' '330913.46020' '810085.01771']",
        "['0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0' '0']"
    ]
    
    # 创建DataFrame
    df = pd.DataFrame({'data': problematic_data})
    return df

def create_normal_data():
    """创建正常的数据格式"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='1H')
    n = len(dates)
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(50000, 60000, n),
        'high': np.random.uniform(50000, 60000, n),
        'low': np.random.uniform(50000, 60000, n),
        'close': np.random.uniform(50000, 60000, n),
        'volume': np.random.uniform(1000, 10000, n)
    })
    
    return data

def test_ml_data_validation():
    """测试ML策略数据验证"""
    print("🔍 测试ML策略数据验证...")
    print("=" * 50)
    
    try:
        # 1. 测试有问题的数据
        print("1️⃣ 测试有问题的数据格式...")
        problematic_data = create_problematic_data()
        print(f"问题数据形状: {problematic_data.shape}")
        print(f"问题数据类型: {problematic_data.dtypes}")
        print("问题数据内容:")
        print(problematic_data.head())
        
        # 创建ML策略
        parameters = {
            'lookback_period': 20,
            'prediction_horizon': 1,
            'model_type': 'random_forest',
            'retrain_frequency': 100,
            'min_training_samples': 50,  # 降低要求
            'up_threshold': 0.01,
            'down_threshold': -0.01,
            'min_confidence': 0.5,
            'position_size': 0.1
        }
        
        strategy = MLStrategy('BTCUSDT', parameters)
        
        # 测试数据验证
        try:
            cleaned_data = strategy._validate_and_clean_data(problematic_data)
            if not cleaned_data.empty:
                print(f"✅ 问题数据验证成功，清理后形状: {cleaned_data.shape}")
                print("清理后数据:")
                print(cleaned_data.head())
            else:
                print("❌ 问题数据验证失败")
        except Exception as e:
            print(f"❌ 问题数据验证异常: {e}")
        
        # 2. 测试正常数据
        print("\n2️⃣ 测试正常数据格式...")
        normal_data = create_normal_data()
        print(f"正常数据形状: {normal_data.shape}")
        print(f"正常数据类型: {normal_data.dtypes}")
        
        try:
            cleaned_normal_data = strategy._validate_and_clean_data(normal_data)
            if not cleaned_normal_data.empty:
                print(f"✅ 正常数据验证成功，清理后形状: {cleaned_normal_data.shape}")
            else:
                print("❌ 正常数据验证失败")
        except Exception as e:
            print(f"❌ 正常数据验证异常: {e}")
        
        # 3. 测试特征准备
        print("\n3️⃣ 测试特征准备...")
        try:
            feature_data = strategy.prepare_features(normal_data)
            print(f"✅ 特征准备成功，特征数量: {len(feature_data.columns)}")
        except Exception as e:
            print(f"❌ 特征准备失败: {e}")
        
        # 4. 测试模型训练
        print("\n4️⃣ 测试模型训练...")
        try:
            success = strategy.train_model(normal_data)
            if success:
                print("✅ 模型训练成功")
            else:
                print("❌ 模型训练失败")
        except Exception as e:
            print(f"❌ 模型训练异常: {e}")
        
        # 5. 测试信号生成
        print("\n5️⃣ 测试信号生成...")
        try:
            signal = strategy.generate_signal(normal_data)
            print(f"✅ 信号生成成功: {signal}")
        except Exception as e:
            print(f"❌ 信号生成失败: {e}")
        
        print("\n✅ 所有测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    test_ml_data_validation() 