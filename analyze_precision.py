#!/usr/bin/env python3
"""
深度分析BTCUSDT精度问题
"""

from backend.client_manager import client_manager
import json

def analyze_btc_precision():
    """深度分析BTCUSDT精度问题"""
    print("🔍 深度分析BTCUSDT精度问题...")
    
    try:
        futures_client = client_manager.get_futures_client()
        
        # 获取交易对信息
        symbol_info = futures_client._get_symbol_info('BTCUSDT')
        
        if symbol_info:
            print(f"交易对: {symbol_info['symbol']}")
            print(f"状态: {symbol_info['status']}")
            
            # 打印所有过滤器
            print(f"\n所有过滤器:")
            for i, f in enumerate(symbol_info['filters']):
                print(f"  {i+1}. {f['filterType']}: {f}")
            
            # 重点分析LOT_SIZE
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    print(f"\n📊 LOT_SIZE详细分析:")
                    min_qty = f['minQty']
                    max_qty = f['maxQty']
                    step_size = f['stepSize']
                    
                    print(f"  最小数量: {min_qty}")
                    print(f"  最大数量: {max_qty}")
                    print(f"  步长: {step_size}")
                    
                    # 分析步长精度
                    step_float = float(step_size)
                    if step_float >= 1:
                        precision = 0
                    else:
                        precision = len(str(step_size).split('.')[-1].rstrip('0'))
                    
                    print(f"  计算的精度: {precision}位小数")
                    
                    # 测试几个数量值
                    test_quantities = [0.013166, 0.01317, 0.013165, 0.01316]
                    
                    print(f"\n🧪 测试不同数量值:")
                    for qty in test_quantities:
                        # 使用当前的调整方法
                        adjusted = futures_client._adjust_quantity_precision(qty, symbol_info)
                        
                        # 手动验证
                        min_qty_float = float(min_qty)
                        steps = round((qty - min_qty_float) / step_float)
                        manual_adjusted = min_qty_float + steps * step_float
                        manual_rounded = round(manual_adjusted, precision)
                        
                        print(f"    原始: {qty:.8f}")
                        print(f"    调整后: {adjusted:.8f}")
                        print(f"    手动计算: {manual_rounded:.8f}")
                        print(f"    字符串格式: '{str(adjusted)}'")
                        
                        # 检查是否符合要求
                        remainder = (adjusted - min_qty_float) % step_float
                        is_valid = abs(remainder) < 1e-10
                        print(f"    是否有效: {is_valid} (余数: {remainder:.2e})")
                        print()
                    
                    break
            
            # 尝试获取当前市场价格
            print(f"📈 获取当前市场价格...")
            try:
                ticker = futures_client.client.futures_symbol_ticker(symbol='BTCUSDT')
                current_price = float(ticker['price'])
                print(f"当前价格: {current_price}")
                
                # 计算合理的交易数量
                balance = 15000.0  # 假设余额
                position_size = 0.01  # 1%
                leverage = 10
                
                position_value = balance * position_size
                quantity = position_value * leverage / current_price
                
                print(f"\n💰 交易计算:")
                print(f"  余额: {balance} USDT")
                print(f"  仓位大小: {position_size*100}%")
                print(f"  杠杆: {leverage}x")
                print(f"  仓位价值: {position_value} USDT")
                print(f"  计算数量: {quantity:.8f}")
                
                # 调整精度
                adjusted_qty = futures_client._adjust_quantity_precision(quantity, symbol_info)
                print(f"  调整后数量: {adjusted_qty:.8f}")
                print(f"  字符串格式: '{str(adjusted_qty)}'")
                
            except Exception as price_error:
                print(f"获取价格失败: {price_error}")
        
        else:
            print("❌ 无法获取交易对信息")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    analyze_btc_precision()