import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from backend.data_collector import DataCollector

@dataclass
class BacktestResult:
    """回测结果数据类"""
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    profit_factor: float
    avg_trade_return: float
    volatility: float
    calmar_ratio: float
    trades: List[Dict]
    equity_curve: pd.Series
    drawdown_curve: pd.Series

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission  # 手续费率
        self.data_collector = DataCollector()
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(self, strategy, symbol: str, start_date: str, end_date: str, 
                    interval: str = '1h') -> BacktestResult:
        """运行回测"""
        try:
            # 获取历史数据
            data = self._get_historical_data(symbol, start_date, end_date, interval)
            if data.empty:
                raise ValueError("无法获取历史数据")
            
            # 计算技术指标
            data = self.data_collector.calculate_technical_indicators(data, symbol)
            
            # 初始化回测状态
            capital = self.initial_capital
            position = 0  # 持仓数量
            entry_price = 0
            trades = []
            equity_curve = []
            
            # 遍历历史数据进行回测
            for i in range(len(data)):
                current_data = data.iloc[:i+1]
                current_price = data.iloc[i]['close']
                current_time = data.iloc[i]['timestamp']
                
                # 跳过数据不足的情况
                if len(current_data) < 50:  # 需要足够的数据计算指标
                    equity_curve.append(capital)
                    continue
                
                # 生成交易信号
                signal = strategy.generate_signal(current_data)
                
                # 执行交易逻辑
                if signal == 'BUY' and position <= 0:
                    # 买入信号
                    if position < 0:  # 先平空仓
                        profit = (entry_price - current_price) * abs(position)
                        capital += profit - (abs(position) * current_price * self.commission)
                        trades.append({
                            'timestamp': current_time,
                            'action': 'COVER',
                            'price': current_price,
                            'quantity': abs(position),
                            'profit': profit,
                            'capital': capital
                        })
                    
                    # 开多仓
                    position_size = strategy.calculate_position_size(current_price, capital)
                    if position_size > 0:
                        position = position_size
                        entry_price = current_price
                        capital -= position * current_price * (1 + self.commission)
                        trades.append({
                            'timestamp': current_time,
                            'action': 'BUY',
                            'price': current_price,
                            'quantity': position,
                            'profit': 0,
                            'capital': capital
                        })
                
                elif signal == 'SELL' and position >= 0:
                    # 卖出信号
                    if position > 0:  # 先平多仓
                        profit = (current_price - entry_price) * position
                        capital += profit + (position * current_price * (1 - self.commission))
                        trades.append({
                            'timestamp': current_time,
                            'action': 'SELL',
                            'price': current_price,
                            'quantity': position,
                            'profit': profit,
                            'capital': capital
                        })
                    
                    # 开空仓（如果策略支持）
                    if hasattr(strategy, 'allow_short') and strategy.allow_short:
                        position_size = strategy.calculate_position_size(current_price, capital)
                        if position_size > 0:
                            position = -position_size
                            entry_price = current_price
                            capital += position_size * current_price * (1 - self.commission)
                            trades.append({
                                'timestamp': current_time,
                                'action': 'SHORT',
                                'price': current_price,
                                'quantity': position_size,
                                'profit': 0,
                                'capital': capital
                            })
                
                # 检查止损止盈
                if position != 0:
                    if strategy.should_stop_loss(current_price):
                        profit = self._close_position(position, entry_price, current_price)
                        capital += profit
                        trades.append({
                            'timestamp': current_time,
                            'action': 'STOP_LOSS',
                            'price': current_price,
                            'quantity': abs(position),
                            'profit': profit,
                            'capital': capital
                        })
                        position = 0
                    
                    elif strategy.should_take_profit(current_price):
                        profit = self._close_position(position, entry_price, current_price)
                        capital += profit
                        trades.append({
                            'timestamp': current_time,
                            'action': 'TAKE_PROFIT',
                            'price': current_price,
                            'quantity': abs(position),
                            'profit': profit,
                            'capital': capital
                        })
                        position = 0
                
                # 计算当前权益
                current_equity = capital
                if position != 0:
                    unrealized_pnl = self._calculate_unrealized_pnl(position, entry_price, current_price)
                    current_equity += unrealized_pnl
                
                equity_curve.append(current_equity)
            
            # 最后平仓
            if position != 0:
                final_price = data.iloc[-1]['close']
                profit = self._close_position(position, entry_price, final_price)
                capital += profit
                trades.append({
                    'timestamp': data.iloc[-1]['timestamp'],
                    'action': 'FINAL_CLOSE',
                    'price': final_price,
                    'quantity': abs(position),
                    'profit': profit,
                    'capital': capital
                })
            
            # 计算回测结果
            result = self._calculate_backtest_metrics(
                equity_curve, trades, data.iloc[0]['timestamp'], data.iloc[-1]['timestamp']
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            raise
    
    def _get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                           interval: str) -> pd.DataFrame:
        """获取历史数据"""
        try:
            # 先尝试从数据库获取
            data = self.data_collector.get_market_data(symbol, interval, limit=10000)
            
            if data.empty:
                # 如果数据库没有数据，从API获取
                self.logger.info(f"从API获取 {symbol} 历史数据...")
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                data = loop.run_until_complete(
                    self.data_collector.collect_historical_data(symbol, interval, days=365)
                )
                loop.close()
            
            # 过滤日期范围
            if not data.empty:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                data = data[(data['timestamp'] >= start_dt) & (data['timestamp'] <= end_dt)]
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def _close_position(self, position: float, entry_price: float, current_price: float) -> float:
        """平仓计算"""
        if position > 0:  # 多仓
            profit = (current_price - entry_price) * position
            total_value = position * current_price * (1 - self.commission)
        else:  # 空仓
            profit = (entry_price - current_price) * abs(position)
            total_value = abs(position) * current_price * (1 + self.commission)
        
        return profit + total_value
    
    def _calculate_unrealized_pnl(self, position: float, entry_price: float, current_price: float) -> float:
        """计算未实现盈亏"""
        if position > 0:  # 多仓
            return (current_price - entry_price) * position
        else:  # 空仓
            return (entry_price - current_price) * abs(position)
    
    def _calculate_backtest_metrics(self, equity_curve: List[float], trades: List[Dict],
                                  start_date: datetime, end_date: datetime) -> BacktestResult:
        """计算回测指标"""
        try:
            equity_series = pd.Series(equity_curve)
            
            # 基本收益指标
            total_return = (equity_series.iloc[-1] - self.initial_capital) / self.initial_capital
            days = (end_date - start_date).days
            annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
            
            # 最大回撤
            peak = equity_series.expanding().max()
            drawdown = (equity_series - peak) / peak
            max_drawdown = drawdown.min()
            
            # 波动率
            returns = equity_series.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # 年化波动率
            
            # 夏普比率
            risk_free_rate = 0.02  # 假设无风险利率2%
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # 卡尔玛比率
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
            
            # 交易统计
            profitable_trades = [t for t in trades if t.get('profit', 0) > 0]
            losing_trades = [t for t in trades if t.get('profit', 0) < 0]
            
            win_rate = len(profitable_trades) / len(trades) if trades else 0
            
            total_profit = sum(t.get('profit', 0) for t in profitable_trades)
            total_loss = abs(sum(t.get('profit', 0) for t in losing_trades))
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            avg_trade_return = sum(t.get('profit', 0) for t in trades) / len(trades) if trades else 0
            
            return BacktestResult(
                total_return=total_return,
                annual_return=annual_return,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                total_trades=len(trades),
                profit_factor=profit_factor,
                avg_trade_return=avg_trade_return,
                volatility=volatility,
                calmar_ratio=calmar_ratio,
                trades=trades,
                equity_curve=equity_series,
                drawdown_curve=drawdown
            )
            
        except Exception as e:
            self.logger.error(f"计算回测指标失败: {e}")
            raise
    
    def generate_backtest_report(self, result: BacktestResult, strategy_name: str, 
                               symbol: str, save_path: str = None) -> str:
        """生成回测报告"""
        try:
            report = f"""
=== 回测报告 ===
策略名称: {strategy_name}
交易对: {symbol}
初始资金: ${self.initial_capital:,.2f}
手续费率: {self.commission:.3%}

=== 收益指标 ===
总收益率: {result.total_return:.2%}
年化收益率: {result.annual_return:.2%}
最大回撤: {result.max_drawdown:.2%}
波动率: {result.volatility:.2%}
夏普比率: {result.sharpe_ratio:.2f}
卡尔玛比率: {result.calmar_ratio:.2f}

=== 交易统计 ===
总交易次数: {result.total_trades}
胜率: {result.win_rate:.2%}
盈亏比: {result.profit_factor:.2f}
平均每笔收益: ${result.avg_trade_return:.2f}

=== 详细交易记录 ===
"""
            
            # 添加交易记录
            for i, trade in enumerate(result.trades[-10:], 1):  # 显示最后10笔交易
                report += f"{i}. {trade['timestamp'].strftime('%Y-%m-%d %H:%M')} "
                report += f"{trade['action']} {trade['quantity']:.4f} @ ${trade['price']:.2f} "
                report += f"盈亏: ${trade.get('profit', 0):.2f}\n"
            
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.logger.info(f"回测报告已保存到: {save_path}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成回测报告失败: {e}")
            return ""
    
    def plot_backtest_results(self, result: BacktestResult, strategy_name: str, 
                            symbol: str, save_path: str = None):
        """绘制回测结果图表"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'{strategy_name} - {symbol} 回测结果', fontsize=16)
            
            # 权益曲线
            axes[0, 0].plot(result.equity_curve.index, result.equity_curve.values)
            axes[0, 0].axhline(y=self.initial_capital, color='r', linestyle='--', alpha=0.7)
            axes[0, 0].set_title('权益曲线')
            axes[0, 0].set_ylabel('资金 ($)')
            axes[0, 0].grid(True, alpha=0.3)
            
            # 回撤曲线
            axes[0, 1].fill_between(result.drawdown_curve.index, 
                                  result.drawdown_curve.values, 0, 
                                  color='red', alpha=0.3)
            axes[0, 1].set_title('回撤曲线')
            axes[0, 1].set_ylabel('回撤 (%)')
            axes[0, 1].grid(True, alpha=0.3)
            
            # 收益分布
            trade_returns = [t.get('profit', 0) for t in result.trades if 'profit' in t]
            if trade_returns:
                axes[1, 0].hist(trade_returns, bins=20, alpha=0.7, edgecolor='black')
                axes[1, 0].axvline(x=0, color='r', linestyle='--', alpha=0.7)
                axes[1, 0].set_title('交易收益分布')
                axes[1, 0].set_xlabel('收益 ($)')
                axes[1, 0].set_ylabel('频次')
            
            # 关键指标
            metrics_text = f"""
总收益率: {result.total_return:.2%}
年化收益率: {result.annual_return:.2%}
最大回撤: {result.max_drawdown:.2%}
夏普比率: {result.sharpe_ratio:.2f}
胜率: {result.win_rate:.2%}
总交易次数: {result.total_trades}
            """
            axes[1, 1].text(0.1, 0.5, metrics_text, fontsize=12, 
                           verticalalignment='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('关键指标')
            axes[1, 1].axis('off')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"回测图表已保存到: {save_path}")
            
            plt.show()
            
        except Exception as e:
            self.logger.error(f"绘制回测结果失败: {e}")
    
    def compare_strategies(self, strategies: List, symbol: str, start_date: str, 
                         end_date: str, interval: str = '1h') -> pd.DataFrame:
        """比较多个策略的回测结果"""
        try:
            results = []
            
            for strategy in strategies:
                strategy_name = strategy.__class__.__name__
                self.logger.info(f"回测策略: {strategy_name}")
                
                result = self.run_backtest(strategy, symbol, start_date, end_date, interval)
                
                results.append({
                    '策略名称': strategy_name,
                    '总收益率': f"{result.total_return:.2%}",
                    '年化收益率': f"{result.annual_return:.2%}",
                    '最大回撤': f"{result.max_drawdown:.2%}",
                    '夏普比率': f"{result.sharpe_ratio:.2f}",
                    '胜率': f"{result.win_rate:.2%}",
                    '交易次数': result.total_trades,
                    '盈亏比': f"{result.profit_factor:.2f}"
                })
            
            comparison_df = pd.DataFrame(results)
            return comparison_df
            
        except Exception as e:
            self.logger.error(f"策略比较失败: {e}")
            return pd.DataFrame()