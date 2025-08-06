#!/usr/bin/env python3
"""
诊断机器学习和缠论策略回测数据为0的问题
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ml_strategy_backtest():
    """测试机器学习策略回测"""
    print("🧠 测试机器学习策略回测...")
    
    try:
        from strategies.ml_strategy import MLStrategy
        from backend.backtesting import BacktestEngine
        from backend.data_collector import DataCollector
        
        # 创建数据收集器
        collector = DataCollector()
        
        # 获取历史数据
        print("1️⃣ 获取历史数据...")
        data = await collector.collect_historical_data('BTCUSDT', '1h', 100)
        print(f"   获取到 {len(data)} 条数据")
        
        if data.empty:
            print("❌ 无法获取历史数据")
            return
        
        # 创建机器学习策略
        print("2️⃣ 创建机器学习策略...")
        ml_strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 20,
            'prediction_horizon': 1,
            'min_confidence': 0.45,  # 降低信心阈值
            'up_threshold': 0.005,   # 0.5%
            'down_threshold': -0.005, # -0.5%
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'position_size': 0.1,
            'retrain_frequency': 30,
            'min_training_samples': 80  # 降低最小训练样本
        })
        
        # 测试策略信号生成
        print("3️⃣ 测试策略信号生成...")
        signals = []
        for i in range(50, len(data)):
            current_data = data.iloc[:i+1]
            signal = ml_strategy.generate_signal(current_data)
            signals.append(signal)
            if signal != 'HOLD':
                print(f"   信号: {signal} at {data.iloc[i]['timestamp']}")
        
        print(f"   生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
        
        # 创建回测引擎
        print("4️⃣ 创建回测引擎...")
        backtest_engine = BacktestEngine(initial_capital=10000.0)
        
        # 运行回测
        print("5️⃣ 运行回测...")
        result = backtest_engine.run_backtest(
            strategy=ml_strategy,
            symbol='BTCUSDT',
            start_date='2025-07-01',
            end_date='2025-08-05',
            interval='1h'
        )
        
        print("✅ 机器学习策略回测结果:")
        print(f"   总收益率: {result.total_return:.2%}")
        print(f"   年化收益率: {result.annual_return:.2%}")
        print(f"   最大回撤: {result.max_drawdown:.2%}")
        print(f"   夏普比率: {result.sharpe_ratio:.2f}")
        print(f"   总交易次数: {result.total_trades}")
        print(f"   胜率: {result.win_rate:.2%}")
        print(f"   盈亏比: {result.profit_factor:.2f}")
        
        if result.total_trades == 0:
            print("⚠️ 警告: 没有生成任何交易")
        
    except Exception as e:
        print(f"❌ 机器学习策略测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

async def test_chanlun_strategy_backtest():
    """测试缠论策略回测"""
    print("\n🎯 测试缠论策略回测...")
    
    try:
        from strategies.chanlun_strategy import ChanlunStrategy
        from backend.backtesting import BacktestEngine
        from backend.data_collector import DataCollector
        
        # 创建数据收集器
        collector = DataCollector()
        
        # 获取历史数据
        print("1️⃣ 获取历史数据...")
        data = await collector.collect_historical_data('BTCUSDT', '1h', 100)
        print(f"   获取到 {len(data)} 条数据")
        
        if data.empty:
            print("❌ 无法获取历史数据")
            return
        
        # 创建缠论策略
        print("2️⃣ 创建缠论策略...")
        chanlun_strategy = ChanlunStrategy('BTCUSDT', {
            'timeframes': ['30m', '1h', '4h'],
            'min_swing_length': 3,
            'central_bank_min_bars': 3,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'ma_short': 5,
            'ma_long': 20,
            'position_size': 0.3,
            'max_position': 1.0,
            'stop_loss': 0.03,
            'take_profit': 0.05,
            'trend_confirmation': 0.02,
            'divergence_threshold': 0.1
        })
        
        # 测试策略信号生成
        print("3️⃣ 测试策略信号生成...")
        signals = []
        for i in range(50, len(data)):
            current_data = data.iloc[:i+1]
            signal = chanlun_strategy.generate_signal(current_data)
            signals.append(signal)
            if signal != 'HOLD':
                print(f"   信号: {signal} at {data.iloc[i]['timestamp']}")
        
        print(f"   生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
        
        # 创建回测引擎
        print("4️⃣ 创建回测引擎...")
        backtest_engine = BacktestEngine(initial_capital=10000.0)
        
        # 运行回测
        print("5️⃣ 运行回测...")
        result = backtest_engine.run_backtest(
            strategy=chanlun_strategy,
            symbol='BTCUSDT',
            start_date='2025-07-01',
            end_date='2025-08-05',
            interval='1h'
        )
        
        print("✅ 缠论策略回测结果:")
        print(f"   总收益率: {result.total_return:.2%}")
        print(f"   年化收益率: {result.annual_return:.2%}")
        print(f"   最大回撤: {result.max_drawdown:.2%}")
        print(f"   夏普比率: {result.sharpe_ratio:.2f}")
        print(f"   总交易次数: {result.total_trades}")
        print(f"   胜率: {result.win_rate:.2%}")
        print(f"   盈亏比: {result.profit_factor:.2f}")
        
        if result.total_trades == 0:
            print("⚠️ 警告: 没有生成任何交易")
        
    except Exception as e:
        print(f"❌ 缠论策略测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

async def test_data_collection():
    """测试数据收集"""
    print("\n📊 测试数据收集...")
    
    try:
        from backend.data_collector import DataCollector
        
        collector = DataCollector()
        
        # 测试获取历史数据
        print("1️⃣ 测试获取历史数据...")
        data = await collector.collect_historical_data('BTCUSDT', '1h', 50)
        
        if data.empty:
            print("❌ 无法获取历史数据")
            return
        
        print(f"✅ 成功获取 {len(data)} 条数据")
        print(f"   时间范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
        print(f"   价格范围: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
        print(f"   数据列: {list(data.columns)}")
        
        # 检查数据质量
        print("2️⃣ 检查数据质量...")
        print(f"   NaN值数量: {data.isnull().sum().sum()}")
        print(f"   无穷大值数量: {np.isinf(data.select_dtypes(include=[np.number])).sum().sum()}")
        
        # 测试技术指标计算
        print("3️⃣ 测试技术指标计算...")
        indicators_data = collector.calculate_technical_indicators(data, 'BTCUSDT')
        print(f"   计算后的数据形状: {indicators_data.shape}")
        print(f"   新增指标列: {[col for col in indicators_data.columns if col not in data.columns]}")
        
    except Exception as e:
        print(f"❌ 数据收集测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

async def main():
    """主函数"""
    print("🔍 诊断策略回测问题")
    print("=" * 60)
    
    # 测试数据收集
    await test_data_collection()
    
    # 测试机器学习策略
    await test_ml_strategy_backtest()
    
    # 测试缠论策略
    await test_chanlun_strategy_backtest()
    
    print("\n🎉 诊断完成!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 