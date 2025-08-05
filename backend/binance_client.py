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
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
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
            return None
    
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
            return order
        except BinanceAPIException as e:
            self.logger.error(f"下单失败: {e}")
            return None
    
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