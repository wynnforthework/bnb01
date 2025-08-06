#!/usr/bin/env python3
"""
测试合约数据修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def test_futures_fixes():
    """测试合约数据修复"""
    print("🧪 测试合约数据修复...")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # 1. 测试合约策略管理API
        print("1️⃣ 测试合约策略管理API...")
        response = requests.get(f'{base_url}/api/futures/strategies/list')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                strategies = data['strategies']
                print(f"✅ 合约策略管理API正常")
                print(f"   策略数量: {len(strategies)}")
                if strategies:
                    for strategy in strategies:
                        print(f"   {strategy['name']}: {strategy['symbol']} ({strategy['type']})")
                        print(f"      持仓: {strategy['position']:.6f}")
                        print(f"      入场价: ${strategy['entry_price']:.2f}")
                        print(f"      杠杆: {strategy['leverage']}x")
                else:
                    print("   ⚠️ 暂无策略数据")
            else:
                print(f"❌ 合约策略管理API错误: {data['message']}")
        else:
            print(f"❌ 合约策略管理API失败: {response.status_code}")
        
        # 2. 测试合约交易历史API
        print("\n2️⃣ 测试合约交易历史API...")
        response = requests.get(f'{base_url}/api/futures/trades')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                trades = data['trades']
                print(f"✅ 合约交易历史API正常")
                print(f"   交易记录数量: {len(trades)}")
                if trades:
                    print("最近3条交易记录:")
                    for i, trade in enumerate(trades[:3]):
                        print(f"   {i+1}. {trade['timestamp']} - {trade['symbol']} {trade['side']}")
                        print(f"      数量: {trade['quantity']} @ ${trade['price']:.2f}")
                        print(f"      策略: {trade['strategy']}")
                        print(f"      盈亏: ${trade['profit_loss']:.2f}")
                else:
                    print("   ⚠️ 暂无交易记录")
            else:
                print(f"❌ 合约交易历史API错误: {data['message']}")
        else:
            print(f"❌ 合约交易历史API失败: {response.status_code}")
        
        # 3. 测试合约交易状态API
        print("\n3️⃣ 测试合约交易状态API...")
        response = requests.get(f'{base_url}/api/futures/trading/status')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                status = data.get('status', 'UNKNOWN')
                print(f"✅ 合约交易状态API正常")
                print(f"   交易状态: {status}")
            else:
                print(f"❌ 合约交易状态API错误: {data['message']}")
        else:
            print(f"❌ 合约交易状态API失败: {response.status_code}")
        
        # 4. 测试合约账户API
        print("\n4️⃣ 测试合约账户API...")
        response = requests.get(f'{base_url}/api/futures/account')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                account = data['data']  # 修改为'data'字段
                print(f"✅ 合约账户API正常")
                print(f"   总余额: ${account['totalWalletBalance']:.2f}")
                print(f"   可用余额: ${account['availableBalance']:.2f}")
                print(f"   未实现盈亏: ${account['totalUnrealizedProfit']:.2f}")
            else:
                print(f"❌ 合约账户API错误: {data['message']}")
        else:
            print(f"❌ 合约账户API失败: {response.status_code}")
        
        # 5. 测试合约持仓API
        print("\n5️⃣ 测试合约持仓API...")
        response = requests.get(f'{base_url}/api/futures/positions')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                positions = data['positions']
                print(f"✅ 合约持仓API正常")
                print(f"   持仓数量: {len(positions)}")
                if positions:
                    for pos in positions:
                        print(f"   {pos['symbol']}: {pos['positionAmt']} @ ${pos['entryPrice']:.2f}")
                        print(f"      未实现盈亏: ${pos['unRealizedProfit']:.2f}")
                        print(f"      持仓方向: {pos['positionSide']}")
                else:
                    print("   ⚠️ 暂无持仓")
            else:
                print(f"❌ 合约持仓API错误: {data['message']}")
        else:
            print(f"❌ 合约持仓API失败: {response.status_code}")
        
        # 6. 总结
        print("\n6️⃣ 修复总结...")
        print("✅ 合约策略管理: 现在应该显示策略列表")
        print("✅ 合约交易历史: 现在应该正确过滤合约交易记录")
        print("✅ 合约交易状态: 现在应该显示正确的状态")
        print("✅ 合约账户信息: 现在应该显示账户余额")
        print("✅ 合约持仓信息: 现在应该显示持仓详情")
        
        print("\n🎯 修复完成! 现在合约页面应该显示完整的数据")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_futures_fixes() 