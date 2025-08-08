#!/usr/bin/env python3
"""
币种管理功能测试脚本
"""

import requests
import json
import time

def test_symbol_management():
    """测试币种管理功能"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 开始测试币种管理功能...")
    
    # 1. 测试获取当前币种列表
    print("\n1. 测试获取当前币种列表")
    try:
        response = requests.get(f"{base_url}/api/spot/symbols", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data['success']:
            print("✅ 获取币种列表成功")
            current_symbols = data['symbols']
        else:
            print("❌ 获取币种列表失败")
            return False
    except Exception as e:
        print(f"❌ 获取币种列表异常: {e}")
        return False
    
    # 2. 测试获取所有可用币种
    print("\n2. 测试获取所有可用币种")
    try:
        response = requests.get(f"{base_url}/api/spot/symbols/available", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data['success']:
            print("✅ 获取可用币种成功")
            available_symbols = data['symbols']
        else:
            print("❌ 获取可用币种失败")
            return False
    except Exception as e:
        print(f"❌ 获取可用币种异常: {e}")
        return False
    
    # 3. 测试更新币种列表
    print("\n3. 测试更新币种列表")
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']
    try:
        response = requests.post(
            f"{base_url}/api/spot/symbols",
            json={'symbols': test_symbols},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data['success']:
            print("✅ 更新币种列表成功")
        else:
            print("❌ 更新币种列表失败")
            return False
    except Exception as e:
        print(f"❌ 更新币种列表异常: {e}")
        return False
    
    # 4. 测试获取策略状态
    print("\n4. 测试获取策略状态")
    try:
        response = requests.get(f"{base_url}/api/spot/strategies/status", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data['success']:
            print("✅ 获取策略状态成功")
        else:
            print("❌ 获取策略状态失败")
            return False
    except Exception as e:
        print(f"❌ 获取策略状态异常: {e}")
        return False
    
    # 5. 测试更新策略
    print("\n5. 测试更新策略")
    try:
        response = requests.post(
            f"{base_url}/api/spot/strategies/update",
            json={'symbols': test_symbols},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data['success']:
            print("✅ 更新策略成功")
        else:
            print("❌ 更新策略失败")
            return False
    except Exception as e:
        print(f"❌ 更新策略异常: {e}")
        return False
    
    # 6. 测试管理策略
    print("\n6. 测试管理策略 - 启用全部")
    try:
        response = requests.post(
            f"{base_url}/api/spot/strategies/manage",
            json={'action': 'enable_all'},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data['success']:
            print("✅ 启用全部策略成功")
        else:
            print("❌ 启用全部策略失败")
            return False
    except Exception as e:
        print(f"❌ 启用全部策略异常: {e}")
        return False
    
    print("\n✅ 币种管理功能测试完成")
    return True

if __name__ == "__main__":
    test_symbol_management()
