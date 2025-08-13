#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一参数应用工具
整合参数分析和应用功能，提供清晰的工作流程
"""

import json
import pandas as pd
import sqlite3
import os
import re
from datetime import datetime

def get_unified_results():
    """获取统一的优化结果（优先使用数据库）"""
    print("🔍 获取统一的优化结果...")
    
    # 优先从数据库读取
    try:
        conn = sqlite3.connect('optimization_results.db')
        df = pd.read_sql_query("""
            SELECT test_id, strategy_type, symbol, params, total_return, 
                   sharpe_ratio, win_rate, max_drawdown, profit_factor,
                   total_trades, avg_trade_duration, timestamp
            FROM optimization_results 
            ORDER BY total_return DESC
        """, conn)
        conn.close()
        
        if not df.empty:
            print(f"  ✅ 从数据库读取了 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"  ⚠️  数据库读取失败: {e}")
    
    # 如果数据库读取失败，从JSON读取
    try:
        with open('optimization_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        if results:
            # 转换为DataFrame格式
            df_data = []
            for result in results:
                df_data.append({
                    'test_id': result['test_id'],
                    'strategy_type': result['strategy_type'],
                    'symbol': result['symbol'],
                    'params': json.dumps(result['params']),
                    'total_return': result['metrics'].get('total_return', 0),
                    'sharpe_ratio': result['metrics'].get('sharpe_ratio', 0),
                    'win_rate': result['metrics'].get('win_rate', 0),
                    'max_drawdown': result['metrics'].get('max_drawdown', 0),
                    'profit_factor': result['metrics'].get('profit_factor', 0),
                    'total_trades': result['metrics'].get('total_trades', 0),
                    'avg_trade_duration': result['metrics'].get('avg_trade_duration', 0),
                    'timestamp': result['timestamp']
                })
            
            df = pd.DataFrame(df_data)
            print(f"  ✅ 从JSON读取了 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"  ❌ JSON读取失败: {e}")
    
    return pd.DataFrame()

def analyze_optimization_results():
    """分析优化结果并找出最佳参数"""
    print("🔍 分析优化结果...")
    
    try:
        df = get_unified_results()
        
        if df.empty:
            print("❌ 没有找到优化结果")
            return None
        
        print(f"📊 共找到 {len(df)} 个测试结果")
        
        # 按策略类型和币种分组
        strategy_groups = {}
        for _, row in df.iterrows():
            key = f"{row['strategy_type']}_{row['symbol']}"
            if key not in strategy_groups:
                strategy_groups[key] = []
            strategy_groups[key].append(row)
        
        # 分析每个策略组的最佳结果
        best_configs = {}
        
        for group_key, group_results in strategy_groups.items():
            print(f"\n🔍 分析 {group_key}:")
            
            # 按总收益排序
            sorted_results = sorted(
                group_results, 
                key=lambda x: x['total_return'], 
                reverse=True
            )
            
            # 获取最佳结果
            best_result = sorted_results[0]
            try:
                params = json.loads(best_result['params'])
            except:
                params = {}
            
            best_configs[group_key] = {
                'strategy_type': best_result['strategy_type'],
                'symbol': best_result['symbol'],
                'parameters': params,
                'performance': {
                    'total_return': best_result['total_return'],
                    'sharpe_ratio': best_result['sharpe_ratio'],
                    'win_rate': best_result['win_rate'],
                    'max_drawdown': best_result['max_drawdown'],
                    'profit_factor': best_result.get('profit_factor', 0),
                    'total_trades': best_result.get('total_trades', 0),
                    'avg_trade_duration': best_result.get('avg_trade_duration', 0)
                },
                'timestamp': best_result['timestamp']
            }
            
            print(f"  🏆 最佳参数:")
            print(f"    总收益: {best_result['total_return']:.2f}%")
            print(f"    夏普比率: {best_result['sharpe_ratio']:.2f}")
            print(f"    胜率: {best_result['win_rate']:.1f}%")
            print(f"    最大回撤: {best_result['max_drawdown']:.2f}%")
            print(f"    交易次数: {best_result.get('total_trades', 0)}")
            print(f"    参数: {params}")
        
        return best_configs
        
    except Exception as e:
        print(f"❌ 分析优化结果失败: {e}")
        return None

def generate_strategy_configs(best_configs):
    """生成策略配置文件"""
    print("\n📝 生成策略配置文件...")
    
    # 按策略类型分组
    strategy_configs = {}
    
    for group_key, config in best_configs.items():
        strategy_type = config['strategy_type']
        symbol = config['symbol']
        
        if strategy_type not in strategy_configs:
            strategy_configs[strategy_type] = {}
        
        strategy_configs[strategy_type][symbol] = {
            'parameters': config['parameters'],
            'performance': config['performance']
        }
    
    # 保存到文件
    config_file = 'best_strategy_configs.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(strategy_configs, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 最佳策略配置已保存到 {config_file}")
    return strategy_configs

def update_strategy_parameters(best_configs):
    """更新策略文件中的默认参数"""
    print("\n🔧 更新策略文件中的默认参数...")
    
    # 按策略类型分组
    strategy_configs = {}
    for group_key, config in best_configs.items():
        strategy_type = config['strategy_type']
        symbol = config['symbol']
        
        if strategy_type not in strategy_configs:
            strategy_configs[strategy_type] = {}
        
        strategy_configs[strategy_type][symbol] = config
    
    # 更新MA策略
    try:
        with open('strategies/ma_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'DEFAULT_PARAMETERS = {' in content:
            # 使用ADAUSDT的最佳参数作为默认值
            ada_params = strategy_configs.get('MA', {}).get('ADAUSDT', {}).get('parameters', {})
            if ada_params:
                new_defaults = f"""DEFAULT_PARAMETERS = {{
    'short_window': {ada_params.get('short_window', 10)},
    'long_window': {ada_params.get('long_window', 30)},
    'position_size': {ada_params.get('position_size', 1.0)},
    'stop_loss': {ada_params.get('stop_loss', 0.02)},
    'take_profit': {ada_params.get('take_profit', 0.05)}
}}"""
                
                content = re.sub(r'DEFAULT_PARAMETERS = \{.*?\}', new_defaults, content, flags=re.DOTALL)
                
                with open('strategies/ma_strategy.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("  ✅ MA策略参数已更新")
        
    except Exception as e:
        print(f"  ❌ 更新MA策略失败: {e}")
    
    # 更新RSI策略
    try:
        with open('strategies/rsi_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'DEFAULT_PARAMETERS = {' in content:
            ada_params = strategy_configs.get('RSI', {}).get('ADAUSDT', {}).get('parameters', {})
            if ada_params:
                new_defaults = f"""DEFAULT_PARAMETERS = {{
    'rsi_period': {ada_params.get('rsi_period', 14)},
    'overbought': {ada_params.get('overbought', 70)},
    'oversold': {ada_params.get('oversold', 30)},
    'position_size': {ada_params.get('position_size', 1.0)},
    'stop_loss': {ada_params.get('stop_loss', 0.02)},
    'take_profit': {ada_params.get('take_profit', 0.05)}
}}"""
                
                content = re.sub(r'DEFAULT_PARAMETERS = \{.*?\}', new_defaults, content, flags=re.DOTALL)
                
                with open('strategies/rsi_strategy.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("  ✅ RSI策略参数已更新")
        
    except Exception as e:
        print(f"  ❌ 更新RSI策略失败: {e}")
    
    # 更新ML策略
    try:
        with open('strategies/ml_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'DEFAULT_PARAMETERS = {' in content:
            ada_params = strategy_configs.get('ML', {}).get('ADAUSDT', {}).get('parameters', {})
            if ada_params:
                new_defaults = f"""DEFAULT_PARAMETERS = {{
    'model_type': '{ada_params.get('model_type', 'random_forest')}',
    'lookback_period': {ada_params.get('lookback_period', 20)},
    'prediction_horizon': {ada_params.get('prediction_horizon', 1)},
    'min_confidence': 0.5,
    'up_threshold': 0.01,
    'down_threshold': -0.01,
    'position_size': {ada_params.get('position_size', 1.0)},
    'stop_loss': {ada_params.get('stop_loss', 0.02)},
    'take_profit': {ada_params.get('take_profit', 0.05)},
    'retrain_frequency': 100,
    'min_training_samples': 100
}}"""
                
                content = re.sub(r'DEFAULT_PARAMETERS = \{.*?\}', new_defaults, content, flags=re.DOTALL)
                
                with open('strategies/ml_strategy.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("  ✅ ML策略参数已更新")
        
    except Exception as e:
        print(f"  ❌ 更新ML策略失败: {e}")
    
    # 更新缠论策略
    try:
        with open('strategies/chanlun_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'DEFAULT_PARAMETERS = {' in content:
            ada_params = strategy_configs.get('Chanlun', {}).get('ADAUSDT', {}).get('parameters', {})
            if ada_params:
                new_defaults = f"""DEFAULT_PARAMETERS = {{
    'timeframes': ['30m', '1h', '4h'],
    'min_swing_length': {ada_params.get('min_swing_length', 3)},
    'central_bank_min_bars': 3,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'rsi_period': 14,
    'ma_short': 5,
    'ma_long': 20,
    'position_size': {ada_params.get('position_size', 0.3)},
    'max_position': 1.0,
    'stop_loss': {ada_params.get('stop_loss', 0.03)},
    'take_profit': {ada_params.get('take_profit', 0.05)},
    'trend_confirmation': {ada_params.get('trend_confirmation', 0.02)},
    'divergence_threshold': 0.1
}}"""
                
                content = re.sub(r'DEFAULT_PARAMETERS = \{.*?\}', new_defaults, content, flags=re.DOTALL)
                
                with open('strategies/chanlun_strategy.py', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("  ✅ 缠论策略参数已更新")
        
    except Exception as e:
        print(f"  ❌ 更新缠论策略失败: {e}")

def create_optimized_configs(best_configs):
    """创建优化后的配置文件"""
    print("\n📝 创建优化后的配置文件...")
    
    # 按策略类型分组
    strategy_configs = {}
    for group_key, config in best_configs.items():
        strategy_type = config['strategy_type']
        symbol = config['symbol']
        
        if strategy_type not in strategy_configs:
            strategy_configs[strategy_type] = {}
        
        strategy_configs[strategy_type][symbol] = config
    
    # 获取所有有优化结果的币种
    symbols = set()
    for config in best_configs.values():
        symbols.add(config['symbol'])
    
    symbols = list(symbols)
    strategy_types = ['MA', 'RSI', 'ML', 'Chanlun']
    
    # 创建优化后的现货配置
    optimized_spot_config = {
        'symbols': symbols,
        'strategy_types': strategy_types,
        'enabled_strategies': {},
        'trading_status': 'stopped',
        'optimized_parameters': strategy_configs
    }
    
    # 为每个币种和策略启用
    for symbol in optimized_spot_config['symbols']:
        for strategy_type in optimized_spot_config['strategy_types']:
            strategy_key = f"{symbol}_{strategy_type}"
            optimized_spot_config['enabled_strategies'][strategy_key] = True
    
    # 保存优化后的配置
    with open('optimized_spot_config.json', 'w', encoding='utf-8') as f:
        json.dump(optimized_spot_config, f, ensure_ascii=False, indent=2)
    
    print("  ✅ 优化后的现货配置已保存: optimized_spot_config.json")
    
    # 创建优化后的合约配置
    optimized_futures_config = {
        'leverage': 10,
        'symbols': symbols,
        'enabled_strategies': strategy_types,
        'optimized_parameters': strategy_configs
    }
    
    with open('optimized_futures_config.json', 'w', encoding='utf-8') as f:
        json.dump(optimized_futures_config, f, ensure_ascii=False, indent=2)
    
    print("  ✅ 优化后的合约配置已保存: optimized_futures_config.json")

def create_comprehensive_summary(best_configs):
    """创建综合总结报告"""
    print("\n📊 创建综合总结报告...")
    
    # 按策略类型分组
    strategy_configs = {}
    for group_key, config in best_configs.items():
        strategy_type = config['strategy_type']
        symbol = config['symbol']
        
        if strategy_type not in strategy_configs:
            strategy_configs[strategy_type] = {}
        
        strategy_configs[strategy_type][symbol] = config
    
    # 生成总结内容
    summary = """# 统一参数应用工具 - 综合总结报告

## 🎯 工具说明

本工具整合了参数分析和应用功能，提供完整的工作流程：

### 功能模块
1. **参数分析**: 从数据库或JSON文件读取优化结果
2. **策略更新**: 直接修改策略文件中的默认参数
3. **配置生成**: 创建优化后的现货和合约配置文件
4. **报告生成**: 生成详细的参数总结报告

## 📊 最佳参数配置

"""
    
    # 添加每个策略的详细信息
    for strategy_type in ['MA', 'RSI', 'ML', 'Chanlun']:
        if strategy_type in strategy_configs:
            summary += f"\n### {strategy_type}策略\n\n"
            
            for symbol, config in strategy_configs[strategy_type].items():
                params = config['parameters']
                perf = config['performance']
                
                summary += f"#### {symbol}\n"
                summary += f"- **参数**: {params}\n"
                summary += f"- **性能**: 总收益 {perf['total_return']:.2f}%, 夏普比率 {perf['sharpe_ratio']:.2f}, 胜率 {perf['win_rate']:.1f}%, 最大回撤 {perf['max_drawdown']:.2f}%\n\n"
    
    summary += """## 🏆 最佳策略排名

按总收益率排序：

"""
    
    # 按总收益率排序
    sorted_results = []
    for config in best_configs.values():
        sorted_results.append({
            'strategy': f"{config['strategy_type']} ({config['symbol']})",
            'total_return': config['performance']['total_return']
        })
    
    sorted_results.sort(key=lambda x: x['total_return'], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        summary += f"{i}. **{result['strategy']}**: {result['total_return']:.2f}% 总收益\n"
    
    summary += """

## 📁 生成的文件

### 配置文件
- `best_strategy_configs.json` - 最佳策略参数配置
- `optimized_spot_config.json` - 优化后的现货配置
- `optimized_futures_config.json` - 优化后的合约配置

### 更新的文件
- `strategies/ma_strategy.py` - MA策略默认参数
- `strategies/rsi_strategy.py` - RSI策略默认参数  
- `strategies/ml_strategy.py` - ML策略默认参数
- `strategies/chanlun_strategy.py` - 缠论策略默认参数

## ⚠️ 风险提示

- 高收益策略通常伴随高风险，最大回撤可能超过500%
- 建议在实盘使用前进行充分测试
- 合理控制仓位大小，避免过度杠杆
- 定期监控策略表现，必要时调整参数

## 🔧 使用方法

1. **运行工具**: `python unified_parameter_applier.py`
2. **查看结果**: 检查生成的文件和更新的策略
3. **应用配置**: 使用 `optimized_spot_config.json` 和 `optimized_futures_config.json`
4. **启动交易**: 在交易系统中启用相应的币种和策略
5. **监控表现**: 定期检查交易表现，必要时重新优化

## 🔄 定期更新

建议定期运行优化脚本，更新参数配置：
```bash
python strategy_optimizer.py
python unified_parameter_applier.py
```

"""
    
    with open('UNIFIED_PARAMETER_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("  ✅ 综合总结报告已创建: UNIFIED_PARAMETER_SUMMARY.md")

def main():
    """主函数"""
    print("🎯 统一参数应用工具")
    print("=" * 60)
    print("📋 功能说明:")
    print("1. 分析优化结果，找出最佳参数")
    print("2. 更新策略文件中的默认参数")
    print("3. 创建优化后的配置文件")
    print("4. 生成综合总结报告")
    print("=" * 60)
    
    # 1. 分析优化结果
    best_configs = analyze_optimization_results()
    if not best_configs:
        print("❌ 无法获取最佳配置")
        return
    
    # 2. 生成策略配置文件
    strategy_configs = generate_strategy_configs(best_configs)
    
    # 3. 更新策略文件中的默认参数
    update_strategy_parameters(best_configs)
    
    # 4. 创建优化后的配置文件
    create_optimized_configs(best_configs)
    
    # 5. 创建综合总结报告
    create_comprehensive_summary(best_configs)
    
    print("\n" + "=" * 60)
    print("✅ 统一参数应用完成！")
    print("\n📋 生成的文件:")
    print("1. best_strategy_configs.json - 最佳策略参数配置")
    print("2. optimized_spot_config.json - 优化后的现货配置")
    print("3. optimized_futures_config.json - 优化后的合约配置")
    print("4. UNIFIED_PARAMETER_SUMMARY.md - 综合总结报告")
    print("\n📋 更新的文件:")
    print("1. strategies/ma_strategy.py - MA策略默认参数")
    print("2. strategies/rsi_strategy.py - RSI策略默认参数")
    print("3. strategies/ml_strategy.py - ML策略默认参数")
    print("4. strategies/chanlun_strategy.py - 缠论策略默认参数")
    print("\n🚀 下一步:")
    print("1. 使用优化后的配置文件启动交易")
    print("2. 监控交易表现")
    print("3. 根据实际情况调整参数")
    print("\n💡 提示: 现在您只需要使用这一个工具，不再需要分别运行两个文件")

if __name__ == "__main__":
    main()
