#!/usr/bin/env python3
"""
诊断合约交易状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading_engine import TradingEngine
from backend.client_manager import client_manager
from datetime import datetime
import pandas as pd

def diagnose_futures_trading():
    print("🔍 诊断合约交易状态...")
    print("=" * 50)
    
    try:
        # 1. 检查合约客户端连接
        print("1. 检查合约客户端连接...")
        futures_client = client_manager.get_futures_client()
        
        # 测试API连接
        try:
            account_info = futures_client.get_account_balance()
            print(f"✅ 合约API连接正常")
            print(f"   总余额: {account_info['totalWalletBalance']} USDT")
            print(f"   可用余额: {account_info['availableBalance']} USDT")
            print(f"   未实现盈亏: {account_info['totalUnrealizedProfit']} USDT")
        except Exception as e:
            print(f"❌ 合约API连接失败: {e}")
            return
        
        # 2. 检查当前持仓
        print("\n2. 检查当前持仓...")
        positions = futures_client.get_positions()
        if positions:
            print(f"✅ 发现 {len(positions)} 个持仓:")
            for pos in positions:
                print(f"   {pos['symbol']}: {pos['positionAmt']} @ {pos['entryPrice']}")
                print(f"   未实现盈亏: {pos['unRealizedProfit']} USDT")
        else:
            print("⚠️ 当前无持仓")
        
        # 3. 检查交易引擎状态
        print("\n3. 检查交易引擎状态...")
        try:
            trading_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
            print(f"✅ 交易引擎初始化成功")
            print(f"   策略数量: {len(trading_engine.strategies)}")
            
            # 列出所有策略
            for strategy_name, strategy in trading_engine.strategies.items():
                print(f"   策略: {strategy_name}")
                print(f"     交易对: {strategy.symbol}")
                print(f"     当前持仓: {getattr(strategy, 'position', 0)}")
                print(f"     是否激活: {getattr(strategy, 'is_active', True)}")
        except Exception as e:
            print(f"❌ 交易引擎初始化失败: {e}")
            return
        
        # 4. 测试策略信号生成
        print("\n4. 测试策略信号生成...")
        test_symbols = ['BTCUSDT', 'ETHUSDT']
        
        for symbol in test_symbols:
            try:
                # 获取市场数据
                data = futures_client.get_klines(symbol, '1h', 100)
                if data is not None and not data.empty:
                    print(f"✅ {symbol} 数据获取成功，数据量: {len(data)}")
                    
                    # 测试策略信号
                    strategy_key = f"{symbol}_MA"
                    if strategy_key in trading_engine.strategies:
                        strategy = trading_engine.strategies[strategy_key]
                        signal = strategy.generate_signal(data)
                        print(f"   当前信号: {signal}")
                        
                        # 检查移动平均线
                        short_ma = data['close'].rolling(window=5).mean().iloc[-1]
                        long_ma = data['close'].rolling(window=15).mean().iloc[-1]
                        current_price = data['close'].iloc[-1]
                        
                        print(f"   当前价格: {current_price:.2f}")
                        print(f"   短期均线: {short_ma:.2f}")
                        print(f"   长期均线: {long_ma:.2f}")
                        print(f"   均线关系: {'短期>长期' if short_ma > long_ma else '短期<长期'}")
                else:
                    print(f"❌ {symbol} 数据获取失败")
            except Exception as e:
                print(f"❌ {symbol} 测试失败: {e}")
        
        # 5. 检查交易历史
        print("\n5. 检查交易历史...")
        try:
            from backend.database import DatabaseManager
            db = DatabaseManager()
            
            # 查询最近的交易记录
            recent_trades = db.get_recent_trades(limit=10)
            if recent_trades:
                print(f"✅ 发现 {len(recent_trades)} 条交易记录:")
                for trade in recent_trades[-5:]:  # 显示最近5条
                    print(f"   {trade['timestamp']}: {trade['symbol']} {trade['side']} {trade['quantity']} @ {trade['price']}")
            else:
                print("⚠️ 暂无交易记录")
        except Exception as e:
            print(f"❌ 查询交易历史失败: {e}")
        
        # 6. 模拟交易循环
        print("\n6. 模拟交易循环...")
        try:
            print("执行一次交易循环...")
            trading_engine._execute_trading_cycle()
            print("✅ 交易循环执行完成")
        except Exception as e:
            print(f"❌ 交易循环执行失败: {e}")
        
        print("\n" + "=" * 50)
        print("诊断完成！")
        
        # 给出建议
        print("\n💡 建议:")
        if not positions:
            print("- 当前无持仓可能的原因:")
            print("  1. 市场条件不满足策略信号触发条件")
            print("  2. 风险管理限制了交易执行")
            print("  3. 策略参数过于保守")
            print("  4. 数据获取或处理存在问题")
            print("- 建议:")
            print("  1. 检查策略参数设置")
            print("  2. 观察实时信号生成情况")
            print("  3. 考虑调整策略敏感度")
        
    except Exception as e:
        print(f"❌ 诊断过程出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    diagnose_futures_trading()