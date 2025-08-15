#!/usr/bin/env python3
"""
简化持仓测试
"""

from backend.position_manager import PositionManager
from backend.risk_manager import RiskManager
from backend.database import DatabaseManager
from backend.binance_client import BinanceClient

def main():
    print("=== 简化持仓测试 ===\n")
    
    try:
        # 1. 检查持仓管理器
        print("1. 检查持仓管理器...")
        pm = PositionManager()
        positions = pm._get_all_positions()
        print(f"持仓数量: {len(positions)}")
        
        for symbol, pos in positions.items():
            print(f"  {symbol}: {pos['quantity']:.6f} @ ${pos['current_price']:.4f}")
        
        # 2. 检查ADA持仓
        print(f"\n2. 检查ADA持仓...")
        if 'ADAUSDT' in positions:
            ada_pos = positions['ADAUSDT']
            print(f"  ADA持仓: {ada_pos['quantity']:.6f} @ ${ada_pos['current_price']:.4f}")
            
            # 计算权重
            portfolio_value = pm.risk_manager._get_portfolio_value()
            ada_value = ada_pos['quantity'] * ada_pos['current_price']
            ada_weight = ada_value / portfolio_value if portfolio_value > 0 else 0
            
            print(f"  投资组合总值: ${portfolio_value:.2f}")
            print(f"  ADA持仓价值: ${ada_value:.2f}")
            print(f"  ADA持仓权重: {ada_weight:.1%}")
            print(f"  减仓阈值: {pm.reduction_threshold:.1%}")
            
            if ada_weight > pm.reduction_threshold:
                print(f"  ⚠️ 需要减仓")
                
                # 执行减仓
                print(f"  执行减仓...")
                result = pm.check_and_reduce_positions()
                print(f"  减仓结果: {result}")
            else:
                print(f"  ✅ 权重合理")
        else:
            print(f"  ❌ 没有ADA持仓")
        
        # 3. 检查币安账户
        print(f"\n3. 检查币安账户...")
        client = BinanceClient()
        account = client.get_account_info()
        
        if account:
            ada_balance = 0
            for balance in account['balances']:
                if balance['asset'] == 'ADA':
                    ada_balance = float(balance['free']) + float(balance['locked'])
                    break
            
            print(f"  ADA账户余额: {ada_balance:.6f}")
            
            if ada_balance > 0:
                current_price = client.get_ticker_price('ADAUSDT')
                if current_price:
                    print(f"  ADA当前价格: ${current_price:.4f}")
                    print(f"  ADA账户价值: ${ada_balance * current_price:.2f}")
        
        print(f"\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
