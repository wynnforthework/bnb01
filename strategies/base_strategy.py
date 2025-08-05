from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class BaseStrategy(ABC):
    """交易策略基类"""
    
    def __init__(self, symbol: str, parameters: Dict[str, Any]):
        self.symbol = symbol
        self.parameters = parameters
        self.position = 0  # 当前持仓
        self.entry_price = 0  # 入场价格
        self.trades = []  # 交易记录
        
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        生成交易信号
        返回: 'BUY', 'SELL', 'HOLD'
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, current_price: float, balance: float) -> float:
        """计算仓位大小"""
        pass
    
    def should_stop_loss(self, current_price: float) -> bool:
        """判断是否应该止损"""
        if self.position == 0:
            return False
            
        if self.position > 0:  # 多头持仓
            loss_percent = (self.entry_price - current_price) / self.entry_price
            return loss_percent > self.parameters.get('stop_loss', 0.02)
        else:  # 空头持仓
            loss_percent = (current_price - self.entry_price) / self.entry_price
            return loss_percent > self.parameters.get('stop_loss', 0.02)
    
    def should_take_profit(self, current_price: float) -> bool:
        """判断是否应该止盈"""
        if self.position == 0:
            return False
            
        if self.position > 0:  # 多头持仓
            profit_percent = (current_price - self.entry_price) / self.entry_price
            return profit_percent > self.parameters.get('take_profit', 0.05)
        else:  # 空头持仓
            profit_percent = (self.entry_price - current_price) / self.entry_price
            return profit_percent > self.parameters.get('take_profit', 0.05)
    
    def update_position(self, side: str, quantity: float, price: float):
        """更新持仓信息"""
        if side == 'BUY':
            if self.position <= 0:
                self.entry_price = price
                self.position = quantity
            else:
                # 加仓
                total_value = self.position * self.entry_price + quantity * price
                self.position += quantity
                self.entry_price = total_value / self.position
        elif side == 'SELL':
            if self.position >= 0:
                self.entry_price = price
                self.position = -quantity
            else:
                # 加仓
                total_value = abs(self.position) * self.entry_price + quantity * price
                self.position -= quantity
                self.entry_price = total_value / abs(self.position)
    
    def close_position(self):
        """平仓"""
        self.position = 0
        self.entry_price = 0