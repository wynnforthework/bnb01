#!/usr/bin/env python3
"""
直接测试下单方法
"""

from backend.client_manager import client_manager

def test_direct_order():
    """直接测试下单方法"""
    print("🧪 直接测试下单方法...")
    
    try:
        futures_client = client_manager.get_futures_client()
        
        # 测试参数
        symbol = 'BTCUSDT'
        side = 'SELL'
        quantity = 0.013166  # 原始数量
        position_side = 'SHORT'
        reduce_only = False
        
        print(f"测试参数:")
        print(f"  symbol: {symbol}")
        print(f"  side: {side}")
        print(f"  quantity: {quantity:.8f}")
        print(f"  position_side: {position_side}")
        print(f"  reduce_only: {reduce_only}")
        
        # 获取交易对信息
        symbol_info = futures_client._get_symbol_info(symbol)
        if symbol_info:
            # 手动调整精度
            adjusted_quantity = futures_client._adjust_quantity_precision(quantity, symbol_info)
            print(f"  调整后数量: {adjusted_quantity:.8f}")
            
            # 模拟构建订单参数
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': adjusted_quantity,
                'positionSide': position_side
            }
            
            if reduce_only:
                order_params['reduceOnly'] = True
            
            print(f"\n构建的订单参数:")
            for key, value in order_params.items():
                print(f"  {key}: {value}")
            
            # 询问是否执行真实下单
            print(f"\n⚠️ 准备执行真实下单测试")
            response = input("输入 'YES' 确认执行真实下单: ")
            
            if response == 'YES':
                print("执行真实下单...")
                try:
                    order = futures_client.client.futures_create_order(**order_params)
                    print(f"✅ 下单成功!")
                    print(f"订单ID: {order.get('orderId', 'N/A')}")
                    print(f"状态: {order.get('status', 'N/A')}")
                except Exception as order_error:
                    print(f"❌ 下单失败: {order_error}")
            else:
                print("取消真实下单测试")
        else:
            print("❌ 无法获取交易对信息")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    test_direct_order()