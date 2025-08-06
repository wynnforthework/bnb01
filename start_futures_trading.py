#!/usr/bin/env python3
"""
启动合约交易
"""

import logging
from backend.trading_engine import TradingEngine

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def start_futures_trading():
    """启动合约交易"""
    print("🚀 启动合约交易系统...")
    
    try:
        # 创建合约交易引擎
        print("1️⃣ 初始化合约交易引擎...")
        futures_engine = TradingEngine(
            trading_mode='FUTURES',
            leverage=10  # 设置10x杠杆
        )
        
        print(f"✅ 合约交易引擎初始化成功")
        print(f"📊 策略数量: {len(futures_engine.strategies)}")
        print(f"🔧 杠杆倍数: {futures_engine.leverage}x")
        
        # 显示策略信息
        print("\n2️⃣ 策略配置:")
        for strategy_name, strategy in futures_engine.strategies.items():
            print(f"  📈 {strategy_name}: {strategy.symbol}")
        
        # 启动交易
        print("\n3️⃣ 启动自动交易...")
        print("⚠️  注意: 这将开始实际的合约交易")
        print("⚠️  系统将自动执行做多做空策略")
        print("⚠️  请确保你了解合约交易的风险")
        
        confirm = input("\n确认启动合约交易? (y/N): ").lower().strip()
        
        if confirm == 'y':
            print("\n🎯 正在启动合约交易...")
            print("💡 提示: 按 Ctrl+C 可以停止交易")
            
            # 启动交易引擎
            futures_engine.start_trading()
            
        else:
            print("🚫 取消启动合约交易")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  收到停止信号，正在关闭交易引擎...")
        if 'futures_engine' in locals():
            futures_engine.stop_trading()
        print("✅ 合约交易已停止")
        
    except Exception as e:
        print(f"❌ 启动合约交易失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

def show_futures_info():
    """显示合约交易信息"""
    print("📋 合约交易功能说明:")
    print("")
    print("🎯 交易特性:")
    print("  ✅ 支持做多做空双向交易")
    print("  ✅ 10x杠杆放大收益")
    print("  ✅ 自动止损止盈")
    print("  ✅ 多种策略组合")
    print("")
    print("📊 策略类型:")
    print("  📈 移动平均线策略 (MA)")
    print("  📊 RSI超买超卖策略")
    print("  🤖 机器学习策略 (ML)")
    print("")
    print("🛡️ 风险管理:")
    print("  🔒 动态止损 (基于ATR)")
    print("  🎯 智能止盈 (2.5倍风险回报比)")
    print("  ⚖️ 仓位管理 (最大30%单币种)")
    print("  📊 实时风险监控")
    print("")
    print("⚠️ 风险提示:")
    print("  🚨 合约交易具有高风险")
    print("  💸 杠杆可能放大亏损")
    print("  📉 市场波动可能导致强制平仓")
    print("  💰 请只使用你能承受损失的资金")

if __name__ == '__main__':
    show_futures_info()
    print("\n" + "="*50)
    start_futures_trading()