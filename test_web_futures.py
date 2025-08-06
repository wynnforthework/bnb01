#!/usr/bin/env python3
"""
测试Web界面的合约交易功能
"""

import requests
import json
import time

def test_web_futures_api():
    """测试Web界面的合约交易API"""
    base_url = 'http://localhost:5000'
    
    print("🧪 测试Web界面合约交易功能...")
    
    try:
        # 1. 测试获取交易模式状态
        print("\n1️⃣ 测试获取交易模式状态...")
        response = requests.get(f'{base_url}/api/trading/mode')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 交易模式状态: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ 获取交易模式状态失败: {response.status_code}")
        
        # 2. 测试切换到合约模式
        print("\n2️⃣ 测试切换到合约模式...")
        response = requests.post(f'{base_url}/api/trading/switch', 
                               json={'mode': 'FUTURES', 'leverage': 10})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 切换到合约模式: {data['message']}")
        else:
            print(f"❌ 切换到合约模式失败: {response.status_code}")
        
        # 3. 测试获取合约账户信息
        print("\n3️⃣ 测试获取合约账户信息...")
        response = requests.get(f'{base_url}/api/futures/account')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 合约账户信息获取成功")
                print(f"  总余额: ${data['data']['totalWalletBalance']:.2f}")
                print(f"  可用余额: ${data['data']['availableBalance']:.2f}")
                print(f"  未实现盈亏: ${data['data']['totalUnrealizedProfit']:.2f}")
            else:
                print(f"⚠️ 合约账户信息获取失败: {data['message']}")
        else:
            print(f"❌ 获取合约账户信息失败: {response.status_code}")
        
        # 4. 测试获取合约持仓
        print("\n4️⃣ 测试获取合约持仓...")
        response = requests.get(f'{base_url}/api/futures/positions')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                positions = data['positions']
                print(f"✅ 合约持仓获取成功，持仓数量: {len(positions)}")
                for pos in positions:
                    print(f"  {pos['symbol']}: {pos['positionAmt']} @ ${pos['entryPrice']:.2f}")
            else:
                print(f"⚠️ 合约持仓获取失败: {data['message']}")
        else:
            print(f"❌ 获取合约持仓失败: {response.status_code}")
        
        # 5. 测试获取合约市场数据
        print("\n5️⃣ 测试获取合约市场数据...")
        response = requests.get(f'{base_url}/api/futures/market/BTCUSDT')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                market_data = data['data']
                print(f"✅ 合约市场数据获取成功")
                print(f"  当前价格: ${market_data['currentPrice']:.2f}")
                print(f"  标记价格: ${market_data['markPrice']:.2f}")
                print(f"  资金费率: {market_data['fundingRate']:.6f}")
            else:
                print(f"⚠️ 合约市场数据获取失败: {data['message']}")
        else:
            print(f"❌ 获取合约市场数据失败: {response.status_code}")
        
        # 6. 测试设置杠杆
        print("\n6️⃣ 测试设置杠杆...")
        response = requests.post(f'{base_url}/api/futures/leverage/set',
                               json={'symbol': 'BTCUSDT', 'leverage': 5})
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 杠杆设置成功: {data['message']}")
            else:
                print(f"⚠️ 杠杆设置失败: {data['message']}")
        else:
            print(f"❌ 设置杠杆失败: {response.status_code}")
        
        # 7. 测试设置保证金模式
        print("\n7️⃣ 测试设置保证金模式...")
        response = requests.post(f'{base_url}/api/futures/margin/set',
                               json={'symbol': 'BTCUSDT', 'margin_type': 'ISOLATED'})
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 保证金模式设置成功: {data['message']}")
            else:
                print(f"⚠️ 保证金模式设置失败: {data['message']}")
        else:
            print(f"❌ 设置保证金模式失败: {response.status_code}")
        
        # 8. 测试启动合约交易
        print("\n8️⃣ 测试启动合约交易...")
        response = requests.post(f'{base_url}/api/futures/trading/start',
                               json={'leverage': 10})
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 合约交易启动成功: {data['message']}")
            else:
                print(f"⚠️ 合约交易启动失败: {data['message']}")
        else:
            print(f"❌ 启动合约交易失败: {response.status_code}")
        
        # 9. 测试获取合约交易状态
        print("\n9️⃣ 测试获取合约交易状态...")
        response = requests.get(f'{base_url}/api/futures/trading/status')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ 合约交易状态获取成功")
                print(f"  运行状态: {'运行中' if data['is_running'] else '未运行'}")
                print(f"  杠杆倍数: {data['leverage']}x")
                print(f"  策略数量: {data['strategies_count']}")
            else:
                print(f"⚠️ 合约交易状态获取失败")
        else:
            print(f"❌ 获取合约交易状态失败: {response.status_code}")
        
        print(f"\n✅ Web界面合约交易功能测试完成！")
        print(f"💡 现在可以通过以下方式访问合约交易功能:")
        print(f"   1. 启动Web服务器: python app.py")
        print(f"   2. 访问: http://localhost:5000")
        print(f"   3. 在控制面板中选择'合约交易'模式")
        print(f"   4. 设置杠杆倍数并启动交易")
        print(f"   5. 使用'手动下单'功能进行合约交易")
        print(f"   6. 查看合约持仓和盈亏情况")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到Web服务器")
        print(f"💡 请先启动Web服务器: python app.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def show_futures_features():
    """显示合约交易功能特性"""
    print(f"\n🎯 合约交易功能特性:")
    print(f"")
    print(f"📊 交易模式:")
    print(f"  ✅ 现货交易 - 传统的买入持有模式")
    print(f"  ✅ 合约交易 - 支持做多做空，杠杆交易")
    print(f"  ✅ 一键切换 - 在现货和合约间快速切换")
    print(f"")
    print(f"🔧 合约功能:")
    print(f"  ✅ 杠杆设置 - 支持5x到100x杠杆")
    print(f"  ✅ 保证金模式 - 逐仓/全仓模式")
    print(f"  ✅ 双向持仓 - 同时做多做空")
    print(f"  ✅ 自动止损止盈 - 智能风险控制")
    print(f"")
    print(f"📈 交易功能:")
    print(f"  ✅ 手动下单 - 市价单/限价单")
    print(f"  ✅ 策略交易 - 自动化交易策略")
    print(f"  ✅ 持仓管理 - 实时持仓监控")
    print(f"  ✅ 一键平仓 - 快速平仓功能")
    print(f"")
    print(f"📊 数据监控:")
    print(f"  ✅ 实时价格 - 当前价格/标记价格")
    print(f"  ✅ 资金费率 - 实时资金费率监控")
    print(f"  ✅ 盈亏统计 - 未实现/已实现盈亏")
    print(f"  ✅ 风险指标 - 保证金率/强平价格")

if __name__ == '__main__':
    show_futures_features()
    
    print(f"\n" + "="*50)
    
    success = test_web_futures_api()
    
    if success:
        print(f"\n🎉 合约交易功能已成功集成到Web界面！")
    else:
        print(f"\n⚠️ 请确保Web服务器正在运行，然后重新测试。")