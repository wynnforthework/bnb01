#!/usr/bin/env python3
"""
检查交易对精度要求
"""

from backend.client_manager import client_manager

def check_btc_precision():
    """检查BTCUSDT的精度要求"""
    print("🔍 检查BTCUSDT合约精度要求...")
    
    try:
        futures_client = client_manager.get_futures_client()
        
        # 获取交易对信息
        symbol_info = futures_client._get_symbol_info('BTCUSDT')
        
        if symbol_info:
            print(f"交易对: {symbol_info['symbol']}")
            print(f"状态: {symbol_info['status']}")
            
            # 查找LOT_SIZE过滤器
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    print(f"\nLOT_SIZE过滤器:")
                    print(f"  最小数量: {f['minQty']}")
                    print(f"  最大数量: {f['maxQty']}")
                    print(f"  步长: {f['stepSize']}")
                    
                    # 计算精度
                    step_size = float(f['stepSize'])
                    if step_size >= 1:
                        precision = 0
                    else:
                        precision = len(str(step_size).split('.')[-1].rstrip('0'))
                    
                    print(f"  计算的精度: {precision}位小数")
                    
                    # 测试数量调整
                    test_quantity = 0.013166
                    adjusted = round(test_quantity, precision)
                    print(f"  测试数量: {test_quantity:.8f}")
                    print(f"  调整后: {adjusted:.8f}")
                    
                    # 检查是否符合最小值
                    min_qty = float(f['minQty'])
                    if adjusted >= min_qty:
                        print(f"  ✅ 符合最小数量要求")
                    else:
                        print(f"  ❌ 低于最小数量要求: {min_qty}")
                    
                    break
            else:
                print("❌ 未找到LOT_SIZE过滤器")
                
            # 查找PRICE_FILTER过滤器
            for f in symbol_info['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    print(f"\nPRICE_FILTER过滤器:")
                    print(f"  最小价格: {f['minPrice']}")
                    print(f"  最大价格: {f['maxPrice']}")
                    print(f"  价格步长: {f['tickSize']}")
                    break
                    
        else:
            print("❌ 无法获取交易对信息")
            
        # 测试实际的精度调整
        print(f"\n🧪 测试精度调整方法...")
        test_quantity = 0.013166
        adjusted_quantity = futures_client._adjust_quantity_precision(test_quantity, symbol_info)
        print(f"原始数量: {test_quantity:.8f}")
        print(f"调整后数量: {adjusted_quantity:.8f}")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    check_btc_precision()