#!/usr/bin/env python3
"""
测试当前问题
"""

import requests
import json

def test_spot_strategies():
    """测试现货策略列表"""
    print("🧪 测试现货策略列表...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/strategies/list', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"API响应成功: {data['success']}")
            print(f"策略数量: {len(data['data'])}")
            
            if data['data']:
                print("前5个策略:")
                for i, strategy in enumerate(data['data'][:5]):
                    print(f"  {i+1}. ID: {strategy['id']}")
                    print(f"     名称: {strategy['name']}")
                    print(f"     符号: {strategy['symbol']}")
                    print(f"     类型: {strategy['type']}")
                    print(f"     状态: {strategy['status']}")
                    print()
            else:
                print("❌ 策略列表为空")
                
                # 尝试直接创建交易引擎测试
                print("尝试直接创建交易引擎...")
                try:
                    from backend.trading_engine import TradingEngine
                    engine = TradingEngine('SPOT')
                    print(f"直接创建的引擎策略数量: {len(engine.strategies)}")
                    for key, strategy in list(engine.strategies.items())[:3]:
                        print(f"  {key}: {strategy.symbol} - {strategy.__class__.__name__}")
                except Exception as engine_error:
                    print(f"创建引擎失败: {engine_error}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_futures_config():
    """测试合约配置更新"""
    print("\n🧪 测试合约配置更新...")
    
    try:
        # 1. 先获取当前配置
        print("1. 获取当前配置...")
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"当前配置: {data['config']}")
            else:
                print(f"获取配置失败: {data['message']}")
        else:
            print(f"获取配置HTTP错误: {response.status_code}")
        
        # 2. 更新配置
        print("\n2. 更新配置...")
        new_config = {
            'leverage': 20,
            'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']
        }
        
        response = requests.post(
            'http://127.0.0.1:5000/api/futures/config/update',
            json=new_config,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 配置更新成功: {data['message']}")
                print(f"新配置: {data['config']}")
            else:
                print(f"❌ 配置更新失败: {data['message']}")
        else:
            print(f"❌ 更新配置HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
        
        # 3. 再次获取配置验证
        print("\n3. 验证配置是否保存...")
        response = requests.get('http://127.0.0.1:5000/api/futures/config/get', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                saved_config = data['config']
                print(f"保存的配置: {saved_config}")
                
                # 验证配置是否正确保存
                if (saved_config['leverage'] == new_config['leverage'] and 
                    saved_config['symbols'] == new_config['symbols']):
                    print("✅ 配置保存验证成功")
                else:
                    print("❌ 配置保存验证失败")
            else:
                print(f"验证配置失败: {data['message']}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == '__main__':
    test_spot_strategies()
    test_futures_config()