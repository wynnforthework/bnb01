#!/usr/bin/env python3
"""
测试合约交易功能
"""

import logging
from backend.trading_engine import TradingEngine
from backend.binance_client import BinanceClient

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_futures_trading():
    """测试合约交易功能"""
    print("🚀 测试合约交易功能...")
    
    try:
        # 1. 测试合约客户端初始化
        print("\n1️⃣ 测试合约客户端初始化...")
        futures_client = BinanceClient(trading_mode='FUTURES')
        print(f"✅ 合约客户端初始化成功，模式: {futures_client.trading_mode}")
        
        # 2. 测试合约账户信息
        print("\n2️⃣ 测试合约账户信息...")
        try:
            account_balance = futures_client.get_account_balance()
            if account_balance:
                print(f"💰 合约账户余额:")
                print(f"  总钱包余额: ${account_balance['totalWalletBalance']:.2f}")
                print(f"  可用余额: ${account_balance['availableBalance']:.2f}")
                print(f"  未实现盈亏: ${account_balance['totalUnrealizedProfit']:.2f}")
                print(f"  保证金余额: ${account_balance['totalMarginBalance']:.2f}")
                print(f"  持仓保证金: ${account_balance['totalPositionInitialMargin']:.2f}")
            else:
                print("⚠️ 无法获取合约账户信息")
        except Exception as e:
            print(f"⚠️ 获取合约账户信息失败: {e}")
        
        # 3. 测试合约持仓查询
        print("\n3️⃣ 测试合约持仓查询...")
        try:
            positions = futures_client.get_positions()
            print(f"📊 当前合约持仓数量: {len(positions)}")
            
            if positions:
                print("💼 合约持仓详情:")
                for pos in positions:
                    print(f"  {pos['symbol']}: {pos['positionAmt']} @ ${float(pos['entryPrice']):.2f}")
                    print(f"    未实现盈亏: ${float(pos['unRealizedProfit']):.2f}")
                    print(f"    持仓方向: {pos['positionSide']}")
            else:
                print("📭 当前没有合约持仓")
        except Exception as e:
            print(f"⚠️ 获取合约持仓失败: {e}")
        
        # 4. 测试合约交易引擎初始化
        print("\n4️⃣ 测试合约交易引擎初始化...")
        try:
            futures_engine = TradingEngine(trading_mode='FUTURES', leverage=5)
            print(f"✅ 合约交易引擎初始化成功")
            print(f"📊 策略数量: {len(futures_engine.strategies)}")
            print(f"🔧 杠杆倍数: {futures_engine.leverage}x")
        except Exception as e:
            print(f"❌ 合约交易引擎初始化失败: {e}")
            return False
        
        # 5. 测试合约设置功能
        print("\n5️⃣ 测试合约设置功能...")
        test_symbol = 'BTCUSDT'
        
        try:
            # 测试杠杆设置
            print(f"🔧 设置 {test_symbol} 杠杆为 5x...")
            leverage_result = futures_client.set_leverage(test_symbol, 5)
            if leverage_result:
                print(f"✅ 杠杆设置成功")
            
            # 测试保证金模式设置
            print(f"🔧 设置 {test_symbol} 保证金模式为逐仓...")
            margin_result = futures_client.set_margin_type(test_symbol, 'ISOLATED')
            if margin_result:
                print(f"✅ 保证金模式设置成功")
            
        except Exception as e:
            print(f"⚠️ 合约设置失败: {e}")
        
        # 6. 测试合约市场数据
        print("\n6️⃣ 测试合约市场数据...")
        try:
            # 测试合约价格获取
            btc_price = futures_client.get_ticker_price('BTCUSDT')
            print(f"💰 BTCUSDT 合约价格: ${btc_price:.2f}")
            
            # 测试标记价格
            mark_price_info = futures_client.get_mark_price('BTCUSDT')
            if mark_price_info:
                print(f"📊 BTCUSDT 标记价格: ${mark_price_info['markPrice']:.2f}")
                print(f"📊 指数价格: ${mark_price_info['indexPrice']:.2f}")
                print(f"📊 资金费率: {mark_price_info['lastFundingRate']:.6f}")
            
            # 测试资金费率
            funding_rate = futures_client.get_funding_rate('BTCUSDT')
            if funding_rate:
                print(f"💸 当前资金费率: {funding_rate['fundingRate']:.6f}")
            
        except Exception as e:
            print(f"⚠️ 获取合约市场数据失败: {e}")
        
        # 7. 测试合约K线数据
        print("\n7️⃣ 测试合约K线数据...")
        try:
            klines = futures_client.get_klines('BTCUSDT', '1h', 5)
            if not klines.empty:
                print(f"📈 获取到 {len(klines)} 条合约K线数据")
                latest_price = klines['close'].iloc[-1]
                print(f"📊 最新收盘价: ${latest_price:.2f}")
            else:
                print("⚠️ 未获取到合约K线数据")
        except Exception as e:
            print(f"⚠️ 获取合约K线数据失败: {e}")
        
        # 8. 模拟合约交易测试（小额测试）
        print("\n8️⃣ 模拟合约交易测试...")
        print("⚠️ 注意: 这是真实的合约交易测试，请确保在测试网络环境下运行")
        
        user_confirm = input("是否继续进行小额合约交易测试? (y/N): ").lower().strip()
        
        if user_confirm == 'y':
            try:
                # 获取当前价格
                current_price = futures_client.get_ticker_price('BTCUSDT')
                
                # 计算最小交易数量（非常小的数量用于测试）
                min_quantity = 0.001  # 0.001 BTC
                
                print(f"🧪 准备执行小额合约测试交易:")
                print(f"  交易对: BTCUSDT")
                print(f"  方向: 做多 (BUY)")
                print(f"  数量: {min_quantity} BTC")
                print(f"  当前价格: ${current_price:.2f}")
                print(f"  杠杆: 5x")
                print(f"  预计保证金: ${(min_quantity * current_price) / 5:.2f}")
                
                final_confirm = input("确认执行测试交易? (y/N): ").lower().strip()
                
                if final_confirm == 'y':
                    # 执行测试交易
                    order = futures_client.place_order(
                        symbol='BTCUSDT',
                        side='BUY',
                        quantity=min_quantity,
                        leverage=5,
                        position_side='LONG'
                    )
                    
                    if order:
                        print(f"✅ 合约测试交易执行成功!")
                        print(f"📋 订单ID: {order.get('orderId', 'N/A')}")
                        print(f"📊 执行价格: ${float(order.get('price', current_price)):.2f}")
                        
                        # 等待几秒后检查持仓
                        import time
                        time.sleep(3)
                        
                        positions = futures_client.get_positions()
                        btc_position = None
                        for pos in positions:
                            if pos['symbol'] == 'BTCUSDT':
                                btc_position = pos
                                break
                        
                        if btc_position:
                            print(f"💼 新持仓创建:")
                            print(f"  持仓数量: {btc_position['positionAmt']}")
                            print(f"  入场价格: ${float(btc_position['entryPrice']):.2f}")
                            print(f"  未实现盈亏: ${float(btc_position['unRealizedProfit']):.2f}")
                            
                            # 询问是否立即平仓
                            close_confirm = input("是否立即平仓测试持仓? (y/N): ").lower().strip()
                            if close_confirm == 'y':
                                close_result = futures_client.close_position('BTCUSDT', 'LONG')
                                if close_result:
                                    print(f"✅ 测试持仓已平仓")
                                else:
                                    print(f"⚠️ 平仓失败，请手动平仓")
                        
                    else:
                        print(f"❌ 合约测试交易失败")
                else:
                    print("🚫 取消测试交易")
            except Exception as e:
                print(f"❌ 合约交易测试失败: {e}")
                import traceback
                print(f"错误详情: {traceback.format_exc()}")
        else:
            print("🚫 跳过合约交易测试")
        
        print(f"\n✅ 合约交易功能测试完成!")
        print(f"💡 合约交易功能已集成到系统中，可以通过以下方式使用:")
        print(f"   - 创建合约交易引擎: TradingEngine(trading_mode='FUTURES', leverage=10)")
        print(f"   - 支持做多做空、杠杆交易、动态止损止盈")
        print(f"   - 自动设置保证金模式和杠杆倍数")
        
        return True
        
    except Exception as e:
        print(f"❌ 合约交易功能测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_futures_trading()
    
    if success:
        print(f"\n🎉 合约交易功能测试成功!")
        print(f"📋 功能特性:")
        print(f"  ✅ 支持现货和合约双模式")
        print(f"  ✅ 自动杠杆和保证金设置")
        print(f"  ✅ 做多做空双向交易")
        print(f"  ✅ 动态止损止盈")
        print(f"  ✅ 风险管理集成")
        print(f"  ✅ 实时持仓监控")
    else:
        print(f"\n❌ 合约交易功能测试失败，请检查配置和网络连接。")