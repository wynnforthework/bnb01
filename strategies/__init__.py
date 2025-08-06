# 交易策略模块

from .base_strategy import BaseStrategy
from .ma_strategy import MovingAverageStrategy
from .rsi_strategy import RSIStrategy
from .ml_strategy import MLStrategy
from .chanlun_strategy import ChanlunStrategy

# 可用策略列表
AVAILABLE_STRATEGIES = {
    'MovingAverageStrategy': MovingAverageStrategy,
    'RSIStrategy': RSIStrategy,
    'MLStrategy': MLStrategy,
    'ChanlunStrategy': ChanlunStrategy
}

# 策略显示名称
STRATEGY_DISPLAY_NAMES = {
    'MovingAverageStrategy': '移动平均策略',
    'RSIStrategy': 'RSI策略',
    'MLStrategy': '机器学习策略',
    'ChanlunStrategy': '缠论01'
}

# 策略描述
STRATEGY_DESCRIPTIONS = {
    'MovingAverageStrategy': '基于移动平均线的趋势跟踪策略',
    'RSIStrategy': '基于RSI指标的超买超卖策略',
    'MLStrategy': '基于机器学习的预测策略',
    'ChanlunStrategy': '基于缠论理论的量化交易策略，包含多周期联动分析、分型识别、中枢构建、买卖点判断等功能'
}