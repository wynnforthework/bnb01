#!/usr/bin/env python3
"""
检查当前持仓状态
"""

import logging
from backend.database import DatabaseManager
from backend.binance_client import BinanceClient

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def check_current_positions():
    """检查当前持仓状态"""
    print("🔍 检查当前持仓状态...")
    
    try:
        # 检查数据库中的持仓
        db_manager = DatabaseManager()
        positions = db_manager.get_positions()
        
        print(f"\n📊 数据库中的持仓数量: {len(positions)}")
        
        if positions:
            print("\n💼 当前持仓:")
            for pos in positions:
                print(f"  {pos.symbol}: {pos.quantity:.6f} @ ${pos.avg_price:.4f}")
                print(f"    当前价格: ${pos.current_price:.4f}")
                print(f"    未实现盈亏: ${pos.unrealized_pnl:.2f}")
        else:
            print("  📭 数据库中没有持仓记录")
        
        # 检查最近的交易记录
        trades = db_manager.get_trades(limit=10)
        print(f"\n📈 最近交易记录数量: {len(trades)}")
        
        if trades:
            print("\n🔄 最近10笔交易:")
            for trade in trades:
                print(f"  {trade.timestamp.strftime('%H:%M:%S')} - {trade.symbol} {trade.side} {trade.quantity:.6f} @ ${trade.price:.4f}")
                if trade.strategy:
                    print(f"    策略: {trade.strategy}, 盈亏: ${trade.profit_loss:.2f}")
        else:
            print("  📭 没有交易记录")
        
        # 检查币安账户余额（如果是实盘）
        try:
            binance_client = BinanceClient()
            usdt_balance = binance_client.get_balance('USDT')
            print(f"\n💰 USDT余额: ${usdt_balance:.2f}")
            
            # 检查其他主要币种余额
            major_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'DOGE']
            print("\n🪙 其他币种余额:")
            for coin in major_coins:
                balance = binance_client.get_balance(coin)
                if balance > 0.001:  # 只显示有意义的余额
                    print(f"  {coin}: {balance:.6f}")
                    
        except Exception as e:
            print(f"⚠️ 无法获取币安余额: {e}")
        
        return len(positions) > 0
        
    except Exception as e:
        print(f"❌ 检查持仓失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    has_positions = check_current_positions()
    
    if not has_positions:
        print("\n💡 建议:")
        print("  1. 启动完整交易系统: python start.py")
        print("  2. 访问Web界面: http://localhost:5000")
        print("  3. 点击'启动交易'按钮")
        print("  4. 等待系统执行实际交易")
    else:
        print("\n✅ 系统已有持仓，交易正在进行中")