#!/usr/bin/env python3
"""
测试修复后的合约配置功能
"""

import requests
import json
import time

def test_config_with_browser_simulation():
    """模拟浏览器行为测试配置"""
    print("🧪 模拟浏览器行为测试合约配置...")
    
    # 1. 设置一个特定的测试配置
    print("1. 设置测试配置...")
    test_config = {
        'leverage': 30,
        'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/futures/config/update',
            json=test_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 配置设置成功: 杠杆={test_config['leverage']}, 币种={len(test_config['symbols'])}个")
            else:
                print(f"❌ 配置设置失败: {data['message']}")
                return
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 设置请求失败: {e}")
        return
    
    # 2. 模拟页面加载（立即获取配置）
    print("\n2. 模拟页面立即加载配置...")
    try:
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['config']:
                config = data['config']
                print(f"✅ 立即加载成功: 杠杆={config['leverage']}, 币种={len(config['symbols'])}个")
                
                # 验证配置
                if (config['leverage'] == test_config['leverage'] and 
                    config['symbols'] == test_config['symbols']):
                    print("✅ 立即验证通过")
                else:
                    print("❌ 立即验证失败")
            else:
                print(f"❌ 立即加载失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 立即加载失败: {e}")
    
    # 3. 模拟页面刷新（等待1秒后获取配置，模拟前端延迟）
    print("\n3. 模拟页面刷新（等待1秒）...")
    time.sleep(1)
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['config']:
                config = data['config']
                print(f"✅ 刷新后加载成功: 杠杆={config['leverage']}, 币种={len(config['symbols'])}个")
                
                # 验证配置
                if (config['leverage'] == test_config['leverage'] and 
                    config['symbols'] == test_config['symbols']):
                    print("✅ 刷新后验证通过")
                else:
                    print("❌ 刷新后验证失败")
                    print(f"期望: 杠杆={test_config['leverage']}, 币种={test_config['symbols']}")
                    print(f"实际: 杠杆={config['leverage']}, 币种={config['symbols']}")
            else:
                print(f"❌ 刷新后加载失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 刷新后加载失败: {e}")
    
    # 4. 测试多次配置更新
    print("\n4. 测试多次配置更新...")
    for i in range(3):
        new_leverage = 20 + i * 5
        print(f"   更新 {i+1}: 杠杆={new_leverage}")
        
        try:
            response = requests.post(
                'http://127.0.0.1:5000/api/futures/config/update',
                json={'leverage': new_leverage, 'symbols': test_config['symbols']},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print(f"   ✅ 更新 {i+1} 成功")
                    
                    # 立即验证
                    verify_response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        if (verify_data['success'] and 
                            verify_data['config']['leverage'] == new_leverage):
                            print(f"   ✅ 验证 {i+1} 通过")
                        else:
                            print(f"   ❌ 验证 {i+1} 失败")
                else:
                    print(f"   ❌ 更新 {i+1} 失败: {data['message']}")
            else:
                print(f"   ❌ 更新 {i+1} HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 更新 {i+1} 异常: {e}")
        
        time.sleep(0.5)  # 短暂延迟
    
    print("\n🎯 测试结论:")
    print("如果所有测试都通过，说明后端配置保存功能正常")
    print("如果用户反映配置刷新后丢失，可能的原因:")
    print("1. 浏览器缓存问题 - 建议用户按 Ctrl+F5 强制刷新")
    print("2. JavaScript执行时机问题 - 已增加延迟和重试机制")
    print("3. 网络请求失败 - 建议检查浏览器控制台")
    print("4. DOM元素未准备好 - 已增加元素存在性检查")

def test_config_persistence_across_sessions():
    """测试配置在会话间的持久性"""
    print("\n🔄 测试配置会话间持久性...")
    
    # 设置一个唯一的配置
    unique_config = {
        'leverage': 77,  # 使用一个特殊的值
        'symbols': ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
    }
    
    print(f"设置唯一配置: 杠杆={unique_config['leverage']}")
    
    try:
        # 设置配置
        response = requests.post(
            'http://127.0.0.1:5000/api/futures/config/update',
            json=unique_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200 and response.json()['success']:
            print("✅ 唯一配置设置成功")
            
            # 多次验证配置持久性
            for i in range(5):
                time.sleep(1)
                verify_response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    if (verify_data['success'] and 
                        verify_data['config']['leverage'] == unique_config['leverage']):
                        print(f"✅ 第{i+1}次验证通过")
                    else:
                        print(f"❌ 第{i+1}次验证失败")
                        break
                else:
                    print(f"❌ 第{i+1}次验证请求失败")
                    break
            else:
                print("✅ 配置持久性测试通过")
        else:
            print("❌ 唯一配置设置失败")
    except Exception as e:
        print(f"❌ 持久性测试异常: {e}")

if __name__ == '__main__':
    test_config_with_browser_simulation()
    test_config_persistence_across_sessions()