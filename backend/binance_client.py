import json
import os
from decimal import Decimal, getcontext
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import logging
from typing import Dict, Optional, Union
from config.config import Config
from backend.network_config import binance_network_config
import time

class BinanceClient:
    def __init__(self, trading_mode='SPOT'):
        """
        初始化币安客户端
        
        Args:
            trading_mode: 'SPOT' 现货交易, 'FUTURES' 合约交易
        """
        self.config = Config()
        self.trading_mode = trading_mode.upper()
        
        # 配置请求参数，包括禁用代理
        requests_params = {
            'timeout': 30,
            'proxies': {
                'http': None,
                'https': None
            }
        }
        
        # 根据交易模式初始化不同的客户端
        if self.trading_mode == 'FUTURES':
            # 合约交易客户端
            if self.config.BINANCE_TESTNET:
                # 测试网络合约
                self.client = Client(
                    api_key=self.config.BINANCE_API_KEY_FUTURES,
                    api_secret=self.config.BINANCE_SECRET_KEY_FUTURES,
                    testnet=True,
                    requests_params=requests_params
                )
                # 设置合约测试网端点
                self.client.FUTURES_URL = 'https://testnet.binancefuture.com'
            else:
                # 主网合约
                self.client = Client(
                    api_key=self.config.BINANCE_API_KEY,
                    api_secret=self.config.BINANCE_SECRET_KEY,
                    testnet=False,
                    requests_params=requests_params
                )
        else:
            # 现货交易客户端
            self.client = Client(
                api_key=self.config.BINANCE_API_KEY,
                api_secret=self.config.BINANCE_SECRET_KEY,
                testnet=self.config.BINANCE_TESTNET,
                requests_params=requests_params
            )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"币安客户端初始化完成，交易模式: {self.trading_mode}")
        
        # 缓存exchange info
        self._exchange_info_cache = None
        self._exchange_info_cache_time = 0
        self._cache_duration = 3600  # 1小时缓存
        
        # 验证API连接
        self._verify_connection()
    
    def _verify_connection(self):
        """验证API连接"""
        try:
            if self.trading_mode == 'FUTURES':
                # 验证合约API连接
                account = self.client.futures_account()
                self.logger.info("合约API连接验证成功")
            else:
                # 验证现货API连接
                account = self.client.get_account()
                self.logger.info("现货API连接验证成功")
        except BinanceAPIException as e:
            self.logger.error(f"API连接验证失败: {e}")
            if "Invalid API-key" in str(e):
                self.logger.error("API密钥无效，请检查配置")
            elif "Signature for this request is not valid" in str(e):
                self.logger.error("API签名无效，请检查密钥配置")
            elif "IP address" in str(e):
                self.logger.error("IP地址未加入白名单")
        except Exception as e:
            self.logger.error(f"API连接验证异常: {e}")
    
    def _safe_api_call(self, api_func, *args, **kwargs):
        """安全的API调用，带重试机制"""
        def api_wrapper():
            # 只对需要签名的API调用添加时间戳和recvWindow参数
            if hasattr(api_func, '__name__'):
                func_name = api_func.__name__
                # 这些API调用需要签名参数
                signed_apis = [
                    'get_account', 'get_asset_balance', 'get_open_orders', 
                    'cancel_order', 'order_market', 'order_limit',
                    'futures_account', 'futures_position_information',
                    'futures_change_leverage', 'futures_change_margin_type',
                    'futures_change_position_mode', 'futures_create_order',
                    'futures_get_open_orders', 'futures_cancel_order',
                    'futures_funding_rate', 'futures_mark_price'
                ]
                
                # 这些API调用不需要额外参数
                public_apis = [
                    'get_klines', 'get_historical_klines', 'get_symbol_ticker',
                    'futures_symbol_ticker', 'get_exchange_info'
                ]
                
                # 只对需要签名的API添加参数
                if any(api_name in func_name for api_name in signed_apis):
                    if 'timestamp' not in kwargs:
                        kwargs['timestamp'] = int(time.time() * 1000)
                    if 'recvWindow' not in kwargs:
                        kwargs['recvWindow'] = 60000
                # 对公开API不添加任何额外参数
                elif any(api_name in func_name for api_name in public_apis):
                    pass  # 不添加任何参数
            
            return api_func(*args, **kwargs)
        
        try:
            return binance_network_config.retry_with_backoff(api_wrapper)
        except Exception as e:
            self.logger.error(f"API调用失败: {e}")
            return None
    
    def get_account_info(self):
        """获取账户信息"""
        try:
            return self._safe_api_call(self.client.get_account)
        except BinanceAPIException as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return None
    
    def get_balance(self, asset='USDT'):
        """获取指定资产余额"""
        try:
            if self.trading_mode == 'FUTURES':
                # 合约账户余额
                account = self._safe_api_call(self.client.futures_account)
                if account:
                    for balance in account['assets']:
                        if balance['asset'] == asset:
                            return float(balance['availableBalance'])
                return 0.0
            else:
                # 现货账户余额
                balance = self._safe_api_call(self.client.get_asset_balance, asset=asset)
                return float(balance['free']) if balance else 0.0
        except BinanceAPIException as e:
            self.logger.error(f"获取余额失败: {e}")
            return 0.0
    
    def get_klines(self, symbol, interval='1h', limit=500):
        """获取K线数据"""
        try:
            # 直接调用，不使用_safe_api_call，因为这是公开API
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if not klines:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 转换数据类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except BinanceAPIException as e:
            self.logger.error(f"获取K线数据失败: {e}")
            return pd.DataFrame()
    
    def get_historical_klines(self, symbol, interval, start_str, end_str=None, limit=1000):
        """获取历史K线数据"""
        try:
            kwargs = {
                'symbol': symbol,
                'interval': interval,
                'start_str': start_str,
                'limit': limit
            }
            if end_str:
                kwargs['end_str'] = end_str
            
            # 直接调用，不使用_safe_api_call，因为这是公开API
            klines = self.client.get_historical_klines(**kwargs)
            
            if not klines:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 转换数据类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except BinanceAPIException as e:
            self.logger.error(f"获取历史K线数据失败: {e}")
            return pd.DataFrame()
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """检查交易对是否有效"""
        try:
            exchange_info = self.get_exchange_info()
            
            if exchange_info:
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol and s['status'] == 'TRADING':
                        return True
            return False
        except Exception as e:
            self.logger.error(f"检查交易对有效性失败: {e}")
            return False
    
    def get_ticker_price(self, symbol):
        """获取当前价格"""
        try:
            if self.trading_mode == 'FUTURES':
                # 直接调用，不使用_safe_api_call，因为这是公开API
                ticker = self.client.futures_symbol_ticker(symbol=symbol)
            else:
                # 直接调用，不使用_safe_api_call，因为这是公开API
                ticker = self.client.get_symbol_ticker(symbol=symbol)
            
            if ticker:
                return float(ticker['price'])
            return None
        except BinanceAPIException as e:
            self.logger.error(f"获取价格失败: {e}")
            return None
    
    def get_position_mode(self):
        """获取当前持仓模式"""
        if self.trading_mode != 'FUTURES':
            return None
        
        try:
            # 获取账户信息
            account_info = self._safe_api_call(self.client.futures_account)
            if account_info and 'dualSidePosition' in account_info:
                return account_info['dualSidePosition']
            return None
        except Exception as e:
            self.logger.error(f"获取持仓模式失败: {e}")
            return None

    def place_order(self, symbol, side, quantity, order_type='MARKET', price=None, 
                   leverage=None, position_side='BOTH', reduce_only=False):
        """下单"""
        try:
            # 获取交易对信息以确定精度
            symbol_info = self._get_symbol_info(symbol)
            if symbol_info:
                # 调整数量精度 - 这会自动确保数量符合LOT_SIZE要求
                quantity = self._adjust_quantity_precision(quantity, symbol_info)
                
                # 调整价格精度（如果是限价单）
                if price and order_type == 'LIMIT':
                    price = self._adjust_price_precision(price, symbol_info)
            
            self.logger.info(f"下单: {symbol} {side} {quantity} @ {price if price else 'MARKET'}")
            
            if self.trading_mode == 'FUTURES':
                # 合约交易
                if leverage:
                    self.set_leverage(symbol, leverage)
                
                # 检查持仓模式并调整position_side
                position_mode = self.get_position_mode()
                if position_mode is not None:
                    if not position_mode:  # 单向持仓模式
                        # 单向持仓模式下，不需要指定positionSide
                        position_side = None
                    else:  # 双向持仓模式
                        # 双向持仓模式下，需要指定LONG或SHORT
                        if position_side == 'BOTH':
                            # 根据交易方向确定持仓方向
                            position_side = 'LONG' if side == 'BUY' else 'SHORT'
                
                if order_type == 'MARKET':
                    # 构建订单参数
                    order_params = {
                        'symbol': symbol,
                        'side': side,
                        'type': 'MARKET',
                        'quantity': str(quantity)
                    }
                    
                    # 只在双向持仓模式下添加positionSide
                    if position_side and position_side != 'BOTH':
                        order_params['positionSide'] = position_side
                    
                    # 只在需要时添加reduceOnly参数
                    if reduce_only:
                        order_params['reduceOnly'] = True
                    
                    order = self._safe_api_call(self.client.futures_create_order, **order_params)
                else:
                    # 构建限价单参数
                    order_params = {
                        'symbol': symbol,
                        'side': side,
                        'type': 'LIMIT',
                        'quantity': str(quantity),
                        'price': price,
                        'timeInForce': 'GTC'
                    }
                    
                    # 只在双向持仓模式下添加positionSide
                    if position_side and position_side != 'BOTH':
                        order_params['positionSide'] = position_side
                    
                    # 只在需要时添加reduceOnly参数
                    if reduce_only:
                        order_params['reduceOnly'] = True
                    
                    order = self._safe_api_call(self.client.futures_create_order, **order_params)
            else:
                # 现货交易
                if order_type == 'MARKET':
                    order = self._safe_api_call(
                        self.client.order_market,
                        symbol=symbol,
                        side=side,
                        quantity=str(quantity)
                    )
                else:
                    order = self._safe_api_call(
                        self.client.order_limit,
                        symbol=symbol,
                        side=side,
                        quantity=str(quantity),
                        price=str(price) if price else None
                    )
            
            if order:
                self.logger.info(f"订单成功: {order.get('orderId', 'N/A')}")
            return order
            
        except BinanceAPIException as e:
            error_msg = str(e)
            if "Filter failure: LOT_SIZE" in error_msg:
                self.logger.error(f"LOT_SIZE过滤器失败 - 数量不符合步长要求: {quantity}")
                # 尝试自动调整数量
                if symbol_info:
                    adjusted_quantity = self._adjust_quantity_precision(quantity, symbol_info)
                    self.logger.info(f"建议调整后的数量: {adjusted_quantity}")
            else:
                self.logger.error(f"下单失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"下单异常: {e}")
            return None
    
    def get_exchange_info(self):
        """获取交易所信息 - 优先从本地文件读取"""
        try:
            # 首先尝试从本地JSON文件读取
            local_file_path = 'exchangeInfo.json'
            if os.path.exists(local_file_path):
                try:
                    with open(local_file_path, 'r', encoding='utf-8') as f:
                        exchange_info = json.load(f)
                    self.logger.info("从本地文件读取交易所信息成功")
                    return exchange_info
                except Exception as e:
                    self.logger.warning(f"读取本地交易所信息失败: {e}")
            
            # 如果本地文件不存在或读取失败，使用API获取
            if self._exchange_info_cache and (time.time() - self._exchange_info_cache_time) < self._cache_duration:
                self.logger.info("使用缓存的交易所信息")
                return self._exchange_info_cache
            
            # 从API获取
            if hasattr(self.client, 'get_exchange_info'):
                exchange_info = self.client.get_exchange_info()
            elif hasattr(self.client, 'get_exchange_information'):
                exchange_info = self.client.get_exchange_information()
            else:
                exchange_info = self.client.get_exchange_info()
            
            # 缓存结果
            self._exchange_info_cache = exchange_info
            self._exchange_info_cache_time = time.time()
            
            self.logger.info("从API获取交易所信息成功")
            return exchange_info
            
        except Exception as e:
            self.logger.error(f"获取交易所信息失败: {e}")
            return None

    def get_round_count(self, symbol):
        """获取交易对的数量精度位数 - 基于LOT_SIZE的stepSize"""
        try:
            exchange_info = self.get_exchange_info()
            if not exchange_info or 'symbols' not in exchange_info:
                return 6  # 默认精度
            
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    filters = symbol_info['filters']
                    for filter_info in filters:
                        if filter_info['filterType'] == 'LOT_SIZE':
                            step_size = filter_info['stepSize']
                            # 计算小数位数
                            step_str = str(step_size)
                            if '.' in step_str:
                                decimal_part = step_str.split('.')[-1]
                                return len(decimal_part)
                            else:
                                return 0
            
            return 6  # 默认精度
            
        except Exception as e:
            self.logger.error(f"获取数量精度位数失败: {e}")
            return 6

    def get_price_precision(self, symbol):
        """获取交易对的价格精度位数 - 基于PRICE_FILTER的tickSize"""
        try:
            exchange_info = self.get_exchange_info()
            if not exchange_info or 'symbols' not in exchange_info:
                return 2  # 默认精度
            
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    filters = symbol_info['filters']
                    for filter_info in filters:
                        if filter_info['filterType'] == 'PRICE_FILTER':
                            tick_size = filter_info['tickSize']
                            # 计算小数位数
                            tick_str = str(tick_size)
                            if '.' in tick_str:
                                decimal_part = tick_str.split('.')[-1]
                                return len(decimal_part)
                            else:
                                return 0
            
            return 2  # 默认精度
            
        except Exception as e:
            self.logger.error(f"获取价格精度位数失败: {e}")
            return 2

    def _get_symbol_info(self, symbol):
        """获取交易对信息"""
        try:
            exchange_info = self.get_exchange_info()
            
            if exchange_info:
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol:
                        return s
            return None
        except Exception as e:
            self.logger.error(f"获取交易对信息失败: {e}")
            return None
    
    def _adjust_quantity_precision(self, quantity, symbol_info):
        """调整数量精度 - 确保符合LOT_SIZE过滤器要求"""
        try:
            # 获取LOT_SIZE过滤器
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    min_qty = float(f['minQty'])
                    max_qty = float(f.get('maxQty', float('inf')))
                    
                    # 确保数量在有效范围内
                    if quantity < min_qty:
                        quantity = min_qty
                    elif quantity > max_qty:
                        quantity = max_qty
                    
                    # 计算步长精度位数
                    step_precision = self._get_step_precision(step_size)
                    
                    # 将数量调整到最接近的有效步长
                    # 使用Decimal进行精确计算
                    from decimal import Decimal, ROUND_DOWN
                    
                    # 将step_size转换为Decimal以确保精度
                    step_decimal = Decimal(str(step_size))
                    quantity_decimal = Decimal(str(quantity))
                    
                    # 计算有多少个完整的步长
                    steps = quantity_decimal / step_decimal
                    # 向下取整到最近的步长
                    valid_steps = steps.quantize(Decimal('1'), rounding=ROUND_DOWN)
                    # 计算有效的数量
                    adjusted_quantity = valid_steps * step_decimal
                    
                    # 确保不小于最小值
                    min_qty_decimal = Decimal(str(min_qty))
                    if adjusted_quantity < min_qty_decimal:
                        adjusted_quantity = min_qty_decimal
                    
                    # 转换为float并格式化到正确精度
                    result_quantity = float(adjusted_quantity)
                    
                    # 使用字符串格式化确保精度正确
                    precise_quantity_str = "{:0.0{}f}".format(result_quantity, step_precision)
                    final_quantity = float(precise_quantity_str)
                    
                    self.logger.info(f"数量精度调整: {quantity:.8f} -> {final_quantity:.8f} (步长: {step_size}, 精度: {step_precision})")
                    return final_quantity
            
            # 如果没有找到过滤器，使用默认精度
            return round(quantity, 6)
            
        except Exception as e:
            self.logger.error(f"调整数量精度失败: {e}")
            return round(quantity, 6)
    
    def _get_step_precision(self, step_size):
        """根据步长计算精度位数 - 正确处理科学计数法"""
        try:
            # 使用Decimal来处理科学计数法
            from decimal import Decimal
            step_decimal = Decimal(str(step_size))
            
            # 转换为字符串，避免科学计数法
            step_str = f"{step_decimal:.10f}"
            
            # 移除尾部的0和小数点
            step_str = step_str.rstrip('0').rstrip('.')
            
            if '.' in step_str:
                # 计算小数位数
                decimal_part = step_str.split('.')[-1]
                return len(decimal_part)
            else:
                return 0
        except Exception as e:
            self.logger.error(f"计算步长精度失败: {e}")
            return 6  # 默认精度
    
    def _validate_quantity(self, quantity, symbol_info):
        """验证数量是否符合LOT_SIZE过滤器要求"""
        try:
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    min_qty = float(f['minQty'])
                    max_qty = float(f.get('maxQty', float('inf')))
                    
                    # 检查数量范围
                    if quantity < min_qty:
                        return {
                            'valid': False,
                            'message': f"数量 {quantity} 小于最小值 {min_qty}"
                        }
                    
                    if quantity > max_qty:
                        return {
                            'valid': False,
                            'message': f"数量 {quantity} 大于最大值 {max_qty}"
                        }
                    
                    # 检查是否符合步长要求
                    from decimal import Decimal
                    step_decimal = Decimal(str(step_size))
                    quantity_decimal = Decimal(str(quantity))
                    
                    # 计算余数
                    remainder = quantity_decimal % step_decimal
                    
                    if remainder != 0:
                        return {
                            'valid': False,
                            'message': f"数量 {quantity} 不符合步长 {step_size} 的要求，余数: {remainder}"
                        }
                    
                    return {'valid': True, 'message': '数量验证通过'}
            
            # 如果没有找到LOT_SIZE过滤器，认为有效
            return {'valid': True, 'message': '未找到LOT_SIZE过滤器'}
            
        except Exception as e:
            self.logger.error(f"数量验证失败: {e}")
            return {'valid': False, 'message': f'验证过程出错: {e}'}
    
    def _adjust_price_precision(self, price, symbol_info):
        """调整价格精度 - 使用PRICE_FILTER的tickSize"""
        try:
            # 获取价格精度位数
            precision = self.get_price_precision(symbol_info['symbol'])
            
            # 使用字符串格式化确保精度正确
            precise_price_str = "{:0.0{}f}".format(price, precision)
            formatted_price = float(precise_price_str)
            
            self.logger.info(f"价格精度调整: {price:.8f} -> {formatted_price:.8f} (精度: {precision})")
            return formatted_price
            
        except Exception as e:
            self.logger.error(f"调整价格精度失败: {e}")
            return round(price, 2)
    
    def get_open_orders(self, symbol=None):
        """获取未成交订单"""
        try:
            if self.trading_mode == 'FUTURES':
                return self._safe_api_call(self.client.futures_get_open_orders, symbol=symbol)
            else:
                return self._safe_api_call(self.client.get_open_orders, symbol=symbol)
        except BinanceAPIException as e:
            self.logger.error(f"获取订单失败: {e}")
            return []
    
    def cancel_order(self, symbol, order_id):
        """取消订单"""
        try:
            if self.trading_mode == 'FUTURES':
                return self._safe_api_call(self.client.futures_cancel_order, symbol=symbol, orderId=order_id)
            else:
                return self._safe_api_call(self.client.cancel_order, symbol=symbol, orderId=order_id)
        except BinanceAPIException as e:
            self.logger.error(f"取消订单失败: {e}")
            return None
    
    # ========== 合约交易专用方法 ==========
    
    def get_leverage(self, symbol: str):
        """获取当前杠杆倍数"""
        if self.trading_mode != 'FUTURES':
            return None
        
        try:
            positions = self._safe_api_call(self.client.futures_position_information, symbol=symbol)
            if positions and len(positions) > 0:
                return int(positions[0].get('leverage', 1))
            return None
        except BinanceAPIException as e:
            self.logger.error(f"获取杠杆倍数失败: {e}")
            return None

    def set_leverage(self, symbol: str, leverage: int):
        """设置杠杆倍数"""
        if self.trading_mode != 'FUTURES':
            self.logger.warning("只有合约交易支持杠杆设置")
            return None
        
        # 先检查当前杠杆倍数
        current_leverage = self.get_leverage(symbol)
        if current_leverage == leverage:
            # 已经是目标杠杆，无需设置
            return True
        
        try:
            # 直接调用API，不使用_safe_api_call来避免错误日志
            result = self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            self.logger.info(f"设置杠杆 {symbol}: {leverage}x")
            return result
        except BinanceAPIException as e:
            if "Leverage reduction is not supported in Isolated Margin Mode with open positions" in str(e):
                # 静默处理，不记录日志，因为这是正常情况（有持仓时无法降低杠杆）
                self.logger.info(f"杠杆设置跳过 {symbol}: 有持仓时无法降低杠杆")
                return True
            else:
                self.logger.error(f"设置杠杆失败: {e}")
                return None
    
    def get_margin_type(self, symbol: str):
        """获取当前保证金模式"""
        if self.trading_mode != 'FUTURES':
            return None
        
        try:
            positions = self._safe_api_call(self.client.futures_position_information, symbol=symbol)
            if positions and len(positions) > 0:
                return positions[0].get('marginType', 'CROSSED')
            return None
        except BinanceAPIException as e:
            self.logger.error(f"获取保证金模式失败: {e}")
            return None

    def set_margin_type(self, symbol: str, margin_type: str = 'ISOLATED'):
        """设置保证金模式"""
        if self.trading_mode != 'FUTURES':
            self.logger.warning("只有合约交易支持保证金模式设置")
            return None
        
        # 先检查当前保证金模式
        current_margin_type = self.get_margin_type(symbol)
        if current_margin_type == margin_type:
            # 已经是目标模式，无需设置
            return True
        
        try:
            # 直接调用API，不使用_safe_api_call来避免错误日志
            result = self.client.futures_change_margin_type(symbol=symbol, marginType=margin_type)
            self.logger.info(f"设置保证金模式 {symbol}: {margin_type}")
            return result
        except BinanceAPIException as e:
            if "No need to change margin type" in str(e):
                # 静默处理，不记录日志，因为这是正常情况
                return True
            else:
                self.logger.error(f"设置保证金模式失败: {e}")
                return None
    
    def get_positions(self):
        """获取合约持仓"""
        if self.trading_mode != 'FUTURES':
            self.logger.warning("只有合约交易支持持仓查询")
            return []
        
        try:
            positions = self._safe_api_call(self.client.futures_position_information)
            # 只返回有持仓的交易对
            active_positions = []
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    active_positions.append(pos)
            return active_positions
        except BinanceAPIException as e:
            self.logger.error(f"获取持仓失败: {e}")
            return []
    
    def get_account_balance(self):
        """获取账户余额详情"""
        try:
            if self.trading_mode == 'FUTURES':
                account = self._safe_api_call(self.client.futures_account)
                return {
                    'totalWalletBalance': float(account['totalWalletBalance']),
                    'totalUnrealizedProfit': float(account['totalUnrealizedProfit']),
                    'totalMarginBalance': float(account['totalMarginBalance']),
                    'totalPositionInitialMargin': float(account['totalPositionInitialMargin']),
                    'totalOpenOrderInitialMargin': float(account['totalOpenOrderInitialMargin']),
                    'availableBalance': float(account['availableBalance']),
                    'maxWithdrawAmount': float(account['maxWithdrawAmount']),
                    'assets': account['assets'],
                    'positions': account['positions']
                }
            else:
                account = self._safe_api_call(self.client.get_account)
                total_btc = float(account['totalAssetOfBtc'])
                balances = []
                for balance in account['balances']:
                    if float(balance['free']) > 0 or float(balance['locked']) > 0:
                        balances.append(balance)
                return {
                    'totalAssetOfBtc': total_btc,
                    'balances': balances
                }
        except BinanceAPIException as e:
            self.logger.error(f"获取账户余额失败: {e}")
            return None
    
    def close_position(self, symbol: str, position_side: str = 'BOTH'):
        """平仓"""
        if self.trading_mode != 'FUTURES':
            self.logger.warning("只有合约交易支持平仓操作")
            return None
        
        try:
            # 获取当前持仓
            positions = self.get_positions()
            target_position = None
            
            for pos in positions:
                if pos['symbol'] == symbol:
                    if position_side == 'BOTH' or pos['positionSide'] == position_side:
                        target_position = pos
                        break
            
            if not target_position:
                self.logger.warning(f"没有找到 {symbol} 的持仓")
                return None
            
            position_amt = float(target_position['positionAmt'])
            if position_amt == 0:
                self.logger.info(f"{symbol} 没有持仓需要平仓")
                return None
            
            # 确定平仓方向
            side = 'SELL' if position_amt > 0 else 'BUY'
            quantity = abs(position_amt)
            
            # 执行平仓
            order = self.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type='MARKET',
                position_side=target_position['positionSide'],
                reduce_only=True
            )
            
            if order:
                self.logger.info(f"平仓成功 {symbol}: {side} {quantity}")
            
            return order
            
        except Exception as e:
            self.logger.error(f"平仓失败: {e}")
            return None
    
    def set_position_mode(self, dual_side_position: bool = True):
        """设置持仓模式"""
        if self.trading_mode != 'FUTURES':
            self.logger.warning("只有合约交易支持持仓模式设置")
            return None
        
        try:
            # 直接调用API，不使用_safe_api_call来避免错误日志
            result = self.client.futures_change_position_mode(dualSidePosition=dual_side_position)
            mode = "双向持仓" if dual_side_position else "单向持仓"
            self.logger.info(f"设置持仓模式: {mode}")
            return result
        except BinanceAPIException as e:
            if "No need to change position side" in str(e):
                # 静默处理，不记录日志，因为这是正常情况
                return True
            else:
                self.logger.error(f"设置持仓模式失败: {e}")
                return None
    
    def get_funding_rate(self, symbol: str):
        """获取资金费率"""
        if self.trading_mode != 'FUTURES':
            self.logger.warning("只有合约交易有资金费率")
            return None
        
        try:
            funding_rate = self._safe_api_call(self.client.futures_funding_rate, symbol=symbol, limit=1)
            if funding_rate:
                return {
                    'symbol': funding_rate[0]['symbol'],
                    'fundingRate': float(funding_rate[0]['fundingRate']),
                    'fundingTime': funding_rate[0]['fundingTime']
                }
            return None
        except BinanceAPIException as e:
            self.logger.error(f"获取资金费率失败: {e}")
            return None
    
    def get_mark_price(self, symbol: str):
        """获取标记价格"""
        if self.trading_mode != 'FUTURES':
            self.logger.warning("只有合约交易有标记价格")
            return None
        
        try:
            mark_price = self._safe_api_call(self.client.futures_mark_price, symbol=symbol)
            return {
                'symbol': mark_price['symbol'],
                'markPrice': float(mark_price['markPrice']),
                'indexPrice': float(mark_price['indexPrice']),
                'estimatedSettlePrice': float(mark_price['estimatedSettlePrice']),
                'lastFundingRate': float(mark_price['lastFundingRate']),
                'nextFundingTime': mark_price['nextFundingTime']
            }
        except BinanceAPIException as e:
            self.logger.error(f"获取标记价格失败: {e}")
            return None