#!/usr/bin/env python3
"""
调试精度问题
"""

from backend.client_manager import client_manager
from backend.trading_engine import TradingEngine
from strategies.rsi_strategy import RSIStrategy

def debug_precision_issue():
    """调试精度问题"""
    print("🔍 调试精度问题...")
    
    try:
        # 创建交易引擎和客户端
        trading_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
        futures_client = client_manager.get_futures_client()
        
        # 获取市场数据
        symbol = 'BTCUSDT'
        data = futures_client.get_klines(symbol, '1h', 100)
        current_price = data['close'].iloc[-1]
        
        print(f"当前价格: {current_price}")
        
        # 创建测试策略
        test_strategy = RSIStrategy(symbol, {
            'position_size': 0.01  # 1%仓位
        })
        
        # 获取账户余额
        account_balance = futures_client.get_account_balance()
        available_balance = float(account_balance['availableBalance'])
        
        print(f"可用余额: {available_balance} USDT")
        
        # 计算数量（模拟交易引擎的计算）
        position_value = available_balance * test_strategy.parameters.get('position_size', 0.02)
        quantity = position_value * trading_engine.leverage / current_price
        
        print(f"仓位价值: {position_value} USDT")
        print(f"杠杆: {trading_engine.leverage}x")
        print(f"计算的数量: {quantity:.8f}")
        
        # 获取交易对信息
        symbol_info = futures_client._get_symbol_info(symbol)
        if symbol_info:
            # 手动调整精度
            adjusted_quantity = futures_client._adjust_quantity_precision(quantity, symbol_info)
            print(f"调整后数量: {adjusted_quantity:.8f}")
            
            # 检查LOT_SIZE过滤器
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    min_qty = float(f['minQty'])
                    step_size = float(f['stepSize'])
                    
                    print(f"最小数量: {min_qty}")
                    print(f"步长: {step_size}")
                    
                    # 验证调整后的数量
                    if adjusted_quantity >= min_qty:
                        print("✅ 数量符合最小值要求")
                    else:
                        print("❌ 数量低于最小值")
                    
                    # 检查是否是步长的倍数
                    remainder = (adjusted_quantity - min_qty) % step_size
                    if abs(remainder) < 1e-8:  # 考虑浮点精度
                        print("✅ 数量符合步长要求")
                    else:
                        print(f"❌ 数量不符合步长要求，余数: {remainder}")
                        # 重新调整
                        steps = round((adjusted_quantity - min_qty) / step_size)
                        corrected_quantity = min_qty + steps * step_size
                        print(f"修正后数量: {corrected_quantity:.8f}")
                    
                    break
        
        # 尝试实际下单（模拟模式）
        print(f"\n🧪 测试下单参数...")
        print("模拟下单参数:")
        print(f"  symbol: {symbol}")
        print(f"  side: SELL")
        print(f"  quantity: {adjusted_quantity:.8f}")
        print(f"  position_side: SHORT")
        print(f"  reduce_only: False")
        
        # 不实际下单，只是测试参数构建
        print("\n⚠️ 这是模拟测试，不会实际下单")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    debug_precision_issue()