#!/usr/bin/env python3
"""
测试回测功能
"""

import asyncio
from backend.data_collector import DataCollector
from backend.backtesting import BacktestEngine
from strategies.ma_strategy import MovingAverageStrategy

async def test_data_collection():
    """测试数据收集"""
    print("🔍 测试数据收集...")
    
    collector = DataCollector()
    data = await collector.collect_historical_data('BTCUSDT', '1h', 30)
    
    print(f"收集到 {len(data)} 条数据")
    if not data.empty:
        print(f"数据范围: {data.iloc[0]['timestamp']} 到 {data.iloc[-1]['timestamp']}")
        print(f"数据列: {list(data.columns)}")
        return True
    else:
        print("❌ 数据收集失败")
        return False

def test_backtest():
    """测试回测功能"""
    print("\n📊 测试回测功能...")
    
    try:
        # 创建回测引擎
        backtest_engine = BacktestEngine()
        
        # 创建策略
        strategy = MovingAverageStrategy('BTCUSDT', {
            'short_window': 10,
            'long_window': 30,
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'position_size': 0.1
        })
        
        # 运行回测
        result = backtest_engine.run_backtest(
            strategy=strategy,
            symbol='BTCUSDT',
            start_date='2024-01-01',
            end_date='2024-12-31',
            interval='1h'
        )
        
        print("✅ 回测成功!")
        print(f"总收益率: {result.total_return:.2%}")
        print(f"年化收益率: {result.annual_return:.2%}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"夏普比率: {result.sharpe_ratio:.2f}")
        print(f"总交易次数: {result.total_trades}")
        print(f"胜率: {result.win_rate:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ 回测失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

async def main():
    """主函数"""
    print("🚀 回测功能测试")
    print("=" * 50)
    
    # 测试数据收集
    data_ok = await test_data_collection()
    
    if data_ok:
        # 测试回测
        backtest_ok = test_backtest()
        
        if backtest_ok:
            print("\n🎉 所有测试通过!")
        else:
            print("\n❌ 回测测试失败")
    else:
        print("\n❌ 数据收集测试失败")

if __name__ == '__main__':
    asyncio.run(main())