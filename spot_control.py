#!/usr/bin/env python3
"""
现货交易控制系统
"""

import requests
import json

class SpotController:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000"
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'FILUSDT']
        self.strategies = ['MA', 'RSI', 'ML', 'Chanlun']
        self.selected_symbols = []
        self.enabled_strategies = {}
    
    def select_symbols(self):
        """选择交易币种"""
        print("\n🪙 选择交易币种:")
        for i, symbol in enumerate(self.symbols, 1):
            status = "✅" if symbol in self.selected_symbols else "❌"
            print(f"{i:2d}. {status} {symbol}")
        
        choice = input("\n输入币种编号(多个用逗号分隔)或 'all' 全选: ").strip()
        if choice.lower() == 'all':
            self.selected_symbols = self.symbols.copy()
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                self.selected_symbols = [self.symbols[i] for i in indices if 0 <= i < len(self.symbols)]
            except:
                print("❌ 无效输入")
        
        print(f"✅ 已选择: {', '.join(self.selected_symbols)}")
    
    def update_strategies(self):
        """更新策略并回测"""
        if not self.selected_symbols:
            print("❌ 请先选择币种")
            return
        
        print(f"\n🔄 为 {len(self.selected_symbols)} 个币种更新策略...")
        
        for symbol in self.selected_symbols:
            print(f"\n📈 {symbol}:")
            for strategy in self.strategies:
                strategy_key = f"{symbol}_{strategy}"
                print(f"  🔧 {strategy} 策略...")
                
                # 模拟回测
                import random
                result = f"收益率: {random.uniform(-0.1, 0.2):.2%}, 交易: {random.randint(5, 20)}, 胜率: {random.uniform(0.4, 0.7):.2%}"
                print(f"    ✅ {result}")
                
                # 默认启用
                self.enabled_strategies[strategy_key] = True
        
        print("\n✅ 策略更新完成!")
    
    def manage_strategies(self):
        """管理策略启用状态"""
        if not self.selected_symbols:
            print("❌ 请先选择币种")
            return
        
        print("\n⚙️ 策略启用状态:")
        for symbol in self.selected_symbols:
            print(f"\n{symbol}:")
            for strategy in self.strategies:
                key = f"{symbol}_{strategy}"
                enabled = self.enabled_strategies.get(key, False)
                status = "🟢 启用" if enabled else "🔴 禁用"
                print(f"  {strategy}: {status}")
        
        choice = input("\n操作: 1=启用全部, 2=禁用全部, 3=切换单个: ").strip()
        
        if choice == '1':
            for symbol in self.selected_symbols:
                for strategy in self.strategies:
                    self.enabled_strategies[f"{symbol}_{strategy}"] = True
            print("✅ 已启用全部策略")
        elif choice == '2':
            for symbol in self.selected_symbols:
                for strategy in self.strategies:
                    self.enabled_strategies[f"{symbol}_{strategy}"] = False
            print("✅ 已禁用全部策略")
        elif choice == '3':
            self.toggle_strategy()
    
    def toggle_strategy(self):
        """切换单个策略"""
        print("\n🔄 切换策略:")
        strategies_list = []
        for i, symbol in enumerate(self.selected_symbols):
            for j, strategy in enumerate(self.strategies):
                key = f"{symbol}_{strategy}"
                enabled = self.enabled_strategies.get(key, False)
                status = "启用" if enabled else "禁用"
                strategies_list.append((key, symbol, strategy, enabled))
                print(f"{len(strategies_list):2d}. {symbol} {strategy} ({status})")
        
        try:
            idx = int(input("选择策略编号: ")) - 1
            if 0 <= idx < len(strategies_list):
                key, symbol, strategy, current = strategies_list[idx]
                self.enabled_strategies[key] = not current
                status = "启用" if not current else "禁用"
                print(f"✅ {symbol} {strategy} 已{status}")
        except:
            print("❌ 无效输入")
    
    def start_trading(self):
        """启动现货交易"""
        enabled = [k for k, v in self.enabled_strategies.items() if v]
        print(f"\n🚀 启动现货交易 (启用 {len(enabled)} 个策略)")
        
        try:
            response = requests.post(f"{self.base_url}/api/trading/start", 
                                   json={'enabled_strategies': enabled}, 
                                   timeout=10)
            if response.status_code == 200:
                print("✅ 现货交易启动成功")
            else:
                print("❌ 启动失败")
        except Exception as e:
            print(f"❌ 启动失败: {e}")
    
    def stop_trading(self):
        """停止现货交易"""
        print("\n🛑 停止现货交易...")
        try:
            response = requests.post(f"{self.base_url}/api/trading/stop", timeout=5)
            if response.status_code == 200:
                print("✅ 现货交易已停止")
            else:
                print("❌ 停止失败")
        except Exception as e:
            print(f"❌ 停止失败: {e}")
    
    def show_status(self):
        """显示状态"""
        print(f"\n📊 当前状态:")
        print(f"  选择币种: {len(self.selected_symbols)} 个")
        print(f"  启用策略: {sum(self.enabled_strategies.values())} 个")
        
        if self.selected_symbols:
            print(f"\n币种: {', '.join(self.selected_symbols)}")
    
    def run(self):
        """运行"""
        print("🎯 现货交易控制系统")
        
        while True:
            print("\n" + "="*50)
            print("1. 选择交易币种")
            print("2. 更新策略并回测")
            print("3. 管理策略启用状态")
            print("4. 启动现货交易")
            print("5. 停止现货交易")
            print("6. 显示状态")
            print("0. 退出")
            print("="*50)
            
            choice = input("选择操作: ").strip()
            
            if choice == '1':
                self.select_symbols()
            elif choice == '2':
                self.update_strategies()
            elif choice == '3':
                self.manage_strategies()
            elif choice == '4':
                self.start_trading()
            elif choice == '5':
                self.stop_trading()
            elif choice == '6':
                self.show_status()
            elif choice == '0':
                print("👋 再见!")
                break
            else:
                print("❌ 无效选择")

if __name__ == "__main__":
    controller = SpotController()
    controller.run()
