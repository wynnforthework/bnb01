#!/usr/bin/env python3
"""
API连接诊断脚本
"""

import os
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

class BinanceDiagnostic:
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        self.testnet = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
        
        # 根据是否测试网络选择基础URL
        if self.testnet:
            self.base_url = 'https://testnet.binance.vision'
        else:
            self.base_url = 'https://api.binance.com'
    
    def check_basic_info(self):
        """检查基本配置信息"""
        print("🔍 检查基本配置")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ API Key未配置")
            return False
        
        if not self.secret_key:
            print("❌ Secret Key未配置")
            return False
        
        print(f"✅ API Key: {self.api_key[:8]}...{self.api_key[-8:]}")
        print(f"✅ Secret Key: {self.secret_key[:8]}...{self.secret_key[-8:]}")
        print(f"✅ 测试网络: {'是' if self.testnet else '否'}")
        print(f"✅ 基础URL: {self.base_url}")
        
        return True
    
    def test_server_connection(self):
        """测试服务器连接"""
        print("\n🌐 测试服务器连接")
        print("=" * 50)
        
        try:
            # 测试服务器时间（无需API密钥）
            response = requests.get(f"{self.base_url}/api/v3/time", timeout=10)
            if response.status_code == 200:
                server_time = response.json()['serverTime']
                print(f"✅ 服务器连接正常")
                print(f"   服务器时间: {server_time}")
                return True
            else:
                print(f"❌ 服务器连接失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 服务器连接异常: {e}")
            return False
    
    def test_public_api(self):
        """测试公开API"""
        print("\n📊 测试公开API")
        print("=" * 50)
        
        try:
            # 测试获取交易对信息
            response = requests.get(f"{self.base_url}/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
            if response.status_code == 200:
                price_data = response.json()
                print(f"✅ 公开API正常")
                print(f"   BTC价格: ${float(price_data['price']):,.2f}")
                return True
            else:
                print(f"❌ 公开API失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 公开API异常: {e}")
            return False
    
    def create_signature(self, params):
        """创建API签名"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def test_private_api(self):
        """测试私有API"""
        print("\n🔐 测试私有API")
        print("=" * 50)
        
        try:
            # 准备请求参数
            timestamp = int(time.time() * 1000)
            params = {
                'timestamp': timestamp,
                'recvWindow': 5000
            }
            
            # 创建签名
            signature = self.create_signature(params)
            params['signature'] = signature
            
            # 准备请求头
            headers = {
                'X-MBX-APIKEY': self.api_key
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v3/account"
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                account_data = response.json()
                print("✅ 私有API连接成功")
                print(f"   账户类型: {account_data.get('accountType', 'N/A')}")
                print(f"   交易权限: {account_data.get('permissions', [])}")
                
                # 显示余额（只显示有余额的）
                balances = account_data.get('balances', [])
                non_zero_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
                
                if non_zero_balances:
                    print("   账户余额:")
                    for balance in non_zero_balances[:5]:  # 只显示前5个
                        free = float(balance['free'])
                        locked = float(balance['locked'])
                        if free > 0 or locked > 0:
                            print(f"     {balance['asset']}: {free + locked:.8f}")
                else:
                    print("   账户余额: 无余额或全部为0")
                
                return True
            else:
                error_data = response.json() if response.content else {}
                error_code = error_data.get('code', 'N/A')
                error_msg = error_data.get('msg', 'Unknown error')
                
                print(f"❌ 私有API失败")
                print(f"   状态码: {response.status_code}")
                print(f"   错误代码: {error_code}")
                print(f"   错误信息: {error_msg}")
                
                # 提供具体的解决建议
                if error_code == -2015:
                    print("\n💡 解决建议:")
                    if self.testnet:
                        print("   1. 确认使用的是测试网络API密钥")
                        print("   2. 测试网络API密钥获取地址: https://testnet.binance.vision/")
                        print("   3. 检查API密钥是否正确复制")
                    else:
                        print("   1. 检查API密钥权限设置")
                        print("   2. 确认IP地址在白名单中")
                        print("   3. 检查API密钥是否启用现货交易权限")
                elif error_code == -1021:
                    print("\n💡 解决建议:")
                    print("   1. 检查系统时间是否准确")
                    print("   2. 尝试同步系统时间")
                
                return False
                
        except Exception as e:
            print(f"❌ 私有API异常: {e}")
            return False
    
    def run_full_diagnostic(self):
        """运行完整诊断"""
        print("🔧 Binance API 连接诊断")
        print("=" * 60)
        
        results = []
        
        # 基本配置检查
        results.append(self.check_basic_info())
        
        # 服务器连接测试
        results.append(self.test_server_connection())
        
        # 公开API测试
        results.append(self.test_public_api())
        
        # 私有API测试
        results.append(self.test_private_api())
        
        # 总结
        print("\n" + "=" * 60)
        print("📋 诊断结果总结")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        print(f"通过测试: {passed}/{total}")
        
        if passed == total:
            print("🎉 所有测试通过！API配置正确")
        else:
            print("❌ 部分测试失败，请根据上述建议进行修复")
            
            if not results[0]:
                print("\n🔧 首先修复基本配置问题")
            elif not results[1] or not results[2]:
                print("\n🔧 检查网络连接和防火墙设置")
            elif not results[3]:
                print("\n🔧 重点检查API密钥配置和权限")

def main():
    diagnostic = BinanceDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == '__main__':
    main()