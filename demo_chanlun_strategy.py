#!/usr/bin/env python3
"""
缠论01策略演示
展示缠论策略的实际应用和交易逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategies.chanlun_strategy import ChanlunStrategy
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def load_chanlun_config():
    """加载缠论策略配置"""
    try:
        with open('config/chanlun_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载配置失败: {e}")
        return None

def create_realistic_test_data():
    """创建更真实的测试数据，模拟BTC价格走势"""
    # 生成更真实的BTC价格数据
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='1H')
    n = len(dates)
    
    # 模拟BTC价格走势（包含趋势、震荡、背离等特征）
    np.random.seed(42)
    base_price = 50000
    
    # 创建趋势周期
    trend_cycle = np.sin(np.linspace(0, 4*np.pi, n)) * 0.1
    noise = np.random.randn(n) * 0.005
    volatility = np.random.randn(n) * 0.01
    
    # 添加背离特征
    divergence_period = n // 4
    divergence = np.zeros(n)
    divergence[divergence_period:divergence_period*2] = -0.02  # 底背离
    divergence[divergence_period*2:divergence_period*3] = 0.02  # 顶背离
    
    prices = base_price * (1 + trend_cycle + noise + volatility + divergence)
    
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
    
    return data

def analyze_chanlun_features(data, strategy):
    """分析缠论特征"""
    print("\n🔍 缠论特征分析")
    print("=" * 50)
    
    # 准备特征数据
    feature_data = strategy.prepare_features(data)
    
    if feature_data.empty:
        print("❌ 特征数据为空")
        return None
    
    # 分析分型
    top_fractals = feature_data[feature_data['top_fractal'] == 1]
    bottom_fractals = feature_data[feature_data['bottom_fractal'] == 1]
    
    print(f"📊 分型统计:")
    print(f"   顶分型: {len(top_fractals)} 个")
    print(f"   底分型: {len(bottom_fractals)} 个")
    
    # 分析笔
    stroke_starts = feature_data[feature_data['stroke_start'] == 1]
    stroke_ends = feature_data[feature_data['stroke_end'] == 1]
    
    print(f"\n📈 笔的统计:")
    print(f"   笔的起点: {len(stroke_starts)} 个")
    print(f"   笔的终点: {len(stroke_ends)} 个")
    
    # 分析买卖点
    buy_points = feature_data[
        (feature_data['buy_point_1'] == 1) | 
        (feature_data['buy_point_2'] == 1) | 
        (feature_data['buy_point_3'] == 1)
    ]
    
    sell_points = feature_data[
        (feature_data['sell_point_1'] == 1) | 
        (feature_data['sell_point_2'] == 1) | 
        (feature_data['sell_point_3'] == 1)
    ]
    
    print(f"\n🎯 买卖点统计:")
    print(f"   买点总数: {len(buy_points)} 个")
    print(f"   卖点总数: {len(sell_points)} 个")
    
    # 分析背离
    price_macd_divergence = feature_data[feature_data['price_macd_divergence'] == 1]
    rsi_divergence = feature_data[feature_data['rsi_divergence'] == 1]
    
    print(f"\n🔄 背离检测:")
    print(f"   价格MACD背离: {len(price_macd_divergence)} 个")
    print(f"   RSI背离: {len(rsi_divergence)} 个")
    
    return feature_data

def simulate_trading(data, strategy):
    """模拟交易"""
    print("\n💰 模拟交易")
    print("=" * 50)
    
    # 交易参数
    initial_balance = 10000  # 初始资金
    balance = initial_balance
    position = 0
    entry_price = 0
    trades = []
    
    print(f"初始资金: ${balance:.2f}")
    
    for i in range(50, len(data)):
        current_data = data.iloc[:i+1]
        current_price = current_data['close'].iloc[-1]
        
        # 生成信号
        signal = strategy.generate_signal(current_data)
        
        # 执行交易
        if signal == 'BUY' and position == 0:
            # 买入
            position_size = strategy.calculate_position_size(current_price, balance)
            cost = position_size * current_price
            if cost <= balance:
                position = position_size
                entry_price = current_price
                balance -= cost
                trades.append({
                    'type': 'BUY',
                    'price': current_price,
                    'quantity': position_size,
                    'timestamp': current_data['timestamp'].iloc[-1],
                    'balance': balance
                })
                print(f"🟢 买入: ${current_price:.2f}, 数量: {position_size:.6f}, 余额: ${balance:.2f}")
        
        elif signal == 'SELL' and position > 0:
            # 卖出
            revenue = position * current_price
            balance += revenue
            profit = revenue - (position * entry_price)
            trades.append({
                'type': 'SELL',
                'price': current_price,
                'quantity': position,
                'timestamp': current_data['timestamp'].iloc[-1],
                'balance': balance,
                'profit': profit
            })
            print(f"🔴 卖出: ${current_price:.2f}, 数量: {position:.6f}, 利润: ${profit:.2f}, 余额: ${balance:.2f}")
            position = 0
            entry_price = 0
        
        # 止损止盈检查
        if position > 0:
            if strategy.should_stop_loss(current_price):
                revenue = position * current_price
                balance += revenue
                loss = revenue - (position * entry_price)
                trades.append({
                    'type': 'STOP_LOSS',
                    'price': current_price,
                    'quantity': position,
                    'timestamp': current_data['timestamp'].iloc[-1],
                    'balance': balance,
                    'loss': loss
                })
                print(f"🛑 止损: ${current_price:.2f}, 损失: ${loss:.2f}, 余额: ${balance:.2f}")
                position = 0
                entry_price = 0
            
            elif strategy.should_take_profit(current_price):
                revenue = position * current_price
                balance += revenue
                profit = revenue - (position * entry_price)
                trades.append({
                    'type': 'TAKE_PROFIT',
                    'price': current_price,
                    'quantity': position,
                    'timestamp': current_data['timestamp'].iloc[-1],
                    'balance': balance,
                    'profit': profit
                })
                print(f"🎯 止盈: ${current_price:.2f}, 利润: ${profit:.2f}, 余额: ${balance:.2f}")
                position = 0
                entry_price = 0
    
    # 计算最终结果
    final_balance = balance
    if position > 0:
        final_balance += position * data['close'].iloc[-1]
    
    total_return = (final_balance - initial_balance) / initial_balance * 100
    
    print(f"\n📊 交易总结:")
    print(f"   初始资金: ${initial_balance:.2f}")
    print(f"   最终资金: ${final_balance:.2f}")
    print(f"   总收益率: {total_return:.2f}%")
    print(f"   交易次数: {len(trades)}")
    
    return trades

def plot_chanlun_analysis(data, feature_data, trades):
    """绘制缠论分析图表"""
    try:
        plt.style.use('seaborn')
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        
        # 价格和买卖点
        axes[0].plot(data['timestamp'], data['close'], label='价格', alpha=0.7)
        
        # 标记买卖点
        if feature_data is not None:
            buy_points = feature_data[
                (feature_data['buy_point_1'] == 1) | 
                (feature_data['buy_point_2'] == 1) | 
                (feature_data['buy_point_3'] == 1)
            ]
            sell_points = feature_data[
                (feature_data['sell_point_1'] == 1) | 
                (feature_data['sell_point_2'] == 1) | 
                (feature_data['sell_point_3'] == 1)
            ]
            
            if len(buy_points) > 0:
                axes[0].scatter(buy_points['timestamp'], buy_points['close'], 
                               color='green', marker='^', s=100, label='买点', alpha=0.8)
            
            if len(sell_points) > 0:
                axes[0].scatter(sell_points['timestamp'], sell_points['close'], 
                               color='red', marker='v', s=100, label='卖点', alpha=0.8)
        
        # 标记交易
        if trades:
            for trade in trades:
                if trade['type'] == 'BUY':
                    axes[0].scatter(trade['timestamp'], trade['price'], 
                                   color='blue', marker='o', s=150, alpha=0.8)
                elif trade['type'] == 'SELL':
                    axes[0].scatter(trade['timestamp'], trade['price'], 
                                   color='orange', marker='s', s=150, alpha=0.8)
        
        axes[0].set_title('缠论01策略 - 价格与买卖点', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('价格 (USD)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # MACD指标
        if feature_data is not None and 'macd' in feature_data.columns:
            axes[1].plot(feature_data['timestamp'], feature_data['macd'], label='MACD', alpha=0.7)
            axes[1].plot(feature_data['timestamp'], feature_data['macd_signal'], label='MACD信号线', alpha=0.7)
            axes[1].bar(feature_data['timestamp'], feature_data['macd_histogram'], 
                       label='MACD柱状图', alpha=0.5, width=0.02)
            axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[1].set_title('MACD指标', fontsize=12)
            axes[1].set_ylabel('MACD')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
        
        # RSI指标
        if feature_data is not None and 'rsi' in feature_data.columns:
            axes[2].plot(feature_data['timestamp'], feature_data['rsi'], label='RSI', color='purple', alpha=0.7)
            axes[2].axhline(y=70, color='red', linestyle='--', alpha=0.5, label='超买线')
            axes[2].axhline(y=30, color='green', linestyle='--', alpha=0.5, label='超卖线')
            axes[2].set_title('RSI指标', fontsize=12)
            axes[2].set_ylabel('RSI')
            axes[2].set_xlabel('时间')
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('chanlun_analysis.png', dpi=300, bbox_inches='tight')
        print("📊 分析图表已保存为: chanlun_analysis.png")
        
    except Exception as e:
        print(f"绘制图表失败: {e}")

def main():
    """主函数"""
    print("🎯 缠论01策略演示")
    print("=" * 60)
    
    try:
        # 1. 加载配置
        print("1️⃣ 加载缠论策略配置...")
        config = load_chanlun_config()
        if config is None:
            print("❌ 配置加载失败")
            return
        
        print("✅ 配置加载成功")
        print(f"   策略名称: {config['display_name']}")
        print(f"   描述: {config['description']}")
        
        # 2. 创建测试数据
        print("\n2️⃣ 创建真实测试数据...")
        data = create_realistic_test_data()
        print(f"✅ 创建了 {len(data)} 条测试数据")
        print(f"   时间范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
        print(f"   价格范围: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
        
        # 3. 初始化策略
        print("\n3️⃣ 初始化缠论策略...")
        strategy = ChanlunStrategy('BTCUSDT', config['parameters'])
        print("✅ 策略初始化成功")
        
        # 4. 分析缠论特征
        feature_data = analyze_chanlun_features(data, strategy)
        
        # 5. 模拟交易
        trades = simulate_trading(data, strategy)
        
        # 6. 绘制分析图表
        print("\n6️⃣ 生成分析图表...")
        plot_chanlun_analysis(data, feature_data, trades)
        
        # 7. 总结
        print("\n🎉 缠论01策略演示完成!")
        print("\n📋 策略特点总结:")
        print("   ✅ 多周期联动分析")
        print("   ✅ 分型与笔的识别")
        print("   ✅ 线段与中枢构建")
        print("   ✅ 三类买卖点判断")
        print("   ✅ 背离检测")
        print("   ✅ 动态仓位管理")
        print("   ✅ 风险控制机制")
        print("   ✅ 趋势与盘整应对")
        
        print("\n🚀 策略已成功集成到交易系统中!")
        print("   可以通过Web界面选择'缠论01'策略进行交易")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 