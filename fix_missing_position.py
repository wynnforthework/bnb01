#!/usr/bin/env python3
"""
修复缺失的持仓记录
"""

import logging
from backend.database import DatabaseManager
from backend.binance_client import BinanceClient

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def fix_missing_positions():
    """修复缺失的持仓记录"""
    print("🔧 修复缺失的持仓记录...")
    
    try:
        db_manager = DatabaseManager()
        binance_client = BinanceClient()
        
        # 1. 检查最近的买入交易
        print("\n1️⃣ 检查最近的买入交易...")
        trades = db_manager.get_trades(limit=10)
        
        buy_trades = [t for t in trades if t.side == 'BUY']
        sell_trades = [t for t in trades if t.side == 'SELL']
        
        print(f"📊 找到 {len(buy_trades)} 笔买入交易")
        print(f"📊 找到 {len(sell_trades)} 笔卖出交易")
        
        # 2. 计算每个交易对的净持仓
        positions = {}
        
        for trade in trades:
            symbol = trade.symbol
            if symbol not in positions:
                positions[symbol] = {
                    'quantity': 0,
                    'total_cost': 0,
                    'trades': []
                }
            
            if trade.side == 'BUY':
                positions[symbol]['quantity'] += trade.quantity
                positions[symbol]['total_cost'] += trade.quantity * trade.price
            elif trade.side == 'SELL':
                positions[symbol]['quantity'] -= trade.quantity
                positions[symbol]['total_cost'] -= trade.quantity * trade.price
            
            positions[symbol]['trades'].append(trade)
        
        # 3. 为有净持仓的交易对创建持仓记录
        print("\n2️⃣ 创建持仓记录...")
        
        for symbol, pos_data in positions.items():
            if pos_data['quantity'] > 0.000001:  # 有实际持仓
                avg_price = pos_data['total_cost'] / pos_data['quantity']
                current_price = binance_client.get_ticker_price(symbol)
                
                if current_price:
                    print(f"📈 创建 {symbol} 持仓记录:")
                    print(f"  数量: {pos_data['quantity']:.6f}")
                    print(f"  平均价格: ${avg_price:.2f}")
                    print(f"  当前价格: ${current_price:.2f}")
                    
                    # 创建或更新持仓记录
                    position = db_manager.update_position(
                        symbol=symbol,
                        quantity=pos_data['quantity'],
                        avg_price=avg_price,
                        current_price=current_price
                    )
                    
                    if position:
                        unrealized_pnl = (current_price - avg_price) * pos_data['quantity']
                        print(f"  未实现盈亏: ${unrealized_pnl:.2f}")
                        print(f"  ✅ 持仓记录已创建")
                    else:
                        print(f"  ❌ 持仓记录创建失败")
                else:
                    print(f"⚠️ 无法获取 {symbol} 的当前价格")
        
        # 4. 验证修复结果
        print("\n3️⃣ 验证修复结果...")
        positions_after = db_manager.get_positions()
        
        print(f"📊 修复后持仓数量: {len(positions_after)}")
        
        if positions_after:
            print("\n💼 当前持仓:")
            total_value = 0
            for pos in positions_after:
                current_price = binance_client.get_ticker_price(pos.symbol)
                if current_price:
                    market_value = pos.quantity * current_price
                    total_value += market_value
                    pnl_percent = ((current_price - pos.avg_price) / pos.avg_price) * 100
                    
                    print(f"  {pos.symbol}:")
                    print(f"    数量: {pos.quantity:.6f}")
                    print(f"    平均价格: ${pos.avg_price:.2f}")
                    print(f"    当前价格: ${current_price:.2f}")
                    print(f"    市值: ${market_value:.2f}")
                    print(f"    盈亏: ${pos.unrealized_pnl:.2f} ({pnl_percent:+.2f}%)")
            
            print(f"\n💰 总持仓市值: ${total_value:.2f}")
            
            # 检查币安余额验证
            usdt_balance = binance_client.get_balance('USDT')
            print(f"💵 USDT余额: ${usdt_balance:.2f}")
            print(f"💎 总资产价值: ${total_value + usdt_balance:.2f}")
            
            return True
        else:
            print("⚠️ 修复后仍然没有持仓记录")
            return False
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = fix_missing_positions()
    
    if success:
        print(f"\n✅ 持仓记录修复成功！")
        print(f"💡 现在可以正常查看持仓状态了。")
    else:
        print(f"\n❌ 持仓记录修复失败。")