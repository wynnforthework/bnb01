#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看策略参数优化结果脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import sqlite3
import pandas as pd
from datetime import datetime

def view_json_results():
    """查看JSON格式的优化结果"""
    print("📄 查看JSON格式的优化结果...")
    
    try:
        with open('optimization_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        if not results:
            print("  ⚠️  暂无优化结果")
            return
        
        print(f"  📊 共有 {len(results)} 个测试结果")
        
        # 按策略类型分组
        strategy_groups = {}
        for result in results:
            key = f"{result['strategy_type']}_{result['symbol']}"
            if key not in strategy_groups:
                strategy_groups[key] = []
            strategy_groups[key].append(result)
        
        # 显示每个策略组的最佳结果
        for group_key, group_results in strategy_groups.items():
            print(f"\n🔍 {group_key}:")
            
            # 按总收益排序
            sorted_results = sorted(
                group_results, 
                key=lambda x: x.get('metrics', {}).get('total_return', 0), 
                reverse=True
            )
            
            # 显示前3个最佳结果
            print("  🏆 前3个最佳结果:")
            for i, result in enumerate(sorted_results[:3]):
                metrics = result.get('metrics', {})
                params = result.get('params', {})
                print(f"    {i+1}. 总收益: {metrics.get('total_return', 0):.2f}%, "
                      f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}, "
                      f"胜率: {metrics.get('win_rate', 0):.1f}%")
                print(f"       参数: {params}")
        
    except FileNotFoundError:
        print("  ❌ 未找到 optimization_results.json 文件")
    except Exception as e:
        print(f"  ❌ 读取JSON结果失败: {e}")

def view_database_results():
    """查看数据库中的优化结果"""
    print("\n🗄️  查看数据库中的优化结果...")
    
    try:
        # 使用统一的数据源
        df_results = get_unified_results()
        
        if not df_results.empty:
            print("  📊 优化结果表:")
            # 显示前10个最佳结果
            top_results = df_results.head(10)[['strategy_type', 'symbol', 'total_return', 'sharpe_ratio', 
                                             'win_rate', 'max_drawdown', 'total_trades', 'timestamp']]
            print(top_results.to_string(index=False))
        else:
            print("    ⚠️  暂无优化结果")
        
        # 查看最佳结果表
        print("\n  🏆 最佳结果表:")
        try:
            conn = sqlite3.connect('optimization_results.db')
            df_best = pd.read_sql_query("""
                SELECT strategy_type, symbol, total_return, sharpe_ratio, 
                       win_rate, max_drawdown, timestamp
                FROM best_results 
                ORDER BY total_return DESC
            """, conn)
            conn.close()
            
            if not df_best.empty:
                print(df_best.to_string(index=False))
            else:
                print("    ⚠️  暂无最佳结果")
        except:
            print("    ⚠️  无法读取最佳结果表")
        
    except Exception as e:
        print(f"  ❌ 读取结果失败: {e}")

def export_best_parameters():
    """导出最佳参数配置"""
    print("\n📤 导出最佳参数配置...")
    
    try:
        conn = sqlite3.connect('optimization_results.db')
        
        # 获取每个策略的最佳参数
        df_best = pd.read_sql_query("""
            SELECT strategy_type, symbol, params, total_return, sharpe_ratio, 
                   win_rate, max_drawdown, timestamp
            FROM best_results 
            ORDER BY total_return DESC
        """, conn)
        
        if df_best.empty:
            print("  ⚠️  暂无最佳参数可导出")
            return
        
        # 创建最佳参数配置
        best_configs = {}
        for _, row in df_best.iterrows():
            strategy_key = f"{row['strategy_type']}_{row['symbol']}"
            try:
                params = json.loads(row['params'])
                best_configs[strategy_key] = {
                    'strategy_type': row['strategy_type'],
                    'symbol': row['symbol'],
                    'parameters': params,
                    'performance': {
                        'total_return': row['total_return'],
                        'sharpe_ratio': row['sharpe_ratio'],
                        'win_rate': row['win_rate'],
                        'max_drawdown': row['max_drawdown']
                    },
                    'timestamp': row['timestamp']
                }
            except:
                continue
        
        # 保存到文件
        with open('best_strategy_parameters.json', 'w', encoding='utf-8') as f:
            json.dump(best_configs, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 已导出 {len(best_configs)} 个最佳参数配置到 best_strategy_parameters.json")
        
        # 显示最佳参数
        for strategy_key, config in best_configs.items():
            print(f"\n  🎯 {strategy_key}:")
            print(f"    参数: {config['parameters']}")
            print(f"    总收益: {config['performance']['total_return']:.2f}%")
            print(f"    夏普比率: {config['performance']['sharpe_ratio']:.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ 导出最佳参数失败: {e}")

def main():
    """主函数"""
    print("🎯 策略参数优化结果查看器")
    print("=" * 50)
    
    # 查看JSON结果
    view_json_results()
    
    # 查看数据库结果
    view_database_results()
    
    # 导出最佳参数
    export_best_parameters()
    
    print("\n" + "=" * 50)
    print("✅ 结果查看完成")

if __name__ == "__main__":
    main()

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

