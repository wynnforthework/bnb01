#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比优化结果脚本
分析 view_optimization_results.py 和 apply_best_parameters.py 得出的最佳参数差异
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime

def load_json_results():
    """从JSON文件加载优化结果"""
    print("📄 从 optimization_results.json 加载数据...")
    
    try:
        with open('optimization_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"  ✅ 加载了 {len(results)} 个测试结果")
        return results
        
    except Exception as e:
        print(f"  ❌ 加载JSON数据失败: {e}")
        return []

def load_database_results():
    """从数据库加载优化结果"""
    print("🗄️  从 optimization_results.db 加载数据...")
    
    try:
        conn = sqlite3.connect('optimization_results.db')
        
        # 查询所有结果
        df = pd.read_sql_query("""
            SELECT test_id, strategy_type, symbol, params, total_return, 
                   sharpe_ratio, win_rate, max_drawdown, timestamp
            FROM optimization_results 
            ORDER BY total_return DESC
        """, conn)
        
        conn.close()
        
        print(f"  ✅ 加载了 {len(df)} 个测试结果")
        return df
        
    except Exception as e:
        print(f"  ❌ 加载数据库数据失败: {e}")
        return pd.DataFrame()

def analyze_json_best_results(json_results):
    """分析JSON数据中的最佳结果"""
    print("\n🔍 分析JSON数据中的最佳结果...")
    
    # 按策略类型和币种分组
    strategy_groups = {}
    for result in json_results:
        key = f"{result['strategy_type']}_{result['symbol']}"
        if key not in strategy_groups:
            strategy_groups[key] = []
        strategy_groups[key].append(result)
    
    # 找出每个组的最佳结果
    json_best = {}
    for group_key, group_results in strategy_groups.items():
        # 按总收益排序
        sorted_results = sorted(
            group_results, 
            key=lambda x: x.get('metrics', {}).get('total_return', 0), 
            reverse=True
        )
        
        if sorted_results:
            best_result = sorted_results[0]
            json_best[group_key] = {
                'strategy_type': best_result['strategy_type'],
                'symbol': best_result['symbol'],
                'params': best_result['params'],
                'total_return': best_result['metrics'].get('total_return', 0),
                'sharpe_ratio': best_result['metrics'].get('sharpe_ratio', 0),
                'win_rate': best_result['metrics'].get('win_rate', 0),
                'max_drawdown': best_result['metrics'].get('max_drawdown', 0),
                'timestamp': best_result['timestamp']
            }
    
    return json_best

def analyze_database_best_results(db_results):
    """分析数据库中的最佳结果"""
    print("\n🔍 分析数据库中的最佳结果...")
    
    if db_results.empty:
        return {}
    
    # 按策略类型和币种分组
    strategy_groups = {}
    for _, row in db_results.iterrows():
        key = f"{row['strategy_type']}_{row['symbol']}"
        if key not in strategy_groups:
            strategy_groups[key] = []
        strategy_groups[key].append(row)
    
    # 找出每个组的最佳结果
    db_best = {}
    for group_key, group_results in strategy_groups.items():
        # 按总收益排序
        sorted_results = sorted(
            group_results, 
            key=lambda x: x['total_return'], 
            reverse=True
        )
        
        if sorted_results:
            best_result = sorted_results[0]
            try:
                params = json.loads(best_result['params'])
            except:
                params = {}
            
            db_best[group_key] = {
                'strategy_type': best_result['strategy_type'],
                'symbol': best_result['symbol'],
                'params': params,
                'total_return': best_result['total_return'],
                'sharpe_ratio': best_result['sharpe_ratio'],
                'win_rate': best_result['win_rate'],
                'max_drawdown': best_result['max_drawdown'],
                'timestamp': best_result['timestamp']
            }
    
    return db_best

def compare_results(json_best, db_best):
    """对比两个数据源的结果"""
    print("\n🔍 对比两个数据源的结果...")
    
    all_keys = set(json_best.keys()) | set(db_best.keys())
    
    print(f"📊 总共找到 {len(all_keys)} 个策略组合")
    print(f"  JSON数据: {len(json_best)} 个")
    print(f"  数据库数据: {len(db_best)} 个")
    
    differences = []
    
    for key in all_keys:
        json_result = json_best.get(key)
        db_result = db_best.get(key)
        
        print(f"\n🔍 对比 {key}:")
        
        if json_result and db_result:
            # 两个数据源都有数据，比较结果
            json_return = json_result['total_return']
            db_return = db_result['total_return']
            
            print(f"  JSON最佳收益: {json_return:.2f}%")
            print(f"  数据库最佳收益: {db_return:.2f}%")
            
            if abs(json_return - db_return) > 0.01:  # 允许0.01%的误差
                print(f"  ⚠️  收益差异: {abs(json_return - db_return):.2f}%")
                differences.append({
                    'key': key,
                    'json_return': json_return,
                    'db_return': db_return,
                    'difference': abs(json_return - db_return)
                })
            else:
                print(f"  ✅ 收益一致")
            
            # 比较参数
            json_params = json_result['params']
            db_params = db_result['params']
            
            if json_params != db_params:
                print(f"  ⚠️  参数不一致:")
                print(f"    JSON参数: {json_params}")
                print(f"    DB参数: {db_params}")
            else:
                print(f"  ✅ 参数一致")
                
        elif json_result:
            print(f"  📄 仅在JSON中找到: {json_result['total_return']:.2f}%")
        elif db_result:
            print(f"  🗄️  仅在数据库中找到: {db_result['total_return']:.2f}%")
    
    return differences

def check_data_synchronization():
    """检查数据同步情况"""
    print("\n🔄 检查数据同步情况...")
    
    # 检查JSON文件的时间戳
    try:
        import os
        json_mtime = os.path.getmtime('optimization_results.json')
        json_time = datetime.fromtimestamp(json_mtime)
        print(f"  JSON文件最后修改时间: {json_time}")
    except:
        print("  ❌ 无法获取JSON文件时间")
    
    # 检查数据库文件的时间戳
    try:
        db_mtime = os.path.getmtime('optimization_results.db')
        db_time = datetime.fromtimestamp(db_mtime)
        print(f"  数据库文件最后修改时间: {db_time}")
    except:
        print("  ❌ 无法获取数据库文件时间")
    
    # 检查两个文件中的最新时间戳
    json_results = load_json_results()
    if json_results:
        latest_json_time = max(r['timestamp'] for r in json_results)
        print(f"  JSON数据最新时间戳: {latest_json_time}")
    
    db_results = load_database_results()
    if not db_results.empty:
        latest_db_time = db_results['timestamp'].max()
        print(f"  数据库最新时间戳: {latest_db_time}")

def main():
    """主函数"""
    print("🎯 优化结果对比分析工具")
    print("=" * 50)
    
    # 1. 加载数据
    json_results = load_json_results()
    db_results = load_database_results()
    
    # 2. 分析最佳结果
    json_best = analyze_json_best_results(json_results)
    db_best = analyze_database_best_results(db_results)
    
    # 3. 对比结果
    differences = compare_results(json_best, db_best)
    
    # 4. 检查数据同步
    check_data_synchronization()
    
    # 5. 总结
    print("\n" + "=" * 50)
    print("📋 分析总结:")
    
    if differences:
        print(f"⚠️  发现 {len(differences)} 个不一致的结果:")
        for diff in differences:
            print(f"  - {diff['key']}: 差异 {diff['difference']:.2f}%")
        
        print("\n🔧 建议解决方案:")
        print("1. 确保两个脚本使用相同的数据源")
        print("2. 统一数据读取逻辑")
        print("3. 定期同步JSON和数据库数据")
        print("4. 使用单一数据源作为权威来源")
    else:
        print("✅ 两个数据源的结果一致")
    
    print("\n💡 推荐做法:")
    print("- 使用数据库作为主要数据源（更稳定）")
    print("- 定期从数据库导出JSON用于备份")
    print("- 统一两个脚本的数据读取逻辑")

if __name__ == "__main__":
    main()
