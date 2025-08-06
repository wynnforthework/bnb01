#!/usr/bin/env python3
"""
测试策略信号生成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.client_manager import client_manager
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
import pandas as pd

def test_strategy_signals():
    print("🧪 测试策略信号生成...")
    print("=" * 50)
    
    # 获取合约客户端
    futures_client = client_manager.get_futures_client()
    
    # 测试交易对
    test_symbols = ['BTCUSDT', 'ETHUSDT']
    
    for symbol in test_symbols:
        print(f"\n📊 测试 {symbol}:")
        
        # 获取市场数据
        data = futures_client.get_klines(symbol, '1h', 100)
        if data is None or data.empty:
            print(f"❌ 无法获取 {symbol} 数据")
            continue
        
        current_price = data['close'].iloc[-1]
        print(f"当前价格: {current_price:.2f}")
        
        # 测试MA策略
        print("\n🔄 移动平均线策略:")
        ma_strategy = MovingAverageStrategy(symbol, {
            'short_window': 5,
            'long_window': 15,
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'position_size': 0.03
        })
        
        ma_signal = ma_strategy.generate_signal(data)
        print(f"信号: {ma_signal}")
        
        # 计算移动平均线
        short_ma = data['close'].rolling(window=5).mean()
        long_ma = data['close'].rolling(window=15).mean()
        
        print(f"短期均线(5): {short_ma.iloc[-1]:.2f}")
        print(f"长期均线(15): {long_ma.iloc[-1]:.2f}")
        print(f"前一期短期均线: {short_ma.iloc[-2]:.2f}")
        print(f"前一期长期均线: {long_ma.iloc[-2]:.2f}")
        
        # 检查金叉死叉条件
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        prev_short = short_ma.iloc[-2]
        prev_long = long_ma.iloc[-2]
        
        print(f"当前: 短期{'>' if current_short > current_long else '<'}长期")
        print(f"前期: 短期{'>' if prev_short > prev_long else '<'}长期")
        
        if prev_short <= prev_long and current_short > current_long:
            print("🟢 检测到金叉信号 (应该买入)")
        elif prev_short >= prev_long and current_short < current_long:
            print("🔴 检测到死叉信号 (应该卖出)")
        else:
            print("⚪ 无交叉信号")
        
        # 测试RSI策略
        print("\n📈 RSI策略:")
        rsi_strategy = RSIStrategy(symbol, {
            'rsi_period': 10,
            'oversold': 35,
            'overbought': 65,
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'position_size': 0.03
        })
        
        rsi_signal = rsi_strategy.generate_signal(data)
        print(f"信号: {rsi_signal}")
        
        # 计算RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=10).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=10).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        print(f"当前RSI: {current_rsi:.2f}")
        
        if current_rsi < 35:
            print("🟢 RSI超卖 (应该买入)")
        elif current_rsi > 65:
            print("🔴 RSI超买 (应该卖出)")
        else:
            print("⚪ RSI中性")
        
        # 显示最近几期的价格变化
        print(f"\n📊 最近5期价格变化:")
        for i in range(-5, 0):
            price = data['close'].iloc[i]
            change = ((price - data['close'].iloc[i-1]) / data['close'].iloc[i-1]) * 100
            print(f"  {i}: {price:.2f} ({change:+.2f}%)")

def create_aggressive_strategy():
    """创建更激进的策略参数"""
    print("\n🚀 创建更激进的策略...")
    
    # 更激进的MA策略参数
    aggressive_ma_params = {
        'short_window': 3,   # 非常短的窗口
        'long_window': 8,    # 非常短的窗口
        'stop_loss': 0.015,  # 更紧的止损
        'take_profit': 0.025, # 更小的止盈
        'position_size': 0.02 # 更小的仓位
    }
    
    print("激进MA策略参数:")
    for key, value in aggressive_ma_params.items():
        print(f"  {key}: {value}")
    
    return aggressive_ma_params

if __name__ == '__main__':
    test_strategy_signals()
    create_aggressive_strategy()