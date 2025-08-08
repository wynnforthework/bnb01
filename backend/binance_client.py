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
            # 使用正确的API方法名称
            if hasattr(self.client, 'get_exchange_info'):
                exchange_info = self.client.get_exchange_info()
            elif hasattr(self.client, 'get_exchange_information'):
                exchange_info = self.client.get_exchange_information()
            else:
                # 如果都不存在，尝试直接获取
                exchange_info = self.client.get_exchange_info()
            
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
    
    def place_order(self, symbol, side, quantity, order_type='MARKET', price=None, 
                   leverage=None, position_side='BOTH', reduce_only=False):
        """下单"""
        try:
            # 获取交易对信息以确定精度
            symbol_info = self._get_symbol_info(symbol)
            if symbol_info:
                # 调整数量精度
                quantity = self._adjust_quantity_precision(quantity, symbol_info)
                
                # 调整价格精度（如果是限价单）
                if price and order_type == 'LIMIT':
                    price = self._adjust_price_precision(price, symbol_info)
            
            self.logger.info(f"下单: {symbol} {side} {quantity} @ {price if price else 'MARKET'}")
            
            if self.trading_mode == 'FUTURES':
                # 合约交易
                if leverage:
                    self.set_leverage(symbol, leverage)
                
                if order_type == 'MARKET':
                    # 构建订单参数
                    order_params = {
                        'symbol': symbol,
                        'side': side,
                        'type': 'MARKET',
                        'quantity': f"{quantity:.5f}",
                        'positionSide': position_side
                    }
                    
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
                        'quantity': f"{quantity:.5f}",
                        'price': price,
                        'positionSide': position_side,
                        'timeInForce': 'GTC'
                    }
                    
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
                        quantity=quantity
                    )
                else:
                    order = self._safe_api_call(
                        self.client.order_limit,
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=price
                    )
            
            if order:
                self.logger.info(f"订单成功: {order.get('orderId', 'N/A')}")
            return order
            
        except BinanceAPIException as e:
            self.logger.error(f"下单失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"下单异常: {e}")
            return None
    
    def _get_symbol_info(self, symbol):
        """获取交易对信息"""
        try:
            # 使用正确的API方法名称
            if hasattr(self.client, 'get_exchange_info'):
                exchange_info = self.client.get_exchange_info()
            elif hasattr(self.client, 'get_exchange_information'):
                exchange_info = self.client.get_exchange_information()
            else:
                # 如果都不存在，尝试直接获取
                exchange_info = self.client.get_exchange_info()
            
            if exchange_info:
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol:
                        return s
            return None
        except Exception as e:
            self.logger.error(f"获取交易对信息失败: {e}")
            return None
    
    def _adjust_quantity_precision(self, quantity, symbol_info):
        """调整数量精度"""
        try:
            # 获取LOT_SIZE过滤器
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    min_qty = float(f['minQty'])
                    
                    # 确保数量不小于最小值
                    if quantity < min_qty:
                        quantity = min_qty
                    
                    # 简化的精度调整：直接使用步长的倍数
                    # 计算最接近的步长倍数
                    steps = round((quantity - min_qty) / step_size)
                    adjusted_quantity = min_qty + steps * step_size
                    
                    # 对于BTCUSDT，步长是0.00001，所以精度是5位小数
                    adjusted_quantity = round(adjusted_quantity, 5)
                    
                    self.logger.info(f"数量精度调整: {quantity:.8f} -> {adjusted_quantity:.8f}")
                    return adjusted_quantity
            
            # 如果没有找到过滤器，使用默认精度
            return round(quantity, 6)
            
        except Exception as e:
            self.logger.error(f"调整数量精度失败: {e}")
            return round(quantity, 6)
    
    def _adjust_price_precision(self, price, symbol_info):
        """调整价格精度"""
        try:
            # 获取PRICE_FILTER过滤器
            for f in symbol_info['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    tick_size = float(f['tickSize'])
                    
                    # 计算精度位数
                    if tick_size >= 1:
                        precision = 0
                    else:
                        precision = len(str(tick_size).split('.')[-1].rstrip('0'))
                    
                    # 调整价格
                    adjusted_price = round(price, precision)
                    
                    self.logger.info(f"价格精度调整: {price:.8f} -> {adjusted_price:.8f}")
                    return adjusted_price
            
            # 如果没有找到过滤器，使用默认精度
            return round(price, 2)
            
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