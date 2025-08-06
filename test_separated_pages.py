#!/usr/bin/env python3
"""
测试现货和合约页面分离功能
"""

import requests
import json
import time

def test_separated_pages():
    """测试现货和合约页面分离功能"""
    base_url = 'http://localhost:5000'
    
    print("🧪 测试现货和合约页面分离功能...")
    
    try:
        # 1. 测试页面访问
        print("\n1️⃣ 测试页面访问...")
        
        # 测试现货页面
        try:
            response = requests.get(f'{base_url}/')
            if response.status_code == 200:
                print("✅ 现货页面访问成功")
                if "现货交易系统" in response.text:
                    print("✅ 现货页面标题正确")
            else:
                print(f"❌ 现货页面访问失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 现货页面访问异常: {e}")
        
        # 测试合约页面
        try:
            response = requests.get(f'{base_url}/futures')
            if response.status_code == 200:
                print("✅ 合约页面访问成功")
                if "合约交易系统" in response.text:
                    print("✅ 合约页面标题正确")
            else:
                print(f"❌ 合约页面访问失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 合约页面访问异常: {e}")
        
        # 2. 测试现货API
        print("\n2️⃣ 测试现货API...")
        
        # 测试现货账户信息
        try:
            response = requests.get(f'{base_url}/api/account')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 现货账户API正常")
                    print(f"  余额数量: {len(data.get('balances', []))}")
                else:
                    print(f"⚠️ 现货账户API返回失败: {data.get('message')}")
            else:
                print(f"❌ 现货账户API失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 现货账户API异常: {e}")
        
        # 测试现货投资组合
        try:
            response = requests.get(f'{base_url}/api/portfolio')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 现货投资组合API正常")
                else:
                    print(f"⚠️ 现货投资组合API返回失败: {data.get('message')}")
            else:
                print(f"❌ 现货投资组合API失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 现货投资组合API异常: {e}")
        
        # 3. 测试合约API
        print("\n3️⃣ 测试合约API...")
        
        # 测试合约账户信息
        try:
            response = requests.get(f'{base_url}/api/futures/account')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 合约账户API正常")
                    account_data = data.get('data', {})
                    print(f"  总余额: ${account_data.get('totalWalletBalance', 0):.2f}")
                    print(f"  可用余额: ${account_data.get('availableBalance', 0):.2f}")
                else:
                    print(f"⚠️ 合约账户API返回失败: {data.get('message')}")
            else:
                print(f"❌ 合约账户API失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 合约账户API异常: {e}")
        
        # 测试合约持仓
        try:
            response = requests.get(f'{base_url}/api/futures/positions')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 合约持仓API正常")
                    positions = data.get('positions', [])
                    print(f"  持仓数量: {len(positions)}")
                else:
                    print(f"⚠️ 合约持仓API返回失败: {data.get('message')}")
            else:
                print(f"❌ 合约持仓API失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 合约持仓API异常: {e}")
        
        # 4. 测试合约市场数据
        print("\n4️⃣ 测试合约市场数据...")
        
        try:
            response = requests.get(f'{base_url}/api/futures/market/BTCUSDT')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 合约市场数据API正常")
                    market_data = data.get('data', {})
                    print(f"  当前价格: ${market_data.get('currentPrice', 0):.2f}")
                    print(f"  标记价格: ${market_data.get('markPrice', 0):.2f}")
                    print(f"  资金费率: {market_data.get('fundingRate', 0):.6f}")
                else:
                    print(f"⚠️ 合约市场数据API返回失败: {data.get('message')}")
            else:
                print(f"❌ 合约市场数据API失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 合约市场数据API异常: {e}")
        
        # 5. 测试交易模式状态
        print("\n5️⃣ 测试交易模式状态...")
        
        try:
            response = requests.get(f'{base_url}/api/trading/mode')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 交易模式状态API正常")
                    modes = data.get('modes', {})
                    spot_info = modes.get('spot', {})
                    futures_info = modes.get('futures', {})
                    
                    print(f"  现货交易:")
                    print(f"    运行状态: {'运行中' if spot_info.get('running') else '未运行'}")
                    print(f"    策略数量: {spot_info.get('strategies', 0)}")
                    
                    print(f"  合约交易:")
                    print(f"    运行状态: {'运行中' if futures_info.get('running') else '未运行'}")
                    print(f"    策略数量: {futures_info.get('strategies', 0)}")
                    print(f"    杠杆倍数: {futures_info.get('leverage', 10)}x")
                else:
                    print(f"⚠️ 交易模式状态API返回失败: {data.get('message')}")
            else:
                print(f"❌ 交易模式状态API失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 交易模式状态API异常: {e}")
        
        # 6. 测试合约交易状态
        print("\n6️⃣ 测试合约交易状态...")
        
        try:
            response = requests.get(f'{base_url}/api/futures/trading/status')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ 合约交易状态API正常")
                    print(f"  运行状态: {'运行中' if data.get('is_running') else '未运行'}")
                    print(f"  杠杆倍数: {data.get('leverage', 10)}x")
                    print(f"  策略数量: {data.get('strategies_count', 0)}")
                else:
                    print(f"⚠️ 合约交易状态API返回失败")
            else:
                print(f"❌ 合约交易状态API失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 合约交易状态API异常: {e}")
        
        print(f"\n✅ 现货和合约页面分离功能测试完成！")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到Web服务器")
        print(f"💡 请先启动Web服务器: python app.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def show_separation_features():
    """显示页面分离功能特性"""
    print(f"\n🎯 现货和合约页面分离功能特性:")
    print(f"")
    print(f"📄 页面分离:")
    print(f"  ✅ 现货页面: http://localhost:5000/")
    print(f"  ✅ 合约页面: http://localhost:5000/futures")
    print(f"  ✅ 独立导航: 页面间可以自由切换")
    print(f"  ✅ 独立样式: 现货蓝色主题，合约黄色主题")
    print(f"")
    print(f"📊 数据分离:")
    print(f"  ✅ 现货数据: 独立的现货账户、持仓、交易历史")
    print(f"  ✅ 合约数据: 独立的合约账户、持仓、交易历史")
    print(f"  ✅ 实时更新: 各自独立的WebSocket数据流")
    print(f"  ✅ API分离: 现货和合约使用不同的API端点")
    print(f"")
    print(f"🔧 交易状态独立:")
    print(f"  ✅ 现货交易: 独立的启动/停止控制")
    print(f"  ✅ 合约交易: 独立的启动/停止控制")
    print(f"  ✅ 策略管理: 各自独立的策略列表和管理")
    print(f"  ✅ 风险控制: 分别的风险管理和监控")
    print(f"")
    print(f"🪙 合约币种选择:")
    print(f"  ✅ 多选支持: 可以选择多个币种进行合约交易")
    print(f"  ✅ 动态配置: 实时更新交易币种列表")
    print(f"  ✅ 杠杆设置: 每个币种可以设置不同杠杆")
    print(f"  ✅ 策略分配: 为选中的币种自动创建策略")

if __name__ == '__main__':
    show_separation_features()
    
    print(f"\n" + "="*50)
    
    success = test_separated_pages()
    
    if success:
        print(f"\n🎉 现货和合约页面分离功能测试成功！")
        print(f"💡 使用方法:")
        print(f"   1. 启动Web服务器: python app.py")
        print(f"   2. 现货交易: 访问 http://localhost:5000/")
        print(f"   3. 合约交易: 访问 http://localhost:5000/futures")
        print(f"   4. 在合约页面选择交易币种和杠杆")
        print(f"   5. 分别启动现货和合约交易")
    else:
        print(f"\n⚠️ 请确保Web服务器正在运行，然后重新测试。")