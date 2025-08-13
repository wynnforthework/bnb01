#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本
"""

print("开始测试...")

try:
    from strategies.ma_strategy import MovingAverageStrategy
    print("✅ 成功导入MA策略")
    
    # 测试MA策略创建
    ma_params = {
        'short_window': 10,
        'long_window': 30,
        'position_size': 0.1,
        'stop_loss': 0.02,
        'take_profit': 0.05
    }
    
    ma_strategy = MovingAverageStrategy('BTCUSDT', parameters=ma_params)
    print("✅ MA策略创建成功")
    print(f"策略参数: {ma_strategy.parameters}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("测试完成")
