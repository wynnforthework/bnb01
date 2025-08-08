#!/usr/bin/env python3
"""
测试回测数据问题修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.backtesting import BacktestEngine
from backend.data_collector import DataCollector
from strategies.ma_strategy import MovingAverageStrategy
import pandas as pd
from datetime import datetime, timedelta

def test_backtest_data_fix():
    """测试回测数据问题修复"""
    print("🧪 测试回测数据问题修复...")
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
        
        # 2. 创建回测引擎
        print("\n2️⃣ 创建回测引擎...")
        backtest_engine = BacktestEngine(initial_capital=10000.0, commission=0.001)
        print("✅ 回测引擎创建成功")
        
        # 3. 创建策略
        print("\n3️⃣ 创建移动平均策略...")
        strategy = MovingAverageStrategy('BTCUSDT')
        print("✅ 策略创建成功")
        
        # 4. 运行回测 - 使用实际数据范围
        print("\n4️⃣ 运行回测...")
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
        
        print("✅ 回测运行成功!")
        print(f"   总收益率: {result.total_return:.2%}")
        print(f"   年化收益率: {result.annual_return:.2%}")
        print(f"   最大回撤: {result.max_drawdown:.2%}")
        print(f"   夏普比率: {result.sharpe_ratio:.2f}")
        print(f"   总交易次数: {result.total_trades}")
        print(f"   胜率: {result.win_rate:.2%}")
        
        # 5. 测试API端点
        print("\n5️⃣ 测试API端点...")
        from app import run_strategy_backtest
        
        backtest_result = run_strategy_backtest('BTCUSDT', 'MA')
        print("✅ API回测成功!")
        print(f"   结果: {backtest_result}")
        
        print("\n🎉 回测数据问题修复验证成功!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backtest_data_fix()
