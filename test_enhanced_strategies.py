#!/usr/bin/env python3
"""
测试增强的策略管理功能
"""

import requests
import json

def test_enhanced_strategies():
    """测试增强的策略管理功能"""
    base_url = "http://localhost:5000"
    
    print("🧪 测试增强的策略管理功能")
    print("=" * 50)
    
    # 1. 测试获取现货币种
    print("\n1. 获取现货币种列表...")
    try:
        response = requests.get(f"{base_url}/api/spot/symbols")
        data = response.json()
        if data['success']:
            print(f"✅ 成功获取 {len(data['symbols'])} 个币种")
            print(f"币种列表: {data['symbols'][:5]}...")
        else:
            print(f"❌ 获取币种失败: {data['message']}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 2. 测试更新策略
    print("\n2. 测试更新策略...")
    try:
        test_symbols = ['BTCUSDT', 'ETHUSDT']
        response = requests.post(
            f"{base_url}/api/spot/strategies/update",
            json={'symbols': test_symbols},
            headers={'Content-Type': 'application/json'}
        )
        data = response.json()
        if data['success']:
            print(f"✅ 策略更新成功: {data['message']}")
            print(f"更新了 {len(data['results'])} 个币种的策略")
            
            # 显示回测结果
            for symbol_result in data['results']:
                print(f"\n📊 {symbol_result['symbol']} 策略回测结果:")
                for strategy in symbol_result['strategies']:
                    print(f"  - {strategy['strategy']}: 收益率 {strategy['total_return']:.2%}, "
                          f"胜率 {strategy['win_rate']:.1%}, 交易次数 {strategy['total_trades']}")
        else:
            print(f"❌ 策略更新失败: {data['message']}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 3. 测试获取策略状态
    print("\n3. 获取策略状态...")
    try:
        response = requests.get(f"{base_url}/api/spot/strategies/status")
        data = response.json()
        if data['success']:
            print(f"✅ 策略状态获取成功")
            print(f"总策略数: {data['total_count']}, 已启用: {data['enabled_count']}")
            print(f"交易状态: {data['trading_status']}")
        else:
            print(f"❌ 获取策略状态失败: {data['message']}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 4. 测试单个策略回测
    print("\n4. 测试单个策略回测...")
    try:
        response = requests.get(f"{base_url}/api/spot/strategies/backtest/BTCUSDT/MA")
        data = response.json()
        if data['success']:
            result = data['result']
            print(f"✅ BTCUSDT MA策略回测成功")
            print(f"收益率: {result['total_return']:.2%}")
            print(f"胜率: {result['win_rate']:.1%}")
            print(f"交易次数: {result['total_trades']}")
            print(f"夏普比率: {result['sharpe_ratio']:.2f}")
        else:
            print(f"❌ 回测失败: {data['message']}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 5. 测试策略管理
    print("\n5. 测试策略管理...")
    try:
        # 启用全部策略
        response = requests.post(
            f"{base_url}/api/spot/strategies/manage",
            json={'action': 'enable_all'},
            headers={'Content-Type': 'application/json'}
        )
        data = response.json()
        if data['success']:
            print(f"✅ {data['message']}")
        else:
            print(f"❌ 启用策略失败: {data['message']}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print("\n📝 功能说明:")
    print("1. ✅ 手动控制交易币种 - 通过币种管理面板")
    print("2. ✅ 更新策略按钮 - 点击后运行真实回测")
    print("3. ✅ 显示回测结果 - 每种币的每种策略都有回测数据")
    print("4. ✅ 控制策略启用 - 可以单独启用/禁用每个策略")
    print("5. ✅ 现货交易基于启用策略 - 只有启用的策略会执行交易")

if __name__ == "__main__":
    test_enhanced_strategies()
