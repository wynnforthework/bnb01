#!/usr/bin/env python3
"""
测试自动减仓功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.position_manager import PositionManager
from backend.risk_manager import RiskManager
from backend.database import DatabaseManager
from backend.binance_client import BinanceClient
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_position_reduction():
    """测试自动减仓功能"""
    
    print("=== 测试自动减仓功能 ===\n")
    
    try:
        # 1. 检查风险管理器的减仓判断
        print("1. 检查风险管理器的减仓判断...")
        risk_manager = RiskManager()
        
        # 检查ADA持仓
        ada_existing = risk_manager.check_existing_position('ADAUSDT')
        print(f"   ADA现有持仓: {ada_existing:.6f}")
        
        if ada_existing > 0:
            current_price = 0.9179  # 使用日志中的价格
            should_reduce, reduce_quantity = risk_manager.should_reduce_position('ADAUSDT', ada_existing, current_price)
            print(f"   是否需要减仓: {should_reduce}")
            print(f"   建议减仓数量: {reduce_quantity:.6f}")
        else:
            print("   ❌ 没有检测到ADA持仓")
        
        # 2. 检查持仓管理器的持仓获取
        print(f"\n2. 检查持仓管理器的持仓获取...")
        position_manager = PositionManager(trading_mode='SPOT')
        
        positions = position_manager._get_all_positions()
        print(f"   获取到的持仓数量: {len(positions)}")
        
        if positions:
            for symbol, position in positions.items():
                print(f"   {symbol}: {position['quantity']:.6f} @ ${position['current_price']:.4f}")
        else:
            print("   ❌ 持仓管理器没有获取到任何持仓")
        
        # 3. 检查数据库中的持仓
        print(f"\n3. 检查数据库中的持仓...")
        db_manager = DatabaseManager()
        db_positions = db_manager.get_positions()
        
        print(f"   数据库中的持仓数量: {len(db_positions)}")
        
        if db_positions:
            for position in db_positions:
                print(f"   {position.symbol}: {position.quantity:.6f} @ ${position.avg_price:.4f}")
        else:
            print("   ❌ 数据库中没有持仓记录")
        
        # 4. 检查币安账户实际持仓
        print(f"\n4. 检查币安账户实际持仓...")
        binance_client = BinanceClient(trading_mode='SPOT')
        
        # 获取账户信息
        account_info = binance_client.get_account_info()
        if account_info:
            ada_balance = 0
            for balance in account_info['balances']:
                if balance['asset'] == 'ADA':
                    ada_balance = float(balance['free']) + float(balance['locked'])
                    break
            
            print(f"   ADA账户余额: {ada_balance:.6f}")
            
            if ada_balance > 0:
                current_price = binance_client.get_ticker_price('ADAUSDT')
                if current_price:
                    ada_value = ada_balance * current_price
                    portfolio_value = risk_manager._get_portfolio_value()
                    ada_weight = ada_value / portfolio_value if portfolio_value > 0 else 0
                    
                    print(f"   ADA当前价格: ${current_price:.4f}")
                    print(f"   ADA持仓价值: ${ada_value:.2f}")
                    print(f"   ADA持仓权重: {ada_weight:.1%}")
                    
                    # 检查是否需要减仓
                    if ada_weight > position_manager.reduction_threshold:
                        print(f"   ⚠️  ADA持仓权重过高，需要减仓")
                        
                        # 手动执行减仓
                        print(f"   手动执行减仓...")
                        reduction_result = position_manager.check_and_reduce_positions()
                        
                        if reduction_result:
                            print(f"   ✅ 减仓执行结果:")
                            for symbol, result in reduction_result.items():
                                if result['success']:
                                    print(f"      {symbol}: 减仓 {result['reduced_quantity']:.6f}")
                                else:
                                    print(f"      {symbol}: 减仓失败 - {result['error']}")
                        else:
                            print(f"   ❌ 减仓执行失败")
                    else:
                        print(f"   ✅ ADA持仓权重合理")
                else:
                    print(f"   ❌ 无法获取ADA价格")
            else:
                print(f"   ❌ ADA账户余额为0")
        else:
            print(f"   ❌ 无法获取账户信息")
        
        # 5. 检查持仓分析
        print(f"\n5. 检查持仓分析...")
        analysis = position_manager.get_position_analysis()
        
        if analysis:
            print(f"   投资组合总值: ${analysis['portfolio_value']:.2f}")
            print(f"   持仓数量: {len(analysis['positions'])}")
            
            if analysis['positions']:
                for symbol, pos in analysis['positions'].items():
                    print(f"   {symbol}: 权重 {pos['weight']:.1%}, 数量 {pos['quantity']:.6f}")
            
            if analysis['recommendations']:
                print(f"   建议:")
                for rec in analysis['recommendations']:
                    print(f"     - {rec['type']}: {rec.get('symbol', '')} {rec.get('message', '')}")
        else:
            print(f"   ❌ 持仓分析失败")
        
        print(f"\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def fix_ada_position_in_db():
    """修复ADA持仓在数据库中的记录"""
    
    print("\n=== 修复ADA持仓记录 ===\n")
    
    try:
        # 获取币安账户中的ADA余额
        binance_client = BinanceClient(trading_mode='SPOT')
        account_info = binance_client.get_account_info()
        
        if account_info:
            ada_balance = 0
            for balance in account_info['balances']:
                if balance['asset'] == 'ADA':
                    ada_balance = float(balance['free']) + float(balance['locked'])
                    break
            
            print(f"ADA账户余额: {ada_balance:.6f}")
            
            if ada_balance > 0:
                # 获取当前价格
                current_price = binance_client.get_ticker_price('ADAUSDT')
                if current_price:
                    print(f"ADA当前价格: ${current_price:.4f}")
                    
                    # 更新数据库中的持仓记录
                    db_manager = DatabaseManager()
                    
                    # 检查是否已有记录
                    from backend.database import Position
                    existing_position = db_manager.session.query(Position).filter_by(symbol='ADAUSDT').first()
                    
                    if existing_position:
                        # 更新现有记录
                        existing_position.quantity = ada_balance
                        existing_position.current_price = current_price
                        print(f"更新现有持仓记录: {ada_balance:.6f} ADA")
                    else:
                        # 创建新记录
                        new_position = Position(
                            symbol='ADAUSDT',
                            quantity=ada_balance,
                            avg_price=current_price,  # 使用当前价格作为平均价格
                            current_price=current_price
                        )
                        db_manager.session.add(new_position)
                        print(f"创建新持仓记录: {ada_balance:.6f} ADA")
                    
                    db_manager.session.commit()
                    print(f"✅ 数据库更新成功")
                    
                    # 验证更新
                    updated_positions = db_manager.get_positions()
                    for pos in updated_positions:
                        if pos.symbol == 'ADAUSDT':
                            print(f"验证: {pos.symbol} - {pos.quantity:.6f} @ ${pos.avg_price:.4f}")
                            break
                else:
                    print(f"❌ 无法获取ADA价格")
            else:
                print(f"❌ ADA余额为0，无需修复")
        else:
            print(f"❌ 无法获取账户信息")
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_position_reduction()
    fix_ada_position_in_db()
