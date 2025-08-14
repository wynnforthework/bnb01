#!/usr/bin/env python3
"""
实时观察合约交易执行情况
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
        return None

def watch_trading():
    """观察交易执行"""
    print("👀 开始观察合约交易执行情况...")
    print("=" * 60)
    
    # 获取初始状态
    print("📊 当前状态:")
    status = get_futures_status()
    if status:
        print(f"   🟢 交易引擎: {status.get('status', 'N/A')}")
        print(f"   📊 杠杆: {status.get('leverage', 'N/A')}x")
        print(f"   📊 策略数量: {status.get('strategies_count', 'N/A')}")
    else:
        print("   ❌ 无法获取交易状态")
        return
    
    # 获取初始交易记录
    initial_trades = get_recent_trades()
    initial_count = len(initial_trades.get('trades', [])) if initial_trades else 0
    print(f"   📊 当前交易记录: {initial_count} 笔")
    
    # 获取初始持仓
    initial_positions = get_futures_positions()
    initial_position_count = len(initial_positions.get('positions', [])) if initial_positions else 0
    print(f"   📈 当前持仓: {initial_position_count} 个")
    
    print(f"\n🔄 开始观察交易执行...")
    print("   每分钟检查一次，按 Ctrl+C 停止")
    print("-" * 60)
    
    check_count = 0
    last_trade_count = initial_count
    last_position_count = initial_position_count
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 检查交易记录
            current_trades = get_recent_trades()
            if current_trades:
                trades = current_trades.get('trades', [])
                current_trade_count = len(trades)
                new_trades = current_trade_count - last_trade_count
                
                if new_trades > 0:
                    print(f"\n🎉 [{current_time}] 发现 {new_trades} 笔新交易!")
                    # 显示新交易
                    new_trade_list = trades[-new_trades:]
                    for trade in new_trade_list:
                        timestamp = trade.get('timestamp', 'N/A')
                        symbol = trade.get('symbol', 'N/A')
                        side = trade.get('side', 'N/A')
                        quantity = trade.get('quantity', 'N/A')
                        price = trade.get('price', 'N/A')
                        strategy = trade.get('strategy', 'N/A')
                        print(f"   📈 {timestamp}: {symbol} {side} {quantity} @ {price} ({strategy})")
                    
                    last_trade_count = current_trade_count
                else:
                    print(f"[{current_time}] 检查 #{check_count}: 无新交易 (总计: {current_trade_count} 笔)")
            else:
                print(f"[{current_time}] 检查 #{check_count}: 无法获取交易记录")
            
            # 检查持仓变化
            current_positions = get_futures_positions()
            if current_positions:
                positions = current_positions.get('positions', [])
                current_position_count = len(positions)
                position_change = current_position_count - last_position_count
                
                if position_change != 0:
                    print(f"   📈 持仓变化: {position_change:+d} (当前: {current_position_count} 个)")
                    for pos in positions:
                        symbol = pos.get('symbol', 'N/A')
                        quantity = pos.get('quantity', 'N/A')
                        entry_price = pos.get('entry_price', 'N/A')
                        unrealized_pnl = pos.get('unrealized_pnl', 'N/A')
                        print(f"      {symbol}: {quantity} @ {entry_price} (盈亏: {unrealized_pnl})")
                    
                    last_position_count = current_position_count
            
            # 等待60秒
            time.sleep(60)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 观察停止")
        print("=" * 60)
        print("📋 观察总结:")
        print(f"   🔍 观察次数: {check_count}")
        print(f"   📊 交易记录: {last_trade_count} 笔")
        print(f"   📈 持仓数量: {last_position_count} 个")
        print("💡 合约交易引擎继续在后台运行")

def main():
    """主函数"""
    print("🚀 合约交易观察工具")
    print("=" * 60)
    
    # 检查Flask应用是否运行
    status = get_futures_status()
    if not status:
        print("❌ 无法连接到Flask应用")
        print("💡 请确保Flask应用正在运行: python start.py")
        return
    
    if status.get('status') != 'RUNNING':
        print("❌ 合约交易引擎未运行")
        print("💡 请在网页界面启动合约交易")
        return
    
    print("✅ 合约交易引擎正在运行")
    watch_trading()

if __name__ == "__main__":
    main()
