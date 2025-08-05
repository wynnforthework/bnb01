import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI策略"""
    
    def __init__(self, symbol: str, parameters: dict = None):
        default_params = {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
            'stop_loss': 0.02,
            'take_profit': 0.05,
            'position_size': 0.1
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(symbol, default_params)
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """计算RSI指标"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.parameters['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.parameters['rsi_period']).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """生成交易信号"""
        if len(data) < self.parameters['rsi_period'] + 1:
            return 'HOLD'
        
        rsi = self.calculate_rsi(data)
        current_rsi = rsi.iloc[-1]
        
        # RSI超卖买入
        if current_rsi < self.parameters['oversold']:
            return 'BUY'
        # RSI超买卖出
        elif current_rsi > self.parameters['overbought']:
            return 'SELL'
        
        return 'HOLD'
    
    def calculate_position_size(self, current_price: float, balance: float) -> float:
        """计算仓位大小"""
        max_position_value = balance * self.parameters['position_size']
        return max_position_value / current_price