import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MovingAverageStrategy(BaseStrategy):
    """移动平均线策略"""
    
    def __init__(self, symbol: str, parameters: dict = None):
        default_params = {
            'short_window': 10,
            'long_window': 30,
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'position_size': 0.1
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(symbol, default_params)
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """生成交易信号"""
        if len(data) < self.parameters['long_window']:
            return 'HOLD'
        
        # 计算移动平均线
        short_ma = data['close'].rolling(window=self.parameters['short_window']).mean()
        long_ma = data['close'].rolling(window=self.parameters['long_window']).mean()
        
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        prev_short = short_ma.iloc[-2]
        prev_long = long_ma.iloc[-2]
        
        # 金叉买入信号
        if prev_short <= prev_long and current_short > current_long:
            return 'BUY'
        # 死叉卖出信号
        elif prev_short >= prev_long and current_short < current_long:
            return 'SELL'
        
        return 'HOLD'
    
    def calculate_position_size(self, current_price: float, balance: float) -> float:
        """计算仓位大小"""
        max_position_value = balance * self.parameters['position_size']
        return max_position_value / current_price