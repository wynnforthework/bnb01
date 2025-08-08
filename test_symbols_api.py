#!/usr/bin/env python3
"""
测试币种管理API
"""

import requests
import json
import time

def test_symbols_api():
    """测试币种管理API"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 测试币种管理API...")
    
    # 测试1: 获取币种列表
    print("\n1. 测试获取币种列表...")
    try:
        response = requests.get(f"{base_url}/api/spot/symbols", timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2: 更新币种列表
    print("\n2. 测试更新币种列表...")
    try:
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']
        response = requests.post(
            f"{base_url}/api/spot/symbols",
            json={'symbols': test_symbols},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试3: 获取策略状态
    print("\n3. 测试获取策略状态...")
    try:
        response = requests.get(f"{base_url}/api/spot/strategies/status", timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试4: 检查其他API是否正常
    print("\n4. 测试其他API...")
    try:
        response = requests.get(f"{base_url}/api/account", timeout=10)
        print(f"账户API状态码: {response.status_code}")
    except Exception as e:
        print(f"账户API请求失败: {e}")

if __name__ == "__main__":
    test_symbols_api()
