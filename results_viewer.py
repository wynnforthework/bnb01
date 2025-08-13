#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略优化结果查看器
用于查看和分析优化结果
"""

import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Optional
import os
from pathlib import Path


class ResultsViewer:
    """结果查看器"""
    
    def __init__(self, database_file: str = 'optimization_results.db'):
        self.database_file = database_file
        self.db_conn = None
        self._connect_database()
    
    def _connect_database(self):
        """连接数据库"""
        try:
            if os.path.exists(self.database_file):
                self.db_conn = sqlite3.connect(self.database_file)
                print(f"✅ 数据库连接成功: {self.database_file}")
            else:
                print(f"❌ 数据库文件不存在: {self.database_file}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
    
    def get_all_results(self) -> pd.DataFrame:
        """获取所有结果"""
        try:
            if not self.db_conn:
                return pd.DataFrame()
            
            query = """
                SELECT * FROM optimization_results 
                ORDER BY total_return DESC
            """
            df = pd.read_sql_query(query, self.db_conn)
            return df
            
        except Exception as e:
            print(f"❌ 获取结果失败: {e}")
            return pd.DataFrame()
    
    def get_best_results(self) -> pd.DataFrame:
        """获取最佳结果"""
        try:
            if not self.db_conn:
                return pd.DataFrame()
            
            query = """
                SELECT * FROM best_results 
                ORDER BY total_return DESC
            """
            df = pd.read_sql_query(query, self.db_conn)
            return df
            
        except Exception as e:
            print(f"❌ 获取最佳结果失败: {e}")
            return pd.DataFrame()
    
    def get_strategy_results(self, strategy_type: str) -> pd.DataFrame:
        """获取特定策略的结果"""
        try:
            if not self.db_conn:
                return pd.DataFrame()
            
            query = """
                SELECT * FROM optimization_results 
                WHERE strategy_type = ?
                ORDER BY total_return DESC
            """
            df = pd.read_sql_query(query, self.db_conn, params=(strategy_type,))
            return df
            
        except Exception as e:
            print(f"❌ 获取策略结果失败: {e}")
            return pd.DataFrame()
    
    def get_symbol_results(self, symbol: str) -> pd.DataFrame:
        """获取特定币种的结果"""
        try:
            if not self.db_conn:
                return pd.DataFrame()
            
            query = """
                SELECT * FROM optimization_results 
                WHERE symbol = ?
                ORDER BY total_return DESC
            """
            df = pd.read_sql_query(query, self.db_conn, params=(symbol,))
            return df
            
        except Exception as e:
            print(f"❌ 获取币种结果失败: {e}")
            return pd.DataFrame()
    
    def get_top_results(self, limit: int = 10) -> pd.DataFrame:
        """获取前N个最佳结果"""
        try:
            if not self.db_conn:
                return pd.DataFrame()
            
            query = """
                SELECT * FROM optimization_results 
                ORDER BY total_return DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, self.db_conn, params=(limit,))
            return df
            
        except Exception as e:
            print(f"❌ 获取前N个结果失败: {e}")
            return pd.DataFrame()
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            if not self.db_conn:
                return {}
            
            # 基本统计
            cursor = self.db_conn.cursor()
            
            # 总测试数
            cursor.execute("SELECT COUNT(*) FROM optimization_results")
            total_tests = cursor.fetchone()[0]
            
            # 策略类型统计
            cursor.execute("""
                SELECT strategy_type, COUNT(*) as count, 
                       AVG(total_return) as avg_return,
                       MAX(total_return) as max_return
                FROM optimization_results 
                GROUP BY strategy_type
            """)
            strategy_stats = cursor.fetchall()
            
            # 币种统计
            cursor.execute("""
                SELECT symbol, COUNT(*) as count,
                       AVG(total_return) as avg_return,
                       MAX(total_return) as max_return
                FROM optimization_results 
                GROUP BY symbol
            """)
            symbol_stats = cursor.fetchall()
            
            # 最佳结果统计
            cursor.execute("""
                SELECT strategy_type, symbol, total_return, sharpe_ratio, win_rate
                FROM best_results
                ORDER BY total_return DESC
            """)
            best_results = cursor.fetchall()
            
            return {
                'total_tests': total_tests,
                'strategy_stats': strategy_stats,
                'symbol_stats': symbol_stats,
                'best_results': best_results
            }
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def display_summary(self):
        """显示摘要信息"""
        print("📊 策略优化结果摘要")
        print("=" * 50)
        
        stats = self.get_statistics()
        if not stats:
            print("❌ 无法获取统计信息")
            return
        
        print(f"📈 总测试次数: {stats['total_tests']}")
        
        print("\n🏆 策略类型统计:")
        for strategy_type, count, avg_return, max_return in stats['strategy_stats']:
            print(f"  {strategy_type}: {count}次测试, "
                  f"平均收益: {avg_return:.2f}%, 最高收益: {max_return:.2f}%")
        
        print("\n💰 币种统计:")
        for symbol, count, avg_return, max_return in stats['symbol_stats']:
            print(f"  {symbol}: {count}次测试, "
                  f"平均收益: {avg_return:.2f}%, 最高收益: {max_return:.2f}%")
        
        print("\n🥇 最佳结果:")
        for i, (strategy_type, symbol, total_return, sharpe_ratio, win_rate) in enumerate(stats['best_results'][:5]):
            print(f"  {i+1}. {strategy_type}_{symbol}: "
                  f"收益: {total_return:.2f}%, "
                  f"夏普比率: {sharpe_ratio:.2f}, "
                  f"胜率: {win_rate:.1f}%")
    
    def display_top_results(self, limit: int = 10):
        """显示前N个最佳结果"""
        print(f"\n🏆 前{limit}个最佳结果")
        print("=" * 50)
        
        df = self.get_top_results(limit)
        if df.empty:
            print("❌ 无结果数据")
            return
        
        for i, row in df.iterrows():
            print(f"{i+1:2d}. {row['strategy_type']}_{row['symbol']}")
            print(f"    收益: {row['total_return']:.2f}%, "
                  f"夏普比率: {row['sharpe_ratio']:.2f}, "
                  f"胜率: {row['win_rate']:.1f}%, "
                  f"最大回撤: {row['max_drawdown']:.2f}%")
            print(f"    参数: {row['params']}")
            print()
    
    def display_strategy_comparison(self):
        """显示策略对比"""
        print("\n📊 策略对比分析")
        print("=" * 50)
        
        strategies = ['MA', 'RSI', 'ML', 'Chanlun']
        
        for strategy in strategies:
            df = self.get_strategy_results(strategy)
            if df.empty:
                print(f"❌ {strategy} 策略无数据")
                continue
            
            print(f"\n🔍 {strategy} 策略:")
            print(f"  测试次数: {len(df)}")
            print(f"  平均收益: {df['total_return'].mean():.2f}%")
            print(f"  最高收益: {df['total_return'].max():.2f}%")
            print(f"  平均夏普比率: {df['sharpe_ratio'].mean():.2f}")
            print(f"  平均胜率: {df['win_rate'].mean():.1f}%")
            print(f"  平均最大回撤: {df['max_drawdown'].mean():.2f}%")
    
    def export_results(self, filename: str = 'optimization_summary.csv'):
        """导出结果到CSV"""
        try:
            df = self.get_all_results()
            if df.empty:
                print("❌ 无数据可导出")
                return
            
            # 解析参数JSON
            df['params'] = df['params'].apply(lambda x: json.loads(x) if x else {})
            
            # 展开参数列
            params_df = pd.json_normalize(df['params'])
            df = pd.concat([df.drop('params', axis=1), params_df], axis=1)
            
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ 结果已导出到: {filename}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
    
    def create_visualizations(self, save_dir: str = 'optimization_plots'):
        """创建可视化图表"""
        try:
            # 创建保存目录
            os.makedirs(save_dir, exist_ok=True)
            
            df = self.get_all_results()
            if df.empty:
                print("❌ 无数据可可视化")
                return
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 1. 收益分布图
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            plt.hist(df['total_return'], bins=30, alpha=0.7, edgecolor='black')
            plt.title('收益分布')
            plt.xlabel('总收益 (%)')
            plt.ylabel('频次')
            
            # 2. 策略收益对比
            plt.subplot(2, 2, 2)
            strategy_returns = df.groupby('strategy_type')['total_return'].mean()
            strategy_returns.plot(kind='bar', color='skyblue')
            plt.title('各策略平均收益')
            plt.xlabel('策略类型')
            plt.ylabel('平均收益 (%)')
            plt.xticks(rotation=45)
            
            # 3. 币种收益对比
            plt.subplot(2, 2, 3)
            symbol_returns = df.groupby('symbol')['total_return'].mean()
            symbol_returns.plot(kind='bar', color='lightgreen')
            plt.title('各币种平均收益')
            plt.xlabel('币种')
            plt.ylabel('平均收益 (%)')
            plt.xticks(rotation=45)
            
            # 4. 夏普比率vs收益散点图
            plt.subplot(2, 2, 4)
            plt.scatter(df['sharpe_ratio'], df['total_return'], alpha=0.6)
            plt.title('夏普比率 vs 总收益')
            plt.xlabel('夏普比率')
            plt.ylabel('总收益 (%)')
            
            plt.tight_layout()
            plt.savefig(f'{save_dir}/optimization_summary.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # 5. 详细策略对比图
            plt.figure(figsize=(15, 10))
            
            strategies = ['MA', 'RSI', 'ML', 'Chanlun']
            metrics = ['total_return', 'sharpe_ratio', 'win_rate', 'max_drawdown']
            metric_names = ['总收益 (%)', '夏普比率', '胜率 (%)', '最大回撤 (%)']
            
            for i, (metric, metric_name) in enumerate(zip(metrics, metric_names)):
                plt.subplot(2, 2, i+1)
                
                data = []
                labels = []
                for strategy in strategies:
                    strategy_data = df[df['strategy_type'] == strategy][metric]
                    if not strategy_data.empty:
                        data.append(strategy_data.values)
                        labels.append(strategy)
                
                if data:
                    plt.boxplot(data, labels=labels)
                    plt.title(f'{metric_name} 分布')
                    plt.ylabel(metric_name)
                    plt.xticks(rotation=45)
            
            plt.tight_layout()
            plt.savefig(f'{save_dir}/strategy_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ 可视化图表已保存到: {save_dir}")
            
        except Exception as e:
            print(f"❌ 创建可视化失败: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.db_conn:
            self.db_conn.close()
            print("🔒 数据库连接已关闭")


def main():
    """主函数"""
    print("📊 策略优化结果查看器")
    print("=" * 50)
    
    # 创建查看器
    viewer = ResultsViewer()
    
    try:
        while True:
            print("\n📋 功能菜单:")
            print("1. 显示摘要信息")
            print("2. 显示前10个最佳结果")
            print("3. 策略对比分析")
            print("4. 查看特定策略结果")
            print("5. 查看特定币种结果")
            print("6. 导出结果到CSV")
            print("7. 创建可视化图表")
            print("0. 退出")
            
            choice = input("\n请选择功能 (0-7): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                viewer.display_summary()
            elif choice == '2':
                limit = input("显示前N个结果 (默认10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                viewer.display_top_results(limit)
            elif choice == '3':
                viewer.display_strategy_comparison()
            elif choice == '4':
                strategy = input("请输入策略类型 (MA/RSI/ML/Chanlun): ").strip()
                if strategy:
                    df = viewer.get_strategy_results(strategy)
                    if not df.empty:
                        print(f"\n📊 {strategy} 策略结果 (前10个):")
                        print(df.head(10)[['symbol', 'total_return', 'sharpe_ratio', 'win_rate']].to_string())
                    else:
                        print(f"❌ 未找到 {strategy} 策略的结果")
            elif choice == '5':
                symbol = input("请输入币种 (如 BTCUSDT): ").strip()
                if symbol:
                    df = viewer.get_symbol_results(symbol)
                    if not df.empty:
                        print(f"\n📊 {symbol} 结果 (前10个):")
                        print(df.head(10)[['strategy_type', 'total_return', 'sharpe_ratio', 'win_rate']].to_string())
                    else:
                        print(f"❌ 未找到 {symbol} 的结果")
            elif choice == '6':
                filename = input("请输入文件名 (默认: optimization_summary.csv): ").strip()
                filename = filename if filename else 'optimization_summary.csv'
                viewer.export_results(filename)
            elif choice == '7':
                save_dir = input("请输入保存目录 (默认: optimization_plots): ").strip()
                save_dir = save_dir if save_dir else 'optimization_plots'
                viewer.create_visualizations(save_dir)
            else:
                print("❌ 无效选择")
    
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 运行失败: {e}")
    finally:
        viewer.close()


if __name__ == "__main__":
    main()
