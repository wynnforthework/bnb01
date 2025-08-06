#!/usr/bin/env python3
"""
简单的缠论策略回测测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategies.chanlun_strategy import ChanlunStrategy
import pandas as pd
import numpy as np

def test_simple_chanlun_backtest():
    """简单的缠论策略回测测试"""
    print("🧪 简单缠论策略回测测试...")
    print("=" * 50)
    
    try:
        # 1. 创建缠论策略
        print("1️⃣ 创建缠论策略...")
        parameters = {
            'timeframes': ['30m', '1h', '4h'],
            'min_swing_length': 2,  # 降低阈值
            'central_bank_min_bars': 2,  # 降低阈值
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'ma_short': 5,
            'ma_long': 20,
            'position_size': 0.25,
            'max_position': 0.9,
            'stop_loss': 0.035,
            'take_profit': 0.07,
            'trend_confirmation': 0.015,
            'divergence_threshold': 0.08
        }
        
        strategy = ChanlunStrategy('BTCUSDT', parameters)
        print("✅ 缠论策略创建成功")
        
        # 2. 创建测试数据
        print("\n2️⃣ 创建测试数据...")
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='1H')
        n = len(dates)
        
        # 模拟BTC价格走势
        np.random.seed(42)
        base_price = 50000
        trend = np.cumsum(np.random.randn(n) * 0.01)
        noise = np.random.randn(n) * 0.005
        prices = base_price * (1 + trend + noise)
        
        # 生成OHLC数据
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices * (1 + np.random.randn(n) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(n)) * 0.002),
            'low': prices * (1 - np.abs(np.random.randn(n)) * 0.002),
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n)
        })
        
        # 确保high >= low
        data['high'] = data[['open', 'close', 'high']].max(axis=1)
        data['low'] = data[['open', 'close', 'low']].min(axis=1)
        
        print(f"✅ 创建了 {len(data)} 条测试数据")
        
        # 3. 测试信号生成
        print("\n3️⃣ 测试信号生成...")
        signals = []
        buy_signals = 0
        sell_signals = 0
        
        for i in range(50, len(data)):  # 从第50个数据点开始
            current_data = data.iloc[:i+1]
            signal = strategy.generate_signal(current_data)
            signals.append(signal)
            
            if signal == 'BUY':
                buy_signals += 1
                print(f"   🟢 BUY信号 at {data.iloc[i]['timestamp']} - 价格: ${data.iloc[i]['close']:.2f}")
            elif signal == 'SELL':
                sell_signals += 1
                print(f"   🔴 SELL信号 at {data.iloc[i]['timestamp']} - 价格: ${data.iloc[i]['close']:.2f}")
        
        print(f"\n   信号统计:")
        print(f"   总信号数: {len(signals)}")
        print(f"   买入信号: {buy_signals}")
        print(f"   卖出信号: {sell_signals}")
        print(f"   持仓信号: {len(signals) - buy_signals - sell_signals}")
        
        # 4. 简单回测
        print("\n4️⃣ 运行简单回测...")
        capital = 10000.0
        position = 0
        entry_price = 0
        trades = []
        
        for i in range(50, len(data)):
            current_data = data.iloc[:i+1]
            current_price = data.iloc[i]['close']
            current_time = data.iloc[i]['timestamp']
            
            signal = strategy.generate_signal(current_data)
            
            # 执行交易逻辑
            if signal == 'BUY' and position <= 0:
                # 买入
                position_size = strategy.calculate_position_size(current_price, capital)
                if position_size > 0:
                    position = position_size
                    entry_price = current_price
                    cost = position * current_price * 1.001  # 包含手续费
                    capital -= cost
                    trades.append({
                        'timestamp': current_time,
                        'action': 'BUY',
                        'price': current_price,
                        'quantity': position,
                        'profit': 0,
                        'capital': capital
                    })
                    print(f"   🟢 买入: ${current_price:.2f}, 数量: {position:.6f}")
            
            elif signal == 'SELL' and position > 0:
                # 卖出
                revenue = position * current_price * 0.999  # 包含手续费
                capital += revenue
                profit = revenue - (position * entry_price)
                trades.append({
                    'timestamp': current_time,
                    'action': 'SELL',
                    'price': current_price,
                    'quantity': position,
                    'profit': profit,
                    'capital': capital
                })
                print(f"   🔴 卖出: ${current_price:.2f}, 数量: {position:.6f}, 利润: ${profit:.2f}")
                position = 0
                entry_price = 0
        
        # 5. 计算回测结果
        print("\n5️⃣ 计算回测结果...")
        
        if len(trades) > 0:
            # 计算总收益率
            final_capital = capital
            if position > 0:
                final_capital += position * data.iloc[-1]['close']
            
            total_return = (final_capital - 10000.0) / 10000.0
            
            # 计算胜率
            profitable_trades = [t for t in trades if t.get('profit', 0) > 0]
            win_rate = len(profitable_trades) / len(trades) if trades else 0
            
            print(f"✅ 回测完成!")
            print(f"   总交易次数: {len(trades)}")
            print(f"   总收益率: {total_return*100:.2f}%")
            print(f"   胜率: {win_rate*100:.1f}%")
            print(f"   最终资金: ${final_capital:.2f}")
            
            if trades:
                print(f"\n   交易记录:")
                for i, trade in enumerate(trades):
                    print(f"     {i+1}. {trade['action']} @ ${trade['price']:.2f}")
        else:
            print("   ⚠️ 回测期间没有产生交易")
            print("   🔍 可能的原因:")
            print("      - 策略参数过于严格")
            print("      - 数据量不足")
            print("      - 信号生成逻辑有问题")
        
        print("\n🎉 简单缠论策略回测测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    test_simple_chanlun_backtest() 