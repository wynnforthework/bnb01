#!/usr/bin/env python3
"""
诊断机器学习策略数据问题
"""

import pandas as pd
import numpy as np
from backend.data_collector import DataCollector
from strategies.ml_strategy import MLStrategy
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_ml_data_issue():
    """诊断机器学习策略数据问题"""
    print("🔍 诊断机器学习策略数据问题...")
    
    try:
        # 1. 检查数据库中的数据
        print("\n1️⃣ 检查数据库中的数据...")
        collector = DataCollector()
        db_data = collector.get_market_data('BTCUSDT', '1h', limit=10)
        print(f"   数据库数据形状: {db_data.shape}")
        print(f"   数据库数据类型: {db_data.dtypes}")
        print(f"   数据库数据示例:")
        print(db_data.head())
        
        # 2. 检查数据收集器的历史数据
        print("\n2️⃣ 检查API历史数据...")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            api_data = loop.run_until_complete(
                collector.collect_historical_data('BTCUSDT', '1h', 10)
            )
            print(f"   API数据形状: {api_data.shape}")
            print(f"   API数据类型: {api_data.dtypes}")
            print(f"   API数据示例:")
            print(api_data.head())
        except Exception as e:
            print(f"   API数据获取失败: {e}")
        finally:
            loop.close()
        
        # 3. 检查机器学习策略的数据处理
        print("\n3️⃣ 检查机器学习策略数据处理...")
        strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'min_training_samples': 50
        })
        
        # 使用数据库数据测试
        if not db_data.empty:
            print("   使用数据库数据测试...")
            cleaned_data = strategy._validate_and_clean_data(db_data)
            print(f"   清理后数据形状: {cleaned_data.shape}")
            print(f"   清理后数据类型: {cleaned_data.dtypes}")
            
            if not cleaned_data.empty:
                feature_data = strategy.prepare_features(cleaned_data)
                print(f"   特征数据形状: {feature_data.shape}")
                print(f"   特征数据类型: {feature_data.dtypes}")
                
                # 检查是否有字符串数据
                string_columns = feature_data.select_dtypes(include=['object']).columns
                if len(string_columns) > 0:
                    print(f"   ⚠️ 发现字符串列: {list(string_columns)}")
                    for col in string_columns:
                        print(f"      {col} 示例值: {feature_data[col].iloc[0]}")
                else:
                    print("   ✅ 所有列都是数值类型")
        
        # 4. 检查回测引擎的数据获取
        print("\n4️⃣ 检查回测引擎数据获取...")
        from backend.backtesting import BacktestEngine
        backtest_engine = BacktestEngine()
        
        backtest_data = backtest_engine._get_historical_data(
            'BTCUSDT', '2025-07-01', '2025-08-05', '1h'
        )
        print(f"   回测数据形状: {backtest_data.shape}")
        print(f"   回测数据类型: {backtest_data.dtypes}")
        
        if not backtest_data.empty:
            print(f"   回测数据示例:")
            print(backtest_data.head())
            
            # 检查是否有字符串数据
            string_columns = backtest_data.select_dtypes(include=['object']).columns
            if len(string_columns) > 0:
                print(f"   ⚠️ 回测数据中发现字符串列: {list(string_columns)}")
                for col in string_columns:
                    print(f"      {col} 示例值: {backtest_data[col].iloc[0]}")
        
        # 5. 测试模型训练
        print("\n5️⃣ 测试模型训练...")
        if not db_data.empty and len(db_data) >= 100:
            try:
                success = strategy.train_model(db_data)
                print(f"   模型训练结果: {success}")
                if success:
                    print("   ✅ 模型训练成功")
                else:
                    print("   ❌ 模型训练失败")
            except Exception as e:
                print(f"   ❌ 模型训练异常: {e}")
                import traceback
                print(f"   错误详情: {traceback.format_exc()}")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_ml_data_issue() 