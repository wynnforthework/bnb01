#!/usr/bin/env python3
"""
调试策略名称问题
"""

from backend.trading_engine import TradingEngine

def debug_strategy_names():
    print("🔍 调试策略名称问题...")
    
    try:
        engine = TradingEngine('SPOT')
        print(f"策略数量: {len(engine.strategies)}")
        
        # 检查前3个策略
        for i, (strategy_key, strategy) in enumerate(list(engine.strategies.items())[:3]):
            print(f"\n策略 {i+1}:")
            print(f"  键: {strategy_key}")
            print(f"  对象: {strategy}")
            print(f"  类名: {strategy.__class__.__name__}")
            print(f"  符号: {strategy.symbol}")
            
            # 构建名称
            strategy_name = f"{strategy.symbol} - {strategy.__class__.__name__}"
            print(f"  构建的名称: {strategy_name}")
            
            # 检查名称类型
            print(f"  名称类型: {type(strategy_name)}")
            print(f"  名称长度: {len(strategy_name)}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(f"详情: {traceback.format_exc()}")

if __name__ == '__main__':
    debug_strategy_names()