#!/usr/bin/env python3
"""
最终交易测试 - 强制执行一笔交易来验证系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading_engine import TradingEngine
from backend.client_manager import client_manager
from strategies.rsi_strategy import RSIStrategy

def force_execute_trade():
    print("🚀 强制执行交易测试...")
    print("=" * 50)
    
    try:
        # 1. 创建交易引擎
        trading_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
        futures_client = client_manager.get_futures_client()
        
        # 2. 选择一个策略进行测试
        symbol = 'BTCUSDT'
        print(f"测试交易对: {symbol}")
        
        # 获取市场数据
        data = futures_client.get_klines(symbol, '1h', 100)
        current_price = data['close'].iloc[-1]
        print(f"当前价格: {current_price:.2f}")
        
        # 3. 创建一个测试策略
        test_strategy = RSIStrategy(symbol, {
            'rsi_period': 10,
            'oversold': 35,
            'overbought': 65,
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'position_size': 0.01  # 使用很小的仓位进行测试
        })
        
        # 4. 生成信号
        signal = test_strategy.generate_signal(data)
        print(f"策略信号: {signal}")
        
        if signal == 'HOLD':
            print("当前信号是HOLD，强制设置为SELL进行测试")
            signal = 'SELL'
        
        # 5. 检查账户余额
        account_balance = futures_client.get_account_balance()
        print(f"可用余额: {account_balance['availableBalance']} USDT")
        
        # 6. 计算交易参数
        position_value = float(account_balance['availableBalance']) * test_strategy.parameters['position_size']
        quantity = position_value * trading_engine.leverage / current_price
        
        print(f"仓位大小: {test_strategy.parameters['position_size']*100}%")
        print(f"仓位价值: {position_value:.2f} USDT")
        print(f"杠杆倍数: {trading_engine.leverage}x")
        print(f"计算数量: {quantity:.6f} {symbol.replace('USDT', '')}")
        
        # 7. 检查最小交易量
        if quantity < 0.001:
            print("❌ 交易量太小，无法执行")
            return
        
        # 8. 执行交易（模拟模式）
        print(f"\n准备执行: {signal} {symbol} {quantity:.6f} @ {current_price:.2f}")
        print("⚠️ 这将是真实交易！")
        
        # 取消注释以下代码来执行真实交易
        response = input("输入 'EXECUTE' 来执行真实交易: ")
        if response == 'EXECUTE':
            print("执行交易...")
            
            try:
                success = trading_engine._execute_futures_trade(
                    test_strategy, 
                    signal, 
                    current_price, 
                    'MANUAL_TEST'
                )
                
                if success:
                    print("✅ 交易执行成功！")
                    
                    # 等待几秒钟然后检查持仓
                    import time
                    time.sleep(5)
                    
                    positions = futures_client.get_positions()
                    if positions:
                        print(f"✅ 发现持仓:")
                        for pos in positions:
                            print(f"  {pos['symbol']}: {pos['positionAmt']} @ {pos['entryPrice']}")
                    else:
                        print("⚠️ 交易执行成功但未发现持仓，可能需要等待")
                else:
                    print("❌ 交易执行失败")
                    
            except Exception as e:
                print(f"❌ 交易执行出错: {e}")
                import traceback
                print(f"错误详情: {traceback.format_exc()}")
        else:
            print("取消交易执行")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    force_execute_trade()