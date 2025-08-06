from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import logging
from config.config import Config

class BinanceClient:
    def __init__(self):
        self.config = Config()
        self.client = Client(
            api_key=self.config.BINANCE_API_KEY,
            api_secret=self.config.BINANCE_SECRET_KEY,
            testnet=self.config.BINANCE_TESTNET
        )
        self.logger = logging.getLogger(__name__)
    
    def get_account_info(self):
        """获取账户信息"""
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return None
    
    def get_balance(self, asset='USDT'):
        """获取指定资产余额"""
        try:
            balance = self.client.get_asset_balance(asset=asset)
            return float(balance['free']) if balance else 0.0
        except BinanceAPIException as e:
            self.logger.error(f"获取余额失败: {e}")
            return 0.0
    
    def get_klines(self, symbol, interval='1h', limit=500):
        """获取K线数据"""
        try:
            # 验证交易对格式
            if not symbol or not isinstance(symbol, str):
                self.logger.error(f"无效的交易对格式: {symbol}")
                return pd.DataFrame()
            
            # 验证交易对是否有效
            if not self._is_valid_symbol(symbol):
                self.logger.error(f"无效的交易对: {symbol}")
                return pd.DataFrame()
            
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if not klines:
                self.logger.warning(f"没有获取到 {symbol} 的K线数据")
                return pd.DataFrame()
            
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
            if "Invalid symbol" in str(e):
                self.logger.error(f"无效的交易对 {symbol}: {e}")
            else:
                self.logger.error(f"获取K线数据失败 {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"获取K线数据异常 {symbol}: {e}")
            return pd.DataFrame()
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """验证交易对是否有效"""
        try:
            # 基本格式检查
            if not symbol.endswith('USDT') and not symbol.endswith('BTC') and not symbol.endswith('ETH'):
                return False
            
            # 长度检查
            if len(symbol) < 6 or len(symbol) > 12:
                return False
            
            # 字符检查
            if not symbol.isalnum() or not symbol.isupper():
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_ticker_price(self, symbol):
        """获取当前价格"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            self.logger.error(f"获取价格失败: {e}")
            return None
    
    def place_order(self, symbol, side, quantity, order_type='MARKET', price=None):
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
            
            if order_type == 'MARKET':
                order = self.client.order_market(
                    symbol=symbol,
                    side=side,
                    quantity=quantity
                )
            else:
                order = self.client.order_limit(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price
                )
            
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
            exchange_info = self.client.get_exchange_info()
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
                    
                    # 计算精度位数
                    if step_size >= 1:
                        precision = 0
                    else:
                        precision = len(str(step_size).split('.')[-1].rstrip('0'))
                    
                    # 调整数量
                    adjusted_quantity = round(quantity, precision)
                    
                    # 确保数量符合最小值要求
                    min_qty = float(f['minQty'])
                    if adjusted_quantity < min_qty:
                        adjusted_quantity = min_qty
                    
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
            return self.client.get_open_orders(symbol=symbol)
        except BinanceAPIException as e:
            self.logger.error(f"获取订单失败: {e}")
            return []
    
    def cancel_order(self, symbol, order_id):
        """取消订单"""
        try:
            return self.client.cancel_order(symbol=symbol, orderId=order_id)
        except BinanceAPIException as e:
            self.logger.error(f"取消订单失败: {e}")
            return None