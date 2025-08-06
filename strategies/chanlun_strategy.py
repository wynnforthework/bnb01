 #!/usr/bin/env python3
"""
缠论01策略 - 基于缠论理论的量化交易策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from .base_strategy import BaseStrategy

class ChanlunStrategy(BaseStrategy):
    """缠论策略 - 多周期联动分析"""
    
    def __init__(self, symbol: str, parameters: Dict = None):
        # 默认参数
        default_params = {
            'timeframes': ['30m', '1h', '4h', '1d'],  # 多周期分析
            'min_swing_length': 3,  # 最小笔长度
            'central_bank_min_bars': 3,  # 中枢最少笔数
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'ma_short': 5,
            'ma_long': 20,
            'position_size': 0.3,  # 初始仓位30%
            'max_position': 1.0,  # 最大仓位100%
            'stop_loss': 0.03,  # 止损3%
            'take_profit': 0.05,  # 止盈5%
            'trend_confirmation': 0.02,  # 趋势确认阈值
            'divergence_threshold': 0.1,  # 背离阈值
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__(symbol, default_params)
        self.logger = logging.getLogger(__name__)
        
        # 缠论数据结构
        self.fractals = []  # 分型
        self.strokes = []   # 笔
        self.segments = []  # 线段
        self.central_banks = []  # 中枢
        self.buy_points = []  # 买点
        self.sell_points = []  # 卖点
        
        # 多周期数据
        self.multi_timeframe_data = {}
        
        # 设置最小训练样本数
        self.min_training_samples = 50
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """准备缠论特征数据"""
        try:
            df = data.copy()
            
            # 确保数据类型正确
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].astype(float)
            
            # 移除包含NaN的行
            df = df.dropna(subset=numeric_columns)
            
            if df.empty:
                return pd.DataFrame()
            
            # 基础技术指标
            df = self._calculate_basic_indicators(df)
            
            # 缠论特征
            df = self._calculate_chanlun_features(df)
            
            # 多周期特征
            df = self._calculate_multi_timeframe_features(df)
            
            # 清理无穷大和NaN值
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(0)
            
            return df
            
        except Exception as e:
            self.logger.error(f"准备缠论特征失败: {e}")
            return data
    
    def _calculate_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算基础技术指标"""
        try:
            # MACD
            exp1 = df['close'].ewm(span=self.parameters['macd_fast']).mean()
            exp2 = df['close'].ewm(span=self.parameters['macd_slow']).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=self.parameters['macd_signal']).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.parameters['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.parameters['rsi_period']).mean()
            rs = gain / loss.where(loss != 0, 1)
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 移动平均线
            df['ma_short'] = df['close'].rolling(window=self.parameters['ma_short']).mean()
            df['ma_long'] = df['close'].rolling(window=self.parameters['ma_long']).mean()
            
            # 价格特征
            df['price_change'] = df['close'].pct_change()
            df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算基础指标失败: {e}")
            return df
    
    def _calculate_chanlun_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算缠论特征"""
        try:
            # 识别分型
            df = self._identify_fractals(df)
            
            # 构建笔
            df = self._build_strokes(df)
            
            # 构建线段
            df = self._build_segments(df)
            
            # 识别中枢
            df = self._identify_central_banks(df)
            
            # 计算买卖点
            df = self._calculate_buy_sell_points(df)
            
            # 背离检测
            df = self._detect_divergence(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算缠论特征失败: {e}")
            return df
    
    def _identify_fractals(self, df: pd.DataFrame) -> pd.DataFrame:
        """识别顶底分型"""
        try:
            df['top_fractal'] = 0
            df['bottom_fractal'] = 0
            
            for i in range(2, len(df) - 2):
                # 顶分型：中间K线最高
                if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                    df['high'].iloc[i] > df['high'].iloc[i-2] and
                    df['high'].iloc[i] > df['high'].iloc[i+1] and 
                    df['high'].iloc[i] > df['high'].iloc[i+2]):
                    df.loc[df.index[i], 'top_fractal'] = 1
                
                # 底分型：中间K线最低
                if (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                    df['low'].iloc[i] < df['low'].iloc[i-2] and
                    df['low'].iloc[i] < df['low'].iloc[i+1] and 
                    df['low'].iloc[i] < df['low'].iloc[i+2]):
                    df.loc[df.index[i], 'bottom_fractal'] = 1
            
            return df
            
        except Exception as e:
            self.logger.error(f"识别分型失败: {e}")
            return df
    
    def _build_strokes(self, df: pd.DataFrame) -> pd.DataFrame:
        """构建笔"""
        try:
            df['stroke_start'] = 0
            df['stroke_end'] = 0
            df['stroke_direction'] = 0  # 1为向上，-1为向下
            
            # 找到所有分型
            top_fractals = df[df['top_fractal'] == 1].index
            bottom_fractals = df[df['bottom_fractal'] == 1].index
            
            # 构建笔的逻辑
            strokes = []
            current_direction = 0
            current_start = None
            
            for i in range(len(df)):
                if df['top_fractal'].iloc[i] == 1:
                    if current_direction == -1:  # 之前向下，现在向上
                        if current_start is not None:
                            strokes.append({
                                'start': current_start,
                                'end': i,
                                'direction': -1,
                                'high': df['high'].iloc[current_start:i+1].max(),
                                'low': df['low'].iloc[current_start:i+1].min()
                            })
                        current_start = i
                        current_direction = 1
                    elif current_direction == 0:  # 第一个分型
                        current_start = i
                        current_direction = 1
                
                elif df['bottom_fractal'].iloc[i] == 1:
                    if current_direction == 1:  # 之前向上，现在向下
                        if current_start is not None:
                            strokes.append({
                                'start': current_start,
                                'end': i,
                                'direction': 1,
                                'high': df['high'].iloc[current_start:i+1].max(),
                                'low': df['low'].iloc[current_start:i+1].min()
                            })
                        current_start = i
                        current_direction = -1
                    elif current_direction == 0:  # 第一个分型
                        current_start = i
                        current_direction = -1
            
            # 标记笔的起止点
            for stroke in strokes:
                if len(stroke) >= self.parameters['min_swing_length']:
                    df.loc[df.index[stroke['start']], 'stroke_start'] = 1
                    df.loc[df.index[stroke['end']], 'stroke_end'] = 1
                    df.loc[df.index[stroke['start']:stroke['end']+1], 'stroke_direction'] = stroke['direction']
            
            return df
            
        except Exception as e:
            self.logger.error(f"构建笔失败: {e}")
            return df
    
    def _build_segments(self, df: pd.DataFrame) -> pd.DataFrame:
        """构建线段"""
        try:
            df['segment_start'] = 0
            df['segment_end'] = 0
            
            # 简化的线段构建逻辑
            # 线段是笔的组合，这里用简化的方法
            stroke_starts = df[df['stroke_start'] == 1].index
            stroke_ends = df[df['stroke_end'] == 1].index
            
            if len(stroke_starts) >= 3:
                # 标记线段起止点
                for i in range(0, len(stroke_starts), 3):
                    if i < len(stroke_starts):
                        df.loc[stroke_starts[i], 'segment_start'] = 1
                    if i + 2 < len(stroke_ends):
                        df.loc[stroke_ends[i + 2], 'segment_end'] = 1
            
            return df
            
        except Exception as e:
            self.logger.error(f"构建线段失败: {e}")
            return df
    
    def _identify_central_banks(self, df: pd.DataFrame) -> pd.DataFrame:
        """识别中枢"""
        try:
            df['central_bank_high'] = np.nan
            df['central_bank_low'] = np.nan
            df['in_central_bank'] = 0
            
            # 简化的中枢识别逻辑
            # 中枢是至少3笔重叠的区间
            stroke_highs = []
            stroke_lows = []
            
            for i in range(len(df)):
                if df['stroke_start'].iloc[i] == 1:
                    # 收集笔的高低点
                    stroke_end_idx = None
                    for j in range(i, len(df)):
                        if df['stroke_end'].iloc[j] == 1:
                            stroke_end_idx = j
                            break
                    
                    if stroke_end_idx is not None:
                        high = df['high'].iloc[i:stroke_end_idx+1].max()
                        low = df['low'].iloc[i:stroke_end_idx+1].min()
                        stroke_highs.append(high)
                        stroke_lows.append(low)
            
            # 识别重叠区间
            if len(stroke_highs) >= self.parameters['central_bank_min_bars']:
                for i in range(len(stroke_highs) - 2):
                    # 检查3笔是否重叠
                    overlap_high = min(stroke_highs[i:i+3])
                    overlap_low = max(stroke_lows[i:i+3])
                    
                    if overlap_high > overlap_low:  # 有重叠
                        # 标记中枢区间
                        df['central_bank_high'] = overlap_high
                        df['central_bank_low'] = overlap_low
                        df['in_central_bank'] = 1
            
            return df
            
        except Exception as e:
            self.logger.error(f"识别中枢失败: {e}")
            return df
    
    def _calculate_buy_sell_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算买卖点"""
        try:
            df['buy_point_1'] = 0  # 第一类买点
            df['buy_point_2'] = 0  # 第二类买点
            df['buy_point_3'] = 0  # 第三类买点
            df['sell_point_1'] = 0  # 第一类卖点
            df['sell_point_2'] = 0  # 第二类卖点
            df['sell_point_3'] = 0  # 第三类卖点
            
            for i in range(20, len(df)):
                # 第一类买点：底背驰
                if self._is_buy_point_1(df, i):
                    df.loc[df.index[i], 'buy_point_1'] = 1
                
                # 第二类买点：不破前低且站上5日均线
                if self._is_buy_point_2(df, i):
                    df.loc[df.index[i], 'buy_point_2'] = 1
                
                # 第三类买点：次级别回调不破中枢上沿
                if self._is_buy_point_3(df, i):
                    df.loc[df.index[i], 'buy_point_3'] = 1
                
                # 卖点逻辑（类似买点）
                if self._is_sell_point_1(df, i):
                    df.loc[df.index[i], 'sell_point_1'] = 1
                
                if self._is_sell_point_2(df, i):
                    df.loc[df.index[i], 'sell_point_2'] = 1
                
                if self._is_sell_point_3(df, i):
                    df.loc[df.index[i], 'sell_point_3'] = 1
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算买卖点失败: {e}")
            return df
    
    def _is_buy_point_1(self, df: pd.DataFrame, i: int) -> bool:
        """判断第一类买点：底背驰"""
        try:
            if i < 20:
                return False
            
            # 检查是否创新低
            current_low = df['low'].iloc[i]
            recent_lows = df['low'].iloc[i-20:i]
            
            if current_low > recent_lows.min():
                return False
            
            # 检查MACD背离
            current_macd = df['macd'].iloc[i]
            current_hist = df['macd_histogram'].iloc[i]
            
            # 计算MACD绿柱面积（简化）
            recent_hist = df['macd_histogram'].iloc[i-10:i]
            hist_area = recent_hist[recent_hist < 0].sum()
            
            # 背离判断：价格创新低但MACD绿柱面积缩小
            if hist_area > -0.08:  # 进一步降低绿柱面积阈值，提高敏感度
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判断第一类买点失败: {e}")
            return False
    
    def _is_buy_point_2(self, df: pd.DataFrame, i: int) -> bool:
        """判断第二类买点：不破前低且站上5日均线"""
        try:
            if i < 10:
                return False
            
            current_price = df['close'].iloc[i]
            ma_short = df['ma_short'].iloc[i]
            
            # 检查是否站上5日均线（放宽条件）
            if current_price < ma_short * 0.995:  # 允许0.5%的误差
                return False
            
            # 检查是否不破前低
            recent_low = df['low'].iloc[i-10:i].min()
            current_low = df['low'].iloc[i]
            
            if current_low < recent_low:
                return False
            
            # 检查次级别底分型确认
            if df['bottom_fractal'].iloc[i] == 1:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判断第二类买点失败: {e}")
            return False
    
    def _is_buy_point_3(self, df: pd.DataFrame, i: int) -> bool:
        """判断第三类买点：次级别回调不破中枢上沿"""
        try:
            if i < 10:
                return False
            
            # 检查是否在中枢内
            if df['in_central_bank'].iloc[i] == 0:
                return False
            
            central_bank_high = df['central_bank_high'].iloc[i]
            if pd.isna(central_bank_high):
                return False
            
            current_price = df['close'].iloc[i]
            
            # 检查是否回调但不破中枢上沿
            if current_price >= central_bank_high:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判断第三类买点失败: {e}")
            return False
    
    def _is_sell_point_1(self, df: pd.DataFrame, i: int) -> bool:
        """判断第一类卖点：顶背驰"""
        try:
            if i < 20:
                return False
            
            # 检查是否创新高
            current_high = df['high'].iloc[i]
            recent_highs = df['high'].iloc[i-20:i]
            
            if current_high < recent_highs.max():
                return False
            
            # 检查MACD背离
            current_hist = df['macd_histogram'].iloc[i]
            
            # 计算MACD红柱面积（简化）
            recent_hist = df['macd_histogram'].iloc[i-10:i]
            hist_area = recent_hist[recent_hist > 0].sum()
            
            # 背离判断：价格创新高但MACD红柱面积缩小
            if hist_area < 0.1:  # 红柱面积较小
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判断第一类卖点失败: {e}")
            return False
    
    def _is_sell_point_2(self, df: pd.DataFrame, i: int) -> bool:
        """判断第二类卖点"""
        # 类似第二类买点的反向逻辑
        return False
    
    def _is_sell_point_3(self, df: pd.DataFrame, i: int) -> bool:
        """判断第三类卖点"""
        # 类似第三类买点的反向逻辑
        return False
    
    def _detect_divergence(self, df: pd.DataFrame) -> pd.DataFrame:
        """检测背离"""
        try:
            df['price_macd_divergence'] = 0
            df['rsi_divergence'] = 0
            
            for i in range(20, len(df)):
                # 价格与MACD背离检测
                if self._check_price_macd_divergence(df, i):
                    df.loc[df.index[i], 'price_macd_divergence'] = 1
                
                # RSI背离检测
                if self._check_rsi_divergence(df, i):
                    df.loc[df.index[i], 'rsi_divergence'] = 1
            
            return df
            
        except Exception as e:
            self.logger.error(f"检测背离失败: {e}")
            return df
    
    def _check_price_macd_divergence(self, df: pd.DataFrame, i: int) -> bool:
        """检查价格与MACD背离"""
        try:
            # 简化的背离检测逻辑
            price_trend = df['close'].iloc[i] - df['close'].iloc[i-10]
            macd_trend = df['macd'].iloc[i] - df['macd'].iloc[i-10]
            
            # 背离：价格趋势与MACD趋势相反
            if (price_trend > 0 and macd_trend < 0) or (price_trend < 0 and macd_trend > 0):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查价格MACD背离失败: {e}")
            return False
    
    def _check_rsi_divergence(self, df: pd.DataFrame, i: int) -> bool:
        """检查RSI背离"""
        try:
            # 简化的RSI背离检测
            price_trend = df['close'].iloc[i] - df['close'].iloc[i-10]
            rsi_trend = df['rsi'].iloc[i] - df['rsi'].iloc[i-10]
            
            # 背离：价格趋势与RSI趋势相反
            if (price_trend > 0 and rsi_trend < 0) or (price_trend < 0 and rsi_trend > 0):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查RSI背离失败: {e}")
            return False
    
    def _calculate_multi_timeframe_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算多周期特征"""
        try:
            # 这里简化处理，实际应该获取多周期数据
            # 添加多周期趋势特征
            df['trend_30m'] = 0
            df['trend_1h'] = 0
            df['trend_4h'] = 0
            df['trend_1d'] = 0
            
            # 简化的多周期趋势判断
            for i in range(20, len(df)):
                # 30分钟趋势
                if df['close'].iloc[i] > df['ma_short'].iloc[i]:
                    df.loc[df.index[i], 'trend_30m'] = 1
                else:
                    df.loc[df.index[i], 'trend_30m'] = -1
                
                # 其他周期类似（简化处理）
                df.loc[df.index[i], 'trend_1h'] = df.loc[df.index[i], 'trend_30m']
                df.loc[df.index[i], 'trend_4h'] = df.loc[df.index[i], 'trend_30m']
                df.loc[df.index[i], 'trend_1d'] = df.loc[df.index[i], 'trend_30m']
            
            return df
            
        except Exception as e:
            self.logger.error(f"计算多周期特征失败: {e}")
            return df
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """生成缠论交易信号"""
        try:
            if len(data) < 50:
                return 'HOLD'
            
            # 准备特征
            feature_data = self.prepare_features(data)
            if feature_data.empty:
                return 'HOLD'
            
            # 获取最新数据
            latest = feature_data.iloc[-1]
            
            # 缠论信号判断
            signal = self._analyze_chanlun_signals(feature_data)
            
            # 仓位管理
            position_signal = self._manage_position(feature_data)
            
            # 综合判断 - 修复逻辑
            if self.position == 0:  # 无持仓时，主要看缠论信号
                if signal == 'BUY':
                    return 'BUY'
                elif signal == 'SELL':
                    return 'SELL'
                else:
                    return 'HOLD'
            else:  # 有持仓时，主要看仓位管理信号
                if position_signal == 'BUY':
                    return 'BUY'
                elif position_signal == 'SELL':
                    return 'SELL'
                else:
                    return 'HOLD'
                
        except Exception as e:
            self.logger.error(f"生成缠论信号失败: {e}")
            return 'HOLD'
    
    def _analyze_chanlun_signals(self, df: pd.DataFrame) -> str:
        """分析缠论信号"""
        try:
            latest = df.iloc[-1]
            
            # 买点判断
            if (latest['buy_point_1'] == 1 or 
                latest['buy_point_2'] == 1 or 
                latest['buy_point_3'] == 1):
                return 'BUY'
            
            # 卖点判断
            if (latest['sell_point_1'] == 1 or 
                latest['sell_point_2'] == 1 or 
                latest['sell_point_3'] == 1):
                return 'SELL'
            
            # 背离信号
            if latest['price_macd_divergence'] == 1:
                if latest['rsi'] < 30:  # 底背离
                    return 'BUY'
                elif latest['rsi'] > 70:  # 顶背离
                    return 'SELL'
            
            # 趋势确认
            if (latest['trend_30m'] == 1 and 
                latest['trend_1h'] == 1 and 
                latest['trend_4h'] == 1):
                return 'BUY'
            elif (latest['trend_30m'] == -1 and 
                  latest['trend_1h'] == -1 and 
                  latest['trend_4h'] == -1):
                return 'SELL'
            
            return 'HOLD'
            
        except Exception as e:
            self.logger.error(f"分析缠论信号失败: {e}")
            return 'HOLD'
    
    def _manage_position(self, df: pd.DataFrame) -> str:
        """仓位管理"""
        try:
            if self.position == 0:
                return 'HOLD'  # 无仓位时等待信号
            
            latest = df.iloc[-1]
            current_price = latest['close']
            
            # 止损检查
            if self.position > 0:  # 多头持仓
                loss_ratio = (self.entry_price - current_price) / self.entry_price
                if loss_ratio > self.parameters['stop_loss']:
                    return 'SELL'  # 止损
                
                # 止盈检查
                profit_ratio = (current_price - self.entry_price) / self.entry_price
                if profit_ratio > self.parameters['take_profit']:
                    return 'SELL'  # 止盈
            
            elif self.position < 0:  # 空头持仓
                loss_ratio = (current_price - self.entry_price) / self.entry_price
                if loss_ratio > self.parameters['stop_loss']:
                    return 'BUY'  # 止损
                
                # 止盈检查
                profit_ratio = (self.entry_price - current_price) / self.entry_price
                if profit_ratio > self.parameters['take_profit']:
                    return 'BUY'  # 止盈
            
            return 'HOLD'
            
        except Exception as e:
            self.logger.error(f"仓位管理失败: {e}")
            return 'HOLD'
    
    def calculate_position_size(self, current_price: float, balance: float) -> float:
        """计算仓位大小"""
        try:
            # 基础仓位
            base_position = balance * self.parameters['position_size']
            
            # 简化版本：直接返回基础仓位
            position_ratio = 0.3  # 默认30%仓位
            
            return (base_position * position_ratio) / current_price
                
        except Exception as e:
            self.logger.error(f"计算仓位大小失败: {e}")
            return 0
    
    def should_stop_loss(self, current_price: float) -> bool:
        """判断是否应该止损"""
        if self.position == 0:
            return False
        
        if self.position > 0:  # 多头持仓
            loss_ratio = (self.entry_price - current_price) / self.entry_price
            return loss_ratio > self.parameters['stop_loss']
        else:  # 空头持仓
            loss_ratio = (current_price - self.entry_price) / self.entry_price
            return loss_ratio > self.parameters['stop_loss']
    
    def should_take_profit(self, current_price: float) -> bool:
        """判断是否应该止盈"""
        if self.position == 0:
            return False
        
        if self.position > 0:  # 多头持仓
            profit_ratio = (current_price - self.entry_price) / self.entry_price
            return profit_ratio > self.parameters['take_profit']
        else:  # 空头持仓
            profit_ratio = (self.entry_price - current_price) / self.entry_price
            return profit_ratio > self.parameters['take_profit']