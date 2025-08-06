#!/usr/bin/env python3
"""
测试前端配置加载问题
"""

import requests
import json

def test_frontend_config_loading():
    """测试前端配置加载"""
    print("🧪 测试前端配置加载问题...")
    
    # 1. 设置一个特定的配置
    print("1. 设置特定配置...")
    test_config = {
        'leverage': 15,
        'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
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
                print(f"✅ 测试配置设置成功: 杠杆={test_config['leverage']}, 币种={test_config['symbols']}")
            else:
                print(f"❌ 设置失败: {data['message']}")
                return
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 设置请求失败: {e}")
        return
    
    # 2. 模拟前端加载配置
    print("\n2. 模拟前端加载配置...")
    try:
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get')
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['config']:
                config = data['config']
                print(f"✅ 前端获取配置成功:")
                print(f"   杠杆: {config['leverage']}")
                print(f"   币种: {config['symbols']}")
                print(f"   更新时间: {config['updated_at']}")
                
                # 验证配置是否正确
                if (config['leverage'] == test_config['leverage'] and 
                    config['symbols'] == test_config['symbols']):
                    print("✅ 配置内容验证成功")
                else:
                    print("❌ 配置内容验证失败")
                    print(f"期望: {test_config}")
                    print(f"实际: {{'leverage': {config['leverage']}, 'symbols': {config['symbols']}}}")
            else:
                print(f"❌ 前端获取配置失败: {data.get('message', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 前端请求失败: {e}")
    
    # 3. 检查合约页面是否能正确访问
    print("\n3. 检查合约页面访问...")
    try:
        response = requests.get('http://127.0.0.1:5000/futures')
        if response.status_code == 200:
            print("✅ 合约页面访问正常")
            # 检查页面是否包含必要的元素
            if 'futures-leverage' in response.text and 'futures-symbols' in response.text:
                print("✅ 页面包含必要的配置元素")
            else:
                print("❌ 页面缺少配置元素")
        else:
            print(f"❌ 合约页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 页面访问失败: {e}")
    
    # 4. 提供调试建议
    print("\n🔧 调试建议:")
    print("如果配置在刷新后丢失，请检查:")
    print("1. 浏览器控制台是否有JavaScript错误")
    print("2. 网络请求是否成功（F12 -> Network）")
    print("3. 是否有缓存问题（Ctrl+F5 强制刷新）")
    print("4. 配置加载的500ms延迟是否足够")
    
    # 5. 测试配置更新后的状态显示
    print("\n5. 测试配置状态显示...")
    print("当前保存的配置应该在页面上显示为:")
    print(f"   杠杆选择框: {test_config['leverage']}x")
    print(f"   币种选择框: {', '.join(test_config['symbols'])} (选中状态)")
    print(f"   状态显示: {test_config['leverage']}x")
    print(f"   币种状态: {', '.join([s.replace('USDT', '') for s in test_config['symbols']])}")

if __name__ == '__main__':
    test_frontend_config_loading()