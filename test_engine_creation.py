#!/usr/bin/env python3
"""
测试交易引擎创建
"""

from backend.trading_engine import TradingEngine

def test_engine_creation():
    """测试交易引擎创建"""
    try:
        print("创建现货交易引擎...")
        engine = TradingEngine('SPOT')
        print(f"成功！策略数量: {len(engine.strategies)}")
        
        print("前5个策略:")
        for i, (key, strategy) in enumerate(list(engine.strategies.items())[:5]):
            print(f"  {i+1}. {key}: {strategy.symbol} - {strategy.__class__.__name__}")
            
        return True
        
    except Exception as e:
        print(f"失败: {e}")
        import traceback
        print("错误详情:")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = test_engine_creation()
    if success:
        print("\n✅ 交易引擎创建成功")
    else:
        print("\n❌ 交易引擎创建失败")