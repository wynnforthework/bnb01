#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复合约交易问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.binance_client import BinanceClient
from config.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_quantity_precision():
    """修复数量精度问题"""
    print("1. 修复数量精度问题")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        symbol = 'BTCUSDT'
        symbol_info = client._get_symbol_info(symbol)
        
        if symbol_info:
            min_qty = None
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    min_qty = float(f['minQty'])
                    break
            
            safe_quantity = min_qty * 10
            print(f"{symbol} 最小数量: {min_qty}")
            print(f"建议订单数量: {safe_quantity}")
            return safe_quantity
        else:
            print(f"❌ 无法获取 {symbol} 信息")
            return None
    except Exception as e:
        print(f"❌ 修复精度失败: {e}")
        return None

def fix_leverage_issue():
    """修复杠杆设置问题"""
    print("\n2. 修复杠杆设置问题")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        positions = client.get_positions()
        active_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        
        if active_positions:
            print("当前有持仓，无法降低杠杆")
            print("建议先平仓再设置杠杆")
            return False
        else:
            print("✅ 无持仓，可以设置杠杆")
            result = client.set_leverage('BTCUSDT', 10)
            if result:
                print("✅ 设置10x杠杆成功")
                return True
            else:
                print("❌ 设置杠杆失败")
                return False
    except Exception as e:
        print(f"❌ 修复杠杆失败: {e}")
        return False

def fix_liquidity_issue():
    """修复流动性问题"""
    print("\n3. 修复流动性问题")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        symbol = 'FILUSDT'
        
        order_book = client.client.futures_order_book(symbol=symbol, limit=5)
        bid_price = float(order_book['bids'][0][0])
        ask_price = float(order_book['asks'][0][0])
        spread = ask_price - bid_price
        spread_percent = (spread / bid_price) * 100
        
        print(f"{symbol} 价差: {spread_percent:.2f}%")
        
        if spread_percent > 5:
            print("⚠️ 流动性不足，建议避免交易")
        else:
            print("✅ 流动性正常")
    except Exception as e:
        print(f"❌ 检查流动性失败: {e}")

def main():
    print("合约交易问题修复")
    print("=" * 30)
    
    config = Config()
    print(f"测试网络: {'是' if config.BINANCE_TESTNET else '否'}")
    
    if not config.BINANCE_API_KEY_FUTURES:
        print("❌ 合约API密钥未设置")
        return
    
    fix_quantity_precision()
    fix_leverage_issue()
    fix_liquidity_issue()
    
    print("\n修复建议:")
    print("1. 使用安全交易对: BTCUSDT, ETHUSDT")
    print("2. 避免FILUSDT等流动性不足的币种")
    print("3. 确保订单数量满足最小要求")
    print("4. 有持仓时不要降低杠杆")
    
    print("\n修复完成")

if __name__ == "__main__":
    main()