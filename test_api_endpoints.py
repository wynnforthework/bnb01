#!/usr/bin/env python3
"""
测试API端点修复
"""

import requests
import json

def test_strategies_api():
    """测试策略列表API"""
    print("🧪 测试策略列表API...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/strategies/list')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                strategies = data['data']
                print(f"✅ 策略数量: {len(strategies)}")
                
                if strategies:
                    print("前3个策略:")
                    for i, strategy in enumerate(strategies[:3]):
                        print(f"  {i+1}. {strategy['name']}")
                        print(f"     状态: {strategy['status']}")
                        print(f"     持仓: {strategy['position']}")
                        print(f"     入场价: {strategy['entry_price']}")
                else:
                    print("⚠️ 策略列表为空")
            else:
                print(f"❌ API错误: {data['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_trades_api():
    """测试交易历史API"""
    print("\n🧪 测试交易历史API...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/trades')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                trades = data['trades']
                print(f"✅ 交易记录数量: {len(trades)}")
                
                if trades:
                    print("最近3条交易记录:")
                    for i, trade in enumerate(trades[:3]):
                        print(f"  {i+1}. {trade['timestamp']} - {trade['symbol']} {trade['side']}")
                        print(f"     数量: {trade['quantity']} @ {trade['price']}")
                        print(f"     策略: {trade['strategy']}")
                else:
                    print("⚠️ 暂无交易记录")
            else:
                print(f"❌ API错误: {data['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_system_status():
    """测试系统状态API"""
    print("\n🧪 测试系统状态API...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/system/status')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                status = data['data']
                print("✅ 系统状态:")
                print(f"  API连接: {'正常' if status['api_connected'] else '异常'}")
                print(f"  数据库: {'正常' if status['database_connected'] else '异常'}")
                print(f"  内存使用: {status['memory_usage']:.1f}%")
                print(f"  运行时间: {status['uptime']}")
            else:
                print(f"❌ API错误: {data['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == '__main__':
    test_strategies_api()
    test_trades_api()
    test_system_status()