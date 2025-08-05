#!/usr/bin/env python3
"""
系统性能监控脚本
"""

import time
import psutil
import logging
from datetime import datetime
from backend.database import DatabaseManager
from backend.binance_client import BinanceClient

class SystemMonitor:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.binance_client = BinanceClient()
        self.logger = logging.getLogger(__name__)
        
    def get_system_stats(self):
        """获取系统统计信息"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now()
        }
    
    def get_trading_stats(self):
        """获取交易统计信息"""
        try:
            # 获取今日交易
            today = datetime.now().date()
            trades = self.db_manager.session.query(
                self.db_manager.Trade
            ).filter(
                self.db_manager.Trade.timestamp >= today
            ).all()
            
            total_trades = len(trades)
            total_pnl = sum(trade.profit_loss for trade in trades)
            winning_trades = len([t for t in trades if t.profit_loss > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 获取账户余额
            balance = self.binance_client.get_balance('USDT')
            
            return {
                'total_trades': total_trades,
                'total_pnl': total_pnl,
                'win_rate': win_rate,
                'balance': balance,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"获取交易统计失败: {e}")
            return None
    
    def print_status(self):
        """打印系统状态"""
        print("\n" + "="*60)
        print(f"📊 系统监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 系统资源
        sys_stats = self.get_system_stats()
        print(f"💻 CPU使用率: {sys_stats['cpu_percent']:.1f}%")
        print(f"🧠 内存使用率: {sys_stats['memory_percent']:.1f}%")
        print(f"💾 磁盘使用率: {sys_stats['disk_percent']:.1f}%")
        
        # 交易统计
        trading_stats = self.get_trading_stats()
        if trading_stats:
            print(f"\n📈 今日交易统计:")
            print(f"   交易次数: {trading_stats['total_trades']}")
            print(f"   总盈亏: ${trading_stats['total_pnl']:.2f}")
            print(f"   胜率: {trading_stats['win_rate']:.1f}%")
            print(f"   USDT余额: ${trading_stats['balance']:.2f}")
        
        print("="*60)

def main():
    """主监控循环"""
    monitor = SystemMonitor()
    
    print("🔍 启动系统监控...")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            monitor.print_status()
            time.sleep(30)  # 每30秒更新一次
            
    except KeyboardInterrupt:
        print("\n👋 监控已停止")

if __name__ == '__main__':
    main()