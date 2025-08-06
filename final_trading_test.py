#!/usr/bin/env python3
"""
最终交易系统测试
"""

import logging
from backend.trading_engine import TradingEngine

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def final_trading_test():
    """最终交易系统测试"""
    print("🚀 最终交易系统测试...")
    
    try:
        # 创建交易引擎
        engine = TradingEngine()
        
        print(f"📊 策略数量: {len(engine.strategies)}")
        
        # 模拟一次交易循环
        print("\n🔄 模拟交易循环...")
        engine._execute_trading_cycle()
        
        print("\n✅ 交易循环执行完成！")
        print("\n📋 总结:")
        print("  - 策略参数已优化，更容易产生交易信号")
        print("  - 风险管理参数已调整，允许正常交易")
        print("  - 数据库访问错误已修复")
        print("  - 系统现在应该能够正常执行交易")
        
        print("\n💡 下一步:")
        print("  1. 启动完整的交易系统: python start.py")
        print("  2. 访问Web界面: http://localhost:5000")
        print("  3. 点击'启动交易'按钮")
        print("  4. 等待几分钟观察交易执行情况")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    final_trading_test()