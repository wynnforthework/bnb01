#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合约交易问题诊断脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.binance_client import BinanceClient
from config.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_futures_connection():
    """测试合约API连接"""
    print("1. 测试合约API连接")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        account = client.get_account_balance()
        if account:
            print(f"✅ 连接成功 - 可用余额: {account['availableBalance']:.2f} USDT")
        else:
            print("❌ 获取账户信息失败")
    except Exception as e:
        print(f"❌ 连接失败: {e}")

def test_leverage():
    """测试杠杆设置"""
    print("\n2. 测试杠杆设置")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        result = client.set_leverage('BTCUSDT', 10)
        if result:
            print("✅ 杠杆设置成功")
        else:
            print("❌ 杠杆设置失败")
    except Exception as e:
        print(f"❌ 杠杆设置异常: {e}")

def test_min_order():
    """测试最小订单"""
    print("\n3. 测试最小订单量")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        account = client.get_account_balance()
        available = float(account['availableBalance'])
        print(f"可用余额: {available:.2f} USDT")
        
        if available < 5:
            print("⚠️ 余额不足，建议充值到测试网")
        else:
            print("✅ 余额充足")
    except Exception as e:
        print(f"❌ 余额检查失败: {e}")

def main():
    print("合约交易问题诊断")
    print("=" * 30)
    
    config = Config()
    print(f"测试网络: {'是' if config.BINANCE_TESTNET else '否'}")
    print(f"合约API密钥: {'已设置' if config.BINANCE_API_KEY_FUTURES else '未设置'}")
    
    if not config.BINANCE_API_KEY_FUTURES:
        print("❌ 合约API密钥未设置")
        return
        
    test_futures_connection()
    test_leverage()
    test_min_order()
    
    print("\n诊断完成")

if __name__ == "__main__":
    main()
