#!/usr/bin/env python3
"""
现货交易Web控制系统
提供图形化界面来管理现货交易
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import threading
import time
from datetime import datetime
import sys
import os

class SpotControlWeb:
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
        self.trading_status = False
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("现货交易控制系统")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 创建界面
        self.create_widgets()
        
        # 启动状态更新线程
        self.status_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.status_thread.start()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎯 现货交易控制系统", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 创建左右分栏
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧：币种选择和策略管理
        self.create_symbol_selection(left_frame)
        self.create_strategy_management(left_frame)
        
        # 右侧：状态显示和控制
        self.create_status_display(right_frame)
        self.create_control_panel(right_frame)
    
    def create_symbol_selection(self, parent):
        """创建币种选择区域"""
        # 币种选择框架
        symbol_frame = ttk.LabelFrame(parent, text="🪙 交易币种选择", padding=10)
        symbol_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 币种列表
        self.symbol_listbox = tk.Listbox(symbol_frame, height=8, selectmode=tk.MULTIPLE)
        self.symbol_listbox.pack(fill=tk.X, pady=(0, 10))
        
        # 添加币种到列表
        for symbol in self.available_symbols:
            self.symbol_listbox.insert(tk.END, symbol)
        
        # 按钮框架
        symbol_buttons_frame = ttk.Frame(symbol_frame)
        symbol_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(symbol_buttons_frame, text="全选", 
                  command=self.select_all_symbols).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(symbol_buttons_frame, text="清空", 
                  command=self.clear_symbols).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(symbol_buttons_frame, text="应用选择", 
                  command=self.apply_symbol_selection).pack(side=tk.LEFT)
    
    def create_strategy_management(self, parent):
        """创建策略管理区域"""
        # 策略管理框架
        strategy_frame = ttk.LabelFrame(parent, text="⚙️ 策略管理", padding=10)
        strategy_frame.pack(fill=tk.BOTH, expand=True)
        
        # 策略列表
        self.strategy_tree = ttk.Treeview(strategy_frame, columns=('symbol', 'strategy', 'status'), 
                                         show='tree headings', height=10)
        self.strategy_tree.heading('#0', text='策略ID')
        self.strategy_tree.heading('symbol', text='币种')
        self.strategy_tree.heading('strategy', text='策略类型')
        self.strategy_tree.heading('status', text='状态')
        
        self.strategy_tree.column('#0', width=150)
        self.strategy_tree.column('symbol', width=100)
        self.strategy_tree.column('strategy', width=100)
        self.strategy_tree.column('status', width=80)
        
        self.strategy_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 策略按钮
        strategy_buttons_frame = ttk.Frame(strategy_frame)
        strategy_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(strategy_buttons_frame, text="更新策略", 
                  command=self.update_strategies).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(strategy_buttons_frame, text="启用全部", 
                  command=self.enable_all_strategies).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(strategy_buttons_frame, text="禁用全部", 
                  command=self.disable_all_strategies).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(strategy_buttons_frame, text="切换状态", 
                  command=self.toggle_strategy).pack(side=tk.LEFT)
    
    def create_status_display(self, parent):
        """创建状态显示区域"""
        # 状态显示框架
        status_frame = ttk.LabelFrame(parent, text="📊 系统状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 状态信息
        self.status_text = scrolledtext.ScrolledText(status_frame, height=15, width=50)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # 更新状态按钮
        ttk.Button(status_frame, text="刷新状态", 
                  command=self.refresh_status).pack(pady=(10, 0))
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        # 控制面板框架
        control_frame = ttk.LabelFrame(parent, text="🎮 交易控制", padding=10)
        control_frame.pack(fill=tk.X)
        
        # 交易状态
        self.trading_status_var = tk.StringVar(value="已停止")
        status_label = ttk.Label(control_frame, text="交易状态:")
        status_label.pack(anchor=tk.W)
        
        self.status_display = ttk.Label(control_frame, textvariable=self.trading_status_var, 
                                       font=('Arial', 12, 'bold'))
        self.status_display.pack(anchor=tk.W, pady=(0, 10))
        
        # 控制按钮
        control_buttons_frame = ttk.Frame(control_frame)
        control_buttons_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(control_buttons_frame, text="启动交易", 
                                      command=self.start_trading)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_buttons_frame, text="停止交易", 
                                     command=self.stop_trading)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_buttons_frame, text="重启交易", 
                  command=self.restart_trading).pack(side=tk.LEFT)
    
    def select_all_symbols(self):
        """全选币种"""
        self.symbol_listbox.selection_set(0, tk.END)
    
    def clear_symbols(self):
        """清空币种选择"""
        self.symbol_listbox.selection_clear(0, tk.END)
    
    def apply_symbol_selection(self):
        """应用币种选择"""
        selection = self.symbol_listbox.curselection()
        self.selected_symbols = [self.available_symbols[i] for i in selection]
        
        messagebox.showinfo("选择确认", f"已选择 {len(self.selected_symbols)} 个币种:\n" + 
                          ", ".join(self.selected_symbols))
        
        # 更新策略列表
        self.update_strategy_tree()
    
    def update_strategy_tree(self):
        """更新策略树形视图"""
        # 清空现有项目
        for item in self.strategy_tree.get_children():
            self.strategy_tree.delete(item)
        
        # 添加策略
        for symbol in self.selected_symbols:
            for strategy in self.strategy_types:
                strategy_id = f"{symbol}_{strategy}"
                enabled = self.enabled_strategies.get(strategy_id, False)
                status = "启用" if enabled else "禁用"
                
                self.strategy_tree.insert('', 'end', strategy_id, 
                                        text=strategy_id,
                                        values=(symbol, strategy, status))
    
    def update_strategies(self):
        """更新策略"""
        if not self.selected_symbols:
            messagebox.showwarning("警告", "请先选择交易币种")
            return
        
        # 显示进度对话框
        progress_window = tk.Toplevel(self.root)
        progress_window.title("更新策略")
        progress_window.geometry("300x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_label = ttk.Label(progress_window, text="正在更新策略...")
        progress_label.pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        def update_process():
            try:
                # 模拟策略更新过程
                total = len(self.selected_symbols) * len(self.strategy_types)
                current = 0
                
                for symbol in self.selected_symbols:
                    for strategy in self.strategy_types:
                        strategy_id = f"{symbol}_{strategy}"
                        
                        # 模拟API调用
                        time.sleep(0.1)
                        
                        # 默认启用策略
                        self.enabled_strategies[strategy_id] = True
                        current += 1
                
                # 更新界面
                self.root.after(0, lambda: self.update_strategy_tree())
                self.root.after(0, lambda: progress_window.destroy())
                self.root.after(0, lambda: messagebox.showinfo("完成", "策略更新完成！"))
                
            except Exception as e:
                self.root.after(0, lambda: progress_window.destroy())
                self.root.after(0, lambda: messagebox.showerror("错误", f"更新失败: {str(e)}"))
        
        threading.Thread(target=update_process, daemon=True).start()
    
    def enable_all_strategies(self):
        """启用全部策略"""
        for symbol in self.selected_symbols:
            for strategy in self.strategy_types:
                self.enabled_strategies[f"{symbol}_{strategy}"] = True
        
        self.update_strategy_tree()
        messagebox.showinfo("完成", "已启用全部策略")
    
    def disable_all_strategies(self):
        """禁用全部策略"""
        for symbol in self.selected_symbols:
            for strategy in self.strategy_types:
                self.enabled_strategies[f"{symbol}_{strategy}"] = False
        
        self.update_strategy_tree()
        messagebox.showinfo("完成", "已禁用全部策略")
    
    def toggle_strategy(self):
        """切换策略状态"""
        selection = self.strategy_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要切换的策略")
            return
        
        for item in selection:
            strategy_id = self.strategy_tree.item(item, 'text')
            current_status = self.enabled_strategies.get(strategy_id, False)
            self.enabled_strategies[strategy_id] = not current_status
        
        self.update_strategy_tree()
        messagebox.showinfo("完成", "策略状态已切换")
    
    def refresh_status(self):
        """刷新状态"""
        try:
            # 获取交易状态
            response = requests.get(f"{self.base_url}/api/trading/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                self.trading_status = status_data.get('trading', False)
                
                # 获取账户信息
                account_response = requests.get(f"{self.base_url}/api/account", timeout=5)
                account_data = account_response.json() if account_response.status_code == 200 else {}
                
                # 更新状态显示
                status_text = f"系统状态更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                status_text += f"交易状态: {'运行中' if self.trading_status else '已停止'}\n"
                status_text += f"已选择币种: {len(self.selected_symbols)} 个\n"
                status_text += f"已启用策略: {sum(self.enabled_strategies.values())} 个\n"
                
                if account_data.get('success'):
                    balances = account_data.get('data', {}).get('balances', [])
                    status_text += f"账户余额: {len(balances)} 种资产\n"
                
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(1.0, status_text)
                
                # 更新交易状态显示
                status_text = "运行中" if self.trading_status else "已停止"
                self.trading_status_var.set(status_text)
                
            else:
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(1.0, "无法连接到服务器")
                
        except Exception as e:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, f"状态更新失败: {str(e)}")
    
    def start_trading(self):
        """启动交易"""
        try:
            response = requests.post(f"{self.base_url}/api/trading/start", 
                                   json={'symbols': self.selected_symbols}, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.trading_status = True
                    self.trading_status_var.set("运行中")
                    messagebox.showinfo("成功", "现货交易已启动")
                else:
                    messagebox.showerror("错误", result.get('message', '启动失败'))
            else:
                messagebox.showerror("错误", "无法连接到服务器")
                
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")
    
    def stop_trading(self):
        """停止交易"""
        try:
            response = requests.post(f"{self.base_url}/api/trading/stop", timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.trading_status = False
                    self.trading_status_var.set("已停止")
                    messagebox.showinfo("成功", "现货交易已停止")
                else:
                    messagebox.showerror("错误", result.get('message', '停止失败'))
            else:
                messagebox.showerror("错误", "无法连接到服务器")
                
        except Exception as e:
            messagebox.showerror("错误", f"停止失败: {str(e)}")
    
    def restart_trading(self):
        """重启交易"""
        self.stop_trading()
        time.sleep(1)
        self.start_trading()
    
    def update_status_loop(self):
        """状态更新循环"""
        while True:
            try:
                self.root.after(0, self.refresh_status)
                time.sleep(30)  # 每30秒更新一次
            except:
                break
    
    def run(self):
        """运行应用"""
        self.root.mainloop()

def main():
    """主函数"""
    app = SpotControlWeb()
    app.run()

if __name__ == "__main__":
    main()
