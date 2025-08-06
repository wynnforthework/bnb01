#!/usr/bin/env python3
"""
测试ML策略修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from strategies.ml_strategy import MLStrategy
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def create_test_data():
    """创建测试数据"""
    # 创建模拟的K线数据
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
    n = len(dates)
    
    # 生成模拟价格数据
    np.random.seed(42)
    base_price = 50000
    returns = np.random.normal(0, 0.02, n)  # 2% 标准差
    prices = [base_price]
    
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
    
    # 创建DataFrame
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.uniform(1000, 10000, n)
    })
    
    # 确保high >= low
    data['high'] = np.maximum(data['high'], data['low'])
    data['open'] = np.clip(data['open'], data['low'], data['high'])
    data['close'] = np.clip(data['close'], data['low'], data['high'])
    
    return data

def test_ml_strategy_fix():
    """测试ML策略修复"""
    print("🔧 测试ML策略修复...")
    print("=" * 50)
    
    try:
        # 1. 创建测试数据
        print("1️⃣ 创建测试数据...")
        data = create_test_data()
        print(f"✅ 创建了 {len(data)} 条测试数据")
        print(f"   价格范围: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
        print(f"   成交量范围: {data['volume'].min():.0f} - {data['volume'].max():.0f}")
        
        # 2. 创建ML策略
        print("\n2️⃣ 创建ML策略...")
        parameters = {
            'lookback_period': 20,
            'prediction_horizon': 1,
            'model_type': 'random_forest',
            'retrain_frequency': 100,
            'min_training_samples': 200,
            'up_threshold': 0.01,
            'down_threshold': -0.01,
            'min_confidence': 0.5,
            'position_size': 0.1
        }
        
        strategy = MLStrategy('BTCUSDT', parameters)
        print("✅ ML策略创建成功")
        
        # 3. 测试特征准备
        print("\n3️⃣ 测试特征准备...")
        try:
            feature_data = strategy.prepare_features(data)
            print(f"✅ 特征准备成功，特征数量: {len(feature_data.columns)}")
            
            # 检查是否有无穷大值
            inf_count = np.isinf(feature_data.select_dtypes(include=[np.number])).sum().sum()
            nan_count = feature_data.isna().sum().sum()
            print(f"   无穷大值数量: {inf_count}")
            print(f"   NaN值数量: {nan_count}")
            
            if inf_count == 0 and nan_count == 0:
                print("✅ 特征数据清理成功，无异常值")
            else:
                print("⚠️ 特征数据仍有异常值")
                
        except Exception as e:
            print(f"❌ 特征准备失败: {e}")
            return
        
        # 4. 测试模型训练
        print("\n4️⃣ 测试模型训练...")
        try:
            success = strategy.train_model(data)
            if success:
                print("✅ 模型训练成功")
                print(f"   模型类型: {strategy.model_type}")
                print(f"   特征数量: {len(strategy.feature_columns)}")
                print(f"   模型已训练: {strategy.is_trained}")
            else:
                print("❌ 模型训练失败")
                return
        except Exception as e:
            print(f"❌ 模型训练异常: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            return
        
        # 5. 测试预测
        print("\n5️⃣ 测试预测...")
        try:
            prediction, confidence = strategy.predict(data)
            print(f"✅ 预测成功")
            print(f"   预测结果: {prediction}")
            print(f"   信心度: {confidence:.3f}")
        except Exception as e:
            print(f"❌ 预测失败: {e}")
            return
        
        # 6. 测试信号生成
        print("\n6️⃣ 测试信号生成...")
        try:
            signal = strategy.generate_signal(data)
            print(f"✅ 信号生成成功")
            print(f"   交易信号: {signal}")
        except Exception as e:
            print(f"❌ 信号生成失败: {e}")
            return
        
        print("\n✅ 所有测试完成! ML策略修复成功!")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    test_ml_strategy_fix() 