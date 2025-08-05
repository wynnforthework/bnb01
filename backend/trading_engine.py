import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, List
from backend.binance_client import BinanceClient
from backend.database import DatabaseManager
from backend.data_collector import DataCollector
from backend.risk_manager import RiskManager
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.ml_strategy import MLStrategy, LSTMStrategy
from config.config import Config

class TradingEngine:
    """增强版交易引擎"""
    
    def __init__(self):
        self.config = Config()
        self.binance_client = BinanceClient()
        self.db_manager = DatabaseManager()
        self.data_collector = DataCollector()
        self.risk_manager = RiskManager()
        self.strategies = {}
        self.is_running = False
        self.data_collection_running = False
        self.logger = logging.getLogger(__name__)
        
        # 初始化策略
        self._initialize_strategies()
        
        # 启动数据收集
        self._start_data_collection()
    
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
                    'position_size': 0.03
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
                    'position_size': 0.03
                }
            )
            self.strategies[f"{symbol}_RSI"] = rsi_strategy
            
            # 机器学习策略
            ml_strategy = MLStrategy(
                symbol=symbol,
                parameters={
                    'model_type': 'random_forest',
                    'lookback_period': 20,
                    'prediction_horizon': 1,
                    'min_confidence': 0.65,
                    'up_threshold': 0.015,
                    'down_threshold': -0.015,
                    'stop_loss': 0.025,
                    'take_profit': 0.06,
                    'position_size': 0.04
                }
            )
            self.strategies[f"{symbol}_ML"] = ml_strategy
            
            # LSTM策略（可选）
            lstm_strategy = LSTMStrategy(
                symbol=symbol,
                parameters={
                    'sequence_length': 60,
                    'prediction_horizon': 1,
                    'epochs': 30,
                    'batch_size': 32,
                    'min_confidence': 0.7,
                    'stop_loss': 0.03,
                    'take_profit': 0.08,
                    'position_size': 0.02
                }
            )
            self.strategies[f"{symbol}_LSTM"] = lstm_strategy
    
    def _start_data_collection(self):
        """启动数据收集"""
        try:
            self.data_collection_running = True
            # 在后台启动数据收集
            import threading
            data_thread = threading.Thread(target=self._run_data_collection)
            data_thread.daemon = True
            data_thread.start()
            self.logger.info("数据收集已启动")
        except Exception as e:
            self.logger.error(f"启动数据收集失败: {e}")
    
    def _run_data_collection(self):
        """运行数据收集循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                self.data_collector.start_real_time_collection(
                    symbols=self.config.DEFAULT_SYMBOLS,
                    intervals=['1m', '5m', '1h']
                )
            )
        except Exception as e:
            self.logger.error(f"数据收集循环错误: {e}")
        finally:
            loop.close()
    
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
        """执行增强版交易循环"""
        # 首先检查整体风险状况
        portfolio_risk = self.risk_manager.calculate_portfolio_risk()
        
        # 如果风险过高，暂停新开仓
        risk_warnings = self.risk_manager._generate_risk_warnings(
            portfolio_risk, 
            self.risk_manager.get_position_risks()
        )
        
        if len(risk_warnings) > 3:  # 风险警告过多
            self.logger.warning("风险警告过多，暂停新开仓")
            return
        
        for strategy_name, strategy in self.strategies.items():
            try:
                # 获取增强的市场数据
                data = self._get_enhanced_market_data(strategy.symbol)
                
                if data is None or len(data) == 0:
                    continue
                
                current_price = data['close'].iloc[-1]
                
                # 检查止损止盈（使用风险管理器计算的动态止损止盈）
                if strategy.position != 0:
                    if self._should_close_position(strategy, current_price):
                        continue
                
                # 生成交易信号
                signal = strategy.generate_signal(data)
                
                if signal in ['BUY', 'SELL']:
                    # 风险检查
                    if self._risk_check_passed(strategy, signal, current_price):
                        self._execute_enhanced_trade(strategy, signal, current_price, 'SIGNAL')
                    
            except Exception as e:
                self.logger.error(f"策略 {strategy_name} 执行错误: {e}")
    
    def _get_enhanced_market_data(self, symbol: str):
        """获取增强的市场数据"""
        try:
            # 优先从数据库获取
            data = self.data_collector.get_market_data(symbol, self.config.DEFAULT_TIMEFRAME, limit=200)
            
            if data.empty or len(data) < 50:
                # 如果数据库数据不足，从API获取
                data = self.binance_client.get_klines(
                    symbol=symbol,
                    interval=self.config.DEFAULT_TIMEFRAME,
                    limit=200
                )
            
            if not data.empty:
                # 计算技术指标
                data = self.data_collector.calculate_technical_indicators(data, symbol)
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取增强市场数据失败: {e}")
            return None
    
    def _should_close_position(self, strategy, current_price: float) -> bool:
        """检查是否应该平仓"""
        try:
            # 使用风险管理器的动态止损止盈
            if strategy.position > 0:  # 多头持仓
                # 动态止损
                stop_loss_price = self.risk_manager.calculate_stop_loss(
                    strategy.symbol, strategy.entry_price, strategy.position, method='atr'
                )
                
                # 动态止盈
                take_profit_price = self.risk_manager.calculate_take_profit(
                    strategy.symbol, strategy.entry_price, stop_loss_price, risk_reward_ratio=2.5
                )
                
                if current_price <= stop_loss_price:
                    self._execute_enhanced_trade(strategy, 'CLOSE', current_price, 'DYNAMIC_STOP_LOSS')
                    return True
                elif current_price >= take_profit_price:
                    self._execute_enhanced_trade(strategy, 'CLOSE', current_price, 'DYNAMIC_TAKE_PROFIT')
                    return True
            
            elif strategy.position < 0:  # 空头持仓
                # 空头止损止盈逻辑
                stop_loss_price = strategy.entry_price * 1.02  # 简化处理
                take_profit_price = strategy.entry_price * 0.95
                
                if current_price >= stop_loss_price:
                    self._execute_enhanced_trade(strategy, 'CLOSE', current_price, 'SHORT_STOP_LOSS')
                    return True
                elif current_price <= take_profit_price:
                    self._execute_enhanced_trade(strategy, 'CLOSE', current_price, 'SHORT_TAKE_PROFIT')
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查平仓条件失败: {e}")
            return False
    
    def _risk_check_passed(self, strategy, signal: str, current_price: float) -> bool:
        """风险检查"""
        try:
            # 计算建议仓位大小
            portfolio_value = self.risk_manager._get_portfolio_value()
            suggested_quantity = self.risk_manager.calculate_position_size(
                strategy.symbol, 1.0, current_price, portfolio_value
            )
            
            if suggested_quantity <= 0:
                return False
            
            # 风险限制检查
            passed, message = self.risk_manager.check_risk_limits(
                strategy.symbol, suggested_quantity, current_price
            )
            
            if not passed:
                self.logger.warning(f"风险检查未通过 {strategy.symbol}: {message}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"风险检查失败: {e}")
            return False
    
    def _execute_enhanced_trade(self, strategy, action: str, price: float, reason: str):
        """执行增强版交易"""
        try:
            balance = self.binance_client.get_balance('USDT')
            portfolio_value = self.risk_manager._get_portfolio_value()
            
            if action == 'BUY' and strategy.position <= 0:
                # 使用风险管理器计算仓位大小
                quantity = self.risk_manager.calculate_position_size(
                    strategy.symbol, 1.0, price, portfolio_value
                )
                
                if quantity > 0:
                    # 再次风险检查
                    passed, message = self.risk_manager.check_risk_limits(
                        strategy.symbol, quantity, price
                    )
                    
                    if not passed:
                        self.logger.warning(f"交易前风险检查失败: {message}")
                        return
                    
                    order = self.binance_client.place_order(
                        symbol=strategy.symbol,
                        side='BUY',
                        quantity=quantity
                    )
                    
                    if order:
                        strategy.update_position('BUY', quantity, price)
                        
                        # 计算止损止盈价格
                        stop_loss = self.risk_manager.calculate_stop_loss(
                            strategy.symbol, price, quantity, method='atr'
                        )
                        take_profit = self.risk_manager.calculate_take_profit(
                            strategy.symbol, price, stop_loss, risk_reward_ratio=2.5
                        )
                        
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__
                        )
                        
                        self.logger.info(f"买入 {strategy.symbol}: {quantity:.6f} @ ${price:.4f}")
                        self.logger.info(f"  止损: ${stop_loss:.4f}, 止盈: ${take_profit:.4f}")
            
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
                        
                        self.logger.info(f"卖出 {strategy.symbol}: {quantity:.6f} @ ${price:.4f}, P&L: ${profit_loss:.2f}")
            
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
                        
                        self.logger.info(f"{reason} 平仓 {strategy.symbol}: {quantity:.6f} @ ${price:.4f}, P&L: ${profit_loss:.2f}")
                        
        except Exception as e:
            self.logger.error(f"执行增强交易失败: {e}")
    
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