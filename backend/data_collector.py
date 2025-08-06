import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from backend.binance_client import BinanceClient
from backend.database import DatabaseManager
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

class MarketData(Base):
    """市场数据表"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=False)
    trades_count = Column(Integer, default=0)
    interval = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d等

class OrderBookData(Base):
    """订单簿数据表"""
    __tablename__ = 'orderbook_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    bids = Column(Text, nullable=False)  # JSON格式存储买单
    asks = Column(Text, nullable=False)  # JSON格式存储卖单
    bid_depth = Column(Float, default=0.0)  # 买单深度
    ask_depth = Column(Float, default=0.0)  # 卖单深度

class TechnicalIndicators(Base):
    """技术指标数据表"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    sma_10 = Column(Float)  # 10日简单移动平均
    sma_20 = Column(Float)  # 20日简单移动平均
    sma_50 = Column(Float)  # 50日简单移动平均
    ema_12 = Column(Float)  # 12日指数移动平均
    ema_26 = Column(Float)  # 26日指数移动平均
    rsi_14 = Column(Float)  # 14日RSI
    macd = Column(Float)    # MACD
    macd_signal = Column(Float)  # MACD信号线
    macd_histogram = Column(Float)  # MACD柱状图
    bb_upper = Column(Float)  # 布林带上轨
    bb_middle = Column(Float)  # 布林带中轨
    bb_lower = Column(Float)  # 布林带下轨
    atr = Column(Float)     # 平均真实波幅
    volume_sma = Column(Float)  # 成交量移动平均

class DataCollector:
    """数据收集器"""
    
    def __init__(self):
        # 使用客户端管理器避免重复初始化
        from backend.client_manager import client_manager
        self.binance_client = client_manager.get_spot_client()
        self.db_manager = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # 创建新表
        Base.metadata.create_all(self.db_manager.engine)
        
    async def collect_historical_data(self, symbol: str, interval: str = '1h', 
                                    days: int = 30) -> pd.DataFrame:
        """收集历史数据"""
        try:
            # 计算开始时间
            start_time = datetime.now() - timedelta(days=days)
            
            # 获取K线数据
            klines = self.binance_client.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_time.strftime('%Y-%m-%d'),
                limit=1000
            )
            
            if not klines:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # 转换其他数值列
            df['taker_buy_base_asset_volume'] = pd.to_numeric(df['taker_buy_base_asset_volume'])
            df['taker_buy_quote_asset_volume'] = pd.to_numeric(df['taker_buy_quote_asset_volume'])
            df['ignore'] = pd.to_numeric(df['ignore'])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['number_of_trades'] = df['number_of_trades'].astype(int)
            
            # 存储到数据库
            await self._store_market_data(df, symbol, interval)
            
            self.logger.info(f"收集了 {len(df)} 条 {symbol} 的历史数据")
            return df
            
        except Exception as e:
            self.logger.error(f"收集历史数据失败: {e}")
            return pd.DataFrame()
    
    async def collect_orderbook_data(self, symbol: str, limit: int = 100) -> Dict:
        """收集订单簿数据"""
        try:
            orderbook = self.binance_client.client.get_order_book(
                symbol=symbol, 
                limit=limit
            )
            
            # 计算深度
            bids = [[float(price), float(qty)] for price, qty in orderbook['bids']]
            asks = [[float(price), float(qty)] for price, qty in orderbook['asks']]
            
            bid_depth = sum([price * qty for price, qty in bids])
            ask_depth = sum([price * qty for price, qty in asks])
            
            # 存储到数据库
            orderbook_record = OrderBookData(
                symbol=symbol,
                timestamp=datetime.now(),
                bids=json.dumps(bids),
                asks=json.dumps(asks),
                bid_depth=bid_depth,
                ask_depth=ask_depth
            )
            
            self.db_manager.session.add(orderbook_record)
            self.db_manager.session.commit()
            
            return {
                'symbol': symbol,
                'bids': bids,
                'asks': asks,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"收集订单簿数据失败: {e}")
            return {}
    
    async def _store_market_data(self, df: pd.DataFrame, symbol: str, interval: str):
        """存储市场数据到数据库"""
        try:
            for _, row in df.iterrows():
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=row['timestamp'],
                    open_price=row['open'],
                    high_price=row['high'],
                    low_price=row['low'],
                    close_price=row['close'],
                    volume=row['volume'],
                    quote_volume=row['quote_asset_volume'],
                    trades_count=row['number_of_trades'],
                    interval=interval
                )
                
                # 检查是否已存在
                existing = self.db_manager.session.query(MarketData).filter_by(
                    symbol=symbol,
                    timestamp=row['timestamp'],
                    interval=interval
                ).first()
                
                if not existing:
                    self.db_manager.session.add(market_data)
            
            self.db_manager.session.commit()
            
        except Exception as e:
            self.logger.error(f"存储市场数据失败: {e}")
            self.db_manager.session.rollback()
    
    def calculate_technical_indicators(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """计算技术指标"""
        try:
            # 首先尝试使用ta库（更稳定）
            try:
                import ta
                self.logger.info("使用ta库计算技术指标")
                return self._calculate_ta_indicators(df, symbol)
            except ImportError:
                pass
            
            # 然后尝试使用talib
            try:
                import talib
                self.logger.info("使用talib计算技术指标")
                
                # 确保数据类型正确
                high = df['high'].astype(float).values
                low = df['low'].astype(float).values
                close = df['close'].astype(float).values
                volume = df['volume'].astype(float).values
                
                # 移动平均线
                df['sma_10'] = talib.SMA(close, timeperiod=10)
                df['sma_20'] = talib.SMA(close, timeperiod=20)
                df['sma_50'] = talib.SMA(close, timeperiod=50)
                df['ema_12'] = talib.EMA(close, timeperiod=12)
                df['ema_26'] = talib.EMA(close, timeperiod=26)
                
                # RSI
                df['rsi_14'] = talib.RSI(close, timeperiod=14)
                
                # MACD
                macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
                df['macd'] = macd
                df['macd_signal'] = macd_signal
                df['macd_histogram'] = macd_hist
                
                # 布林带
                bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
                df['bb_upper'] = bb_upper
                df['bb_middle'] = bb_middle
                df['bb_lower'] = bb_lower
                
                # ATR
                df['atr'] = talib.ATR(high, low, close, timeperiod=14)
                
                # 成交量移动平均
                df['volume_sma'] = talib.SMA(volume, timeperiod=20)
                
                # 存储技术指标到数据库
                self._store_technical_indicators(df, symbol)
                
                return df
                
            except ImportError:
                self.logger.info("talib未安装，使用简化版技术指标计算")
                return self._calculate_simple_indicators(df, symbol)
            
        except Exception as e:
            self.logger.error(f"计算技术指标失败: {e}")
            return self._calculate_simple_indicators(df, symbol)
    
    def _calculate_ta_indicators(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """使用ta库计算技术指标"""
        try:
            import ta
            
            # 移动平均线
            df['sma_10'] = ta.trend.sma_indicator(df['close'], window=10)
            df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
            df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
            df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
            
            # RSI
            df['rsi_14'] = ta.momentum.rsi(df['close'], window=14)
            
            # MACD
            macd_line = ta.trend.macd(df['close'])
            macd_signal = ta.trend.macd_signal(df['close'])
            df['macd'] = macd_line
            df['macd_signal'] = macd_signal
            df['macd_histogram'] = macd_line - macd_signal
            
            # 布林带
            bb_indicator = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bb_indicator.bollinger_hband()
            df['bb_middle'] = bb_indicator.bollinger_mavg()
            df['bb_lower'] = bb_indicator.bollinger_lband()
            
            # ATR
            df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
            
            # 成交量移动平均
            df['volume_sma'] = ta.trend.sma_indicator(df['volume'], window=20)
            
            # 存储技术指标到数据库
            self._store_technical_indicators(df, symbol)
            
            return df
            
        except Exception as e:
            self.logger.error(f"使用ta库计算技术指标失败: {e}")
            return self._calculate_simple_indicators(df, symbol)
    
    def _calculate_simple_indicators(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """简化版技术指标计算（不依赖talib）"""
        try:
            # 简单移动平均
            df['sma_10'] = df['close'].rolling(window=10).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # 指数移动平均
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi_14'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # 布林带
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['atr'] = true_range.rolling(window=14).mean()
            
            # 成交量移动平均
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            
            # 存储技术指标
            self._store_technical_indicators(df, symbol)
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算简化技术指标失败: {e}")
            return df
    
    def _store_technical_indicators(self, df: pd.DataFrame, symbol: str):
        """存储技术指标到数据库"""
        try:
            for _, row in df.iterrows():
                if pd.isna(row.get('sma_10')):  # 跳过无效数据
                    continue
                    
                indicator = TechnicalIndicators(
                    symbol=symbol,
                    timestamp=row['timestamp'],
                    sma_10=row.get('sma_10'),
                    sma_20=row.get('sma_20'),
                    sma_50=row.get('sma_50'),
                    ema_12=row.get('ema_12'),
                    ema_26=row.get('ema_26'),
                    rsi_14=row.get('rsi_14'),
                    macd=row.get('macd'),
                    macd_signal=row.get('macd_signal'),
                    macd_histogram=row.get('macd_histogram'),
                    bb_upper=row.get('bb_upper'),
                    bb_middle=row.get('bb_middle'),
                    bb_lower=row.get('bb_lower'),
                    atr=row.get('atr'),
                    volume_sma=row.get('volume_sma')
                )
                
                # 检查是否已存在
                existing = self.db_manager.session.query(TechnicalIndicators).filter_by(
                    symbol=symbol,
                    timestamp=row['timestamp']
                ).first()
                
                if not existing:
                    self.db_manager.session.add(indicator)
            
            self.db_manager.session.commit()
            
        except Exception as e:
            self.logger.error(f"存储技术指标失败: {e}")
            self.db_manager.session.rollback()
    
    async def start_real_time_collection(self, symbols: List[str], intervals: List[str] = ['1m', '5m', '1h']):
        """启动实时数据收集"""
        self.logger.info("启动实时数据收集...")
        
        while True:
            try:
                tasks = []
                for symbol in symbols:
                    for interval in intervals:
                        # 收集最新的K线数据
                        task = self.collect_latest_data(symbol, interval)
                        tasks.append(task)
                    
                    # 收集订单簿数据
                    orderbook_task = self.collect_orderbook_data(symbol)
                    tasks.append(orderbook_task)
                
                # 并发执行所有任务
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # 等待下一次收集
                await asyncio.sleep(60)  # 每分钟收集一次
                
            except Exception as e:
                self.logger.error(f"实时数据收集错误: {e}")
                await asyncio.sleep(10)
    
    async def collect_latest_data(self, symbol: str, interval: str):
        """收集最新数据"""
        try:
            # 获取最新的K线数据
            klines = self.binance_client.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=1
            )
            
            if klines:
                kline = klines[0]
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    open_price=float(kline[1]),
                    high_price=float(kline[2]),
                    low_price=float(kline[3]),
                    close_price=float(kline[4]),
                    volume=float(kline[5]),
                    quote_volume=float(kline[7]),
                    trades_count=int(kline[8]),
                    interval=interval
                )
                
                # 检查是否已存在
                existing = self.db_manager.session.query(MarketData).filter_by(
                    symbol=symbol,
                    timestamp=market_data.timestamp,
                    interval=interval
                ).first()
                
                if not existing:
                    self.db_manager.session.add(market_data)
                    self.db_manager.session.commit()
                    
        except Exception as e:
            self.logger.error(f"收集最新数据失败 {symbol}-{interval}: {e}")
    
    def get_market_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """从数据库获取市场数据"""
        try:
            query = self.db_manager.session.query(MarketData).filter_by(
                symbol=symbol,
                interval=interval
            ).order_by(MarketData.timestamp.desc()).limit(limit)
            
            data = []
            for record in query:
                data.append({
                    'timestamp': record.timestamp,
                    'open': record.open_price,
                    'high': record.high_price,
                    'low': record.low_price,
                    'close': record.close_price,
                    'volume': record.volume,
                    'quote_volume': record.quote_volume,
                    'trades_count': record.trades_count
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            return pd.DataFrame()
    
    def get_technical_indicators(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """从数据库获取技术指标数据"""
        try:
            query = self.db_manager.session.query(TechnicalIndicators).filter_by(
                symbol=symbol
            ).order_by(TechnicalIndicators.timestamp.desc()).limit(limit)
            
            data = []
            for record in query:
                data.append({
                    'timestamp': record.timestamp,
                    'sma_10': record.sma_10,
                    'sma_20': record.sma_20,
                    'sma_50': record.sma_50,
                    'ema_12': record.ema_12,
                    'ema_26': record.ema_26,
                    'rsi_14': record.rsi_14,
                    'macd': record.macd,
                    'macd_signal': record.macd_signal,
                    'macd_histogram': record.macd_histogram,
                    'bb_upper': record.bb_upper,
                    'bb_middle': record.bb_middle,
                    'bb_lower': record.bb_lower,
                    'atr': record.atr,
                    'volume_sma': record.volume_sma
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取技术指标数据失败: {e}")
            return pd.DataFrame()