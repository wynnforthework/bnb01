#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略优化器测试脚本
"""

import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any

# 导入项目模块
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.ml_strategy import MLStrategy
from strategies.chanlun_strategy import ChanlunStrategy


def test_strategy_creation():
    """测试策略创建"""
    print("🧪 测试策略创建...")
    
    # 测试MA策略
    try:
        ma_params = {
            'short_window': 10,
            'long_window': 30,
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.05
        }
        ma_strategy = MovingAverageStrategy('BTCUSDT', parameters=ma_params)
        print("✅ MA策略创建成功")
    except Exception as e:
        print(f"❌ MA策略创建失败: {e}")
    
    # 测试RSI策略
    try:
        rsi_params = {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.05
        }
        rsi_strategy = RSIStrategy('BTCUSDT', parameters=rsi_params)
        print("✅ RSI策略创建成功")
    except Exception as e:
        print(f"❌ RSI策略创建失败: {e}")
    
    # 测试ML策略
    try:
        ml_params = {
            'lookback_period': 30,
            'prediction_horizon': 1,
            'model_type': 'random_forest',
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.05
        }
        ml_strategy = MLStrategy('BTCUSDT', parameters=ml_params)
        print("✅ ML策略创建成功")
    except Exception as e:
        print(f"❌ ML策略创建失败: {e}")
    
    # 测试Chanlun策略
    try:
        chanlun_params = {
            'min_swing_length': 3,
            'trend_confirmation': 0.02,
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.05
        }
        chanlun_strategy = ChanlunStrategy('BTCUSDT', parameters=chanlun_params)
        print("✅ Chanlun策略创建成功")
    except Exception as e:
        print(f"❌ Chanlun策略创建失败: {e}")


def test_parameter_generation():
    """测试参数生成"""
    print("\n🧪 测试参数生成...")
    
    # 策略参数范围定义
    strategy_param_ranges = {
        'MA': {
            'short_window': range(5, 21),
            'long_window': range(20, 101),
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        },
        'RSI': {
            'rsi_period': range(7, 22),
            'overbought': range(65, 81),
            'oversold': range(20, 36),
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        },
        'ML': {
            'lookback_period': range(10, 51),
            'prediction_horizon': [1, 2, 3, 5],
            'model_type': ['random_forest', 'gradient_boosting', 'logistic_regression'],
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        },
        'Chanlun': {
            'min_swing_length': range(3, 8),
            'trend_confirmation': [0.01, 0.02, 0.03, 0.05],
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        }
    }
    
    def generate_random_params(strategy_type: str) -> Dict[str, Any]:
        """生成随机参数组合"""
        param_ranges = strategy_param_ranges.get(strategy_type, {})
        params = {}
        
        for param_name, param_range in param_ranges.items():
            if isinstance(param_range, range):
                params[param_name] = random.choice(param_range)
            elif isinstance(param_range, list):
                params[param_name] = random.choice(param_range)
            else:
                params[param_name] = param_range
        
        return params
    
    # 测试每种策略的参数生成
    for strategy_type in ['MA', 'RSI', 'ML', 'Chanlun']:
        try:
            params = generate_random_params(strategy_type)
            print(f"✅ {strategy_type} 策略参数生成成功: {params}")
        except Exception as e:
            print(f"❌ {strategy_type} 策略参数生成失败: {e}")


def test_strategy_creation_with_random_params():
    """测试使用随机参数创建策略"""
    print("\n🧪 测试使用随机参数创建策略...")
    
    # 策略参数范围定义
    strategy_param_ranges = {
        'MA': {
            'short_window': range(5, 21),
            'long_window': range(20, 101),
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        },
        'RSI': {
            'rsi_period': range(7, 22),
            'overbought': range(65, 81),
            'oversold': range(20, 36),
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        },
        'ML': {
            'lookback_period': range(10, 51),
            'prediction_horizon': [1, 2, 3, 5],
            'model_type': ['random_forest', 'gradient_boosting', 'logistic_regression'],
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        },
        'Chanlun': {
            'min_swing_length': range(3, 8),
            'trend_confirmation': [0.01, 0.02, 0.03, 0.05],
            'position_size': [0.1, 0.5, 1.0, 2.0, 5.0],
            'stop_loss': [0.01, 0.02, 0.03, 0.05],
            'take_profit': [0.02, 0.03, 0.05, 0.08, 0.10]
        }
    }
    
    def generate_random_params(strategy_type: str) -> Dict[str, Any]:
        """生成随机参数组合"""
        param_ranges = strategy_param_ranges.get(strategy_type, {})
        params = {}
        
        for param_name, param_range in param_ranges.items():
            if isinstance(param_range, range):
                params[param_name] = random.choice(param_range)
            elif isinstance(param_range, list):
                params[param_name] = random.choice(param_range)
            else:
                params[param_name] = param_range
        
        return params
    
    def create_strategy(strategy_type: str, symbol: str, params: Dict[str, Any]):
        """创建策略实例"""
        try:
            if strategy_type == 'MA':
                return MovingAverageStrategy(symbol=symbol, parameters=params)
            elif strategy_type == 'RSI':
                return RSIStrategy(symbol=symbol, parameters=params)
            elif strategy_type == 'ML':
                return MLStrategy(symbol=symbol, parameters=params)
            elif strategy_type == 'Chanlun':
                return ChanlunStrategy(symbol=symbol, parameters=params)
            else:
                print(f"❌ 不支持的策略类型: {strategy_type}")
                return None
                
        except Exception as e:
            print(f"❌ 创建策略失败: {e}")
            return None
    
    # 测试每种策略
    for strategy_type in ['MA', 'RSI', 'ML', 'Chanlun']:
        try:
            params = generate_random_params(strategy_type)
            strategy = create_strategy(strategy_type, 'BTCUSDT', params)
            if strategy:
                print(f"✅ {strategy_type} 策略创建成功，参数: {params}")
            else:
                print(f"❌ {strategy_type} 策略创建失败")
        except Exception as e:
            print(f"❌ {strategy_type} 策略测试失败: {e}")


def main():
    """主函数"""
    print("🎯 策略优化器测试脚本")
    print("=" * 50)
    
    # 运行测试
    test_strategy_creation()
    test_parameter_generation()
    test_strategy_creation_with_random_params()
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    main()
