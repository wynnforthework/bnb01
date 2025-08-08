#!/usr/bin/env python3
"""
测试现货交易管理功能
"""

import requests
import json

def test_spot_management():
    """测试现货交易管理功能"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 测试现货交易管理功能")
    print("=" * 50)
    
    # 1. 测试获取币种列表
    print("\n1. 测试获取币种列表...")
    response = requests.get(f"{base_url}/api/spot/symbols")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取 {len(data['symbols'])} 个币种")
        print(f"   币种列表: {', '.join(data['symbols'][:5])}...")
    else:
        print("❌ 获取币种列表失败")
        return
    
    # 2. 测试更新币种选择
    print("\n2. 测试更新币种选择...")
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    response = requests.post(f"{base_url}/api/spot/symbols", 
                           json={'symbols': test_symbols})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print("❌ 更新币种选择失败")
        return
    
    # 3. 测试更新策略
    print("\n3. 测试更新策略...")
    response = requests.post(f"{base_url}/api/spot/strategies/update", 
                           json={'symbols': test_symbols})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        print(f"   生成了 {len(data['results'])} 个币种的策略")
        for result in data['results']:
            print(f"   {result['symbol']}: {len(result['strategies'])} 个策略")
    else:
        print("❌ 更新策略失败")
        return
    
    # 4. 测试启用全部策略
    print("\n4. 测试启用全部策略...")
    response = requests.post(f"{base_url}/api/spot/strategies/manage", 
                           json={'action': 'enable_all'})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print("❌ 启用全部策略失败")
        return
    
    # 5. 测试获取策略状态
    print("\n5. 测试获取策略状态...")
    response = requests.get(f"{base_url}/api/spot/strategies/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 策略状态: {data['enabled_count']}/{data['total_count']} 已启用")
        print(f"   交易状态: {data['trading_status']}")
    else:
        print("❌ 获取策略状态失败")
        return
    
    # 6. 测试启动交易
    print("\n6. 测试启动交易...")
    response = requests.post(f"{base_url}/api/spot/trading/start")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        print(f"   启用的策略: {len(data['enabled_strategies'])} 个")
    else:
        print("❌ 启动交易失败")
        return
    
    # 7. 测试获取交易状态
    print("\n7. 测试获取交易状态...")
    response = requests.get(f"{base_url}/api/spot/trading/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 交易状态: {'运行中' if data['trading'] else '已停止'}")
        print(f"   启用策略: {data['enabled_strategies']} 个")
        print(f"   总策略: {data['total_strategies']} 个")
        print(f"   币种数量: {data['symbols_count']} 个")
    else:
        print("❌ 获取交易状态失败")
        return
    
    # 8. 测试停止交易
    print("\n8. 测试停止交易...")
    response = requests.post(f"{base_url}/api/spot/trading/stop")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print("❌ 停止交易失败")
        return
    
    print("\n🎉 所有测试通过！现货交易管理功能正常工作。")

if __name__ == "__main__":
    test_spot_management()
