#!/usr/bin/env python3
"""
修复合约交易逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading_engine import TradingEngine
from backend.client_manager import client_manager

def fix_futures_trading_logic():
    """修复合约交易逻辑"""
    print("🔧 修复合约交易逻辑...")
    
    # 创建一个修复版的交易执行方法
    def _execute_futures_trade(self, strategy, action, price, reason):
        """执行合约交易（支持做多和做空）"""
        try:
            account_balance = self.binance_client.get_account_balance()
            available_balance = float(account_balance['availableBalance'])
            
            # 计算仓位大小
            position_value = available_balance * strategy.parameters.get('position_size', 0.02)
            quantity = position_value / price
            
            # 最小交易量检查
            if quantity < 0.001:  # 根据交易对调整最小量
                self.logger.warning(f"交易量太小: {quantity}, 跳过交易")
                return False
            
            if action == 'BUY':
                # 开多头仓位或平空头仓位
                if strategy.position <= 0:  # 无仓位或有空头仓位
                    # 如果有空头仓位，先平仓
                    if strategy.position < 0:
                        close_quantity = abs(strategy.position)
                        close_order = self.binance_client.place_futures_order(
                            symbol=strategy.symbol,
                            side='BUY',
                            quantity=close_quantity,
                            position_side='SHORT'
                        )
                        if close_order:
                            self.logger.info(f"平空头仓位 {strategy.symbol}: {close_quantity}")
                            strategy.position = 0
                    
                    # 开多头仓位
                    order = self.binance_client.place_futures_order(
                        symbol=strategy.symbol,
                        side='BUY',
                        quantity=quantity,
                        position_side='LONG'
                    )
                    
                    if order:
                        strategy.position = quantity
                        strategy.entry_price = price
                        self.logger.info(f"开多头仓位 {strategy.symbol}: {quantity} @ {price}")
                        return True
            
            elif action == 'SELL':
                # 开空头仓位或平多头仓位
                if strategy.position >= 0:  # 无仓位或有多头仓位
                    # 如果有多头仓位，先平仓
                    if strategy.position > 0:
                        close_quantity = strategy.position
                        close_order = self.binance_client.place_futures_order(
                            symbol=strategy.symbol,
                            side='SELL',
                            quantity=close_quantity,
                            position_side='LONG'
                        )
                        if close_order:
                            self.logger.info(f"平多头仓位 {strategy.symbol}: {close_quantity}")
                            strategy.position = 0
                    
                    # 开空头仓位
                    order = self.binance_client.place_futures_order(
                        symbol=strategy.symbol,
                        side='SELL',
                        quantity=quantity,
                        position_side='SHORT'
                    )
                    
                    if order:
                        strategy.position = -quantity  # 负数表示空头仓位
                        strategy.entry_price = price
                        self.logger.info(f"开空头仓位 {strategy.symbol}: {quantity} @ {price}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"执行合约交易失败: {e}")
            return False
    
    # 将修复的方法绑定到TradingEngine类
    TradingEngine._execute_futures_trade = _execute_futures_trade
    
    print("✅ 合约交易逻辑修复完成")
    return True

def test_fixed_trading():
    """测试修复后的交易逻辑"""
    print("\n🧪 测试修复后的交易逻辑...")
    
    try:
        # 修复交易逻辑
        fix_futures_trading_logic()
        
        # 创建交易引擎
        trading_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
        
        # 获取一个RSI策略（因为它正在产生SELL信号）
        rsi_strategy = None
        for strategy_name, strategy in trading_engine.strategies.items():
            if 'RSI' in strategy_name and 'BTCUSDT' in strategy_name:
                rsi_strategy = strategy
                break
        
        if rsi_strategy:
            print(f"找到策略: {strategy_name}")
            
            # 获取市场数据
            futures_client = client_manager.get_futures_client()
            data = futures_client.get_klines(rsi_strategy.symbol, '1h', 100)
            
            if data is not None and not data.empty:
                current_price = data['close'].iloc[-1]
                signal = rsi_strategy.generate_signal(data)
                
                print(f"当前价格: {current_price}")
                print(f"策略信号: {signal}")
                print(f"当前持仓: {rsi_strategy.position}")
                
                if signal in ['BUY', 'SELL']:
                    print(f"尝试执行交易: {signal}")
                    
                    # 模拟交易执行（不实际下单）
                    print("⚠️ 这是模拟交易，不会实际下单")
                    print(f"如果执行，将会: {signal} {rsi_strategy.symbol} @ {current_price}")
                    
                    # 实际执行交易（取消注释以启用真实交易）
                    # success = trading_engine._execute_futures_trade(rsi_strategy, signal, current_price, 'TEST')
                    # print(f"交易执行结果: {'成功' if success else '失败'}")
                else:
                    print("当前无交易信号")
            else:
                print("无法获取市场数据")
        else:
            print("未找到RSI策略")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    fix_futures_trading_logic()
    test_fixed_trading()