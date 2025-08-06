#!/usr/bin/env python3
"""
测试合约配置持久化问题
"""

import requests
import json
import time

def test_config_persistence():
    """测试配置持久化"""
    print("🧪 测试合约配置持久化...")
    
    # 1. 获取初始配置
    print("1. 获取初始配置...")
    try:
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                initial_config = data['config']
                print(f"初始配置: 杠杆={initial_config['leverage']}, 币种数量={len(initial_config['symbols'])}")
            else:
                print(f"获取初始配置失败: {data['message']}")
                return
        else:
            print(f"HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"请求失败: {e}")
        return
    
    # 2. 更新配置
    print("\n2. 更新配置...")
    new_config = {
        'leverage': 25,
        'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT']
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/futures/config/update',
            json=new_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 配置更新成功: {data['message']}")
                updated_config = data['config']
                print(f"更新后配置: 杠杆={updated_config['leverage']}, 币种数量={len(updated_config['symbols'])}")
            else:
                print(f"❌ 配置更新失败: {data['message']}")
                return
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 更新请求失败: {e}")
        return
    
    # 3. 立即验证配置
    print("\n3. 立即验证配置...")
    try:
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                current_config = data['config']
                print(f"当前配置: 杠杆={current_config['leverage']}, 币种数量={len(current_config['symbols'])}")
                
                # 验证配置是否正确保存
                if (current_config['leverage'] == new_config['leverage'] and 
                    current_config['symbols'] == new_config['symbols']):
                    print("✅ 配置验证成功")
                else:
                    print("❌ 配置验证失败")
                    print(f"期望: 杠杆={new_config['leverage']}, 币种={new_config['symbols']}")
                    print(f"实际: 杠杆={current_config['leverage']}, 币种={current_config['symbols']}")
            else:
                print(f"❌ 获取配置失败: {data['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 验证请求失败: {e}")
    
    # 4. 模拟页面刷新（等待几秒后再次获取）
    print("\n4. 模拟页面刷新（等待5秒）...")
    time.sleep(5)
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                refresh_config = data['config']
                print(f"刷新后配置: 杠杆={refresh_config['leverage']}, 币种数量={len(refresh_config['symbols'])}")
                
                # 检查配置是否持久化
                if (refresh_config['leverage'] == new_config['leverage'] and 
                    refresh_config['symbols'] == new_config['symbols']):
                    print("✅ 配置持久化成功")
                else:
                    print("❌ 配置持久化失败")
                    print("问题：配置保存在内存中，服务器重启或页面刷新会丢失")
            else:
                print(f"❌ 获取刷新后配置失败: {data['message']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 刷新验证请求失败: {e}")

if __name__ == '__main__':
    test_config_persistence()