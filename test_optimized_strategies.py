#!/usr/bin/env python3
"""
测试优化后的策略参数
"""

import logging
from backend.trading_engine import TradingEngine

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_optimized_strategies():
    """测试优化后的策略"""
    print("🔍 测试优化后的策略参数...")
    
    try:
        # 创建交易引擎
        engine = TradingEngine()
        
        print(f"📊 策略数量: {len(engine.strategies)}")
        
        # 测试主要交易对的策略信号
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        for symbol in test_symbols:
            print(f"\n🔍 测试 {symbol} 的优化策略:")
            
            # 获取市场数据
            data = engine._get_enhanced_market_data(symbol)
            if data is None or data.empty:
                print(f"  ❌ 无法获取 {symbol} 市场数据")
                continue
            
            print(f"  ✅ 获取到 {len(data)} 条数据")
            current_price = data['close'].iloc[-1]
            print(f"  💰 当前价格: ${current_price:.4f}")
            
            # 测试优化后的策略
            strategy_types = ['MA', 'RSI', 'ML']
            signals_generated = []
            
            for strategy_type in strategy_types:
                strategy_key = f"{symbol}_{strategy_type}"
                if strategy_key in engine.strategies:
                    strategy = engine.strategies[strategy_key]
                    
                    try:
                        signal = strategy.generate_signal(data)
                        signals_generated.append(signal)
                        
                        # 显示策略参数
                        if strategy_type == 'MA':
                            params = f"短期窗口:{strategy.parameters['short_window']}, 长期窗口:{strategy.parameters['long_window']}"
                        elif strategy_type == 'RSI':
                            params = f"RSI周期:{strategy.parameters['rsi_period']}, 超卖:{strategy.parameters['oversold']}, 超买:{strategy.parameters['overbought']}"
                        elif strategy_type == 'ML':
                            params = f"信心阈值:{strategy.parameters['min_confidence']}, 上涨阈值:{strategy.parameters['up_threshold']}"
                        
                        print(f"  📊 {strategy_type}策略: {signal} ({params})")
                        
                        if signal in ['BUY', 'SELL']:
                            # 检查风险
                            risk_passed = engine._risk_check_passed(strategy, signal, current_price)
                            print(f"    🛡️ 风险检查: {'✅ 通过' if risk_passed else '❌ 未通过'}")
                            
                    except Exception as e:
                        print(f"  ❌ {strategy_type}策略测试失败: {e}")
            
            # 统计信号
            buy_signals = signals_generated.count('BUY')
            sell_signals = signals_generated.count('SELL')
            hold_signals = signals_generated.count('HOLD')
            
            print(f"  📈 信号统计: BUY={buy_signals}, SELL={sell_signals}, HOLD={hold_signals}")
            
            if buy_signals > 0 or sell_signals > 0:
                print(f"  ✅ {symbol} 有交易信号产生！")
            else:
                print(f"  ⚠️ {symbol} 暂无交易信号")
        
        # 总结
        print(f"\n📋 优化总结:")
        print(f"  - MA策略: 窗口从10/30改为5/15，更敏感")
        print(f"  - RSI策略: 周期从14改为10，阈值从30/70改为35/65")
        print(f"  - ML策略: 信心阈值从0.55降到0.45，价格阈值从1%降到0.5%")
        print(f"  - 所有策略: 止盈目标从5%降到4%")
        
        print(f"\n💡 建议:")
        print(f"  - 启动交易引擎后，策略会每分钟检查一次信号")
        print(f"  - 优化后的参数应该能产生更多交易机会")
        print(f"  - 如果仍无交易，可能是当前市场处于横盘状态")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    test_optimized_strategies()