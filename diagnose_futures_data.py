#!/usr/bin/env python3
"""
诊断合约数据问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def diagnose_futures_data():
    """诊断合约数据问题"""
    print("🔍 诊断合约数据问题...")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # 1. 测试合约持仓API
        print("1️⃣ 测试合约持仓API...")
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
                else:
                    print("   ⚠️ 暂无持仓")
            else:
                print(f"❌ 合约持仓API错误: {data['message']}")
        else:
            print(f"❌ 合约持仓API失败: {response.status_code}")
        
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
        
        # 3. 测试合约策略管理API
        print("\n3️⃣ 测试合约策略管理API...")
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
        
        # 4. 测试现货交易历史API（对比）
        print("\n4️⃣ 测试现货交易历史API（对比）...")
        response = requests.get(f'{base_url}/api/trades')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                trades = data['trades']
                print(f"✅ 现货交易历史API正常")
                print(f"   交易记录数量: {len(trades)}")
                if trades:
                    print("最近3条现货交易记录:")
                    for i, trade in enumerate(trades[:3]):
                        print(f"   {i+1}. {trade['timestamp']} - {trade['symbol']} {trade['side']}")
                        print(f"      数量: {trade['quantity']} @ ${trade['price']:.2f}")
                        print(f"      策略: {trade['strategy']}")
                        print(f"      盈亏: ${trade['profit_loss']:.2f}")
                else:
                    print("   ⚠️ 暂无现货交易记录")
            else:
                print(f"❌ 现货交易历史API错误: {data['message']}")
        else:
            print(f"❌ 现货交易历史API失败: {response.status_code}")
        
        # 5. 测试合约交易状态
        print("\n5️⃣ 测试合约交易状态...")
        response = requests.get(f'{base_url}/api/futures/trading/status')
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                status = data['status']
                print(f"✅ 合约交易状态API正常")
                print(f"   交易状态: {status}")
            else:
                print(f"❌ 合约交易状态API错误: {data['message']}")
        else:
            print(f"❌ 合约交易状态API失败: {response.status_code}")
        
        # 6. 分析问题
        print("\n6️⃣ 问题分析...")
        print("根据测试结果，可能的问题原因:")
        print("1. 合约交易引擎未启动或未正确初始化")
        print("2. 合约交易记录未正确保存到数据库")
        print("3. 合约策略未正确创建或运行")
        print("4. 数据库查询过滤条件可能有问题")
        
        print("\n建议解决方案:")
        print("1. 检查合约交易引擎是否正确启动")
        print("2. 验证数据库中的交易记录")
        print("3. 检查合约策略的创建和运行")
        print("4. 确认API端点的数据过滤逻辑")
        
        print("\n✅ 诊断完成!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 诊断过程中发生错误: {e}")

if __name__ == "__main__":
    diagnose_futures_data() 