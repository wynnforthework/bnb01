#!/usr/bin/env python3
"""
验证MATICUSDT符号修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_fix():
    """验证修复结果"""
    print("🔍 验证MATICUSDT符号修复...")
    
    try:
        from backend.client_manager import client_manager
        
        # 测试现货交易 - 应该不再尝试MATICUSDT
        print("\n📊 测试现货交易引擎初始化...")
        try:
            from backend.trading_engine import TradingEngine
            spot_engine = TradingEngine(trading_mode='SPOT')
            print("✅ 现货交易引擎初始化成功")
            
            # 检查策略中是否包含MATICUSDT
            matic_strategies = [k for k in spot_engine.strategies.keys() if 'MATICUSDT' in k]
            if matic_strategies:
                print(f"⚠️ 现货策略中仍包含MATICUSDT: {matic_strategies}")
            else:
                print("✅ 现货策略中已移除MATICUSDT")
                
        except Exception as e:
            print(f"❌ 现货交易引擎初始化失败: {e}")
        
        # 测试合约交易 - MATICUSDT应该仍然有效
        print("\n🚀 测试合约交易...")
        try:
            futures_client = client_manager.get_futures_client()
            klines = futures_client.get_klines('MATICUSDT', '1h', 1)
            if klines is not None and not klines.empty:
                print("✅ MATICUSDT: 合约交易仍然有效")
            else:
                print("❌ MATICUSDT: 合约交易无效")
        except Exception as e:
            print(f"❌ MATICUSDT: 合约交易测试失败 - {e}")
        
        print("\n✅ 验证完成")
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")

if __name__ == "__main__":
    verify_fix()
