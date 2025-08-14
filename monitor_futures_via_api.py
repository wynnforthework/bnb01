#!/usr/bin/env python3
"""
通过API监控合约交易状态
"""

import requests
import json
import time
from datetime import datetime

def get_futures_status():
    """获取合约交易状态"""
    try:
        response = requests.get('http://localhost:5000/api/futures/trading/status', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")
        return None

def get_recent_trades():
    """获取最近的交易记录"""
    try:
        response = requests.get('http://localhost:5000/api/trades', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ 获取交易记录失败: {e}")
        return None

def get_futures_positions():
    """获取合约持仓"""
    try:
        response = requests.get('http://localhost:5000/api/futures/positions', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return None

def monitor_futures_trading():
    """监控合约交易"""
    print("🔍 通过API监控合约交易状态")
    print("=" * 60)
    
    # 获取初始状态
    initial_status = get_futures_status()
    if not initial_status:
        print("❌ 无法获取交易状态，请确保Flask应用正在运行")
        return
    
    print(f"✅ 合约交易引擎状态: {initial_status.get('status', 'N/A')}")
    print(f"📊 杠杆: {initial_status.get('leverage', 'N/A')}x")
    print(f"📊 策略数量: {initial_status.get('strategies_count', 'N/A')}")
    
    # 获取初始交易记录
    initial_trades = get_recent_trades()
    initial_count = len(initial_trades.get('trades', [])) if initial_trades else 0
    print(f"📊 初始交易记录数量: {initial_count}")
    
    # 监控循环
    monitor_count = 0
    while monitor_count < 10:  # 监控10次
        monitor_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n🔄 监控检查 #{monitor_count} - {current_time}")
        print("-" * 40)
        
        # 检查交易状态
        status = get_futures_status()
        if status:
            print(f"✅ 交易引擎状态: {status.get('status', 'N/A')}")
            print(f"📊 策略数量: {status.get('strategies_count', 'N/A')}")
        else:
            print("❌ 无法获取交易状态")
            break
        
        # 检查新的交易记录
        current_trades = get_recent_trades()
        if current_trades:
            trades = current_trades.get('trades', [])
            current_count = len(trades)
            new_trades = current_count - initial_count
            
            print(f"📊 交易记录: 总数={current_count}, 新增={new_trades}")
            
            if new_trades > 0:
                print("🎉 发现新交易！")
                # 显示最新的交易
                latest_trades = trades[-new_trades:]
                for trade in latest_trades:
                    timestamp = trade.get('timestamp', 'N/A')
                    symbol = trade.get('symbol', 'N/A')
                    side = trade.get('side', 'N/A')
                    quantity = trade.get('quantity', 'N/A')
                    price = trade.get('price', 'N/A')
                    strategy = trade.get('strategy', 'N/A')
                    print(f"   📈 {timestamp}: {symbol} {side} {quantity} @ {price} ({strategy})")
        else:
            print("❌ 无法获取交易记录")
        
        # 检查合约持仓
        positions = get_futures_positions()
        if positions:
            active_positions = positions.get('positions', [])
            print(f"📊 合约持仓: {len(active_positions)} 个活跃持仓")
            
            for pos in active_positions:
                symbol = pos.get('symbol', 'N/A')
                quantity = pos.get('quantity', 'N/A')
                entry_price = pos.get('entry_price', 'N/A')
                unrealized_pnl = pos.get('unrealized_pnl', 'N/A')
                print(f"   {symbol}: {quantity} @ {entry_price} (盈亏: {unrealized_pnl})")
        else:
            print("❌ 无法获取合约持仓")
        
        # 等待60秒
        if monitor_count < 10:
            print("⏳ 等待60秒后继续监控...")
            time.sleep(60)
    
    print("\n" + "=" * 60)
    print("📋 监控总结:")
    print("✅ 通过API成功监控合约交易状态")
    print("💡 交易引擎正在后台运行")
    print("🔍 可以在网页界面查看实时状态")

def quick_status_check():
    """快速状态检查"""
    print("🔍 快速状态检查...")
    
    # 检查交易状态
    status = get_futures_status()
    if status:
        print(f"✅ 交易引擎状态: {status.get('status', 'N/A')}")
        print(f"📊 杠杆: {status.get('leverage', 'N/A')}x")
        print(f"📊 策略数量: {status.get('strategies_count', 'N/A')}")
    else:
        print("❌ 无法获取交易状态")
        return
    
    # 检查最近的交易
    trades = get_recent_trades()
    if trades:
        recent_trades = trades.get('trades', [])
        print(f"📊 最近交易记录: {len(recent_trades)} 笔")
        
        for trade in recent_trades[-3:]:  # 显示最近3条
            timestamp = trade.get('timestamp', 'N/A')
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', 'N/A')
            quantity = trade.get('quantity', 'N/A')
            price = trade.get('price', 'N/A')
            print(f"   {timestamp}: {symbol} {side} {quantity} @ {price}")
    else:
        print("❌ 无法获取交易记录")
    
    # 检查持仓
    positions = get_futures_positions()
    if positions:
        active_positions = positions.get('positions', [])
        print(f"📊 活跃持仓: {len(active_positions)} 个")
        
        for pos in active_positions:
            symbol = pos.get('symbol', 'N/A')
            quantity = pos.get('quantity', 'N/A')
            unrealized_pnl = pos.get('unrealized_pnl', 'N/A')
            print(f"   {symbol}: {quantity} (盈亏: {unrealized_pnl})")
    else:
        print("❌ 无法获取持仓信息")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='通过API监控合约交易')
    parser.add_argument('--quick', action='store_true', help='快速状态检查')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_status_check()
    else:
        monitor_futures_trading()
