import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from backend.database import DatabaseManager
from backend.binance_client import BinanceClient

@dataclass
class RiskMetrics:
    """风险指标数据类"""
    portfolio_value: float
    daily_pnl: float
    daily_return: float
    volatility: float
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    max_drawdown: float
    sharpe_ratio: float
    beta: float
    correlation_btc: float

@dataclass
class PositionRisk:
    """单个持仓风险"""
    symbol: str
    quantity: float
    market_value: float
    weight: float  # 在投资组合中的权重
    volatility: float
    var_95: float
    beta: float
    correlation: float

class RiskManager:
    """风险管理器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.binance_client = BinanceClient()
        self.logger = logging.getLogger(__name__)
        
        # 风险参数配置
        self.max_position_weight = 0.2  # 单个资产最大权重20%
        self.max_portfolio_var = 0.05   # 投资组合最大VaR 5%
        self.max_daily_loss = 0.03      # 最大日损失3%
        self.max_drawdown = 0.15        # 最大回撤15%
        self.min_liquidity_ratio = 0.1  # 最小流动性比例10%
        
        # 相关性阈值
        self.max_correlation = 0.8      # 最大相关性0.8
        
    def calculate_position_size(self, symbol: str, signal_strength: float, 
                              current_price: float, portfolio_value: float,
                              volatility: float = None) -> float:
        """计算仓位大小"""
        try:
            # 获取资产波动率
            if volatility is None:
                volatility = self._calculate_volatility(symbol)
            
            # Kelly公式计算最优仓位
            win_rate = self._get_strategy_win_rate(symbol)
            avg_win = self._get_average_win(symbol)
            avg_loss = self._get_average_loss(symbol)
            
            if avg_loss > 0:
                kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # 限制在0-25%之间
            else:
                kelly_fraction = 0.1
            
            # 基于波动率调整
            volatility_adjustment = min(1.0, 0.2 / volatility) if volatility > 0 else 1.0
            
            # 基于信号强度调整
            signal_adjustment = min(1.0, abs(signal_strength))
            
            # 计算建议仓位
            suggested_weight = kelly_fraction * volatility_adjustment * signal_adjustment
            
            # 应用风险限制
            max_weight = self._get_max_position_weight(symbol, portfolio_value)
            final_weight = min(suggested_weight, max_weight)
            
            # 转换为实际数量
            position_value = portfolio_value * final_weight
            position_size = position_value / current_price
            
            self.logger.info(f"计算仓位 {symbol}: 权重={final_weight:.2%}, 数量={position_size:.6f}")
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"计算仓位大小失败: {e}")
            return 0.0
    
    def check_risk_limits(self, symbol: str, quantity: float, price: float) -> Tuple[bool, str]:
        """检查风险限制"""
        try:
            portfolio_value = self._get_portfolio_value()
            position_value = quantity * price
            
            # 检查单个资产权重限制
            weight = position_value / portfolio_value if portfolio_value > 0 else 0
            if weight > self.max_position_weight:
                return False, f"超过单个资产最大权重限制 {self.max_position_weight:.1%}"
            
            # 检查流动性
            if not self._check_liquidity(symbol, quantity):
                return False, "流动性不足"
            
            # 检查相关性
            if not self._check_correlation_limit(symbol):
                return False, "与现有持仓相关性过高"
            
            # 检查VaR限制
            projected_var = self._calculate_projected_var(symbol, quantity, price)
            if projected_var > self.max_portfolio_var:
                return False, f"超过投资组合VaR限制 {self.max_portfolio_var:.1%}"
            
            # 检查日损失限制
            current_daily_loss = self._get_current_daily_loss()
            if current_daily_loss > self.max_daily_loss:
                return False, f"超过日损失限制 {self.max_daily_loss:.1%}"
            
            return True, "风险检查通过"
            
        except Exception as e:
            self.logger.error(f"风险检查失败: {e}")
            return False, f"风险检查错误: {str(e)}"
    
    def calculate_stop_loss(self, symbol: str, entry_price: float, 
                          position_size: float, method: str = 'atr') -> float:
        """计算止损价格"""
        try:
            if method == 'atr':
                # 基于ATR的止损
                atr = self._get_atr(symbol)
                atr_multiplier = 2.0  # ATR倍数
                stop_loss = entry_price - (atr * atr_multiplier)
                
            elif method == 'percentage':
                # 基于百分比的止损
                stop_loss_pct = 0.02  # 2%止损
                stop_loss = entry_price * (1 - stop_loss_pct)
                
            elif method == 'support':
                # 基于支撑位的止损
                support_level = self._find_support_level(symbol)
                stop_loss = support_level * 0.99  # 支撑位下方1%
                
            else:
                # 默认2%止损
                stop_loss = entry_price * 0.98
            
            # 确保止损价格合理
            min_stop_loss = entry_price * 0.95  # 最大5%止损
            max_stop_loss = entry_price * 0.99  # 最小1%止损
            
            stop_loss = max(min_stop_loss, min(stop_loss, max_stop_loss))
            
            self.logger.info(f"计算止损 {symbol}: 入场价={entry_price:.4f}, 止损价={stop_loss:.4f}")
            
            return stop_loss
            
        except Exception as e:
            self.logger.error(f"计算止损失败: {e}")
            return entry_price * 0.98  # 默认2%止损
    
    def calculate_take_profit(self, symbol: str, entry_price: float, 
                            stop_loss: float, risk_reward_ratio: float = 2.0) -> float:
        """计算止盈价格"""
        try:
            # 基于风险回报比计算止盈
            risk = entry_price - stop_loss
            reward = risk * risk_reward_ratio
            take_profit = entry_price + reward
            
            # 检查阻力位
            resistance_level = self._find_resistance_level(symbol)
            if resistance_level > 0 and take_profit > resistance_level:
                take_profit = resistance_level * 0.99  # 阻力位下方1%
            
            self.logger.info(f"计算止盈 {symbol}: 入场价={entry_price:.4f}, 止盈价={take_profit:.4f}")
            
            return take_profit
            
        except Exception as e:
            self.logger.error(f"计算止盈失败: {e}")
            return entry_price * 1.04  # 默认4%止盈
    
    def calculate_portfolio_risk(self) -> RiskMetrics:
        """计算投资组合风险指标"""
        try:
            positions = self.db_manager.get_positions()
            if not positions:
                return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            
            # 获取投资组合价值
            portfolio_value = self._get_portfolio_value()
            
            # 计算日收益率
            daily_returns = self._get_portfolio_daily_returns()
            
            if len(daily_returns) < 2:
                return RiskMetrics(portfolio_value, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            
            # 计算风险指标
            daily_pnl = daily_returns.iloc[-1] if len(daily_returns) > 0 else 0
            daily_return = daily_pnl / portfolio_value if portfolio_value > 0 else 0
            volatility = daily_returns.std() * np.sqrt(252)  # 年化波动率
            
            # VaR计算
            var_95 = np.percentile(daily_returns, 5)
            var_99 = np.percentile(daily_returns, 1)
            
            # 最大回撤
            cumulative_returns = (1 + daily_returns).cumprod()
            peak = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = drawdown.min()
            
            # 夏普比率
            risk_free_rate = 0.02 / 252  # 日无风险利率
            excess_returns = daily_returns - risk_free_rate
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            
            # Beta和相关性（相对于BTC）
            btc_returns = self._get_btc_returns()
            if len(btc_returns) > 0 and len(daily_returns) > 0:
                # 对齐数据
                common_dates = daily_returns.index.intersection(btc_returns.index)
                if len(common_dates) > 10:
                    portfolio_aligned = daily_returns.loc[common_dates]
                    btc_aligned = btc_returns.loc[common_dates]
                    
                    correlation_btc = portfolio_aligned.corr(btc_aligned)
                    beta = portfolio_aligned.cov(btc_aligned) / btc_aligned.var()
                else:
                    correlation_btc = 0
                    beta = 1
            else:
                correlation_btc = 0
                beta = 1
            
            return RiskMetrics(
                portfolio_value=portfolio_value,
                daily_pnl=daily_pnl,
                daily_return=daily_return,
                volatility=volatility,
                var_95=var_95,
                var_99=var_99,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                beta=beta,
                correlation_btc=correlation_btc
            )
            
        except Exception as e:
            self.logger.error(f"计算投资组合风险失败: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    def get_position_risks(self) -> List[PositionRisk]:
        """获取各持仓的风险指标"""
        try:
            positions = self.db_manager.get_positions()
            portfolio_value = self._get_portfolio_value()
            position_risks = []
            
            for position in positions:
                current_price = self.binance_client.get_ticker_price(position.symbol)
                if not current_price:
                    continue
                
                market_value = position.quantity * current_price
                weight = market_value / portfolio_value if portfolio_value > 0 else 0
                
                # 计算个股风险指标
                volatility = self._calculate_volatility(position.symbol)
                returns = self._get_asset_returns(position.symbol)
                
                var_95 = 0
                beta = 1
                correlation = 0
                
                if len(returns) > 10:
                    var_95 = np.percentile(returns, 5) * market_value
                    
                    # 计算Beta和相关性
                    btc_returns = self._get_btc_returns()
                    if len(btc_returns) > 0:
                        common_dates = returns.index.intersection(btc_returns.index)
                        if len(common_dates) > 10:
                            asset_aligned = returns.loc[common_dates]
                            btc_aligned = btc_returns.loc[common_dates]
                            
                            correlation = asset_aligned.corr(btc_aligned)
                            beta = asset_aligned.cov(btc_aligned) / btc_aligned.var()
                
                position_risk = PositionRisk(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    market_value=market_value,
                    weight=weight,
                    volatility=volatility,
                    var_95=var_95,
                    beta=beta,
                    correlation=correlation
                )
                
                position_risks.append(position_risk)
            
            return position_risks
            
        except Exception as e:
            self.logger.error(f"获取持仓风险失败: {e}")
            return []
    
    def generate_risk_report(self) -> str:
        """生成风险报告"""
        try:
            portfolio_risk = self.calculate_portfolio_risk()
            position_risks = self.get_position_risks()
            
            report = f"""
=== 投资组合风险报告 ===
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 投资组合概况 ===
总资产价值: ${portfolio_risk.portfolio_value:,.2f}
今日盈亏: ${portfolio_risk.daily_pnl:,.2f} ({portfolio_risk.daily_return:.2%})
年化波动率: {portfolio_risk.volatility:.2%}
夏普比率: {portfolio_risk.sharpe_ratio:.2f}
最大回撤: {portfolio_risk.max_drawdown:.2%}

=== 风险指标 ===
95% VaR: ${portfolio_risk.var_95:,.2f}
99% VaR: ${portfolio_risk.var_99:,.2f}
Beta (vs BTC): {portfolio_risk.beta:.2f}
与BTC相关性: {portfolio_risk.correlation_btc:.2f}

=== 持仓风险分析 ===
"""
            
            for risk in position_risks:
                report += f"""
{risk.symbol}:
  持仓数量: {risk.quantity:.6f}
  市值: ${risk.market_value:,.2f}
  权重: {risk.weight:.2%}
  波动率: {risk.volatility:.2%}
  95% VaR: ${risk.var_95:,.2f}
  Beta: {risk.beta:.2f}
  相关性: {risk.correlation:.2f}
"""
            
            # 风险警告
            warnings = self._generate_risk_warnings(portfolio_risk, position_risks)
            if warnings:
                report += "\n=== 风险警告 ===\n"
                for warning in warnings:
                    report += f"⚠️ {warning}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成风险报告失败: {e}")
            return "风险报告生成失败"
    
    def _generate_risk_warnings(self, portfolio_risk: RiskMetrics, 
                              position_risks: List[PositionRisk]) -> List[str]:
        """生成风险警告"""
        warnings = []
        
        # 检查投资组合风险
        if abs(portfolio_risk.var_95) > self.max_portfolio_var * portfolio_risk.portfolio_value:
            warnings.append(f"投资组合VaR超过限制: {abs(portfolio_risk.var_95):,.2f}")
        
        if abs(portfolio_risk.max_drawdown) > self.max_drawdown:
            warnings.append(f"最大回撤超过限制: {portfolio_risk.max_drawdown:.2%}")
        
        if portfolio_risk.volatility > 0.5:  # 50%年化波动率
            warnings.append(f"投资组合波动率过高: {portfolio_risk.volatility:.2%}")
        
        # 检查持仓风险
        for risk in position_risks:
            if risk.weight > self.max_position_weight:
                warnings.append(f"{risk.symbol} 权重超过限制: {risk.weight:.2%}")
            
            if abs(risk.correlation) > self.max_correlation:
                warnings.append(f"{risk.symbol} 与BTC相关性过高: {risk.correlation:.2f}")
        
        # 检查集中度风险
        total_weight = sum(risk.weight for risk in position_risks)
        if total_weight > 0.8:  # 80%以上资金投入
            warnings.append(f"资金使用率过高: {total_weight:.2%}")
        
        return warnings
    
    # 辅助方法
    def _get_portfolio_value(self) -> float:
        """获取投资组合总价值"""
        try:
            positions = self.db_manager.get_positions()
            total_value = 0
            
            for position in positions:
                current_price = self.binance_client.get_ticker_price(position.symbol)
                if current_price:
                    total_value += position.quantity * current_price
            
            # 加上现金余额
            cash_balance = self.binance_client.get_balance('USDT')
            total_value += cash_balance
            
            return total_value
            
        except Exception as e:
            self.logger.error(f"获取投资组合价值失败: {e}")
            return 0.0
    
    def _calculate_volatility(self, symbol: str, days: int = 30) -> float:
        """计算资产波动率"""
        try:
            from backend.data_collector import DataCollector
            data_collector = DataCollector()
            data = data_collector.get_market_data(symbol, '1d', limit=days)
            
            if len(data) < 2:
                return 0.2  # 默认20%波动率
            
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(365)  # 年化波动率
            
            return volatility
            
        except Exception as e:
            self.logger.error(f"计算波动率失败: {e}")
            return 0.2
    
    def _get_strategy_win_rate(self, symbol: str) -> float:
        """获取策略胜率"""
        try:
            trades = self.db_manager.session.query(self.db_manager.Trade).filter_by(
                symbol=symbol
            ).limit(100).all()
            
            if not trades:
                return 0.5  # 默认50%胜率
            
            winning_trades = len([t for t in trades if t.profit_loss > 0])
            return winning_trades / len(trades)
            
        except Exception as e:
            self.logger.error(f"获取策略胜率失败: {e}")
            return 0.5
    
    def _get_average_win(self, symbol: str) -> float:
        """获取平均盈利"""
        try:
            trades = self.db_manager.session.query(self.db_manager.Trade).filter_by(
                symbol=symbol
            ).filter(self.db_manager.Trade.profit_loss > 0).limit(50).all()
            
            if not trades:
                return 0.02  # 默认2%
            
            return sum(t.profit_loss for t in trades) / len(trades)
            
        except Exception as e:
            self.logger.error(f"获取平均盈利失败: {e}")
            return 0.02
    
    def _get_average_loss(self, symbol: str) -> float:
        """获取平均亏损"""
        try:
            trades = self.db_manager.session.query(self.db_manager.Trade).filter_by(
                symbol=symbol
            ).filter(self.db_manager.Trade.profit_loss < 0).limit(50).all()
            
            if not trades:
                return 0.01  # 默认1%
            
            return abs(sum(t.profit_loss for t in trades) / len(trades))
            
        except Exception as e:
            self.logger.error(f"获取平均亏损失败: {e}")
            return 0.01
    
    def _get_max_position_weight(self, symbol: str, portfolio_value: float) -> float:
        """获取最大持仓权重"""
        # 基于流动性和波动率调整最大权重
        volatility = self._calculate_volatility(symbol)
        
        # 高波动率资产降低权重
        volatility_adjustment = min(1.0, 0.3 / volatility) if volatility > 0 else 1.0
        
        return self.max_position_weight * volatility_adjustment
    
    def _check_liquidity(self, symbol: str, quantity: float) -> bool:
        """检查流动性"""
        try:
            # 获取24小时成交量
            ticker = self.binance_client.client.get_ticker(symbol=symbol)
            volume_24h = float(ticker['volume'])
            
            # 检查交易量是否足够
            current_price = self.binance_client.get_ticker_price(symbol)
            trade_value = quantity * current_price
            
            # 交易量不应超过24小时成交量的1%
            return trade_value < volume_24h * current_price * 0.01
            
        except Exception as e:
            self.logger.error(f"检查流动性失败: {e}")
            return True  # 默认通过
    
    def _check_correlation_limit(self, symbol: str) -> bool:
        """检查相关性限制"""
        try:
            positions = self.db_manager.get_positions()
            if not positions:
                return True
            
            new_asset_returns = self._get_asset_returns(symbol)
            if len(new_asset_returns) < 10:
                return True
            
            for position in positions:
                existing_returns = self._get_asset_returns(position.symbol)
                if len(existing_returns) < 10:
                    continue
                
                # 计算相关性
                common_dates = new_asset_returns.index.intersection(existing_returns.index)
                if len(common_dates) > 10:
                    correlation = new_asset_returns.loc[common_dates].corr(
                        existing_returns.loc[common_dates]
                    )
                    
                    if abs(correlation) > self.max_correlation:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查相关性失败: {e}")
            return True
    
    def _calculate_projected_var(self, symbol: str, quantity: float, price: float) -> float:
        """计算预期VaR"""
        try:
            # 简化计算：基于历史波动率
            volatility = self._calculate_volatility(symbol)
            position_value = quantity * price
            
            # 95% VaR = 1.65 * 波动率 * 头寸价值
            var_95 = 1.65 * volatility * position_value / np.sqrt(252)  # 日VaR
            
            return var_95
            
        except Exception as e:
            self.logger.error(f"计算预期VaR失败: {e}")
            return 0.0
    
    def _get_current_daily_loss(self) -> float:
        """获取当前日损失"""
        try:
            today = datetime.now().date()
            trades_today = self.db_manager.session.query(self.db_manager.Trade).filter(
                self.db_manager.Trade.timestamp >= today
            ).all()
            
            total_loss = sum(t.profit_loss for t in trades_today if t.profit_loss < 0)
            portfolio_value = self._get_portfolio_value()
            
            return abs(total_loss) / portfolio_value if portfolio_value > 0 else 0
            
        except Exception as e:
            self.logger.error(f"获取当前日损失失败: {e}")
            return 0.0
    
    def _get_atr(self, symbol: str, period: int = 14) -> float:
        """获取ATR指标"""
        try:
            from backend.data_collector import DataCollector
            data_collector = DataCollector()
            indicators = data_collector.get_technical_indicators(symbol, limit=period + 5)
            
            if not indicators.empty and 'atr' in indicators.columns:
                return indicators['atr'].iloc[-1]
            
            # 如果没有ATR数据，基于价格计算简单ATR
            data = data_collector.get_market_data(symbol, '1d', limit=period + 5)
            if len(data) < period:
                return 0.02  # 默认2%
            
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            return atr
            
        except Exception as e:
            self.logger.error(f"获取ATR失败: {e}")
            return 0.02
    
    def _find_support_level(self, symbol: str) -> float:
        """寻找支撑位"""
        try:
            from backend.data_collector import DataCollector
            data_collector = DataCollector()
            data = data_collector.get_market_data(symbol, '1d', limit=50)
            
            if len(data) < 10:
                return 0
            
            # 简单支撑位：最近20天的最低价
            support = data['low'].tail(20).min()
            return support
            
        except Exception as e:
            self.logger.error(f"寻找支撑位失败: {e}")
            return 0
    
    def _find_resistance_level(self, symbol: str) -> float:
        """寻找阻力位"""
        try:
            from backend.data_collector import DataCollector
            data_collector = DataCollector()
            data = data_collector.get_market_data(symbol, '1d', limit=50)
            
            if len(data) < 10:
                return 0
            
            # 简单阻力位：最近20天的最高价
            resistance = data['high'].tail(20).max()
            return resistance
            
        except Exception as e:
            self.logger.error(f"寻找阻力位失败: {e}")
            return 0
    
    def _get_portfolio_daily_returns(self) -> pd.Series:
        """获取投资组合日收益率"""
        try:
            # 这里需要实现投资组合历史价值的计算
            # 简化实现：基于交易记录计算
            trades = self.db_manager.get_trades(limit=100)
            
            if not trades:
                return pd.Series()
            
            # 按日期分组计算日收益
            daily_pnl = {}
            for trade in trades:
                date = trade.timestamp.date()
                if date not in daily_pnl:
                    daily_pnl[date] = 0
                daily_pnl[date] += trade.profit_loss
            
            dates = sorted(daily_pnl.keys())
            returns = [daily_pnl[date] for date in dates]
            
            return pd.Series(returns, index=dates)
            
        except Exception as e:
            self.logger.error(f"获取投资组合日收益率失败: {e}")
            return pd.Series()
    
    def _get_btc_returns(self) -> pd.Series:
        """获取BTC收益率"""
        try:
            from backend.data_collector import DataCollector
            data_collector = DataCollector()
            data = data_collector.get_market_data('BTCUSDT', '1d', limit=100)
            
            if data.empty:
                return pd.Series()
            
            returns = data['close'].pct_change().dropna()
            returns.index = data['timestamp'].iloc[1:].dt.date
            
            return returns
            
        except Exception as e:
            self.logger.error(f"获取BTC收益率失败: {e}")
            return pd.Series()
    
    def _get_asset_returns(self, symbol: str) -> pd.Series:
        """获取资产收益率"""
        try:
            from backend.data_collector import DataCollector
            data_collector = DataCollector()
            data = data_collector.get_market_data(symbol, '1d', limit=100)
            
            if data.empty:
                return pd.Series()
            
            returns = data['close'].pct_change().dropna()
            returns.index = data['timestamp'].iloc[1:].dt.date
            
            return returns
            
        except Exception as e:
            self.logger.error(f"获取资产收益率失败: {e}")
            return pd.Series()