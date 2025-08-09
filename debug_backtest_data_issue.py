#!/usr/bin/env python3
"""
诊断回测数据问题
检查为什么只有BTCUSDT有回测数据，其他币种回测结果为0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.data_collector import DataCollector
from backend.backtesting import BacktestEngine
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.ml_strategy import MLStrategy
from strategies.chanlun_strategy import ChanlunStrategy
from datetime import datetime, timedelta
import pandas as pd

def check_database_data():
    """检查数据库中的数据情况"""
    print("🔍 检查数据库中的数据情况...")
    
    dc = DataCollector()
    symbols = ['BTCUSDT', 'ETHUSDT', 'MATICUSDT']
    
    for symbol in symbols:
        print(f"\n📊 {symbol}:")
        
        # 检查市场数据
        market_data = dc.get_market_data(symbol, '1h', limit=1000)
        print(f"  市场数据: {len(market_data)} 条记录")
        
        if not market_data.empty:
            print(f"  数据范围: {market_data['timestamp'].min()} 到 {market_data['timestamp'].max()}")
            print(f"  最新价格: {market_data.iloc[-1]['close']:.4f}")
        else:
            print("  ⚠️  没有市场数据")
        
        # 检查技术指标数据
        tech_data = dc.get_technical_indicators(symbol, limit=1000)
        print(f"  技术指标: {len(tech_data)} 条记录")

def test_strategy_backtest():
    """测试策略回测"""
    print("\n🧪 测试策略回测...")
    
    dc = DataCollector()
    backtest_engine = BacktestEngine()
    symbols = ['BTCUSDT', 'ETHUSDT', 'MATICUSDT']
    strategies = ['MA', 'RSI', 'ML', 'Chanlun']
    
    for symbol in symbols:
        print(f"\n🎯 {symbol} 策略回测测试:")
        
        # 检查数据可用性
        market_data = dc.get_market_data(symbol, '1h', limit=1000)
        if market_data.empty:
            print(f"  ❌ {symbol} 没有市场数据，跳过回测")
            continue
        
        # 确定数据范围
        start_date = market_data['timestamp'].min()
        end_date = market_data['timestamp'].max()
        print(f"  数据范围: {start_date} 到 {end_date}")
        
        for strategy_type in strategies:
            try:
                print(f"    🔄 测试 {strategy_type} 策略...")
                
                # 创建策略实例
                if strategy_type == 'MA':
                    strategy = MovingAverageStrategy(symbol, {
                        'short_window': 10,
                        'long_window': 20,
                        'stop_loss': 0.02,
                        'take_profit': 0.05,
                        'position_size': 0.1
                    })
                elif strategy_type == 'RSI':
                    strategy = RSIStrategy(symbol, {
                        'rsi_period': 14,
                        'oversold': 30,
                        'overbought': 70,
                        'stop_loss': 0.02,
                        'take_profit': 0.05,
                        'position_size': 0.1
                    })
                elif strategy_type == 'ML':
                    strategy = MLStrategy(symbol, {
                        'model_type': 'random_forest',
                        'lookback_period': 30,
                        'prediction_horizon': 1,
                        'min_confidence': 0.65,
                        'up_threshold': 0.015,
                        'down_threshold': -0.015,
                        'stop_loss': 0.03,
                        'take_profit': 0.06,
                        'position_size': 0.05
                    })
                elif strategy_type == 'Chanlun':
                    strategy = ChanlunStrategy(symbol, {
                        'timeframes': ['30m', '1h', '4h'],
                        'min_swing_length': 2,
                        'central_bank_min_bars': 2,
                        'macd_fast': 12,
                        'macd_slow': 26,
                        'macd_signal': 9,
                        'rsi_period': 14,
                        'ma_short': 5,
                        'ma_long': 20,
                        'position_size': 0.2,
                        'max_position': 0.8,
                        'stop_loss': 0.04,
                        'take_profit': 0.08,
                        'trend_confirmation': 0.01,
                        'divergence_threshold': 0.05
                    })
                
                # 运行回测
                result = backtest_engine.run_backtest(
                    strategy=strategy,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval='1h'
                )
                
                print(f"      ✅ {strategy_type}: 收益率 {result.total_return:.2%}, 交易次数 {result.total_trades}")
                
            except Exception as e:
                print(f"      ❌ {strategy_type} 回测失败: {e}")

def check_strategy_signal_generation():
    """检查策略信号生成"""
    print("\n📡 检查策略信号生成...")
    
    dc = DataCollector()
    symbols = ['BTCUSDT', 'ETHUSDT', 'MATICUSDT']
    
    for symbol in symbols:
        print(f"\n🎯 {symbol} 信号生成测试:")
        
        market_data = dc.get_market_data(symbol, '1h', limit=100)
        if market_data.empty:
            print(f"  ❌ 没有数据")
            continue
        
        # 测试MA策略信号生成
        try:
            ma_strategy = MovingAverageStrategy(symbol, {
                'short_window': 10,
                'long_window': 20,
                'stop_loss': 0.02,
                'take_profit': 0.05,
                'position_size': 0.1
            })
            
            # 计算技术指标
            data_with_indicators = dc.calculate_technical_indicators(market_data, symbol)
            
            if len(data_with_indicators) >= 20:
                signal = ma_strategy.generate_signal(data_with_indicators)
                print(f"  MA策略信号: {signal}")
            else:
                print(f"  ⚠️  数据不足，需要至少20个数据点")
                
        except Exception as e:
            print(f"  ❌ MA策略信号生成失败: {e}")

def main():
    """主函数"""
    print("🚀 开始诊断回测数据问题...")
    
    try:
        # 1. 检查数据库数据
        check_database_data()
        
        # 2. 测试策略回测
        test_strategy_backtest()
        
        # 3. 检查策略信号生成
        check_strategy_signal_generation()
        
        print("\n✅ 诊断完成!")
        
    except Exception as e:
        print(f"❌ 诊断过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
