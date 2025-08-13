#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复优化结果同步问题
统一 view_optimization_results.py 和 apply_best_parameters.py 的数据读取逻辑
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime
import os

def sync_database_to_json():
    """将数据库数据同步到JSON文件"""
    print("🔄 将数据库数据同步到JSON文件...")
    
    try:
        # 从数据库读取所有数据
        conn = sqlite3.connect('optimization_results.db')
        
        df = pd.read_sql_query("""
            SELECT test_id, strategy_type, symbol, params, total_return, 
                   sharpe_ratio, win_rate, max_drawdown, profit_factor,
                   total_trades, avg_trade_duration, timestamp, trading_mode,
                   start_date, end_date
            FROM optimization_results 
            ORDER BY timestamp DESC
        """, conn)
        
        conn.close()
        
        if df.empty:
            print("  ⚠️  数据库中没有数据")
            return False
        
        # 转换为JSON格式
        json_results = []
        for _, row in df.iterrows():
            try:
                params = json.loads(row['params'])
            except:
                params = {}
            
            result = {
                'test_id': row['test_id'],
                'strategy_type': row['strategy_type'],
                'symbol': row['symbol'],
                'params': params,
                'metrics': {
                    'total_return': row['total_return'],
                    'sharpe_ratio': row['sharpe_ratio'],
                    'max_drawdown': row['max_drawdown'],
                    'win_rate': row['win_rate'],
                    'profit_factor': row['profit_factor'],
                    'total_trades': row['total_trades'],
                    'avg_trade_duration': row['avg_trade_duration']
                },
                'timestamp': row['timestamp'],
                'trading_mode': row['trading_mode'],
                'start_date': row['start_date'],
                'end_date': row['end_date']
            }
            json_results.append(result)
        
        # 保存到JSON文件
        with open('optimization_results.json', 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 成功同步 {len(json_results)} 条记录到JSON文件")
        return True
        
    except Exception as e:
        print(f"  ❌ 同步失败: {e}")
        return False

def sync_json_to_database():
    """将JSON数据同步到数据库"""
    print("🔄 将JSON数据同步到数据库...")
    
    try:
        # 读取JSON文件
        with open('optimization_results.json', 'r', encoding='utf-8') as f:
            json_results = json.load(f)
        
        if not json_results:
            print("  ⚠️  JSON文件中没有数据")
            return False
        
        # 连接到数据库
        conn = sqlite3.connect('optimization_results.db')
        cursor = conn.cursor()
        
        # 清空现有数据
        cursor.execute('DELETE FROM optimization_results')
        
        # 插入新数据
        for result in json_results:
            cursor.execute('''
                INSERT OR REPLACE INTO optimization_results 
                (test_id, strategy_type, symbol, params, total_return, sharpe_ratio, 
                 max_drawdown, win_rate, profit_factor, total_trades, avg_trade_duration,
                 timestamp, trading_mode, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['test_id'],
                result['strategy_type'],
                result['symbol'],
                json.dumps(result['params']),
                result['metrics'].get('total_return', 0),
                result['metrics'].get('sharpe_ratio', 0),
                result['metrics'].get('max_drawdown', 0),
                result['metrics'].get('win_rate', 0),
                result['metrics'].get('profit_factor', 0),
                result['metrics'].get('total_trades', 0),
                result['metrics'].get('avg_trade_duration', 0),
                result['timestamp'],
                result.get('trading_mode', 'SPOT'),
                result.get('start_date', ''),
                result.get('end_date', '')
            ))
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ 成功同步 {len(json_results)} 条记录到数据库")
        return True
        
    except Exception as e:
        print(f"  ❌ 同步失败: {e}")
        return False

def update_view_optimization_results():
    """更新 view_optimization_results.py 使用统一的数据源"""
    print("📝 更新 view_optimization_results.py...")
    
    try:
        with open('view_optimization_results.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经使用统一的数据源
        if 'def get_unified_results():' in content:
            print("  ✅ 已经使用统一的数据源")
            return True
        
        # 添加统一数据源函数
        unified_function = '''
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

'''
        
        # 在文件末尾添加新函数
        content += unified_function
        
        # 更新view_database_results函数
        old_function = '''def view_database_results():
    """查看数据库中的优化结果"""
    print("\\n🗄️  查看数据库中的优化结果...")
    
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
        print("\\n  🏆 最佳结果表:")
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
        print(f"  ❌ 读取数据库结果失败: {e}")'''
        
        new_function = '''def view_database_results():
    """查看数据库中的优化结果"""
    print("\\n🗄️  查看数据库中的优化结果...")
    
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
        print("\\n  🏆 最佳结果表:")
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
        print(f"  ❌ 读取结果失败: {e}")'''
        
        content = content.replace(old_function, new_function)
        
        # 保存更新后的文件
        with open('view_optimization_results.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ view_optimization_results.py 更新完成")
        return True
        
    except Exception as e:
        print(f"  ❌ 更新失败: {e}")
        return False

def update_apply_best_parameters():
    """更新 apply_best_parameters.py 使用统一的数据源"""
    print("📝 更新 apply_best_parameters.py...")
    
    try:
        with open('apply_best_parameters.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经使用统一的数据源
        if 'def get_unified_results():' in content:
            print("  ✅ 已经使用统一的数据源")
            return True
        
        # 添加统一数据源函数
        unified_function = '''
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

'''
        
        # 在文件末尾添加新函数
        content += unified_function
        
        # 更新analyze_optimization_results函数
        old_function = '''def analyze_optimization_results():
    """分析优化结果并找出最佳参数"""
    print("🔍 分析优化结果...")
    
    try:
        # 读取优化结果
        with open('optimization_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        if not results:
            print("❌ 没有找到优化结果")
            return None
        
        print(f"📊 共找到 {len(results)} 个测试结果")
        
        # 按策略类型和币种分组
        strategy_groups = {}
        for result in results:
            key = f"{result['strategy_type']}_{result['symbol']}"
            if key not in strategy_groups:
                strategy_groups[key] = []
            strategy_groups[key].append(result)
        
        # 分析每个策略组的最佳结果
        best_configs = {}
        
        for group_key, group_results in strategy_groups.items():
            print(f"\\n🔍 分析 {group_key}:")
            
            # 按总收益排序
            sorted_results = sorted(
                group_results, 
                key=lambda x: x.get('metrics', {}).get('total_return', 0), 
                reverse=True
            )
            
            # 获取最佳结果
            best_result = sorted_results[0]
            best_configs[group_key] = {
                'strategy_type': best_result['strategy_type'],
                'symbol': best_result['symbol'],
                'parameters': best_result['params'],
                'performance': best_result['metrics'],
                'timestamp': best_result['timestamp']
            }
            
            print(f"  🏆 最佳参数:")
            print(f"    总收益: {best_result['metrics'].get('total_return', 0):.2f}%")
            print(f"    夏普比率: {best_result['metrics'].get('sharpe_ratio', 0):.2f}")
            print(f"    胜率: {best_result['metrics'].get('win_rate', 0):.1f}%")
            print(f"    最大回撤: {best_result['metrics'].get('max_drawdown', 0):.2f}%")
            print(f"    交易次数: {best_result['metrics'].get('total_trades', 0)}")
            print(f"    参数: {best_result['params']}")
        
        return best_configs
        
    except Exception as e:
        print(f"❌ 分析优化结果失败: {e}")
        return None'''
        
        new_function = '''def analyze_optimization_results():
    """分析优化结果并找出最佳参数"""
    print("🔍 分析优化结果...")
    
    try:
        # 使用统一的数据源
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
            print(f"\\n🔍 分析 {group_key}:")
            
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
        return None'''
        
        content = content.replace(old_function, new_function)
        
        # 保存更新后的文件
        with open('apply_best_parameters.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ apply_best_parameters.py 更新完成")
        return True
        
    except Exception as e:
        print(f"  ❌ 更新失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 优化结果同步修复工具")
    print("=" * 50)
    
    # 1. 同步数据
    print("📊 数据同步:")
    db_to_json = sync_database_to_json()
    json_to_db = sync_json_to_database()
    
    # 2. 更新脚本
    print("\n📝 脚本更新:")
    update_view = update_view_optimization_results()
    update_apply = update_apply_best_parameters()
    
    # 3. 总结
    print("\n" + "=" * 50)
    print("📋 修复总结:")
    
    if db_to_json and json_to_db and update_view and update_apply:
        print("✅ 所有修复都成功完成")
        print("\n🎯 现在两个脚本将使用统一的数据源:")
        print("- 优先从数据库读取数据")
        print("- 如果数据库不可用，则从JSON读取")
        print("- 确保结果一致性")
    else:
        print("⚠️  部分修复失败，请检查错误信息")
    
    print("\n💡 建议:")
    print("1. 运行 python compare_optimization_results.py 验证修复效果")
    print("2. 运行 python view_optimization_results.py 查看结果")
    print("3. 运行 python apply_best_parameters.py 应用最佳参数")

if __name__ == "__main__":
    main()
