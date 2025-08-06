#!/usr/bin/env python3
"""
检查策略列表和交易历史时间问题
"""

import requests
import json
from datetime import datetime

def check_strategies():
    """检查策略列表"""
    print("🔍 检查策略列表...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/strategies/list')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                strategies = data['data']
                print(f"策略数量: {len(strategies)}")
                
                if strategies:
                    print("前3个策略:")
                    for i, strategy in enumerate(strategies[:3]):
                        print(f"  {i+1}. ID: {strategy['id']}")
                        print(f"     名称: {strategy['name']}")
                        print(f"     符号: {strategy['symbol']}")
                        print(f"     类型: {strategy['type']}")
                        print(f"     状态: {strategy['status']}")
                        print()
                        
                    # 检查是否是假数据
                    if any('demo' in s['id'] or 'example' in s['id'] for s in strategies):
                        print("⚠️ 检测到假数据（包含demo或example）")
                    else:
                        print("✅ 数据看起来是真实的")
                else:
                    print("⚠️ 策略列表为空")
            else:
                print(f"❌ API错误: {data['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def check_trades_time():
    """检查交易历史时间"""
    print("\n🔍 检查交易历史时间...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/trades')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                trades = data['trades']
                print(f"交易记录数量: {len(trades)}")
                
                if trades:
                    print("最近3条交易时间:")
                    for i, trade in enumerate(trades[:3]):
                        timestamp = trade['timestamp']
                        print(f"  {i+1}. 原始时间: {timestamp}")
                        
                        # 检查时间格式
                        if 'T' in timestamp and ('Z' in timestamp or '+' in timestamp):
                            print(f"     格式: ISO格式（需要转换为本地时间）")
                        elif len(timestamp) == 19 and '-' in timestamp and ':' in timestamp:
                            print(f"     格式: 本地时间格式（已转换）")
                        else:
                            print(f"     格式: 未知格式")
                        
                        # 尝试解析时间
                        try:
                            if 'T' in timestamp:
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                print(f"     解析: {dt}")
                            else:
                                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                                print(f"     解析: {dt}")
                        except Exception as parse_error:
                            print(f"     解析失败: {parse_error}")
                        print()
                else:
                    print("⚠️ 暂无交易记录")
            else:
                print(f"❌ API错误: {data['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == '__main__':
    check_strategies()
    check_trades_time()