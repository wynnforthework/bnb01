#!/usr/bin/env python3
"""
诊断交易执行问题
"""

import logging
from backend.trading_engine import TradingEngine
from backend.binance_client import BinanceClient
from backend.risk_manager import RiskManager
from strategies.rsi_strategy import RSIStrategy
from strategies.ma_strategy import MovingAverageStrategy

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def diagnose_trading_issues():
    """诊断交易执行问题"""
    print("🔍 诊断交易执行问题...")
    
    try:
        # 1. 检查交易引擎初始化
        print("\n1️⃣ 检查交易引擎...")
        engine = TradingEngine()
        print(f"✅ 交易引擎初始化成功，策略数量: {len(engine.strategies)}")
        
        # 2. 检查币安连接
        print("\n2️⃣ 检查币安连接...")
        binance_client = BinanceClient()
        balance = binance_client.get_balance('USDT')
        print(f"✅ 币安连接正常，USDT余额: ${balance:.2f}")
        
        # 3. 检查策略信号生成
        print("\n3️⃣ 检查策略信号生成...")
        signal_count = 0
        for strategy_name, strategy in engine.strategies.items():
            try:
                data = engine._get_enhanced_market_data(strategy.symbol)
                if data is not None and not data.empty and len(data) > 50:
                    signal = strategy.generate_signal(data)
                    if signal in ['BUY', 'SELL']:
                        signal_count += 1
                        current_price = data['close'].iloc[-1]
                        print(f"  📊 {strategy_name}: {signal} @ ${current_price:.4f}")
                        
                        # 4. 检查风险管理
                        risk_manager = RiskManager()
                        portfolio_value = risk_manager._get_portfolio_value()
                        suggested_quantity = risk_manager.calculate_position_size(
                            strategy.symbol, 1.0, current_price, portfolio_value
                        )
                        
                        passed, message = risk_manager.check_risk_limits(
                            strategy.symbol, suggested_quantity, current_price
                        )
                        
                        print(f"    💰 建议仓位: {suggested_quantity:.6f}")
                        print(f"    🛡️ 风险检查: {'✅' if passed else '❌'} {message}")
                        
                        # 5. 模拟订单执行
                        if passed and suggested_quantity > 0:
                            print(f"    🔄 模拟执行交易...")
                            
                            # 检查是否会实际下单
                            if signal == 'BUY' and strategy.position <= 0:
                                print(f"    ✅ 满足买入条件")
                                
                                # 检查订单执行逻辑
                                print(f"    📋 订单详情:")
                                print(f"      - 交易对: {strategy.symbol}")
                                print(f"      - 方向: BUY")
                                print(f"      - 数量: {suggested_quantity:.6f}")
                                print(f"      - 价格: ${current_price:.4f}")
                                print(f"      - 总价值: ${suggested_quantity * current_price:.2f}")
                                
                                # 检查是否有阻止交易的条件
                                if strategy.position > 0:
                                    print(f"    ⚠️ 已有持仓，跳过买入")
                                else:
                                    print(f"    🚀 应该执行买入交易！")
                                    
                            elif signal == 'SELL' and strategy.position > 0:
                                print(f"    ✅ 满足卖出条件")
                                print(f"    🚀 应该执行卖出交易！")
                            else:
                                print(f"    ⚠️ 不满足交易条件:")
                                print(f"      - 信号: {signal}")
                                print(f"      - 当前持仓: {strategy.position}")
                        else:
                            print(f"    ❌ 不满足交易条件")
                            
            except Exception as e:
                print(f"  ❌ {strategy_name} 检查失败: {e}")
        
        print(f"\n📊 总结: 发现 {signal_count} 个交易信号")
        
        # 6. 检查实际交易执行逻辑
        print("\n4️⃣ 检查实际交易执行...")
        
        # 找一个有BUY信号的策略进行深度测试
        test_strategy = None
        test_signal = None
        test_data = None
        
        for strategy_name, strategy in engine.strategies.items():
            try:
                data = engine._get_enhanced_market_data(strategy.symbol)
                if data is not None and not data.empty and len(data) > 50:
                    signal = strategy.generate_signal(data)
                    if signal == 'BUY' and strategy.position <= 0:
                        test_strategy = strategy
                        test_signal = signal
                        test_data = data
                        print(f"  🎯 选择测试策略: {strategy_name}")
                        break
            except:
                continue
        
        if test_strategy:
            current_price = test_data['close'].iloc[-1]
            print(f"  💰 当前价格: ${current_price:.4f}")
            
            # 检查风险检查是否通过
            risk_passed = engine._risk_check_passed(test_strategy, test_signal, current_price)
            print(f"  🛡️ 风险检查: {'✅ 通过' if risk_passed else '❌ 未通过'}")
            
            if risk_passed:
                print(f"  🚀 理论上应该执行交易！")
                print(f"\n💡 可能的问题:")
                print(f"    1. 交易引擎没有持续运行")
                print(f"    2. 订单执行时出现异常")
                print(f"    3. 币安API限制或网络问题")
                print(f"    4. 测试网络的特殊限制")
                
                # 尝试实际执行一次交易看看会发生什么
                print(f"\n🧪 尝试执行测试交易...")
                try:
                    # 模拟执行交易
                    engine._execute_enhanced_trade(test_strategy, test_signal, current_price, 'DIAGNOSTIC_TEST')
                    print(f"  ✅ 测试交易执行完成")
                except Exception as e:
                    print(f"  ❌ 测试交易执行失败: {e}")
                    import traceback
                    print(f"  错误详情: {traceback.format_exc()}")
        else:
            print(f"  ⚠️ 没有找到合适的测试策略")
        
        return True
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    diagnose_trading_issues()