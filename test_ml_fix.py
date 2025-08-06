#!/usr/bin/env python3
"""
测试机器学习策略修复
"""

import asyncio
import pandas as pd
import numpy as np
from backend.data_collector import DataCollector
from strategies.ml_strategy import MLStrategy
from backend.backtesting import BacktestEngine

async def test_ml_fix():
    """测试机器学习策略修复"""
    print("🧪 测试机器学习策略修复...")
    
    try:
        # 1. 测试数据收集
        print("\n1️⃣ 测试数据收集...")
        collector = DataCollector()
        
        # 从API获取数据
        api_data = await collector.collect_historical_data('BTCUSDT', '1h', 10)
        print(f"   API数据形状: {api_data.shape}")
        print(f"   API数据类型: {api_data.dtypes}")
        print(f"   API数据列: {list(api_data.columns)}")
        
        # 检查是否有字符串列
        string_columns = api_data.select_dtypes(include=['object']).columns
        if len(string_columns) > 0:
            print(f"   ⚠️ 发现字符串列: {list(string_columns)}")
        else:
            print("   ✅ 所有列都是数值类型")
        
        # 2. 测试机器学习策略
        print("\n2️⃣ 测试机器学习策略...")
        strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 20,
            'prediction_horizon': 1,
            'min_confidence': 0.3,  # 降低信心阈值
            'up_threshold': 0.003,   # 降低阈值
            'down_threshold': -0.003, # 降低阈值
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'position_size': 0.1,
            'min_training_samples': 30  # 减少最小训练样本
        })
        
        # 测试数据验证
        if not api_data.empty:
            print(f"   原始数据形状: {api_data.shape}")
            print(f"   原始数据列: {list(api_data.columns)}")
            
            cleaned_data = strategy._validate_and_clean_data(api_data)
            print(f"   清理后数据形状: {cleaned_data.shape}")
            
            if not cleaned_data.empty:
                print(f"   清理后数据列: {list(cleaned_data.columns)}")
                
                # 测试特征准备
                feature_data = strategy.prepare_features(cleaned_data)
                print(f"   特征数据形状: {feature_data.shape}")
                
                # 检查特征数据类型
                string_features = feature_data.select_dtypes(include=['object']).columns
                if len(string_features) > 0:
                    print(f"   ⚠️ 特征数据中发现字符串列: {list(string_features)}")
                else:
                    print("   ✅ 特征数据所有列都是数值类型")
                
                # 测试模型训练
                print("\n3️⃣ 测试模型训练...")
                try:
                    success = strategy.train_model(cleaned_data)
                    print(f"   模型训练结果: {success}")
                    if success:
                        print("   ✅ 模型训练成功")
                        
                        # 测试预测
                        prediction, confidence = strategy.predict(cleaned_data)
                        print(f"   预测结果: {prediction}, 信心度: {confidence:.3f}")
                        
                        # 测试信号生成
                        signal = strategy.generate_signal(cleaned_data)
                        print(f"   生成信号: {signal}")
                    else:
                        print("   ❌ 模型训练失败")
                except Exception as e:
                    print(f"   ❌ 模型训练异常: {e}")
                    import traceback
                    print(f"   错误详情: {traceback.format_exc()}")
            else:
                print("   ❌ 数据清理后为空")
        else:
            print("   ❌ API数据为空")
        
        # 3. 测试回测
        print("\n4️⃣ 测试回测...")
        backtest_engine = BacktestEngine()
        
        try:
            result = backtest_engine.run_backtest(
                strategy=strategy,
                symbol='BTCUSDT',
                start_date='2025-07-01',
                end_date='2025-08-05',
                interval='1h'
            )
            
            print("✅ 回测成功!")
            print(f"   总收益率: {result.total_return:.2%}")
            print(f"   年化收益率: {result.annual_return:.2%}")
            print(f"   最大回撤: {result.max_drawdown:.2%}")
            print(f"   夏普比率: {result.sharpe_ratio:.2f}")
            print(f"   总交易次数: {result.total_trades}")
            print(f"   胜率: {result.win_rate:.2%}")
            
        except Exception as e:
            print(f"❌ 回测失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_ml_fix()) 