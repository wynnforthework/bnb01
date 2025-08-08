#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的合约交易功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading_engine import TradingEngine
from config.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_safe_trading():
    """测试安全交易功能"""
    print("测试安全交易功能")
    print("=" * 40)
    
    try:
        # 初始化交易引擎
        engine = TradingEngine(trading_mode='FUTURES', leverage=10)
        
        # 测试流动性检查
        print("\n1. 测试流动性检查")
        safe_symbols = ['BTCUSDT', 'ETHUSDT']
        problematic_symbols = ['FILUSDT']
        
        for symbol in safe_symbols:
            liquidity_ok = engine._check_liquidity(symbol)
            print(f"{symbol}: {'✅ 流动性正常' if liquidity_ok else '❌ 流动性不足'}")
        
        for symbol in problematic_symbols:
            liquidity_ok = engine._check_liquidity(symbol)
            print(f"{symbol}: {'✅ 流动性正常' if liquidity_ok else '❌ 流动性不足'}")
        
        # 测试安全数量计算
        print("\n2. 测试安全数量计算")
        for symbol in safe_symbols:
            try:
                price = engine.binance_client.get_ticker_price(symbol)
                if price:
                    safe_qty = engine._get_safe_quantity(symbol, price, 0.02)
                    print(f"{symbol}: 安全数量 {safe_qty:.6f} @ {price:.2f}")
                else:
                    print(f"{symbol}: 价格获取失败")
            except Exception as e:
                print(f"{symbol}: 计算失败 - {e}")
        
        # 测试策略添加
        print("\n3. 测试策略添加")
        for symbol in safe_symbols:
            try:
                result = engine.add_strategy(symbol, 'MA', {'position_size': 0.02})
                if result:
                    print(f"✅ {symbol} MA策略添加成功")
                else:
                    print(f"❌ {symbol} MA策略添加失败")
            except Exception as e:
                print(f"❌ {symbol} 策略添加异常: {e}")
        
        print("\n✅ 安全交易测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 安全交易测试失败: {e}")
        return False

def test_problematic_symbols():
    """测试问题交易对"""
    print("\n测试问题交易对")
    print("=" * 40)
    
    try:
        engine = TradingEngine(trading_mode='FUTURES', leverage=10)
        
        problematic_symbols = ['FILUSDT']
        
        for symbol in problematic_symbols:
            print(f"\n测试 {symbol}:")
            
            # 检查流动性
            liquidity_ok = engine._check_liquidity(symbol)
            print(f"  流动性: {'正常' if liquidity_ok else '不足'}")
            
            # 尝试获取价格
            try:
                price = engine.binance_client.get_ticker_price(symbol)
                if price:
                    print(f"  价格: {price:.6f}")
                    
                    # 尝试计算安全数量
                    safe_qty = engine._get_safe_quantity(symbol, price, 0.02)
                    print(f"  安全数量: {safe_qty:.6f}")
                    
                    # 尝试添加策略（应该被拒绝）
                    result = engine.add_strategy(symbol, 'MA', {'position_size': 0.02})
                    print(f"  策略添加: {'成功' if result else '失败（预期）'}")
                else:
                    print(f"  价格获取失败")
            except Exception as e:
                print(f"  测试异常: {e}")
        
        print("\n✅ 问题交易对测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 问题交易对测试失败: {e}")
        return False

def main():
    print("修复后的合约交易测试")
    print("=" * 50)
    
    config = Config()
    print(f"测试网络: {'是' if config.BINANCE_TESTNET else '否'}")
    print(f"合约API密钥: {'已设置' if config.BINANCE_API_KEY_FUTURES else '未设置'}")
    
    if not config.BINANCE_API_KEY_FUTURES:
        print("❌ 合约API密钥未设置")
        return
    
    # 运行测试
    test_safe_trading()
    test_problematic_symbols()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print("✅ 安全交易对应该正常工作")
    print("✅ 问题交易对应该被拒绝")
    print("✅ 订单数量应该满足最小要求")
    print("✅ 流动性检查应该生效")
    print("=" * 50)

if __name__ == "__main__":
    main()