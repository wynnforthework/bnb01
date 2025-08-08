#!/usr/bin/env python3
"""
检查现货交易的策略和币种对应关系
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_strategy_mapping():
    """检查策略和币种的对应关系"""
    print("🔍 检查现货交易的策略和币种对应关系...")
    print("=" * 80)
    
    try:
        # 1. 获取策略列表
        print("1️⃣ 获取策略列表...")
        response = requests.get('http://127.0.0.1:5000/api/strategies/list', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                strategies = data['data']
                print(f"✅ 找到 {len(strategies)} 个策略")
                
                # 2. 分析策略分布
                print("\n2️⃣ 分析策略分布...")
                strategy_analysis = analyze_strategies(strategies)
                display_strategy_analysis(strategy_analysis)
                
                # 3. 检查交易对分布
                print("\n3️⃣ 检查交易对分布...")
                symbol_analysis = analyze_symbols(strategies)
                display_symbol_analysis(symbol_analysis)
                
                # 4. 检查策略类型分布
                print("\n4️⃣ 检查策略类型分布...")
                type_analysis = analyze_strategy_types(strategies)
                display_type_analysis(type_analysis)
                
                # 5. 检查活跃策略
                print("\n5️⃣ 检查活跃策略...")
                active_analysis = analyze_active_strategies(strategies)
                display_active_analysis(active_analysis)
                
                # 6. 生成策略映射表
                print("\n6️⃣ 生成策略映射表...")
                generate_strategy_mapping_table(strategies)
                
            else:
                print(f"❌ 策略列表API错误: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ 策略列表HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查策略映射失败: {e}")

def analyze_strategies(strategies):
    """分析策略数据"""
    analysis = {
        'total': len(strategies),
        'active': 0,
        'inactive': 0,
        'with_position': 0,
        'without_position': 0,
        'symbols': set(),
        'types': set(),
        'active_strategies': [],
        'position_strategies': []
    }
    
    for strategy in strategies:
        # 统计状态
        if strategy.get('status') == 'active':
            analysis['active'] += 1
            analysis['active_strategies'].append(strategy)
        else:
            analysis['inactive'] += 1
        
        # 统计持仓
        if strategy.get('position', 0) > 0:
            analysis['with_position'] += 1
            analysis['position_strategies'].append(strategy)
        else:
            analysis['without_position'] += 1
        
        # 收集交易对和类型
        analysis['symbols'].add(strategy.get('symbol', 'Unknown'))
        analysis['types'].add(strategy.get('type', 'Unknown'))
    
    return analysis

def display_strategy_analysis(analysis):
    """显示策略分析结果"""
    print(f"📊 策略总数: {analysis['total']}")
    print(f"📈 活跃策略: {analysis['active']}")
    print(f"📉 非活跃策略: {analysis['inactive']}")
    print(f"💼 有持仓策略: {analysis['with_position']}")
    print(f"📭 无持仓策略: {analysis['without_position']}")
    print(f"🪙 交易对数量: {len(analysis['symbols'])}")
    print(f"🧠 策略类型数量: {len(analysis['types'])}")

def analyze_symbols(strategies):
    """分析交易对分布"""
    symbol_stats = {}
    
    for strategy in strategies:
        symbol = strategy.get('symbol', 'Unknown')
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'total': 0,
                'active': 0,
                'with_position': 0,
                'types': set(),
                'strategies': []
            }
        
        symbol_stats[symbol]['total'] += 1
        symbol_stats[symbol]['strategies'].append(strategy)
        
        if strategy.get('status') == 'active':
            symbol_stats[symbol]['active'] += 1
        
        if strategy.get('position', 0) > 0:
            symbol_stats[symbol]['with_position'] += 1
        
        symbol_stats[symbol]['types'].add(strategy.get('type', 'Unknown'))
    
    return symbol_stats

def display_symbol_analysis(symbol_stats):
    """显示交易对分析结果"""
    print(f"📊 交易对分布:")
    for symbol, stats in sorted(symbol_stats.items()):
        print(f"  {symbol}:")
        print(f"    总策略数: {stats['total']}")
        print(f"    活跃策略: {stats['active']}")
        print(f"    有持仓策略: {stats['with_position']}")
        print(f"    策略类型: {', '.join(stats['types'])}")

def analyze_strategy_types(strategies):
    """分析策略类型分布"""
    type_stats = {}
    
    for strategy in strategies:
        strategy_type = strategy.get('type', 'Unknown')
        if strategy_type not in type_stats:
            type_stats[strategy_type] = {
                'total': 0,
                'active': 0,
                'with_position': 0,
                'symbols': set(),
                'strategies': []
            }
        
        type_stats[strategy_type]['total'] += 1
        type_stats[strategy_type]['strategies'].append(strategy)
        
        if strategy.get('status') == 'active':
            type_stats[strategy_type]['active'] += 1
        
        if strategy.get('position', 0) > 0:
            type_stats[strategy_type]['with_position'] += 1
        
        type_stats[strategy_type]['symbols'].add(strategy.get('symbol', 'Unknown'))
    
    return type_stats

def display_type_analysis(type_stats):
    """显示策略类型分析结果"""
    print(f"📊 策略类型分布:")
    for strategy_type, stats in sorted(type_stats.items()):
        print(f"  {strategy_type}:")
        print(f"    总数量: {stats['total']}")
        print(f"    活跃数量: {stats['active']}")
        print(f"    有持仓数量: {stats['with_position']}")
        print(f"    交易对: {', '.join(sorted(stats['symbols']))}")

def analyze_active_strategies(strategies):
    """分析活跃策略"""
    active_strategies = [s for s in strategies if s.get('status') == 'active']
    position_strategies = [s for s in strategies if s.get('position', 0) > 0]
    
    return {
        'active': active_strategies,
        'with_position': position_strategies,
        'active_count': len(active_strategies),
        'position_count': len(position_strategies)
    }

def display_active_analysis(analysis):
    """显示活跃策略分析结果"""
    print(f"📈 活跃策略 ({analysis['active_count']}个):")
    for strategy in analysis['active']:
        print(f"  - {strategy.get('name', 'Unknown')}")
        print(f"    交易对: {strategy.get('symbol', 'Unknown')}")
        print(f"    类型: {strategy.get('type', 'Unknown')}")
        print(f"    持仓: {strategy.get('position', 0)}")
        print(f"    入场价: {strategy.get('entry_price', 0)}")
    
    print(f"\n💼 有持仓策略 ({analysis['position_count']}个):")
    for strategy in analysis['with_position']:
        print(f"  - {strategy.get('name', 'Unknown')}")
        print(f"    交易对: {strategy.get('symbol', 'Unknown')}")
        print(f"    类型: {strategy.get('type', 'Unknown')}")
        print(f"    持仓: {strategy.get('position', 0)}")
        print(f"    入场价: {strategy.get('entry_price', 0)}")

def generate_strategy_mapping_table(strategies):
    """生成策略映射表"""
    print("📋 策略映射表:")
    print("=" * 80)
    
    # 按交易对分组
    symbol_groups = {}
    for strategy in strategies:
        symbol = strategy.get('symbol', 'Unknown')
        if symbol not in symbol_groups:
            symbol_groups[symbol] = []
        symbol_groups[symbol].append(strategy)
    
    # 显示映射表
    for symbol, symbol_strategies in sorted(symbol_groups.items()):
        print(f"\n🪙 {symbol}:")
        print("-" * 40)
        
        for strategy in symbol_strategies:
            status_icon = "🟢" if strategy.get('status') == 'active' else "🔴"
            position_icon = "💰" if strategy.get('position', 0) > 0 else "📭"
            
            print(f"  {status_icon} {position_icon} {strategy.get('name', 'Unknown')}")
            print(f"    类型: {strategy.get('type', 'Unknown')}")
            print(f"    状态: {strategy.get('status', 'Unknown')}")
            print(f"    持仓: {strategy.get('position', 0)}")
            print(f"    入场价: {strategy.get('entry_price', 0)}")
            print()

def create_strategy_summary():
    """创建策略总结"""
    summary = """
# 现货交易策略映射总结

## 策略类型说明

### 1. MA策略 (MovingAverageStrategy)
- **功能**: 基于移动平均线的趋势跟踪策略
- **适用**: 趋势明显的市场
- **交易逻辑**: 短期均线上穿长期均线买入，下穿卖出

### 2. RSI策略 (RSIStrategy)
- **功能**: 基于相对强弱指数的超买超卖策略
- **适用**: 震荡市场
- **交易逻辑**: RSI低于30买入，高于70卖出

### 3. ML策略 (MLStrategy)
- **功能**: 基于机器学习的预测策略
- **适用**: 需要历史数据训练
- **交易逻辑**: 模型预测上涨买入，预测下跌卖出

### 4. Chanlun策略 (ChanlunStrategy)
- **功能**: 基于缠论理论的量化策略
- **适用**: 技术分析导向
- **交易逻辑**: 根据缠论买卖点信号交易

## 交易对分配

每个交易对通常会有4种策略同时运行：
- MA策略
- RSI策略  
- ML策略
- Chanlun策略

## 策略选择逻辑

系统会根据以下因素选择策略：
1. **市场条件**: 趋势市场用MA，震荡市场用RSI
2. **历史表现**: 表现好的策略会获得更多资金
3. **风险控制**: 不同策略有不同的止损止盈设置
4. **资金分配**: 系统会动态调整各策略的资金分配

## 监控建议

1. **定期检查策略表现**
2. **关注活跃策略的交易**
3. **监控持仓变化**
4. **分析策略胜率**
"""
    
    with open('STRATEGY_MAPPING_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("✅ 策略映射总结已创建: STRATEGY_MAPPING_SUMMARY.md")

if __name__ == "__main__":
    check_strategy_mapping()
    create_strategy_summary()
