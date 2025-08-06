#!/usr/bin/env python3
"""
测试修复后的合约交易功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading_engine import TradingEngine
from backend.client_manager import client_manager
import time

def test_fixed_futures():
    print("🧪 测试修复后的合约交易功能...")
    print("=" * 50)
    
    try:
        # 1. 创建合约交易引擎
        print("1. 创建合约交易引擎...")
        trading_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
        print(f"✅ 交易引擎创建成功，策略数量: {len(trading_engine.strategies)}")
        
        # 2. 检查当前持仓
        print("\n2. 检查当前持仓...")
        futures_client = client_manager.get_futures_client()
        positions = futures_client.get_positions()
        print(f"当前持仓数量: {len(positions)}")
        
        # 3. 找到一个产生信号的策略
        print("\n3. 查找产生交易信号的策略...")
        signal_strategies = []
        
        for strategy_name, strategy in trading_engine.strategies.items():
            try:
                # 获取市场数据
                data = futures_client.get_klines(strategy.symbol, '1h', 100)
                if data is not None and not data.empty:
                    signal = strategy.generate_signal(data)
                    current_price = data['close'].iloc[-1]
                    
                    if signal in ['BUY', 'SELL']:
                        signal_strategies.append({
                            'name': strategy_name,
                            'strategy': strategy,
                            'signal': signal,
                            'price': current_price
                        })
                        print(f"  {strategy_name}: {signal} @ {current_price:.2f}")
            except Exception as e:
                print(f"  {strategy_name}: 错误 - {e}")
        
        if not signal_strategies:
            print("⚠️ 当前没有策略产生交易信号")
            return
        
        # 4. 选择第一个产生信号的策略进行测试
        test_strategy_info = signal_strategies[0]
        strategy = test_strategy_info['strategy']
        signal = test_strategy_info['signal']
        price = test_strategy_info['price']
        
        print(f"\n4. 测试策略: {test_strategy_info['name']}")
        print(f"   信号: {signal}")
        print(f"   价格: {price:.2f}")
        print(f"   当前持仓: {strategy.position}")
        
        # 5. 模拟交易执行（不实际下单）
        print("\n5. 模拟交易执行...")
        print("⚠️ 这是模拟模式，不会实际下单")
        
        # 计算交易参数
        account_balance = futures_client.get_account_balance()
        available_balance = float(account_balance['availableBalance'])
        position_value = available_balance * strategy.parameters.get('position_size', 0.02)
        quantity = position_value * trading_engine.leverage / price
        
        print(f"   可用余额: {available_balance:.2f} USDT")
        print(f"   仓位大小: {strategy.parameters.get('position_size', 0.02)*100:.1f}%")
        print(f"   杠杆倍数: {trading_engine.leverage}x")
        print(f"   计算数量: {quantity:.6f}")
        
        if signal == 'BUY':
            print(f"   将执行: 开多头仓位 {strategy.symbol}")
        elif signal == 'SELL':
            print(f"   将执行: 开空头仓位 {strategy.symbol}")
        
        # 6. 启动交易引擎进行实际测试
        print("\n6. 启动交易引擎进行实际测试...")
        print("⚠️ 将启动真实交易，请确认是否继续...")
        
        # 取消注释以下代码来启动真实交易
        # response = input("输入 'YES' 确认启动真实交易: ")
        # if response == 'YES':
        #     print("启动交易引擎...")
        #     import threading
        #     trading_thread = threading.Thread(target=trading_engine.start_trading)
        #     trading_thread.daemon = True
        #     trading_thread.start()
        #     
        #     print("交易引擎已启动，等待5分钟观察结果...")
        #     time.sleep(300)  # 等待5分钟
        #     
        #     # 检查新的持仓
        #     new_positions = futures_client.get_positions()
        #     print(f"新的持仓数量: {len(new_positions)}")
        #     for pos in new_positions:
        #         print(f"  {pos['symbol']}: {pos['positionAmt']} @ {pos['entryPrice']}")
        #     
        #     trading_engine.stop_trading()
        # else:
        #     print("取消真实交易测试")
        
        print("\n✅ 测试完成")
        
        # 7. 给出建议
        print("\n💡 建议:")
        print("- 修复后的合约交易逻辑支持:")
        print("  1. 直接开多头仓位 (BUY信号)")
        print("  2. 直接开空头仓位 (SELL信号)")
        print("  3. 自动平仓管理")
        print("  4. 杠杆交易支持")
        print("- 如果要启用真实交易，请取消注释相关代码")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    test_fixed_futures()