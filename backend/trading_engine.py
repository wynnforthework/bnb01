import logging
import time
import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, List
from backend.binance_client import BinanceClient
from backend.database import DatabaseManager
from backend.data_collector import DataCollector
from backend.risk_manager import RiskManager
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.ml_strategy import MLStrategy, LSTMStrategy
from strategies.chanlun_strategy import ChanlunStrategy
from config.config import Config

class TradingEngine:
    """增强版交易引擎 - 支持现货和合约交易"""
    
    def __init__(self, trading_mode='SPOT', leverage=10, selected_symbols=None, enabled_strategies=None):
        """
        初始化交易引擎
        
        Args:
            trading_mode: 'SPOT' 现货交易, 'FUTURES' 合约交易
            leverage: 合约交易杠杆倍数 (仅合约模式有效)
            selected_symbols: 用户选择的币种列表，如果为None则使用默认配置
            enabled_strategies: 启用的策略列表，如果为None则使用所有策略
        """
        self.config = Config()
        self.trading_mode = trading_mode.upper()
        self.leverage = leverage
        
        # 用户选择的币种和策略
        self.selected_symbols = selected_symbols or self.config.DEFAULT_SYMBOLS
        self.enabled_strategies = enabled_strategies or ['MA', 'RSI', 'ML', 'Chanlun']
        
        # 使用客户端管理器避免重复初始化
        from backend.client_manager import client_manager
        self.binance_client = client_manager.get_client(self.trading_mode)
        self.db_manager = DatabaseManager()
        self.data_collector = DataCollector()
        self.risk_manager = RiskManager()
        
        self.strategies = {}
        self.is_running = False
        self.data_collection_running = False
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"交易引擎初始化完成，模式: {self.trading_mode}")
        self.logger.info(f"选择的币种: {self.selected_symbols}")
        self.logger.info(f"启用的策略: {self.enabled_strategies}")
        
        if self.trading_mode == 'FUTURES':
            self.logger.info(f"合约杠杆: {self.leverage}x")
            # 初始化合约设置
            self._initialize_futures_settings()
        
        # 初始化策略
        self._initialize_strategies()
        
        # 启动数据收集
        self._start_data_collection()
    
    def _initialize_futures_settings(self):
        """初始化合约交易设置"""
        try:
            # 设置持仓模式为双向持仓
            self.binance_client.set_position_mode(dual_side_position=True)
            
            # 只为用户选择的币种设置合约参数
            for symbol in self.selected_symbols:
                try:
                    # 设置保证金模式为逐仓（静默处理已设置的情况）
                    margin_result = self.binance_client.set_margin_type(symbol, 'ISOLATED')
                    
                    # 设置杠杆
                    leverage_result = self.binance_client.set_leverage(symbol, self.leverage)
                    
                    if margin_result and leverage_result:
                        self.logger.info(f"合约设置完成 {symbol}: {self.leverage}x 逐仓")
                    else:
                        self.logger.warning(f"合约设置部分失败 {symbol}")
                    
                except Exception as e:
                    self.logger.warning(f"设置合约参数失败 {symbol}: {e}")
            
            self.logger.info("合约交易设置初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化合约设置失败: {e}")
    
    def _check_liquidity(self, symbol: str) -> bool:
        """检查交易对流动性"""
        try:
            order_book = self.binance_client.client.futures_order_book(symbol=symbol, limit=5)
            bid_price = float(order_book['bids'][0][0])
            ask_price = float(order_book['asks'][0][0])
            spread = ask_price - bid_price
            spread_percent = (spread / bid_price) * 100
            
            # 如果价差超过5%，认为流动性不足
            if spread_percent > 5:
                self.logger.warning(f"流动性不足 {symbol}: 价差 {spread_percent:.2f}%")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"检查流动性失败 {symbol}: {e}")
            return False
    
    def _get_safe_quantity(self, symbol: str, price: float, position_size: float = 0.02) -> float:
        """获取安全的订单数量"""
        try:
            # 获取账户余额
            account = self.binance_client.get_account_balance()
            available_balance = float(account['availableBalance'])
            
            # 计算仓位价值
            position_value = available_balance * position_size
            
            # 获取交易对信息
            symbol_info = self.binance_client._get_symbol_info(symbol)
            if symbol_info:
                # 获取最小数量
                min_qty = None
                for f in symbol_info['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        min_qty = float(f['minQty'])
                        break
                
                if min_qty:
                    # 计算订单数量
                    quantity = position_value * self.leverage / price
                    
                    # 确保数量不小于最小数量的10倍
                    safe_min_qty = min_qty * 10
                    if quantity < safe_min_qty:
                        quantity = safe_min_qty
                    
                    self.logger.info(f"安全订单数量 {symbol}: {quantity} (最小: {safe_min_qty})")
                    return quantity
            
            # 默认计算
            quantity = position_value * self.leverage / price
            return max(quantity, 0.001)  # 至少0.001
            
        except Exception as e:
            self.logger.error(f"计算安全数量失败 {symbol}: {e}")
            return 0.001  # 默认最小数量
    
    def _initialize_strategies(self):
        """初始化交易策略 - 只为用户选择的币种创建策略"""
        # 验证用户选择的交易对有效性
        valid_symbols = []
        for symbol in self.selected_symbols:
            if self.binance_client._is_valid_symbol(symbol):
                # 进一步验证是否能获取数据
                try:
                    test_data = self.binance_client.get_klines(symbol, '1h', 1)
                    if test_data is not None and not test_data.empty:
                        valid_symbols.append(symbol)
                        self.logger.info(f"验证交易对 {symbol}: 有效")
                    else:
                        self.logger.warning(f"验证交易对 {symbol}: 无法获取数据")
                except Exception as e:
                    self.logger.warning(f"验证交易对 {symbol} 失败: {e}")
            else:
                self.logger.warning(f"交易对格式无效: {symbol}")
        
        if not valid_symbols:
            self.logger.error("没有找到有效的交易对，使用默认配置")
            valid_symbols = ['BTCUSDT', 'ETHUSDT']  # 最基本的交易对
        
        # 只为用户选择的币种创建策略
        for symbol in valid_symbols:
            # 根据启用的策略类型创建策略
            if 'MA' in self.enabled_strategies:
                # MA策略 - 使用更敏感的参数
                ma_strategy = MovingAverageStrategy(
                    symbol=symbol,
                    parameters={
                        'short_window': 5,   # 更短的窗口，更敏感
                        'long_window': 15,   # 更短的窗口，更敏感
                        'stop_loss': 0.02,
                        'take_profit': 0.04, # 降低止盈目标
                        'position_size': 0.03
                    }
                )
                self.strategies[f"{symbol}_MA"] = ma_strategy
            
            if 'RSI' in self.enabled_strategies:
                # RSI策略 - 使用更敏感的参数
                rsi_strategy = RSIStrategy(
                    symbol=symbol,
                    parameters={
                        'rsi_period': 10,    # 更短的周期，更敏感
                        'oversold': 35,      # 提高超卖阈值，更容易触发买入
                        'overbought': 65,    # 降低超买阈值，更容易触发卖出
                        'stop_loss': 0.02,
                        'take_profit': 0.04, # 降低止盈目标
                        'position_size': 0.03
                    }
                )
                self.strategies[f"{symbol}_RSI"] = rsi_strategy
            
            if 'ML' in self.enabled_strategies:
                # 机器学习策略 - 使用更敏感的参数
                ml_strategy = MLStrategy(
                    symbol=symbol,
                    parameters={
                        'model_type': 'random_forest',
                        'lookback_period': 15,   # 更短的回看期
                        'prediction_horizon': 1,
                        'min_confidence': 0.45,  # 进一步降低信心阈值
                        'up_threshold': 0.005,   # 0.5% - 更敏感的阈值
                        'down_threshold': -0.005, # -0.5% - 更敏感的阈值
                        'stop_loss': 0.02,
                        'take_profit': 0.04,     # 降低止盈目标
                        'position_size': 0.03,
                        'retrain_frequency': 30, # 更频繁重训练
                        'min_training_samples': 80  # 降低最小训练样本
                    }
                )
                self.strategies[f"{symbol}_ML"] = ml_strategy
            
            if 'Chanlun' in self.enabled_strategies:
                # 缠论策略 - 基于缠论理论的量化交易策略
                chanlun_strategy = ChanlunStrategy(
                    symbol=symbol,
                    parameters={
                        'timeframes': ['30m', '1h', '4h'],
                        'min_swing_length': 3,
                        'central_bank_min_bars': 3,
                        'macd_fast': 12,
                        'macd_slow': 26,
                        'macd_signal': 9,
                        'rsi_period': 14,
                        'ma_short': 5,
                        'ma_long': 20,
                        'position_size': 0.3,
                        'max_position': 1.0,
                        'stop_loss': 0.03,
                        'take_profit': 0.05,
                        'trend_confirmation': 0.02,
                        'divergence_threshold': 0.1
                    }
                )
                self.strategies[f"{symbol}_Chanlun"] = chanlun_strategy
        
        self.logger.info(f"已为 {len(valid_symbols)} 个币种创建了 {len(self.strategies)} 个策略")
    
    def add_strategy(self, symbol: str, strategy_type: str, parameters: dict = None):
        """动态添加策略"""
        try:
            if parameters is None:
                parameters = {}
            
            strategy_key = f"{symbol}_{strategy_type}"
            
            if strategy_type == 'MA':
                strategy = MovingAverageStrategy(symbol, parameters)
            elif strategy_type == 'RSI':
                strategy = RSIStrategy(symbol, parameters)
            elif strategy_type == 'ML':
                strategy = MLStrategy(symbol, parameters)
            elif strategy_type == 'LSTM':
                strategy = LSTMStrategy(symbol, parameters)
            elif strategy_type == 'Chanlun':
                strategy = ChanlunStrategy(symbol, parameters)
            else:
                self.logger.error(f"不支持的策略类型: {strategy_type}")
                return False
            
            self.strategies[strategy_key] = strategy
            self.logger.info(f"已添加策略: {strategy_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    def remove_strategy(self, strategy_key: str):
        """移除策略"""
        try:
            if strategy_key in self.strategies:
                del self.strategies[strategy_key]
                self.logger.info(f"已移除策略: {strategy_key}")
                return True
            else:
                self.logger.warning(f"策略不存在: {strategy_key}")
                return False
        except Exception as e:
            self.logger.error(f"移除策略失败: {e}")
            return False
    
    def _start_data_collection(self):
        """启动数据收集 - 只为用户选择的币种收集数据"""
        try:
            self.data_collection_running = True
            # 在后台启动数据收集
            import threading
            data_thread = threading.Thread(target=self._run_data_collection)
            data_thread.daemon = True
            data_thread.start()
            self.logger.info(f"数据收集已启动，收集币种: {self.selected_symbols}")
        except Exception as e:
            self.logger.error(f"启动数据收集失败: {e}")
    
    def _run_data_collection(self):
        """运行数据收集循环 - 只为用户选择的币种收集数据"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                self.data_collector.start_real_time_collection(
                    symbols=self.selected_symbols,  # 只收集用户选择的币种
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
                    self.logger.warning(f"策略 {strategy_name}: 无法获取市场数据")
                    continue
                
                current_price = data['close'].iloc[-1]
                
                # 检查止损止盈（使用风险管理器计算的动态止损止盈）
                if strategy.position != 0:
                    if self._should_close_position(strategy, current_price):
                        continue
                
                # 生成交易信号
                signal = strategy.generate_signal(data)
                
                # 详细输出策略信号信息
                self._log_strategy_signal(strategy_name, strategy, signal, current_price, data)
                
                if signal in ['BUY', 'SELL']:
                    # 风险检查
                    if self._risk_check_passed(strategy, signal, current_price):
                        self._execute_enhanced_trade(strategy, signal, current_price, 'SIGNAL')
                    else:
                        # 记录风险检查失败的原因
                        self._log_risk_check_failure(strategy_name, strategy, signal, current_price)
                    
            except Exception as e:
                self.logger.error(f"策略 {strategy_name} 执行错误: {e}")
    
    def _get_enhanced_market_data(self, symbol: str):
        """获取增强的市场数据"""
        try:
            # 验证交易对格式
            if not symbol or not isinstance(symbol, str):
                self.logger.error(f"无效的交易对: {symbol}")
                return pd.DataFrame()
            
            # 优先从数据库获取
            data = self.data_collector.get_market_data(symbol, self.config.DEFAULT_TIMEFRAME, limit=200)
            
            if data is None or data.empty or len(data) < 50:
                # 如果数据库数据不足，从API获取
                self.logger.info(f"从API获取 {symbol} 数据...")
                api_data = self.binance_client.get_klines(
                    symbol=symbol,
                    interval=self.config.DEFAULT_TIMEFRAME,
                    limit=200
                )
                
                if api_data is not None and not api_data.empty:
                    data = api_data
                else:
                    self.logger.warning(f"无法获取 {symbol} 的市场数据")
                    return pd.DataFrame()
            
            if data is not None and not data.empty:
                # 计算技术指标
                try:
                    data = self.data_collector.calculate_technical_indicators(data, symbol)
                except Exception as indicator_error:
                    self.logger.warning(f"计算技术指标失败: {indicator_error}")
                    # 即使技术指标计算失败，也返回基础数据
            
            return data if data is not None else pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"获取增强市场数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
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
    
    def _log_strategy_signal(self, strategy_name: str, strategy, signal: str, current_price: float, data):
        """记录策略信号详细信息"""
        try:
            # 获取市场数据统计信息
            data_length = len(data) if data is not None else 0
            price_change = 0
            if data_length >= 2:
                price_change = ((current_price - data['close'].iloc[-2]) / data['close'].iloc[-2]) * 100
            
            # 构建详细的信号信息
            signal_info = f"策略: {strategy_name}"
            signal_info += f" | 信号: {signal}"
            signal_info += f" | 当前价格: ${current_price:.4f}"
            signal_info += f" | 价格变化: {price_change:+.2f}%"
            signal_info += f" | 当前持仓: {strategy.position:.6f}"
            signal_info += f" | 市场数据: {data_length} 条记录"
            
            # 根据信号类型输出不同级别的日志
            if signal == 'HOLD':
                self.logger.info(f"📊 {signal_info}")
            elif signal in ['BUY', 'SELL']:
                self.logger.info(f"🎯 {signal_info}")
            else:
                self.logger.warning(f"❓ {signal_info} | 未知信号类型: {signal}")
                # 将未知信号视为HOLD
                signal = 'HOLD'
                
        except Exception as e:
            self.logger.error(f"记录策略信号信息失败: {e}")
    
    def _log_risk_check_failure(self, strategy_name: str, strategy, signal: str, current_price: float):
        """记录风险检查失败的详细原因"""
        try:
            # 获取风险检查的详细信息
            portfolio_value = self.risk_manager._get_portfolio_value()
            suggested_quantity = self.risk_manager.calculate_position_size(
                strategy.symbol, 1.0, current_price, portfolio_value
            )
            
            # 执行详细的风险检查以获取失败原因
            passed, message = self.risk_manager.check_risk_limits(
                strategy.symbol, suggested_quantity, current_price
            )
            
            # 构建失败原因信息
            failure_info = f"❌ 策略: {strategy_name}"
            failure_info += f" | 信号: {signal}"
            failure_info += f" | 当前价格: ${current_price:.4f}"
            failure_info += f" | 建议仓位: {suggested_quantity:.6f}"
            failure_info += f" | 投资组合价值: ${portfolio_value:.2f}"
            failure_info += f" | 失败原因: {message}"
            
            self.logger.warning(failure_info)
            
            # 如果是仓位大小为0的情况，提供更详细的解释
            if suggested_quantity <= 0:
                self._log_position_size_analysis(strategy_name, strategy, current_price, portfolio_value)
                
        except Exception as e:
            self.logger.error(f"记录风险检查失败信息失败: {e}")
    
    def _log_position_size_analysis(self, strategy_name: str, strategy, current_price: float, portfolio_value: float):
        """分析并记录仓位大小为0的原因"""
        try:
            # 获取策略历史数据
            from backend.database import Trade
            completed_trades = self.db_manager.session.query(Trade).filter_by(
                symbol=strategy.symbol
            ).filter(Trade.profit_loss != 0).limit(10).all()
            
            # 获取策略性能指标
            win_rate = self.risk_manager._get_strategy_win_rate(strategy.symbol)
            avg_win = self.risk_manager._get_average_win(strategy.symbol)
            avg_loss = self.risk_manager._get_average_loss(strategy.symbol)
            volatility = self.risk_manager._calculate_volatility(strategy.symbol)
            
            # 构建分析信息
            analysis_info = f"📊 仓位分析 - {strategy_name}:"
            analysis_info += f" | 历史交易: {len(completed_trades)} 条"
            analysis_info += f" | 策略胜率: {win_rate:.2%}"
            analysis_info += f" | 平均盈利: {avg_win:.2%}"
            analysis_info += f" | 平均亏损: {avg_loss:.2%}"
            analysis_info += f" | 资产波动率: {volatility:.2%}"
            
            if len(completed_trades) < 5:
                analysis_info += " | 原因: 历史数据不足，使用保守默认值"
            elif win_rate == 0:
                analysis_info += " | 原因: 策略历史表现不佳"
            else:
                analysis_info += " | 原因: Kelly公式计算结果为0"
            
            self.logger.info(analysis_info)
            
        except Exception as e:
            self.logger.error(f"分析仓位大小失败: {e}")
    
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
                    
                    # 根据交易模式执行订单
                    if self.trading_mode == 'FUTURES':
                        order = self.binance_client.place_order(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=quantity,
                            leverage=self.leverage,
                            position_side='LONG'
                        )
                    else:
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
                        
                        # 更新数据库中的持仓记录
                        current_price = self.binance_client.get_ticker_price(strategy.symbol)
                        if current_price:
                            self.db_manager.update_position(
                                symbol=strategy.symbol,
                                quantity=quantity,
                                avg_price=price,
                                current_price=current_price
                            )
                        
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__
                        )
                        
                        # 详细的交易执行信息
                        trade_type = "合约做多" if self.trading_mode == 'FUTURES' else "现货买入"
                        trade_info = f"✅ 交易执行成功 - {trade_type}"
                        trade_info += f" | 交易对: {strategy.symbol}"
                        trade_info += f" | 数量: {quantity:.6f}"
                        trade_info += f" | 价格: ${price:.4f}"
                        trade_info += f" | 价值: ${quantity * price:.2f}"
                        
                        if self.trading_mode == 'FUTURES':
                            trade_info += f" | 杠杆: {self.leverage}x"
                        
                        trade_info += f" | 止损: ${stop_loss:.4f}"
                        trade_info += f" | 止盈: ${take_profit:.4f}"
                        trade_info += f" | 风险回报比: {((take_profit - price) / (price - stop_loss)):.2f}"
                        
                        self.logger.info(trade_info)
                        self.logger.info(f"📊 持仓已更新到数据库")
            
            elif action == 'SELL' and strategy.position >= 0:
                if strategy.position > 0:
                    quantity = strategy.position
                    
                    # 根据交易模式执行订单
                    if self.trading_mode == 'FUTURES':
                        # 合约模式：可以开空仓或平多仓
                        order = self.binance_client.place_order(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=quantity,
                            position_side='LONG',
                            reduce_only=True  # 平仓操作
                        )
                    else:
                        # 现货模式：卖出持仓
                        order = self.binance_client.place_order(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=quantity
                        )
                    
                    if order:
                        profit_loss = (price - strategy.entry_price) * quantity
                        strategy.close_position()
                        
                        # 从数据库中移除持仓记录（卖出全部）
                        from backend.database import Position
                        position = self.db_manager.session.query(Position).filter_by(symbol=strategy.symbol).first()
                        if position:
                            self.db_manager.session.delete(position)
                            self.db_manager.session.commit()
                        
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__,
                            profit_loss=profit_loss
                        )
                        
                        # 详细的卖出交易信息
                        trade_type = "合约平多" if self.trading_mode == 'FUTURES' else "现货卖出"
                        trade_info = f"💰 交易执行成功 - {trade_type}"
                        trade_info += f" | 交易对: {strategy.symbol}"
                        trade_info += f" | 数量: {quantity:.6f}"
                        trade_info += f" | 价格: ${price:.4f}"
                        trade_info += f" | 价值: ${quantity * price:.2f}"
                        trade_info += f" | 入场价: ${strategy.entry_price:.4f}"
                        trade_info += f" | 盈亏: ${profit_loss:.2f}"
                        trade_info += f" | 收益率: {(profit_loss / (strategy.entry_price * quantity)) * 100:+.2f}%"
                        
                        self.logger.info(trade_info)
                        self.logger.info(f"📊 持仓已从数据库移除")
            
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
                        
                        # 详细的平仓交易信息
                        close_info = f"🔄 {reason} 平仓执行成功"
                        close_info += f" | 交易对: {strategy.symbol}"
                        close_info += f" | 数量: {quantity:.6f}"
                        close_info += f" | 价格: ${price:.4f}"
                        close_info += f" | 价值: ${quantity * price:.2f}"
                        close_info += f" | 入场价: ${strategy.entry_price:.4f}"
                        close_info += f" | 盈亏: ${profit_loss:.2f}"
                        close_info += f" | 收益率: {(profit_loss / (strategy.entry_price * abs(strategy.position))) * 100:+.2f}%"
                        
                        self.logger.info(close_info)
                        
        except Exception as e:
            self.logger.error(f"执行增强交易失败: {e}")
    
    def _execute_trade(self, strategy, action, price, reason):
        """执行交易（支持现货和合约）"""
        try:
            if self.trading_mode == 'FUTURES':
                return self._execute_futures_trade(strategy, action, price, reason)
            else:
                return self._execute_spot_trade(strategy, action, price, reason)
        except Exception as e:
            self.logger.error(f"执行交易失败: {e}")
            return False
    
    def _execute_spot_trade(self, strategy, action, price, reason):
        """执行现货交易"""
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
                        strategy.position = quantity
                        strategy.entry_price = price
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__
                        )
                        self.logger.info(f"现货买入 {strategy.symbol}: {quantity} @ {price}")
                        return True
            
            elif action == 'SELL' and strategy.position > 0:
                quantity = strategy.position
                order = self.binance_client.place_order(
                    symbol=strategy.symbol,
                    side='SELL',
                    quantity=quantity
                )
                if order:
                    profit_loss = (price - strategy.entry_price) * quantity
                    strategy.position = 0
                    strategy.entry_price = 0
                    self.db_manager.add_trade(
                        symbol=strategy.symbol,
                        side='SELL',
                        quantity=quantity,
                        price=price,
                        strategy=strategy.__class__.__name__,
                        profit_loss=profit_loss
                    )
                    self.logger.info(f"现货卖出 {strategy.symbol}: {quantity} @ {price}, P&L: {profit_loss}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"执行现货交易失败: {e}")
            return False
    
    def _execute_futures_trade(self, strategy, action, price, reason):
        """执行合约交易（支持做多和做空）"""
        try:
            # 检查流动性
            if not self._check_liquidity(strategy.symbol):
                self.logger.warning(f"流动性不足，跳过交易 {strategy.symbol}")
                return False
            
            # 获取安全的订单数量
            quantity = self._get_safe_quantity(strategy.symbol, price, strategy.parameters.get('position_size', 0.02))
            
            if quantity <= 0:
                self.logger.warning(f"订单数量无效: {quantity}, 跳过交易")
                return False
            
            if action == 'BUY':
                # 开多头仓位或平空头仓位
                if strategy.position <= 0:  # 无仓位或有空头仓位
                    # 如果有空头仓位，先平仓
                    if strategy.position < 0:
                        close_quantity = abs(strategy.position)
                        close_order = self.binance_client.place_order(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=close_quantity,
                            position_side='SHORT',
                            reduce_only=True
                        )
                        if close_order:
                            self.logger.info(f"平空头仓位 {strategy.symbol}: {close_quantity}")
                            strategy.position = 0
                    
                    # 开多头仓位
                    order = self.binance_client.place_order(
                        symbol=strategy.symbol,
                        side='BUY',
                        quantity=quantity,
                        position_side='LONG',
                        reduce_only=False  # 开仓时不使用reduce_only
                    )
                    
                    if order:
                        strategy.position = quantity
                        strategy.entry_price = price
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__
                        )
                        self.logger.info(f"合约开多 {strategy.symbol}: {quantity} @ {price} (杠杆: {self.leverage}x)")
                        return True
            
            elif action == 'SELL':
                # 开空头仓位或平多头仓位
                if strategy.position >= 0:  # 无仓位或有多头仓位
                    # 如果有多头仓位，先平仓
                    if strategy.position > 0:
                        close_quantity = strategy.position
                        close_order = self.binance_client.place_order(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=close_quantity,
                            position_side='LONG',
                            reduce_only=True
                        )
                        if close_order:
                            profit_loss = (price - strategy.entry_price) * close_quantity
                            self.logger.info(f"平多头仓位 {strategy.symbol}: {close_quantity}, P&L: {profit_loss}")
                            strategy.position = 0
                    
                    # 开空头仓位
                    order = self.binance_client.place_order(
                        symbol=strategy.symbol,
                        side='SELL',
                        quantity=quantity,
                        position_side='SHORT',
                        reduce_only=False  # 开仓时不使用reduce_only
                    )
                    
                    if order:
                        strategy.position = -quantity  # 负数表示空头仓位
                        strategy.entry_price = price
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__
                        )
                        self.logger.info(f"合约开空 {strategy.symbol}: {quantity} @ {price} (杠杆: {self.leverage}x)")
                        return True
            
            elif action == 'CLOSE':
                if strategy.position != 0:
                    if strategy.position > 0:  # 平多头仓位
                        order = self.binance_client.place_order(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=strategy.position,
                            position_side='LONG',
                            reduce_only=True
                        )
                    else:  # 平空头仓位
                        order = self.binance_client.place_order(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=abs(strategy.position),
                            position_side='SHORT',
                            reduce_only=True
                        )
                    
                    if order:
                        profit_loss = (price - strategy.entry_price) * strategy.position
                        quantity = abs(strategy.position)
                        strategy.position = 0
                        strategy.entry_price = 0
                        
                        self.db_manager.add_trade(
                            symbol=strategy.symbol,
                            side='SELL' if strategy.position > 0 else 'BUY',
                            quantity=quantity,
                            price=price,
                            strategy=strategy.__class__.__name__,
                            profit_loss=profit_loss
                        )
                        self.logger.info(f"{reason} 合约平仓 {strategy.symbol}: {quantity} @ {price}, P&L: {profit_loss}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"执行合约交易失败: {e}")
            return False
    
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