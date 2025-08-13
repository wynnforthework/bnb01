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
        conn = sqlite3.connect('optimization_results.db')
        
        # 查看优化结果表
        print("  📊 优化结果表:")
        df_results = pd.read_sql_query("""
            SELECT strategy_type, symbol, total_return, sharpe_ratio, 
                   win_rate, max_drawdown, total_trades, timestamp
            FROM optimization_results 
            ORDER BY total_return DESC
            LIMIT 10
        """, conn)
        
        if not df_results.empty:
            print(df_results.to_string(index=False))
        else:
            print("    ⚠️  暂无优化结果")
        
        # 查看最佳结果表
        print("\n  🏆 最佳结果表:")
        df_best = pd.read_sql_query("""
            SELECT strategy_type, symbol, total_return, sharpe_ratio, 
                   win_rate, max_drawdown, timestamp
            FROM best_results 
            ORDER BY total_return DESC
        """, conn)
        
        if not df_best.empty:
            print(df_best.to_string(index=False))
        else:
            print("    ⚠️  暂无最佳结果")
        
        conn.close()
        
    except FileNotFoundError:
        print("  ❌ 未找到 optimization_results.db 文件")
    except Exception as e:
        print(f"  ❌ 读取数据库结果失败: {e}")

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
