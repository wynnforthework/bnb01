#!/usr/bin/env python3
"""
修复问题并重启服务
"""

import requests
import time
import subprocess
import sys

def stop_server():
    """停止服务器"""
    print("🛑 尝试停止服务器...")
    try:
        # 尝试通过API停止
        response = requests.post('http://127.0.0.1:5000/api/trading/stop', timeout=5)
        print("通过API停止交易引擎")
    except:
        pass
    
    try:
        response = requests.post('http://127.0.0.1:5000/api/futures/trading/stop', timeout=5)
        print("通过API停止合约交易引擎")
    except:
        pass

def test_fixes():
    """测试修复"""
    print("🧪 测试修复...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"尝试 {attempt + 1}/{max_retries}...")
            
            # 测试策略列表
            response = requests.get('http://127.0.0.1:5000/api/strategies/list', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['data']:
                    strategy = data['data'][0]
                    strategy_id = strategy.get('id', 'unknown')
                    strategy_name = strategy.get('name', 'str')
                    
                    print(f"策略ID: {strategy_id}")
                    print(f"策略名称: {strategy_name}")
                    
                    if strategy_id != 'unknown' and strategy_name != 'str':
                        print("✅ 策略列表修复成功")
                        strategy_fixed = True
                    else:
                        print("❌ 策略列表还有问题")
                        strategy_fixed = False
                else:
                    print("❌ 策略列表为空")
                    strategy_fixed = False
            else:
                print(f"❌ 策略API失败: {response.status_code}")
                strategy_fixed = False
            
            # 测试交易历史
            response = requests.get('http://127.0.0.1:5000/api/trades', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['trades']:
                    trade = data['trades'][0]
                    timestamp = trade.get('timestamp', '')
                    
                    print(f"交易时间: {timestamp}")
                    
                    if 'T' not in timestamp and len(timestamp) == 19:
                        print("✅ 时间格式修复成功")
                        time_fixed = True
                    else:
                        print("❌ 时间格式还有问题")
                        time_fixed = False
                else:
                    print("⚠️ 无交易历史数据")
                    time_fixed = True  # 没有数据不算错误
            else:
                print(f"❌ 交易API失败: {response.status_code}")
                time_fixed = False
            
            if strategy_fixed and time_fixed:
                print("🎉 所有问题都已修复！")
                return True
            else:
                print(f"⚠️ 还有问题需要解决，等待10秒后重试...")
                time.sleep(10)
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器")
            return False
        except Exception as e:
            print(f"❌ 测试出错: {e}")
            time.sleep(5)
    
    print("❌ 修复测试失败")
    return False

def main():
    print("🔧 开始修复和重启流程...")
    
    # 停止服务器
    stop_server()
    
    print("\n等待5秒让服务器完全停止...")
    time.sleep(5)
    
    print("\n📝 修复建议:")
    print("1. 策略列表问题可能是因为全局变量未正确初始化")
    print("2. 时间转换问题可能是因为代码更改未生效")
    print("3. 建议手动重启服务器以应用所有更改")
    print("\n手动重启步骤:")
    print("1. 按 Ctrl+C 停止当前服务器（如果还在运行）")
    print("2. 运行: python start_server.py")
    print("3. 等待服务器完全启动后测试功能")
    
    # 等待用户确认
    input("\n按回车键继续测试修复效果...")
    
    # 测试修复
    if test_fixes():
        print("\n🎉 修复成功！")
    else:
        print("\n❌ 修复失败，请手动重启服务器")

if __name__ == '__main__':
    main()