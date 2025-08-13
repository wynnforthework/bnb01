#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略参数优化测试脚本
支持随机参数组合测试、自动分析结果、持续优化
"""

import json
import random
import time
import threading
import signal
import sys
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import sqlite3
import os
from pathlib import Path

# 导入项目模块
from backend.trading_engine import TradingEngine
from backend.backtesting import BacktestEngine
from backend.data_collector import DataCollector
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.ml_strategy import MLStrategy
from strategies.chanlun_strategy import ChanlunStrategy


@dataclass
class OptimizationConfig:
    """优化配置"""
    # 测试配置
    symbols: List[str] = None
    trading_mode: str = 'SPOT'  # SPOT 或 FUTURES
    start_date: str = '2025-08-06'
    end_date: str = '2025-08-13'
    
    # 优化配置
    max_iterations: int = 1000
    population_size: int = 50
    elite_size: int = 10
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    
    # 测试间隔
    test_interval: int = 5  # 秒
    
    # 结果保存
    save_results: bool = True
    results_file: str = 'optimization_results.json'
    database_file: str = 'optimization_results.db'
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = [ 'ETHUSDT']  #['BTCUSDT', 'ETHUSDT', 'BNBUSDT']


@dataclass
class StrategyParams:
    """策略参数"""
    strategy_type: str
    symbol: str
    params: Dict[str, Any]
    test_id: str = None
    
    def __post_init__(self):
        if self.test_id is None:
            self.test_id = f"{self.strategy_type}_{self.symbol}_{int(time.time())}"


@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    strategy_type: str
    symbol: str
    params: Dict[str, Any]
    metrics: Dict[str, float]
    timestamp: str
    trading_mode: str
    start_date: str
    end_date: str
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class StrategyOptimizer:
    """策略参数优化器"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.running = False
        self.results = []
        self.best_results = {}
        self.current_iteration = 0
        self.db_conn = None
        self.backtest_engine = BacktestEngine(initial_capital=10000.0)
        self.data_collector = DataCollector()
        
        # 策略参数范围定义
        self.strategy_param_ranges = {
            'MA': {
                'short_window': range(5, 21),
                'long_window': range(20, 101),
                'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
                'stop_loss': [0.01, 0.02, 0.03, 0.05],
                'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
            },
            'RSI': {
                'rsi_period': range(7, 22),
                'overbought': range(65, 81),
                'oversold': range(20, 36),
                'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
                'stop_loss': [0.01, 0.02, 0.03, 0.05],
                'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
            },
            'ML': {
                'lookback_period': range(10, 51),
                'prediction_horizon': [1, 2, 3, 5],
                'model_type': ['random_forest', 'gradient_boosting', 'logistic_regression'],
                'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
                'stop_loss': [0.01, 0.02, 0.03, 0.05],
                'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
            },
            'Chanlun': {
                'min_swing_length': range(3, 8),
                'trend_confirmation': [0.01, 0.02, 0.03, 0.05],
                'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
                'stop_loss': [0.01, 0.02, 0.03, 0.05],
                'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
            }
        }
        
        self._init_database()
        self._setup_signal_handlers()
    
    def check_data_availability(self) -> bool:
        """检查数据库中的数据是否足够"""
        print("🔍 检查数据库中的数据可用性...")
        
        try:
            # 检查配置的币种是否有足够的数据
            for symbol in self.config.symbols:
                print(f"  检查 {symbol} 的数据...")
                
                # 获取数据库中的数据
                market_data = self.data_collector.get_market_data(symbol, '1h', limit=1000)
                
                if market_data.empty:
                    print(f"    ❌ {symbol} 没有数据")
                    return False
                
                # 检查数据量是否足够（至少需要50条记录用于策略计算）
                if len(market_data) < 50:
                    print(f"    ⚠️  {symbol} 数据不足，只有 {len(market_data)} 条记录")
                    return False
                
                # 检查数据时间范围是否覆盖回测期间
                start_date = pd.to_datetime(self.config.start_date)
                end_date = pd.to_datetime(self.config.end_date)
                
                data_start = market_data['timestamp'].min()
                data_end = market_data['timestamp'].max()
                
                print(f"    数据范围: {data_start} 到 {data_end}")
                print(f"    回测范围: {start_date} 到 {end_date}")
                print(f"    数据条数: {len(market_data)}")
                
                # 检查数据是否足够进行回测
                # 如果数据范围不覆盖回测期间，但数据量足够，我们可以调整回测范围
                if data_start > start_date or data_end < end_date:
                    print(f"    ⚠️  {symbol} 数据范围不覆盖回测期间")
                    
                    # 计算实际可用的数据范围
                    actual_start = max(data_start, start_date)
                    actual_end = min(data_end, end_date)
                    
                    # 检查是否有足够的数据进行回测（至少需要30天的数据）
                    data_span = actual_end - actual_start
                    if data_span.days < 30:
                        print(f"    ❌ 可用数据时间跨度不足: {data_span.days} 天")
                        return False
                    
                    print(f"    ✅ 可用数据时间跨度: {data_span.days} 天，将调整回测范围")
                    # 更新配置中的日期范围
                    self.config.start_date = actual_start.strftime('%Y-%m-%d')
                    self.config.end_date = actual_end.strftime('%Y-%m-%d')
                    return True
                
                print(f"    ✅ {symbol} 数据充足")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 检查数据可用性失败: {e}")
            return False
    
    async def collect_historical_data(self, days: int = 90):
        """收集历史数据"""
        print(f"📊 开始收集历史数据（最近 {days} 天）...")
        
        try:
            success_count = 0
            for symbol in self.config.symbols:
                print(f"  收集 {symbol} 的历史数据...")
                
                try:
                    # 收集历史数据，使用回测开始日期
                    data = await self.data_collector.collect_historical_data(
                        symbol, '1h', days, start_date=self.config.start_date
                    )
                    
                    if not data.empty:
                        print(f"    ✅ {symbol} 数据收集成功，获得 {len(data)} 条记录")
                        print(f"    数据范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
                        success_count += 1
                    else:
                        print(f"    ❌ {symbol} 数据收集失败")
                        
                except Exception as e:
                    print(f"    ❌ {symbol} 数据收集异常: {e}")
            
            print(f"📈 数据收集完成: {success_count}/{len(self.config.symbols)} 个币种成功")
            return success_count == len(self.config.symbols)
            
        except Exception as e:
            print(f"❌ 数据收集过程失败: {e}")
            return False
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect(self.config.database_file)
            cursor = self.db_conn.cursor()
            
            # 创建结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE,
                    strategy_type TEXT,
                    symbol TEXT,
                    params TEXT,
                    total_return REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    profit_factor REAL,
                    total_trades INTEGER,
                    avg_trade_duration REAL,
                    timestamp TEXT,
                    trading_mode TEXT,
                    start_date TEXT,
                    end_date TEXT
                )
            ''')
            
            # 创建最佳结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS best_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_type TEXT,
                    symbol TEXT,
                    params TEXT,
                    total_return REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    profit_factor REAL,
                    timestamp TEXT
                )
            ''')
            
            self.db_conn.commit()
            print(f"✅ 数据库初始化完成: {self.config.database_file}")
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print("\n🛑 收到停止信号，正在保存结果...")
        self.stop()
        sys.exit(0)
    
    def generate_random_params(self, strategy_type: str) -> Dict[str, Any]:
        """生成随机参数组合"""
        param_ranges = self.strategy_param_ranges.get(strategy_type, {})
        params = {}
        
        for param_name, param_range in param_ranges.items():
            if isinstance(param_range, range):
                params[param_name] = random.choice(param_range)
            elif isinstance(param_range, list):
                params[param_name] = random.choice(param_range)
            else:
                params[param_name] = param_range
        
        return params
    
    def run_backtest(self, strategy_params: StrategyParams) -> Optional[TestResult]:
        """运行回测"""
        try:
            print(f"🔄 测试 {strategy_params.strategy_type} 策略 - {strategy_params.symbol}")
            print(f"   参数: {strategy_params.params}")
            
            # 创建策略实例
            strategy = self._create_strategy(strategy_params)
            if not strategy:
                return None
            
            # 运行回测
            results = self.backtest_engine.run_backtest(
                strategy=strategy,
                symbol=strategy_params.symbol,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                interval='1h'
            )
            
            if not results:
                print(f"❌ 回测失败: {strategy_params.test_id}")
                return None
            
            # 计算指标
            metrics = self._calculate_metrics(results)
            
            # 创建测试结果
            test_result = TestResult(
                test_id=strategy_params.test_id,
                strategy_type=strategy_params.strategy_type,
                symbol=strategy_params.symbol,
                params=strategy_params.params,
                metrics=metrics,
                timestamp=datetime.now().isoformat(),
                trading_mode=self.config.trading_mode,
                start_date=self.config.start_date,
                end_date=self.config.end_date
            )
            
            print(f"✅ 测试完成 - 总收益: {metrics.get('total_return', 0):.2f}%, "
                  f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
            
            return test_result
            
        except Exception as e:
            print(f"❌ 回测异常: {e}")
            return None
    
    def _create_strategy(self, strategy_params: StrategyParams):
        """创建策略实例"""
        try:
            if strategy_params.strategy_type == 'MA':
                return MovingAverageStrategy(
                    symbol=strategy_params.symbol,
                    parameters=strategy_params.params
                )
            elif strategy_params.strategy_type == 'RSI':
                return RSIStrategy(
                    symbol=strategy_params.symbol,
                    parameters=strategy_params.params
                )
            elif strategy_params.strategy_type == 'ML':
                return MLStrategy(
                    symbol=strategy_params.symbol,
                    parameters=strategy_params.params
                )
            elif strategy_params.strategy_type == 'Chanlun':
                return ChanlunStrategy(
                    symbol=strategy_params.symbol,
                    parameters=strategy_params.params
                )
            else:
                print(f"❌ 不支持的策略类型: {strategy_params.strategy_type}")
                return None
                
        except Exception as e:
            print(f"❌ 创建策略失败: {e}")
            return None
    
    def _calculate_metrics(self, results) -> Dict[str, float]:
        """计算回测指标"""
        try:
            trades = results.trades
            equity_curve = results.equity_curve
            
            if not trades:
                return {
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'total_trades': 0,
                    'avg_trade_duration': 0.0
                }
            
            # 使用BacktestResult对象的属性
            total_return = results.total_return * 100  # 转换为百分比
            sharpe_ratio = results.sharpe_ratio
            max_drawdown = results.max_drawdown * 100  # 转换为百分比
            win_rate = results.win_rate * 100  # 转换为百分比
            profit_factor = results.profit_factor
            total_trades = results.total_trades
            
            # 计算平均交易时长
            trade_durations = []
            for trade in trades:
                if 'timestamp' in trade:
                    # 这里需要根据实际的交易数据结构来计算时长
                    # 暂时使用默认值
                    trade_durations.append(1.0)  # 假设平均1小时
            
            avg_trade_duration = np.mean(trade_durations) if trade_durations else 0
            
            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': total_trades,
                'avg_trade_duration': avg_trade_duration
            }
            
        except Exception as e:
            print(f"❌ 计算指标失败: {e}")
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'avg_trade_duration': 0.0
            }
    
    def save_result(self, result: TestResult):
        """保存测试结果"""
        try:
            # 保存到内存
            self.results.append(result)
            
            # 保存到数据库
            if self.db_conn:
                cursor = self.db_conn.cursor()
                
                # 插入结果
                cursor.execute('''
                    INSERT OR REPLACE INTO optimization_results 
                    (test_id, strategy_type, symbol, params, total_return, sharpe_ratio, 
                     max_drawdown, win_rate, profit_factor, total_trades, avg_trade_duration,
                     timestamp, trading_mode, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.test_id,
                    result.strategy_type,
                    result.symbol,
                    json.dumps(result.params),
                    result.metrics.get('total_return', 0),
                    result.metrics.get('sharpe_ratio', 0),
                    result.metrics.get('max_drawdown', 0),
                    result.metrics.get('win_rate', 0),
                    result.metrics.get('profit_factor', 0),
                    result.metrics.get('total_trades', 0),
                    result.metrics.get('avg_trade_duration', 0),
                    result.timestamp,
                    result.trading_mode,
                    result.start_date,
                    result.end_date
                ))
                
                self.db_conn.commit()
            
            # 保存到JSON文件
            if self.config.save_results:
                self._save_to_json()
                
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
    
    def _save_to_json(self):
        """保存结果到JSON文件"""
        try:
            results_data = []
            for result in self.results:
                results_data.append(asdict(result))
            
            with open(self.config.results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ 保存JSON文件失败: {e}")
    
    def analyze_results(self):
        """分析结果并找出最佳参数"""
        try:
            if not self.results:
                print("📊 暂无测试结果")
                return
            
            print("\n📊 分析测试结果...")
            
            # 按策略类型分组
            strategy_groups = {}
            for result in self.results:
                key = f"{result.strategy_type}_{result.symbol}"
                if key not in strategy_groups:
                    strategy_groups[key] = []
                strategy_groups[key].append(result)
            
            # 分析每个策略组
            for group_key, group_results in strategy_groups.items():
                print(f"\n🔍 分析 {group_key}:")
                
                # 按总收益排序
                sorted_results = sorted(
                    group_results, 
                    key=lambda x: x.metrics.get('total_return', 0), 
                    reverse=True
                )
                
                # 显示前5个最佳结果
                print("🏆 前5个最佳结果:")
                for i, result in enumerate(sorted_results[:5]):
                    metrics = result.metrics
                    print(f"  {i+1}. 总收益: {metrics.get('total_return', 0):.2f}%, "
                          f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}, "
                          f"胜率: {metrics.get('win_rate', 0):.1f}%, "
                          f"最大回撤: {metrics.get('max_drawdown', 0):.2f}%")
                    print(f"     参数: {result.params}")
                
                # 更新最佳结果
                if sorted_results:
                    best_result = sorted_results[0]
                    self.best_results[group_key] = best_result
                    
                    # 保存到数据库
                    if self.db_conn:
                        cursor = self.db_conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO best_results 
                            (strategy_type, symbol, params, total_return, sharpe_ratio,
                             max_drawdown, win_rate, profit_factor, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            best_result.strategy_type,
                            best_result.symbol,
                            json.dumps(best_result.params),
                            best_result.metrics.get('total_return', 0),
                            best_result.metrics.get('sharpe_ratio', 0),
                            best_result.metrics.get('max_drawdown', 0),
                            best_result.metrics.get('win_rate', 0),
                            best_result.metrics.get('profit_factor', 0),
                            best_result.timestamp
                        ))
                        self.db_conn.commit()
            
            print(f"\n✅ 分析完成，共测试 {len(self.results)} 个参数组合")
            
        except Exception as e:
            print(f"❌ 分析结果失败: {e}")
    
    def generate_next_params(self, strategy_type: str, symbol: str) -> StrategyParams:
        """生成下一组参数（基于遗传算法）"""
        try:
            # 获取当前策略组的最佳结果
            group_key = f"{strategy_type}_{symbol}"
            best_result = self.best_results.get(group_key)
            
            if best_result and random.random() < self.config.mutation_rate:
                # 基于最佳结果进行变异
                params = best_result.params.copy()
                
                # 随机选择一些参数进行变异
                param_ranges = self.strategy_param_ranges.get(strategy_type, {})
                mutation_params = random.sample(list(param_ranges.keys()), 
                                              min(2, len(param_ranges)))
                
                for param_name in mutation_params:
                    param_range = param_ranges[param_name]
                    if isinstance(param_range, range):
                        params[param_name] = random.choice(param_range)
                    elif isinstance(param_range, list):
                        params[param_name] = random.choice(param_range)
                
                print(f"🧬 基于最佳结果变异生成参数: {params}")
            else:
                # 完全随机生成
                params = self.generate_random_params(strategy_type)
                print(f"🎲 随机生成参数: {params}")
            
            return StrategyParams(
                strategy_type=strategy_type,
                symbol=symbol,
                params=params
            )
            
        except Exception as e:
            print(f"❌ 生成参数失败: {e}")
            return self.generate_random_params(strategy_type)
    
    async def run_optimization(self):
        """运行优化过程"""
        print("🚀 开始策略参数优化...")
        print(f"📋 配置信息:")
        print(f"   交易模式: {self.config.trading_mode}")
        print(f"   测试币种: {', '.join(self.config.symbols)}")
        print(f"   回测时间: {self.config.start_date} 到 {self.config.end_date}")
        print(f"   最大迭代次数: {self.config.max_iterations}")
        print(f"   测试间隔: {self.config.test_interval}秒")
        
        # 检查数据可用性
        print("\n" + "=" * 50)
        if not self.check_data_availability():
            print("\n⚠️  数据不足，开始自动收集历史数据...")
            
            # 计算需要收集的天数
            start_date = pd.to_datetime(self.config.start_date)
            end_date = pd.to_datetime(self.config.end_date)
            days_needed = max(90, (end_date - start_date).days + 30)  # 至少90天，或者回测期间+30天
            
            if await self.collect_historical_data(days_needed):
                print("✅ 数据收集完成，重新检查数据可用性...")
                if not self.check_data_availability():
                    print("❌ 数据收集后仍然不足，无法继续优化")
                    return
            else:
                print("❌ 数据收集失败，无法继续优化")
                return
        
        print("✅ 数据检查通过，开始优化过程...")
        print("=" * 50)
        
        self.running = True
        self.current_iteration = 0
        
        try:
            while self.running and self.current_iteration < self.config.max_iterations:
                self.current_iteration += 1
                print(f"\n🔄 第 {self.current_iteration} 次迭代")
                
                # 为每个策略类型和币种生成参数
                for strategy_type in ['MA', 'RSI', 'ML', 'Chanlun']:
                    for symbol in self.config.symbols:
                        if not self.running:
                            break
                        
                        # 生成参数
                        strategy_params = self.generate_next_params(strategy_type, symbol)
                        
                        # 运行测试
                        result = self.run_backtest(strategy_params)
                        
                        if result:
                            # 保存结果
                            self.save_result(result)
                            
                            # 每10次迭代分析一次结果
                            if len(self.results) % 10 == 0:
                                self.analyze_results()
                        
                        # 等待间隔
                        if self.config.test_interval > 0:
                            time.sleep(self.config.test_interval)
                
                # 定期保存结果
                if self.current_iteration % 50 == 0:
                    self._save_to_json()
                    print(f"💾 已保存 {len(self.results)} 个测试结果")
        
        except KeyboardInterrupt:
            print("\n🛑 用户中断优化过程")
        except Exception as e:
            print(f"❌ 优化过程异常: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止优化"""
        self.running = False
        print("\n🛑 停止优化过程")
        
        # 最终分析
        self.analyze_results()
        
        # 保存最终结果
        if self.config.save_results:
            self._save_to_json()
            print(f"💾 最终结果已保存到 {self.config.results_file}")
        
        # 关闭数据库连接
        if self.db_conn:
            self.db_conn.close()
            print("🔒 数据库连接已关闭")


def load_config(config_file: str = 'optimization_config.json') -> OptimizationConfig:
    """加载配置文件"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return OptimizationConfig(**config_data)
        else:
            # 创建默认配置
            config = OptimizationConfig()
            save_config(config, config_file)
            return config
            
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return OptimizationConfig()


def save_config(config: OptimizationConfig, config_file: str = 'optimization_config.json'):
    """保存配置文件"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(config), f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到 {config_file}")
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")


async def main():
    """主函数"""
    print("🎯 策略参数优化测试脚本")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 显示配置
    print("📋 当前配置:")
    print(f"   交易模式: {config.trading_mode}")
    print(f"   测试币种: {', '.join(config.symbols)}")
    print(f"   回测时间: {config.start_date} 到 {config.end_date}")
    print(f"   最大迭代次数: {config.max_iterations}")
    print(f"   测试间隔: {config.test_interval}秒")
    
    # 询问是否修改配置
    modify_config = input("\n❓ 是否修改配置? (y/N): ").lower().strip()
    if modify_config == 'y':
        print("\n📝 配置修改:")
        
        # 交易模式
        mode = input(f"   交易模式 (当前: {config.trading_mode}) [SPOT/FUTURES]: ").strip()
        if mode in ['SPOT', 'FUTURES']:
            config.trading_mode = mode
        
        # 测试币种
        symbols_input = input(f"   测试币种 (当前: {', '.join(config.symbols)}) [用逗号分隔]: ").strip()
        if symbols_input:
            config.symbols = [s.strip() for s in symbols_input.split(',')]
        
        # 回测时间
        start_date = input(f"   开始日期 (当前: {config.start_date}) [YYYY-MM-DD]: ").strip()
        if start_date:
            config.start_date = start_date
        
        end_date = input(f"   结束日期 (当前: {config.end_date}) [YYYY-MM-DD]: ").strip()
        if end_date:
            config.end_date = end_date
        
        # 最大迭代次数
        max_iter = input(f"   最大迭代次数 (当前: {config.max_iterations}): ").strip()
        if max_iter.isdigit():
            config.max_iterations = int(max_iter)
        
        # 测试间隔
        interval = input(f"   测试间隔秒数 (当前: {config.test_interval}): ").strip()
        if interval.isdigit():
            config.test_interval = int(interval)
        
        # 保存配置
        save_config(config)
    
    # 创建优化器
    optimizer = StrategyOptimizer(config)
    
    # 开始优化
    try:
        await optimizer.run_optimization()
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 运行失败: {e}")
    finally:
        optimizer.stop()


def run_main():
    """运行主函数的包装器"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 运行失败: {e}")


if __name__ == "__main__":
    run_main()
