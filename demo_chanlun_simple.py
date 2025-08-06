#!/usr/bin/env python3
"""
缠论01策略简化演示
展示缠论策略的核心功能，不依赖matplotlib
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
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

def create_test_data():
    """创建测试数据"""
    # 生成模拟的K线数据
    dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='1H')
    n = len(dates)
    
    # 模拟价格走势
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
    
    return data

def analyze_strategy_features(data, strategy):
    """分析策略特征"""
    print("\n🔍 缠论特征分析")
    print("=" * 50)
    
    # 准备特征数据
    feature_data = strategy.prepare_features(data)
    
    if feature_data.empty:
        print("❌ 特征数据为空")
        return None
    
    print(f"✅ 特征数据准备成功")
    print(f"   数据形状: {feature_data.shape}")
    
    # 检查关键特征
    key_features = [
        'top_fractal', 'bottom_fractal', 
        'stroke_start', 'stroke_end',
        'buy_point_1', 'buy_point_2', 'buy_point_3',
        'sell_point_1', 'sell_point_2', 'sell_point_3',
        'price_macd_divergence', 'rsi_divergence',
        'macd', 'rsi', 'ma_short', 'ma_long'
    ]
    
    print(f"\n📊 特征统计:")
    for feature in key_features:
        if feature in feature_data.columns:
            if feature_data[feature].dtype in ['int64', 'float64']:
                count = feature_data[feature].sum()
                print(f"   {feature}: {count}")
            else:
                print(f"   {feature}: 已计算")
    
    return feature_data

def test_signal_generation(data, strategy):
    """测试信号生成"""
    print("\n🎯 信号生成测试")
    print("=" * 50)
    
    signals = []
    signal_details = []
    
    for i in range(50, len(data), 5):  # 每5个数据点测试一次
        current_data = data.iloc[:i+1]
        signal = strategy.generate_signal(current_data)
        signals.append(signal)
        
        signal_details.append({
            'index': i,
            'timestamp': current_data['timestamp'].iloc[-1],
            'price': current_data['close'].iloc[-1],
            'signal': signal
        })
        
        if signal != 'HOLD':
            print(f"   {current_data['timestamp'].iloc[-1]}: {signal} @ ${current_data['close'].iloc[-1]:.2f}")
    
    # 统计信号
    signal_counts = pd.Series(signals).value_counts()
    print(f"\n📈 信号统计:")
    for signal, count in signal_counts.items():
        print(f"   {signal}: {count}")
    
    return signal_details

def test_position_management(strategy):
    """测试仓位管理"""
    print("\n💰 仓位管理测试")
    print("=" * 50)
    
    # 模拟不同场景
    test_scenarios = [
        {'price': 50000, 'balance': 10000, 'position': 0, 'entry_price': 0},
        {'price': 51000, 'balance': 10000, 'position': 0.1, 'entry_price': 50000},
        {'price': 48000, 'balance': 10000, 'position': 0.1, 'entry_price': 50000},
        {'price': 52000, 'balance': 10000, 'position': 0.1, 'entry_price': 50000},
    ]
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n   场景 {i+1}:")
        print(f"   当前价格: ${scenario['price']:.2f}")
        print(f"   账户余额: ${scenario['balance']:.2f}")
        print(f"   持仓数量: {scenario['position']:.6f}")
        print(f"   入场价格: ${scenario['entry_price']:.2f}")
        
        # 设置策略状态
        strategy.position = scenario['position']
        strategy.entry_price = scenario['entry_price']
        
        # 计算仓位大小
        position_size = strategy.calculate_position_size(scenario['price'], scenario['balance'])
        print(f"   建议仓位: {position_size:.6f}")
        
        # 检查止损止盈
        stop_loss = strategy.should_stop_loss(scenario['price'])
        take_profit = strategy.should_take_profit(scenario['price'])
        print(f"   需要止损: {stop_loss}")
        print(f"   需要止盈: {take_profit}")

def test_chanlun_logic(data, strategy):
    """测试缠论逻辑"""
    print("\n🧠 缠论逻辑测试")
    print("=" * 50)
    
    feature_data = strategy.prepare_features(data)
    if feature_data is None:
        return
    
    # 测试分型识别
    top_fractals = feature_data[feature_data['top_fractal'] == 1]
    bottom_fractals = feature_data[feature_data['bottom_fractal'] == 1]
    
    print(f"📊 分型识别:")
    print(f"   顶分型数量: {len(top_fractals)}")
    print(f"   底分型数量: {len(bottom_fractals)}")
    
    if len(top_fractals) > 0:
        print(f"   顶分型示例:")
        for i, (idx, row) in enumerate(top_fractals.head(3).iterrows()):
            print(f"     {i+1}. {row['timestamp']} - ${row['close']:.2f}")
    
    if len(bottom_fractals) > 0:
        print(f"   底分型示例:")
        for i, (idx, row) in enumerate(bottom_fractals.head(3).iterrows()):
            print(f"     {i+1}. {row['timestamp']} - ${row['close']:.2f}")
    
    # 测试买卖点
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
    
    print(f"\n🎯 买卖点识别:")
    print(f"   买点数量: {len(buy_points)}")
    print(f"   卖点数量: {len(sell_points)}")
    
    if len(buy_points) > 0:
        print(f"   买点示例:")
        for i, (idx, row) in enumerate(buy_points.head(3).iterrows()):
            buy_types = []
            if row['buy_point_1'] == 1: buy_types.append('第一类')
            if row['buy_point_2'] == 1: buy_types.append('第二类')
            if row['buy_point_3'] == 1: buy_types.append('第三类')
            print(f"     {i+1}. {row['timestamp']} - {', '.join(buy_types)}买点 - ${row['close']:.2f}")
    
    if len(sell_points) > 0:
        print(f"   卖点示例:")
        for i, (idx, row) in enumerate(sell_points.head(3).iterrows()):
            sell_types = []
            if row['sell_point_1'] == 1: sell_types.append('第一类')
            if row['sell_point_2'] == 1: sell_types.append('第二类')
            if row['sell_point_3'] == 1: sell_types.append('第三类')
            print(f"     {i+1}. {row['timestamp']} - {', '.join(sell_types)}卖点 - ${row['close']:.2f}")
    
    # 测试背离检测
    price_macd_divergence = feature_data[feature_data['price_macd_divergence'] == 1]
    rsi_divergence = feature_data[feature_data['rsi_divergence'] == 1]
    
    print(f"\n🔄 背离检测:")
    print(f"   价格MACD背离: {len(price_macd_divergence)} 个")
    print(f"   RSI背离: {len(rsi_divergence)} 个")

def main():
    """主函数"""
    print("🎯 缠论01策略简化演示")
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
        print("\n2️⃣ 创建测试数据...")
        data = create_test_data()
        print(f"✅ 创建了 {len(data)} 条测试数据")
        print(f"   时间范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
        print(f"   价格范围: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
        
        # 3. 初始化策略
        print("\n3️⃣ 初始化缠论策略...")
        strategy = ChanlunStrategy('BTCUSDT', config['parameters'])
        print("✅ 策略初始化成功")
        
        # 4. 分析特征
        feature_data = analyze_strategy_features(data, strategy)
        
        # 5. 测试信号生成
        signal_details = test_signal_generation(data, strategy)
        
        # 6. 测试仓位管理
        test_position_management(strategy)
        
        # 7. 测试缠论逻辑
        test_chanlun_logic(data, strategy)
        
        # 8. 总结
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
        
        print("\n📊 策略配置:")
        print(f"   初始仓位: {config['parameters']['position_size'] * 100}%")
        print(f"   最大仓位: {config['parameters']['max_position'] * 100}%")
        print(f"   止损比例: {config['parameters']['stop_loss'] * 100}%")
        print(f"   止盈比例: {config['parameters']['take_profit'] * 100}%")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 