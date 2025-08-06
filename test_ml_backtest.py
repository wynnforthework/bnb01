#!/usr/bin/env python3
"""
测试机器学习策略回测
"""

import asyncio
from backend.data_collector import DataCollector
from backend.backtesting import BacktestEngine
from strategies.ml_strategy import MLStrategy

async def test_ml_backtest():
    """测试机器学习策略回测"""
    print("🧠 测试机器学习策略回测...")
    
    try:
        # 先收集数据
        collector = DataCollector()
        data = await collector.collect_historical_data('BTCUSDT', '1h', 30)
        print(f"收集到 {len(data)} 条数据")
        
        # 创建回测引擎
        backtest_engine = BacktestEngine()
        
        # 创建机器学习策略
        ml_strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 20,
            'prediction_horizon': 1,
            'min_confidence': 0.55,
            'up_threshold': 0.005,    # 0.5%
            'down_threshold': -0.005, # -0.5%
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'position_size': 0.1,
            'min_training_samples': 100
        })
        
        # 运行回测
        result = backtest_engine.run_backtest(
            strategy=ml_strategy,
            symbol='BTCUSDT',
            start_date='2025-07-01',  # 使用有数据的日期范围
            end_date='2025-08-05',
            interval='1h'
        )
        
        print("✅ 机器学习策略回测成功!")
        print(f"总收益率: {result.total_return:.2%}")
        print(f"年化收益率: {result.annual_return:.2%}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"夏普比率: {result.sharpe_ratio:.2f}")
        print(f"总交易次数: {result.total_trades}")
        print(f"胜率: {result.win_rate:.2%}")
        print(f"盈亏比: {result.profit_factor:.2f}")
        print(f"平均每笔收益: ${result.avg_trade_return:.2f}")
        
        # 显示交易详情
        if result.trades:
            print(f"\n📊 交易详情 (共{len(result.trades)}笔):")
            profitable_trades = [t for t in result.trades if t.get('profit', 0) > 0]
            losing_trades = [t for t in result.trades if t.get('profit', 0) < 0]
            
            print(f"盈利交易: {len(profitable_trades)} 笔")
            print(f"亏损交易: {len(losing_trades)} 笔")
            
            if profitable_trades:
                total_profit = sum(t.get('profit', 0) for t in profitable_trades)
                print(f"总盈利: ${total_profit:.2f}")
            
            if losing_trades:
                total_loss = sum(t.get('profit', 0) for t in losing_trades)
                print(f"总亏损: ${total_loss:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 机器学习策略回测失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    asyncio.run(test_ml_backtest())