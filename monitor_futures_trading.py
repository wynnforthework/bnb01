#!/usr/bin/env python3
"""
监控合约交易执行情况
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app
import time
from datetime import datetime

def monitor_futures_trading():
    """监控合约交易"""
    print("🔍 开始监控合约交易执行情况...")
    print("=" * 60)
    
    try:
        # 检查交易引擎状态
        if not hasattr(app, 'futures_trading_engine'):
            print("❌ 未找到合约交易引擎")
            return
        
        engine = app.futures_trading_engine
        
        if not engine.is_running:
            print("❌ 合约交易引擎未运行")
            return
        
        print("✅ 合约交易引擎正在运行")
        print(f"📊 监控币种: {engine.selected_symbols}")
        print(f"📊 启用策略: {engine.enabled_strategies}")
        
        # 获取初始交易记录数量
        from backend.database import DatabaseManager
        db = DatabaseManager()
        initial_trades = db.get_trades(limit=100)
        initial_count = len(initial_trades)
        print(f"📊 初始交易记录数量: {initial_count}")
        
        # 监控循环
        monitor_count = 0
        while monitor_count < 10:  # 监控10次
            monitor_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n🔄 监控检查 #{monitor_count} - {current_time}")
            print("-" * 40)
            
            # 检查交易引擎状态
            if engine.is_running:
                print("✅ 交易引擎运行正常")
            else:
                print("❌ 交易引擎已停止")
                break
            
            # 检查策略状态
            print("📋 策略状态:")
            for name, strategy in engine.strategies.items():
                if 'ADAUSDT' in name:  # 只显示ADAUSDT的策略
                    print(f"   {name}: 持仓={strategy.position}, 入场价={strategy.entry_price}")
            
            # 检查新的交易记录
            current_trades = db.get_trades(limit=100)
            current_count = len(current_trades)
            new_trades = current_count - initial_count
            
            print(f"📊 交易记录: 总数={current_count}, 新增={new_trades}")
            
            if new_trades > 0:
                print("🎉 发现新交易！")
                # 显示最新的交易
                latest_trades = current_trades[-new_trades:]
                for trade in latest_trades:
                    print(f"   📈 {trade.timestamp}: {trade.symbol} {trade.side} {trade.quantity} @ {trade.price} ({trade.strategy})")
            
            # 检查合约持仓
            try:
                from backend.client_manager import client_manager
                futures_client = client_manager.get_futures_client()
                positions = futures_client.client.futures_position_information()
                active_positions = [p for p in positions if float(p['positionAmt']) != 0]
                
                print(f"📊 合约持仓: {len(active_positions)} 个活跃持仓")
                for pos in active_positions:
                    symbol = pos['symbol']
                    position_amt = float(pos['positionAmt'])
                    entry_price = float(pos['entryPrice'])
                    unrealized_pnl = float(pos['unRealizedProfit'])
                    print(f"   {symbol}: {position_amt} @ {entry_price} (盈亏: {unrealized_pnl:.2f})")
                    
            except Exception as e:
                print(f"❌ 检查合约持仓失败: {e}")
            
            # 等待60秒
            if monitor_count < 10:
                print("⏳ 等待60秒后继续监控...")
                time.sleep(60)
        
        print("\n" + "=" * 60)
        print("📋 监控总结:")
        print(f"✅ 合约交易引擎运行正常")
        print(f"📊 监控期间新增交易: {new_trades} 笔")
        print("💡 交易引擎将继续在后台运行")
        print("🔍 可以在网页界面查看实时状态")
        
    except Exception as e:
        print(f"❌ 监控过程中出错: {e}")

def quick_status_check():
    """快速状态检查"""
    print("🔍 快速状态检查...")
    
    try:
        if not hasattr(app, 'futures_trading_engine'):
            print("❌ 未找到合约交易引擎")
            return
        
        engine = app.futures_trading_engine
        print(f"✅ 交易引擎状态: {'🟢 运行中' if engine.is_running else '🔴 未运行'}")
        
        if engine.is_running:
            # 检查最近的交易
            from backend.database import DatabaseManager
            db = DatabaseManager()
            recent_trades = db.get_trades(limit=5)
            
            print(f"📊 最近交易记录: {len(recent_trades)} 笔")
            for trade in recent_trades:
                print(f"   {trade.timestamp}: {trade.symbol} {trade.side} {trade.quantity} @ {trade.price}")
        
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='监控合约交易')
    parser.add_argument('--quick', action='store_true', help='快速状态检查')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_status_check()
    else:
        monitor_futures_trading()
