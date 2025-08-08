#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟合约交易测试 - 重现用户遇到的错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.binance_client import BinanceClient
from config.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_small_order():
    """测试小额订单 - 模拟APIError -2010"""
    print("1. 测试小额订单")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        
        # 获取交易对信息以确定最小数量
        symbol = 'BTCUSDT'
        symbol_info = client._get_symbol_info(symbol)
        
        if symbol_info:
            # 获取最小数量
            min_qty = None
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    min_qty = float(f['minQty'])
                    break
            
            if min_qty:
                print(f"{symbol} 最小数量: {min_qty}")
                quantity = min_qty * 2  # 使用2倍最小数量
            else:
                quantity = 0.001  # 默认值
        else:
            quantity = 0.001
        
        print(f"尝试下单: {symbol} BUY {quantity}")
        
        order = client.place_order(
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            order_type='MARKET',
            position_side='LONG'
        )
        
        if order:
            print("✅ 小额订单成功")
        else:
            print("❌ 小额订单失败")
            
    except Exception as e:
        print(f"❌ 小额订单异常: {e}")

def test_liquidity_check():
    """测试流动性检查 - 模拟FILUSDT流动性不足"""
    print("\n2. 测试流动性检查")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        
        # 测试FILUSDT的流动性
        symbol = 'FILUSDT'
        
        # 获取订单簿数据
        try:
            order_book = client.client.futures_order_book(symbol=symbol, limit=5)
            print(f"✅ {symbol} 订单簿获取成功")
            print(f"   买一价: {order_book['bids'][0][0]}")
            print(f"   卖一价: {order_book['asks'][0][0]}")
            spread = float(order_book['asks'][0][0]) - float(order_book['bids'][0][0])
            print(f"   买卖价差: {spread:.6f}")
            
            if spread > 0.1:  # 价差超过0.1认为流动性不足
                print("   ⚠️ 流动性不足警告")
            else:
                print("   ✅ 流动性正常")
                
        except Exception as e:
            print(f"❌ {symbol} 订单簿获取失败: {e}")
            
    except Exception as e:
        print(f"❌ 流动性检查失败: {e}")

def test_network_issues():
    """测试网络连接问题"""
    print("\n3. 测试网络连接")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        
        # 测试数据获取
        symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
        
        for symbol in symbols:
            try:
                # 获取K线数据
                klines = client.get_klines(symbol, '1m', 1)
                if klines is not None and not klines.empty:
                    print(f"✅ {symbol} 数据获取正常")
                else:
                    print(f"❌ {symbol} 数据获取失败")
            except Exception as e:
                print(f"❌ {symbol} 数据获取异常: {e}")
                
    except Exception as e:
        print(f"❌ 网络连接测试失败: {e}")

def test_leverage_requirements():
    """测试不同杠杆倍数的要求"""
    print("\n4. 测试杠杆要求")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        
        # 获取当前持仓
        positions = client.get_positions()
        has_positions = any(float(pos['positionAmt']) != 0 for pos in positions)
        
        if has_positions:
            print("⚠️ 当前有持仓，只能增加杠杆不能减少")
        
        # 测试不同杠杆倍数
        test_leverages = [10, 20, 50, 100]  # 只测试增加杠杆
        
        for leverage in test_leverages:
            try:
                result = client.set_leverage('BTCUSDT', leverage)
                if result:
                    print(f"✅ {leverage}x 杠杆设置成功")
                else:
                    print(f"❌ {leverage}x 杠杆设置失败")
            except Exception as e:
                print(f"❌ {leverage}x 杠杆设置异常: {e}")
                
    except Exception as e:
        print(f"❌ 杠杆要求测试失败: {e}")

def test_minimum_balance():
    """测试最小余额要求"""
    print("\n5. 测试最小余额要求")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        
        # 获取账户信息
        account = client.get_account_balance()
        available = float(account['availableBalance'])
        
        print(f"当前可用余额: {available:.2f} USDT")
        
        # 计算不同杠杆下的最小保证金
        test_leverages = [1, 5, 10, 20]
        symbol = 'BTCUSDT'
        
        try:
            price = client.get_ticker_price(symbol)
            if price:
                print(f"{symbol} 当前价格: {price:.2f}")
                
                for leverage in test_leverages:
                    # 计算最小保证金（假设最小订单为0.001 BTC）
                    min_quantity = 0.001
                    min_margin = (min_quantity * price) / leverage
                    print(f"   {leverage}x 杠杆最小保证金: {min_margin:.4f} USDT")
                    
                    if available >= min_margin:
                        print(f"   ✅ 余额足够进行 {leverage}x 杠杆交易")
                    else:
                        print(f"   ❌ 余额不足进行 {leverage}x 杠杆交易")
                        
        except Exception as e:
            print(f"❌ 价格获取失败: {e}")
            
    except Exception as e:
        print(f"❌ 最小余额测试失败: {e}")

def test_api_permissions():
    """测试API权限"""
    print("\n6. 测试API权限")
    try:
        client = BinanceClient(trading_mode='FUTURES')
        
        # 测试读取权限
        print("测试读取权限:")
        try:
            account = client.get_account_balance()
            print("   ✅ 账户信息读取权限正常")
        except Exception as e:
            print(f"   ❌ 账户信息读取权限异常: {e}")
            
        try:
            positions = client.get_positions()
            print("   ✅ 持仓信息读取权限正常")
        except Exception as e:
            print(f"   ❌ 持仓信息读取权限异常: {e}")
            
        # 测试交易权限（不实际下单）
        print("\n测试交易权限:")
        try:
            symbol_info = client._get_symbol_info('BTCUSDT')
            if symbol_info:
                print("   ✅ 交易对信息读取权限正常")
            else:
                print("   ❌ 交易对信息读取权限异常")
        except Exception as e:
            print(f"   ❌ 交易对信息读取权限异常: {e}")
            
    except Exception as e:
        print(f"❌ API权限测试失败: {e}")

def main():
    print("合约交易模拟测试")
    print("=" * 40)
    
    config = Config()
    print(f"测试网络: {'是' if config.BINANCE_TESTNET else '否'}")
    print(f"合约API密钥: {'已设置' if config.BINANCE_API_KEY_FUTURES else '未设置'}")
    
    if not config.BINANCE_API_KEY_FUTURES:
        print("❌ 合约API密钥未设置")
        return
        
    test_small_order()
    test_liquidity_check()
    test_network_issues()
    test_leverage_requirements()
    test_minimum_balance()
    test_api_permissions()
    
    print("\n模拟测试完成")

if __name__ == "__main__":
    main()
