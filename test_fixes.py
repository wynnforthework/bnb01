#!/usr/bin/env python3
"""
测试修复后的功能
"""

import requests
from datetime import datetime, timezone, timedelta

def test_time_conversion():
    """测试时间转换"""
    print("🧪 测试时间转换...")
    
    # 模拟数据库时间戳（假设是UTC时间）
    utc_time = datetime(2025, 8, 6, 2, 41, 33, 724277)
    print(f"原始UTC时间: {utc_time}")
    
    # 转换为UTC+8
    utc_plus_8 = timezone(timedelta(hours=8))
    utc_time_with_tz = utc_time.replace(tzinfo=timezone.utc)
    local_time = utc_time_with_tz.astimezone(utc_plus_8)
    formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"转换后的本地时间: {formatted_time}")
    print(f"应该显示: 2025-08-06 10:41:33 (UTC+8)")

def test_api_directly():
    """直接测试API"""
    print("\n🧪 测试API响应...")
    
    try:
        # 测试策略列表
        print("测试策略列表API...")
        response = requests.get('http://127.0.0.1:5000/api/strategies/list', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['data']:
                strategy = data['data'][0]
                print(f"第一个策略: ID={strategy.get('id', 'N/A')}, 名称={strategy.get('name', 'N/A')}")
            else:
                print("策略列表为空或失败")
        else:
            print(f"策略API失败: {response.status_code}")
        
        # 测试交易历史
        print("\n测试交易历史API...")
        response = requests.get('http://127.0.0.1:5000/api/trades', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['trades']:
                trade = data['trades'][0]
                timestamp = trade.get('timestamp', 'N/A')
                print(f"最新交易时间: {timestamp}")
                
                # 检查时间格式
                if 'T' in timestamp:
                    print("❌ 时间还是ISO格式，转换未生效")
                elif len(timestamp) == 19 and '-' in timestamp and ':' in timestamp:
                    print("✅ 时间已转换为本地格式")
                else:
                    print(f"⚠️ 时间格式未知: {timestamp}")
            else:
                print("交易历史为空或失败")
        else:
            print(f"交易API失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == '__main__':
    test_time_conversion()
    test_api_directly()