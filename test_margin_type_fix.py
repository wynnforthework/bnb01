#!/usr/bin/env python3
"""
测试保证金模式设置修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.binance_client import BinanceClient
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_margin_type_fix():
    """测试保证金模式设置修复"""
    print("🔧 测试保证金模式设置修复...")
    
    try:
        # 创建合约客户端
        client = BinanceClient(trading_mode='FUTURES')
        
        # 测试交易对
        test_symbol = 'BNBUSDT'
        
        print(f"\n📊 测试交易对: {test_symbol}")
        
        # 1. 获取当前保证金模式
        print("\n1️⃣ 获取当前保证金模式...")
        current_margin = client.get_margin_type(test_symbol)
        print(f"   当前保证金模式: {current_margin}")
        
        # 2. 获取当前杠杆倍数
        print("\n2️⃣ 获取当前杠杆倍数...")
        current_leverage = client.get_leverage(test_symbol)
        print(f"   当前杠杆倍数: {current_leverage}")
        
        # 3. 设置保证金模式（应该静默处理）
        print("\n3️⃣ 设置保证金模式为逐仓...")
        margin_result = client.set_margin_type(test_symbol, 'ISOLATED')
        print(f"   设置结果: {margin_result}")
        
        # 4. 设置杠杆倍数
        print("\n4️⃣ 设置杠杆倍数为10x...")
        leverage_result = client.set_leverage(test_symbol, 10)
        print(f"   设置结果: {leverage_result}")
        
        # 5. 再次获取设置后的状态
        print("\n5️⃣ 验证设置结果...")
        final_margin = client.get_margin_type(test_symbol)
        final_leverage = client.get_leverage(test_symbol)
        print(f"   最终保证金模式: {final_margin}")
        print(f"   最终杠杆倍数: {final_leverage}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_margin_type_fix()
