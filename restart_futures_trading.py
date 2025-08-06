#!/usr/bin/env python3
"""
重启合约交易以应用修复
"""

import requests
import time

def restart_futures_trading():
    print("🔄 重启合约交易以应用修复...")
    
    base_url = "http://127.0.0.1:5000"
    
    try:
        # 1. 停止当前的合约交易
        print("1. 停止当前的合约交易...")
        stop_response = requests.post(f"{base_url}/api/futures/trading/stop")
        if stop_response.status_code == 200:
            result = stop_response.json()
            print(f"✅ {result.get('message', '停止成功')}")
        else:
            print(f"⚠️ 停止请求失败: {stop_response.status_code}")
        
        # 等待几秒钟
        time.sleep(3)
        
        # 2. 启动合约交易（使用修复后的逻辑）
        print("\n2. 启动合约交易（使用修复后的逻辑）...")
        start_data = {
            "leverage": 10,
            "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        }
        
        start_response = requests.post(
            f"{base_url}/api/futures/trading/start",
            json=start_data,
            headers={"Content-Type": "application/json"}
        )
        
        if start_response.status_code == 200:
            result = start_response.json()
            print(f"✅ {result.get('message', '启动成功')}")
        else:
            print(f"❌ 启动请求失败: {start_response.status_code}")
            print(f"响应: {start_response.text}")
        
        # 3. 检查交易状态
        print("\n3. 检查交易状态...")
        status_response = requests.get(f"{base_url}/api/futures/trading/status")
        if status_response.status_code == 200:
            result = status_response.json()
            if result.get('success'):
                is_running = result.get('is_running', False)
                print(f"交易状态: {'运行中' if is_running else '未运行'}")
            else:
                print(f"获取状态失败: {result.get('message')}")
        
        # 4. 等待一段时间观察结果
        print("\n4. 等待60秒观察交易结果...")
        for i in range(60, 0, -10):
            print(f"剩余等待时间: {i}秒", end='\r')
            time.sleep(10)
        
        print("\n\n5. 检查持仓变化...")
        positions_response = requests.get(f"{base_url}/api/futures/positions")
        if positions_response.status_code == 200:
            result = positions_response.json()
            if result.get('success'):
                positions = result.get('positions', [])
                if positions:
                    print(f"✅ 发现 {len(positions)} 个持仓:")
                    for pos in positions:
                        print(f"  {pos['symbol']}: {pos['positionAmt']} @ {pos['entryPrice']}")
                        print(f"    未实现盈亏: {pos['unRealizedProfit']} USDT")
                else:
                    print("⚠️ 仍然没有持仓")
                    print("可能的原因:")
                    print("- 市场条件变化，信号消失")
                    print("- 风险管理限制")
                    print("- 需要更长时间等待")
            else:
                print(f"获取持仓失败: {result.get('message')}")
        
        print("\n✅ 重启完成")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 重启过程出错: {e}")

if __name__ == '__main__':
    restart_futures_trading()