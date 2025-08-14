#!/usr/bin/env python3
"""
启动合约交易引擎
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app
import threading
import time

def start_futures_trading():
    """启动合约交易"""
    print("🚀 启动合约交易引擎...")
    
    try:
        # 检查当前状态
        if not hasattr(app, 'futures_trading_engine'):
            print("❌ 未找到合约交易引擎")
            return False
        
        engine = app.futures_trading_engine
        
        if engine.is_running:
            print("✅ 合约交易引擎已在运行中")
            return True
        
        print(f"📊 当前配置:")
        print(f"   交易模式: {engine.trading_mode}")
        print(f"   选择币种: {engine.selected_symbols}")
        print(f"   启用策略: {engine.enabled_strategies}")
        print(f"   策略数量: {len(engine.strategies)}")
        
        # 启动交易引擎
        print("🔄 启动交易引擎...")
        trading_thread = threading.Thread(target=engine.start_trading)
        trading_thread.daemon = True
        trading_thread.start()
        
        # 等待一下确认启动
        time.sleep(2)
        
        if engine.is_running:
            print("✅ 合约交易引擎启动成功！")
            print("📈 交易引擎正在后台运行，将自动执行交易策略")
            return True
        else:
            print("❌ 合约交易引擎启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 启动合约交易失败: {e}")
        return False

def check_futures_status():
    """检查合约交易状态"""
    print("\n📊 检查合约交易状态...")
    
    if not hasattr(app, 'futures_trading_engine'):
        print("❌ 未找到合约交易引擎")
        return
    
    engine = app.futures_trading_engine
    print(f"   运行状态: {'🟢 运行中' if engine.is_running else '🔴 未运行'}")
    print(f"   交易模式: {engine.trading_mode}")
    print(f"   选择币种: {engine.selected_symbols}")
    print(f"   启用策略: {engine.enabled_strategies}")
    
    # 检查策略状态
    print(f"\n📋 策略状态:")
    for name, strategy in engine.strategies.items():
        if 'ADAUSDT' in name:  # 只显示ADAUSDT的策略
            print(f"   {name}: 持仓={strategy.position}, 入场价={strategy.entry_price}")

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 合约交易引擎启动工具")
    print("=" * 50)
    
    # 检查当前状态
    check_futures_status()
    
    # 询问是否启动
    print("\n❓ 是否启动合约交易引擎？")
    print("   这将开始自动交易，请确保:")
    print("   1. 合约账户有足够余额")
    print("   2. 策略参数设置合理")
    print("   3. 风险控制配置正确")
    
    # 自动启动（因为这是诊断工具）
    print("\n🔄 自动启动合约交易引擎...")
    success = start_futures_trading()
    
    if success:
        print("\n✅ 启动完成！")
        print("📈 合约交易引擎现在正在运行")
        print("🔄 交易循环将每分钟执行一次")
        print("📊 可以在网页界面查看交易状态")
        
        # 再次检查状态
        time.sleep(1)
        check_futures_status()
        
        print("\n💡 提示:")
        print("   - 交易引擎会在后台持续运行")
        print("   - 可以在网页界面查看实时状态")
        print("   - 如需停止，请在网页界面点击停止按钮")
    else:
        print("\n❌ 启动失败")
        print("💡 请检查配置和网络连接")

if __name__ == "__main__":
    main()
