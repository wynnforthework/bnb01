#!/usr/bin/env python3
"""
调试ML策略数据问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from backend.trading_engine import TradingEngine
from backend.client_manager import client_manager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def debug_ml_data():
    """调试ML策略数据问题"""
    print("🔍 调试ML策略数据问题...")
    print("=" * 50)
    
    try:
        # 1. 初始化交易引擎
        print("1️⃣ 初始化交易引擎...")
        engine = TradingEngine(trading_mode='SPOT')
        print("✅ 交易引擎初始化成功")
        
        # 2. 获取市场数据
        print("\n2️⃣ 获取市场数据...")
        symbol = 'BTCUSDT'
        data = engine._get_enhanced_market_data(symbol)
        
        if data is None or data.empty:
            print("❌ 无法获取市场数据")
            return
        
        print(f"✅ 获取到 {len(data)} 条数据")
        print(f"   数据形状: {data.shape}")
        print(f"   列名: {list(data.columns)}")
        print(f"   数据类型:")
        for col, dtype in data.dtypes.items():
            print(f"     {col}: {dtype}")
        
        # 3. 检查数据内容
        print("\n3️⃣ 检查数据内容...")
        print("前5行数据:")
        print(data.head())
        
        # 4. 检查数值列
        print("\n4️⃣ 检查数值列...")
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in data.columns:
                print(f"   {col}:")
                print(f"     类型: {data[col].dtype}")
                print(f"     前5个值: {data[col].head().tolist()}")
                print(f"     是否有NaN: {data[col].isna().sum()}")
                print(f"     是否有inf: {np.isinf(data[col]).sum()}")
        
        # 5. 尝试数据转换
        print("\n5️⃣ 尝试数据转换...")
        try:
            # 复制数据
            test_data = data.copy()
            
            # 转换数值列
            for col in numeric_columns:
                if col in test_data.columns:
                    if test_data[col].dtype == 'object':
                        print(f"   转换 {col} 从 {test_data[col].dtype} 到数值...")
                        test_data[col] = pd.to_numeric(test_data[col], errors='coerce')
                        print(f"   转换后类型: {test_data[col].dtype}")
                        print(f"   转换后前5个值: {test_data[col].head().tolist()}")
            
            print("✅ 数据转换成功")
            
        except Exception as e:
            print(f"❌ 数据转换失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
        
        # 6. 测试ML策略
        print("\n6️⃣ 测试ML策略...")
        try:
            from strategies.ml_strategy import MLStrategy
            
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
            
            strategy = MLStrategy(symbol, parameters)
            print("✅ ML策略创建成功")
            
            # 测试特征准备
            feature_data = strategy.prepare_features(data)
            print(f"✅ 特征准备成功，特征数量: {len(feature_data.columns)}")
            
            # 测试模型训练
            success = strategy.train_model(data)
            if success:
                print("✅ 模型训练成功")
            else:
                print("❌ 模型训练失败")
                
        except Exception as e:
            print(f"❌ ML策略测试失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
        
        print("\n✅ 调试完成!")
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_ml_data() 