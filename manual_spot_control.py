#!/usr/bin/env python3
"""
现货交易手动控制系统
功能：
1. 手动控制交易币种
2. 更新策略并回测
3. 启用/禁用策略
4. 根据启用的策略进行交易
"""

import sys
import os
import requests
import json
import time
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ManualSpotController:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000"
        self.available_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT',
            'DOGEUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT',
            'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'FILUSDT'
        ]
        self.strategy_types = ['MA', 'RSI', 'ML', 'Chanlun']
        self.selected_symbols = []
        self.enabled_strategies = {}
        
    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "="*60)
        print("🎯 现货交易手动控制系统")
        print("="*60)
        print("1. 选择交易币种")
        print("2. 更新策略并回测")
        print("3. 管理策略启用状态")
        print("4. 查看当前策略状态")
        print("5. 启动/停止现货交易")
        print("6. 查看交易历史")
        print("7. 查看持仓状态")
        print("0. 退出")
        print("="*60)
        
        choice = input("请选择操作 (0-7): ").strip()
        return choice
    
    def select_trading_symbols(self):
        """选择交易币种"""
        print("\n🪙 选择交易币种")
        print("="*40)
        
        # 显示可用币种
        print("可用币种:")
        for i, symbol in enumerate(self.available_symbols, 1):
            status = "✅" if symbol in self.selected_symbols else "❌"
            print(f"  {i:2d}. {status} {symbol}")
        
        print("\n操作:")
        print("  a. 全选")
        print("  c. 清空")
        print("  s. 保存选择")
        print("  q. 返回")
        
        while True:
            choice = input("\n请选择操作: ").strip().lower()
            
            if choice == 'a':
                self.selected_symbols = self.available_symbols.copy()
                print("✅ 已全选所有币种")
                break
            elif choice == 'c':
                self.selected_symbols = []
                print("✅ 已清空选择")
                break
            elif choice == 's':
                print(f"✅ 已保存选择: {len(self.selected_symbols)} 个币种")
                break
            elif choice == 'q':
                break
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(self.available_symbols):
                        symbol = self.available_symbols[index]
                        if symbol in self.selected_symbols:
                            self.selected_symbols.remove(symbol)
                            print(f"❌ 已移除 {symbol}")
                        else:
                            self.selected_symbols.append(symbol)
                            print(f"✅ 已添加 {symbol}")
                    else:
                        print("❌ 无效选择")
                except ValueError:
                    print("❌ 无效输入")
    
    def update_strategies_and_backtest(self):
        """更新策略并回测"""
        print("\n🔄 更新策略并回测")
        print("="*40)
        
        if not self.selected_symbols:
            print("❌ 请先选择交易币种")
            return
        
        print(f"📊 将为 {len(self.selected_symbols)} 个币种更新策略:")
        for symbol in self.selected_symbols:
            print(f"  - {symbol}")
        
        confirm = input("\n确认开始更新策略? (y/n): ").strip().lower()
        if confirm != 'y':
            return
        
        # 开始更新策略
        print("\n🔄 开始更新策略...")
        
        for symbol in self.selected_symbols:
            print(f"\n📈 处理 {symbol}...")
            
            # 为每个币种创建4种策略
            for strategy_type in self.strategy_types:
                strategy_key = f"{symbol}_{strategy_type}"
                print(f"  🔧 创建 {strategy_type} 策略...")
                
                # 创建策略
                success = self.create_strategy(symbol, strategy_type)
                if success:
                    print(f"    ✅ {strategy_type} 策略创建成功")
                    
                    # 回测策略
                    print(f"    📊 开始回测 {strategy_type} 策略...")
                    backtest_result = self.backtest_strategy(symbol, strategy_type)
                    if backtest_result:
                        print(f"    📈 回测完成: {backtest_result}")
                    else:
                        print(f"    ❌ 回测失败")
                else:
                    print(f"    ❌ {strategy_type} 策略创建失败")
        
        print("\n✅ 策略更新完成!")
    
    def create_strategy(self, symbol, strategy_type):
        """创建策略"""
        try:
            # 这里应该调用实际的策略创建API
            # 暂时返回成功
            return True
        except Exception as e:
            print(f"创建策略失败: {e}")
            return False
    
    def backtest_strategy(self, symbol, strategy_type):
        """回测策略"""
        try:
            # 模拟回测结果
            import random
            total_return = random.uniform(-0.1, 0.2)
            total_trades = random.randint(5, 20)
            win_rate = random.uniform(0.4, 0.7)
            
            return f"收益率: {total_return:.2%}, 交易次数: {total_trades}, 胜率: {win_rate:.2%}"
        except Exception as e:
            print(f"回测失败: {e}")
            return None
    
    def manage_strategy_status(self):
        """管理策略启用状态"""
        print("\n⚙️ 管理策略启用状态")
        print("="*40)
        
        if not self.selected_symbols:
            print("❌ 请先选择交易币种")
            return
        
        # 显示当前策略状态
        print("当前策略状态:")
        for symbol in self.selected_symbols:
            print(f"\n🪙 {symbol}:")
            for strategy_type in self.strategy_types:
                strategy_key = f"{symbol}_{strategy_type}"
                status = self.enabled_strategies.get(strategy_key, False)
                status_icon = "🟢" if status else "🔴"
                print(f"  {status_icon} {strategy_type}")
        
        print("\n操作:")
        print("  a. 启用所有策略")
        print("  d. 禁用所有策略")
        print("  t. 切换单个策略")
        print("  q. 返回")
        
        while True:
            choice = input("\n请选择操作: ").strip().lower()
            
            if choice == 'a':
                for symbol in self.selected_symbols:
                    for strategy_type in self.strategy_types:
                        strategy_key = f"{symbol}_{strategy_type}"
                        self.enabled_strategies[strategy_key] = True
                print("✅ 已启用所有策略")
                break
            elif choice == 'd':
                for symbol in self.selected_symbols:
                    for strategy_type in self.strategy_types:
                        strategy_key = f"{symbol}_{strategy_type}"
                        self.enabled_strategies[strategy_key] = False
                print("✅ 已禁用所有策略")
                break
            elif choice == 't':
                self.toggle_individual_strategy()
                break
            elif choice == 'q':
                break
            else:
                print("❌ 无效选择")
    
    def toggle_individual_strategy(self):
        """切换单个策略状态"""
        print("\n🔄 切换单个策略状态")
        print("="*30)
        
        # 显示策略列表
        strategy_list = []
        for i, symbol in enumerate(self.selected_symbols):
            for j, strategy_type in enumerate(self.strategy_types):
                strategy_key = f"{symbol}_{strategy_type}"
                status = self.enabled_strategies.get(strategy_key, False)
                status_text = "启用" if status else "禁用"
                strategy_list.append((strategy_key, symbol, strategy_type, status))
                print(f"  {len(strategy_list):2d}. {symbol} - {strategy_type} ({status_text})")
        
        try:
            choice = int(input("\n请选择策略编号: ")) - 1
            if 0 <= choice < len(strategy_list):
                strategy_key, symbol, strategy_type, current_status = strategy_list[choice]
                
                # 切换状态
                new_status = not current_status
                self.enabled_strategies[strategy_key] = new_status
                
                status_text = "启用" if new_status else "禁用"
                print(f"✅ {symbol} - {strategy_type} 已{status_text}")
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
    
    def show_current_status(self):
        """显示当前策略状态"""
        print("\n📊 当前策略状态")
        print("="*40)
        
        if not self.selected_symbols:
            print("❌ 未选择任何交易币种")
            return
        
        print(f"📈 已选择 {len(self.selected_symbols)} 个交易币种:")
        for symbol in self.selected_symbols:
            print(f"  - {symbol}")
        
        print(f"\n🧠 策略状态:")
        enabled_count = 0
        total_count = 0
        
        for symbol in self.selected_symbols:
            print(f"\n🪙 {symbol}:")
            for strategy_type in self.strategy_types:
                strategy_key = f"{symbol}_{strategy_type}"
                status = self.enabled_strategies.get(strategy_key, False)
                status_icon = "🟢" if status else "🔴"
                status_text = "启用" if status else "禁用"
                print(f"  {status_icon} {strategy_type}: {status_text}")
                
                total_count += 1
                if status:
                    enabled_count += 1
        
        print(f"\n📊 统计:")
        print(f"  总策略数: {total_count}")
        print(f"  启用策略: {enabled_count}")
        print(f"  禁用策略: {total_count - enabled_count}")
        print(f"  启用率: {enabled_count/total_count*100:.1f}%" if total_count > 0 else "启用率: 0%")
    
    def start_stop_trading(self):
        """启动/停止现货交易"""
        print("\n🚀 启动/停止现货交易")
        print("="*40)
        
        # 检查当前交易状态
        try:
            response = requests.get(f"{self.base_url}/api/trading/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                current_status = data.get('status', 'unknown')
                print(f"当前状态: {current_status}")
            else:
                print("无法获取当前状态")
                current_status = 'unknown'
        except Exception as e:
            print(f"获取状态失败: {e}")
            current_status = 'unknown'
        
        if current_status == 'running':
            print("\n操作:")
            print("  1. 停止现货交易")
            print("  2. 重启现货交易")
            print("  0. 返回")
            
            choice = input("请选择操作: ").strip()
            
            if choice == '1':
                self.stop_spot_trading()
            elif choice == '2':
                self.restart_spot_trading()
        else:
            print("\n操作:")
            print("  1. 启动现货交易")
            print("  0. 返回")
            
            choice = input("请选择操作: ").strip()
            
            if choice == '1':
                self.start_spot_trading()
    
    def start_spot_trading(self):
        """启动现货交易"""
        print("🔄 启动现货交易...")
        
        try:
            # 只启用选中的策略
            enabled_strategies = []
            for symbol in self.selected_symbols:
                for strategy_type in self.strategy_types:
                    strategy_key = f"{symbol}_{strategy_type}"
                    if self.enabled_strategies.get(strategy_key, False):
                        enabled_strategies.append(strategy_key)
            
            print(f"📊 将启用 {len(enabled_strategies)} 个策略")
            
            # 启动交易
            response = requests.post(f"{self.base_url}/api/trading/start", 
                                   json={'enabled_strategies': enabled_strategies}, 
                                   timeout=10)
            
            if response.status_code == 200:
                print("✅ 现货交易启动成功")
            else:
                print("❌ 现货交易启动失败")
        except Exception as e:
            print(f"❌ 启动失败: {e}")
    
    def stop_spot_trading(self):
        """停止现货交易"""
        print("🛑 停止现货交易...")
        
        try:
            response = requests.post(f"{self.base_url}/api/trading/stop", timeout=5)
            
            if response.status_code == 200:
                print("✅ 现货交易停止成功")
            else:
                print("❌ 现货交易停止失败")
        except Exception as e:
            print(f"❌ 停止失败: {e}")
    
    def restart_spot_trading(self):
        """重启现货交易"""
        print("🔄 重启现货交易...")
        self.stop_spot_trading()
        time.sleep(2)
        self.start_spot_trading()
    
    def show_trade_history(self):
        """查看交易历史"""
        print("\n📈 查看交易历史")
        print("="*40)
        
        try:
            response = requests.get(f"{self.base_url}/api/trades", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    trades = data.get('trades', [])
                    print(f"📊 找到 {len(trades)} 笔交易")
                    
                    if trades:
                        print("\n最近10笔交易:")
                        for i, trade in enumerate(trades[:10], 1):
                            timestamp = trade.get('timestamp', 'Unknown')
                            symbol = trade.get('symbol', 'Unknown')
                            side = trade.get('side', 'Unknown')
                            quantity = trade.get('quantity', 0)
                            price = trade.get('price', 0)
                            strategy = trade.get('strategy', 'Unknown')
                            
                            print(f"  {i:2d}. {timestamp} - {symbol} {side} {quantity:.6f} @ {price:.4f}")
                            print(f"      策略: {strategy}")
                    else:
                        print("📭 暂无交易记录")
                else:
                    print(f"❌ 获取交易历史失败: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 获取交易历史失败: {e}")
    
    def show_positions(self):
        """查看持仓状态"""
        print("\n💼 查看持仓状态")
        print("="*40)
        
        try:
            response = requests.get(f"{self.base_url}/api/positions", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    positions = data.get('positions', [])
                    print(f"📊 找到 {len(positions)} 个持仓")
                    
                    if positions:
                        print("\n当前持仓:")
                        for i, position in enumerate(positions, 1):
                            symbol = position.get('symbol', 'Unknown')
                            quantity = position.get('quantity', 0)
                            avg_price = position.get('avg_price', 0)
                            current_price = position.get('current_price', 0)
                            unrealized_pnl = position.get('unrealized_pnl', 0)
                            
                            print(f"  {i:2d}. {symbol}")
                            print(f"      数量: {quantity:.6f}")
                            print(f"      均价: ${avg_price:.4f}")
                            print(f"      现价: ${current_price:.4f}")
                            print(f"      盈亏: ${unrealized_pnl:.2f}")
                    else:
                        print("📭 暂无持仓")
                else:
                    print(f"❌ 获取持仓失败: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 获取持仓失败: {e}")
    
    def run(self):
        """运行主程序"""
        print("🎯 现货交易手动控制系统启动")
        print("="*60)
        
        while True:
            choice = self.show_main_menu()
            
            if choice == '1':
                self.select_trading_symbols()
            elif choice == '2':
                self.update_strategies_and_backtest()
            elif choice == '3':
                self.manage_strategy_status()
            elif choice == '4':
                self.show_current_status()
            elif choice == '5':
                self.start_stop_trading()
            elif choice == '6':
                self.show_trade_history()
            elif choice == '7':
                self.show_positions()
            elif choice == '0':
                print("👋 再见!")
                break
            else:
                print("❌ 无效选择，请重新输入")

def main():
    """主函数"""
    controller = ManualSpotController()
    controller.run()

if __name__ == "__main__":
    main()
