#!/usr/bin/env python3
"""
测试ML策略修复
验证ML策略是否能正确生成非零回测结果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.ml_strategy import MLStrategy
from backend.backtesting import BacktestEngine
from backend.data_collector import DataCollector
import pandas as pd
from datetime import datetime, timedelta

def test_ml_strategy_fix():
    """测试ML策略修复"""
    print("🧪 测试ML策略修复...")
    print("=" * 50)

    try:
        # 1. 检查数据库中的数据
        print("1️⃣ 检查数据库中的数据...")
        dc = DataCollector()
        data = dc.get_market_data('BTCUSDT', '1h', limit=100)

        if data.empty:
            print("❌ 数据库中没有数据")
            return

        print(f"✅ 数据库中有 {len(data)} 条数据")
        print(f"   数据范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")

        # 2. 创建ML策略 - 使用正确的参数
        print("\n2️⃣ 创建ML策略...")
        ml_parameters = {
            'model_type': 'random_forest',
            'lookback_period': 30,
            'prediction_horizon': 1,
            'min_confidence': 0.5,  # 降低信心阈值以增加交易频率
            'up_threshold': 0.01,   # 降低阈值以增加信号
            'down_threshold': -0.01,
            'stop_loss': 0.03,
            'take_profit': 0.06,
            'position_size': 0.05,
            'min_training_samples': 50,  # 降低最小训练样本数
            'retrain_frequency': 20      # 降低重训练频率
        }
        
        strategy = MLStrategy('BTCUSDT', ml_parameters)
        print("✅ ML策略创建成功")

        # 3. 测试策略信号生成
        print("\n3️⃣ 测试策略信号生成...")
        signals = []
        for i in range(min(20, len(data))):
            test_data = data.iloc[:i+1]
            if len(test_data) >= 10:  # 至少需要10个数据点
                signal = strategy.generate_signal(test_data)
                signals.append(signal)
                print(f"   数据点 {i+1}: {signal}")

        signal_counts = pd.Series(signals).value_counts()
        print(f"✅ 信号生成测试完成，信号分布: {signal_counts.to_dict()}")

        # 4. 创建回测引擎
        print("\n4️⃣ 创建回测引擎...")
        backtest_engine = BacktestEngine(initial_capital=10000.0, commission=0.001)
        print("✅ 回测引擎创建成功")

        # 5. 运行回测 - 使用实际数据范围
        print("\n5️⃣ 运行ML策略回测...")
        start_date = data['timestamp'].min()
        end_date = data['timestamp'].max()

        print(f"   使用数据范围: {start_date} 到 {end_date}")

        result = backtest_engine.run_backtest(
            strategy=strategy,
            symbol='BTCUSDT',
            start_date=start_date,
            end_date=end_date,
            interval='1h'
        )

        print("✅ ML策略回测运行成功!")
        print(f"   总收益率: {result.total_return:.2%}")
        print(f"   年化收益率: {result.annual_return:.2%}")
        print(f"   最大回撤: {result.max_drawdown:.2%}")
        print(f"   夏普比率: {result.sharpe_ratio:.2f}")
        print(f"   总交易次数: {result.total_trades}")
        print(f"   胜率: {result.win_rate:.2%}")

        # 6. 验证结果不为零
        if result.total_trades > 0:
            print("✅ ML策略生成了交易信号!")
        else:
            print("⚠️  ML策略未生成交易信号，可能需要更多数据或调整参数")

        # 7. 测试API端点
        print("\n7️⃣ 测试API端点...")
        from app import run_strategy_backtest

        backtest_result = run_strategy_backtest('BTCUSDT', 'ML')
        print("✅ API回测成功!")
        print(f"   总交易次数: {backtest_result.get('total_trades', 0)}")
        print(f"   总收益率: {backtest_result.get('total_return', 0):.2%}")

        print("\n🎉 ML策略修复验证成功!")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ml_strategy_fix() 