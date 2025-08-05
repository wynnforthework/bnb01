import logging
import time
from datetime import datetime
from typing import Dict, List
from backend.binance_client import BinanceClient
from backend.database import DatabaseManager
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
from config.config import Config

class TradingEngine:
    """交易引擎"""
    
    def __init__(self):
        self.config = Config()
        self.binance_client = BinanceClient()
        self.db_manager = DatabaseManager()
        self.strategies = {}
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
        # 初始化策略
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """初始化交易策略"""
        for symbol in self.config.DEFAULT_SYMBOLS:
            # MA策略
            ma_strategy = MovingAverageStrategy(
                symbol=symbol,
                parameters={
                    'short_window': 10,
                    'long_window': 30,
                    'stop_loss': 0.02,
                    'take_profit': 0.05,
                    'position_size': 0.05
                }
            )
            self.strategies[f"{symbol}_MA"] = ma_strategy
            
            # RSI策略
            rsi_strategy = RSIStrategy(
                symbol=symbol,
                parameters={
                    'rsi_period': 14,
                    'oversold': 30,
                    'overbought': 70,
                    'stop_loss': 0.02,
                    'take_profit': 0.05,
                    'position_size': 0.05
                }
            )
            self.strategies[f"{symbol}_RSI"] = rsi_strategy
    
    def start_trading(self):
        """启动交易"""
        self.is_running = True
        self.logger.info("交易引擎启动")
        
        while self.is_running:
            try:
                self._execute_trading_cycle()
                time.sleep(60)  # 每分钟执行一次
            except Exception as e:
                self.logger.error(f"交易循环错误: {e}")
                time.sleep(10)
    
    def stop_trading(self):
        """停止交易"""
        self.is_running = False
        self.logger.info("交易引擎停止")
    
    def _execute_trading_cycle(self):
        """执行交易循环"""
        for strategy_name, strategy in self.strategies.items():
            try:
                # 获取市场数据
                data = self.binance_client.get_klines(
                    symbol=strategy.symbol,
                    interval=self.config.DEFAULT_TIMEFRAME,
                    limit=100
                )
                
                if data is None or len(data) == 0:
                    continue
                
                current_price = data['close'].iloc[-1]
                
                # 检查止损止盈
                if strategy.should_stop_loss(current_price):
                    self._execute_trade(strategy, 'CLOSE', current_price, 'STOP_LOSS')
                    continue
                
                if strategy.should_take_profit(current_price):
                    self._execute_trade(strategy, 'CLOSE', current_price, 'TAKE_PROFIT')
                    continue
                
                # 生成交易信号
                signal = strategy.generate_signal(data)
                
                if signal in ['BUY', 'SELL']:
                    self._execute_trade(strategy, signal, current_price, 'SIGNAL')
                    
            except Exception as e:
                self.logger.error(f"策略 {strategy_name} 执行错误: {e}")
    
    def _execute_trade(self, strategy, action, price, reason):
        """执行交易"""
        try:
            balance = self.binance_client.get_balance('USDT')
            
            if action == 'BUY' and strategy.position <= 0:
                quantity = strategy.calculate_position_size(price, balance)
                if quantity > 0:
                    order = self.binance_client.place_order(
                        symbol=strategy.symbol,
                        side='BUY',
                        quantity=quantity
                    )
                    if order:
                        strategy.update_position('BUY', quantity, price)
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__
                        )
                        self.logger.info(f"买入 {strategy.symbol}: {quantity} @ {price}")
            
            elif action == 'SELL' and strategy.position >= 0:
                if strategy.position > 0:
                    quantity = strategy.position
                    order = self.binance_client.place_order(
                        symbol=strategy.symbol,
                        side='SELL',
                        quantity=quantity
                    )
                    if order:
                        profit_loss = (price - strategy.entry_price) * quantity
                        strategy.close_position()
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__,
                            profit_loss=profit_loss
                        )
                        self.logger.info(f"卖出 {strategy.symbol}: {quantity} @ {price}, P&L: {profit_loss}")
            
            elif action == 'CLOSE':
                if strategy.position != 0:
                    side = 'SELL' if strategy.position > 0 else 'BUY'
                    quantity = abs(strategy.position)
                    order = self.binance_client.place_order(
                        symbol=strategy.symbol,
                        side=side,
                        quantity=quantity
                    )
                    if order:
                        profit_loss = (price - strategy.entry_price) * strategy.position
                        strategy.close_position()
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side=side,
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__,
                            profit_loss=profit_loss
                        )
                        self.logger.info(f"{reason} 平仓 {strategy.symbol}: {quantity} @ {price}, P&L: {profit_loss}")
                        
        except Exception as e:
            self.logger.error(f"执行交易失败: {e}")
    
    def get_portfolio_status(self):
        """获取投资组合状态"""
        positions = self.db_manager.get_positions()
        total_value = 0
        portfolio = []
        
        for position in positions:
            current_price = self.binance_client.get_ticker_price(position.symbol)
            if current_price:
                market_value = position.quantity * current_price
                unrealized_pnl = (current_price - position.avg_price) * position.quantity
                total_value += market_value
                
                portfolio.append({
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'avg_price': position.avg_price,
                    'current_price': current_price,
                    'market_value': market_value,
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_percent': (unrealized_pnl / (position.avg_price * position.quantity)) * 100
                })
        
        return {
            'positions': portfolio,
            'total_value': total_value,
            'cash_balance': self.binance_client.get_balance('USDT')
        }