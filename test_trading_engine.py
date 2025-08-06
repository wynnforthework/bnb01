#!/usr/bin/env python3
"""
测试交易引擎执行
"""

import logging
from backend.trading_engine import TradingEngine
from backend.binance_client import BinanceClient
from backend.database import DatabaseManager
from strategies.ma_strategy import MovingAverageStrategy

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_trading_execution():
    """测试交易执行"""
    print("🧪 测试交易引擎执行...")
    
    try:
        # 1. 创建一个测试策略，强制产生BUY信号
        print("\n1️⃣ 创建测试策略...")
        
        # 创建一个修改过的MA策略，更容易产生BUY信号
        class TestMAStrategy(MovingAverageStrategy):
            def generate_signal(self, data):
                """强制产生BUY信号用于测试"""
                if len(data) < max(self.parameters['short_window'], self.parameters['long_window']):
                    return 'HOLD'
                
                # 计算移动平均线
                short_ma = data['close'].rolling(window=self.parameters['short_window']).mean()
                long_ma = data['close'].rolling(window=self.parameters['long_window']).mean()
                
                current_short = short_ma.iloc[-1]
                current_long = long_ma.iloc[-1]
                prev_short = short_ma.iloc[-2]
                prev_long = long_ma.iloc[-2]
                
                # 放宽买入条件
                if current_short > current_long * 0.999:  # 只要短期MA接近长期MA就买入
                    return 'BUY'
                elif current_short < current_long * 0.995:  # 短期MA明显低于长期MA就卖出
                    return 'SELL'
                
                return 'HOLD'
        
        # 创建测试策略
        test_strategy = TestMAStrategy(
            symbol='BTCUSDT',
            parameters={
                'short_window': 5,
                'long_window': 10,
                'stop_loss': 0.02,
                'take_profit': 0.04,
                'position_size': 0.05
            }
        )
        
        print(f"✅ 测试策略创建成功: {test_strategy.symbol}")
        
        # 2. 创建交易引擎
        print("\n2️⃣ 创建交易引擎...")
        engine = TradingEngine()
        
        # 添加测试策略
        engine.strategies['TEST_BTCUSDT_MA'] = test_strategy
        print(f"✅ 测试策略已添加到交易引擎")
        
        # 3. 获取市场数据并测试信号
        print("\n3️⃣ 测试信号生成...")
        data = engine._get_enhanced_market_data('BTCUSDT')
        
        if data is not None and not data.empty and len(data) > 20:
            signal = test_strategy.generate_signal(data)
            current_price = data['close'].iloc[-1]
            
            print(f"📊 当前价格: ${current_price:.2f}")
            print(f"🎯 生成信号: {signal}")
            
            if signal == 'BUY':
                print(f"✅ 成功生成BUY信号！")
                
                # 4. 测试风险检查
                print("\n4️⃣ 测试风险检查...")
                risk_passed = engine._risk_check_passed(test_strategy, signal, current_price)
                print(f"🛡️ 风险检查: {'✅ 通过' if risk_passed else '❌ 未通过'}")
                
                if risk_passed:
                    # 5. 执行实际交易
                    print("\n5️⃣ 执行实际交易...")
                    
                    # 检查初始余额
                    binance_client = BinanceClient()
                    initial_balance = binance_client.get_balance('USDT')
                    print(f"💰 初始USDT余额: ${initial_balance:.2f}")
                    
                    # 执行交易
                    try:
                        engine._execute_enhanced_trade(test_strategy, signal, current_price, 'TEST_EXECUTION')
                        print(f"🚀 交易执行完成！")
                        
                        # 检查交易后状态
                        import time
                        time.sleep(2)  # 等待交易处理
                        
                        # 检查余额变化
                        new_balance = binance_client.get_balance('USDT')
                        print(f"💰 交易后USDT余额: ${new_balance:.2f}")
                        print(f"💸 余额变化: ${initial_balance - new_balance:.2f}")
                        
                        # 检查数据库记录
                        db_manager = DatabaseManager()
                        recent_trades = db_manager.get_trades(limit=5)
                        
                        print(f"\n📈 最近交易记录:")
                        for trade in recent_trades:
                            print(f"  {trade.timestamp.strftime('%H:%M:%S')} - {trade.symbol} {trade.side} {trade.quantity:.6f} @ ${trade.price:.2f}")
                        
                        # 检查持仓
                        positions = db_manager.get_positions()
                        print(f"\n💼 当前持仓:")
                        for pos in positions:
                            print(f"  {pos.symbol}: {pos.quantity:.6f} @ ${pos.avg_price:.2f}")
                        
                        if len(recent_trades) > 0 or len(positions) > 0:
                            print(f"\n🎉 交易执行成功！系统正常工作！")
                            return True
                        else:
                            print(f"\n⚠️ 交易可能没有实际执行")
                            
                    except Exception as e:
                        print(f"❌ 交易执行失败: {e}")
                        import traceback
                        print(f"错误详情: {traceback.format_exc()}")
                        
                else:
                    print(f"❌ 风险检查未通过，无法执行交易")
                    
            else:
                print(f"⚠️ 没有生成BUY信号，当前信号: {signal}")
                
                # 尝试调整策略参数使其产生BUY信号
                print(f"\n🔧 尝试调整策略参数...")
                
                # 创建一个总是产生BUY信号的测试策略
                class ForceBuyStrategy(MovingAverageStrategy):
                    def generate_signal(self, data):
                        return 'BUY'  # 强制返回BUY信号
                
                force_buy_strategy = ForceBuyStrategy(
                    symbol='BTCUSDT',
                    parameters={
                        'short_window': 5,
                        'long_window': 10,
                        'stop_loss': 0.02,
                        'take_profit': 0.04,
                        'position_size': 0.01  # 小仓位测试
                    }
                )
                
                signal = force_buy_strategy.generate_signal(data)
                print(f"🎯 强制信号: {signal}")
                
                if signal == 'BUY':
                    risk_passed = engine._risk_check_passed(force_buy_strategy, signal, current_price)
                    print(f"🛡️ 风险检查: {'✅ 通过' if risk_passed else '❌ 未通过'}")
                    
                    if risk_passed:
                        print(f"🚀 执行强制买入测试...")
                        engine._execute_enhanced_trade(force_buy_strategy, signal, current_price, 'FORCE_BUY_TEST')
                        
                        # 检查结果
                        import time
                        time.sleep(2)
                        
                        db_manager = DatabaseManager()
                        recent_trades = db_manager.get_trades(limit=3)
                        
                        if len(recent_trades) > 0:
                            print(f"🎉 强制买入测试成功！")
                            for trade in recent_trades:
                                print(f"  📈 {trade.symbol} {trade.side} {trade.quantity:.6f} @ ${trade.price:.2f}")
                            return True
                        else:
                            print(f"❌ 强制买入测试失败")
        else:
            print(f"❌ 无法获取足够的市场数据")
        
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_trading_execution()
    
    if success:
        print(f"\n✅ 交易引擎测试成功！系统可以正常执行交易。")
        print(f"💡 建议: 现在可以启动完整的交易系统，等待市场条件产生真实的交易信号。")
    else:
        print(f"\n❌ 交易引擎测试失败，需要进一步调试。")