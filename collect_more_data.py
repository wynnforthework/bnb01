#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收集更多历史数据脚本
用于为策略参数优化提供更充足的数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from backend.data_collector import DataCollector
from datetime import datetime, timedelta
import pandas as pd

async def collect_historical_data_for_symbol(symbol: str, days: int = 90):
    """为指定币种收集历史数据"""
    print(f"📊 开始收集 {symbol} 的历史数据...")
    
    try:
        dc = DataCollector()
        
        # 收集历史数据
        print(f"  正在收集最近 {days} 天的数据...")
        data = await dc.collect_historical_data(symbol, '1h', days)
        
        if not data.empty:
            print(f"  ✅ {symbol} 数据收集成功，获得 {len(data)} 条记录")
            print(f"  数据范围: {data['timestamp'].min()} 到 {data['timestamp'].max()}")
            print(f"  最新价格: {data.iloc[-1]['close']:.4f}")
            return True
        else:
            print(f"  ❌ {symbol} 数据收集失败")
            return False
            
    except Exception as e:
        print(f"  ❌ {symbol} 数据收集异常: {e}")
        return False

async def collect_data_for_all_symbols():
    """为所有币种收集数据"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'MATICUSDT', 'ADAUSDT', 'SOLUSDT']
    
    print("🚀 开始收集历史数据...")
    print("=" * 50)
    
    success_count = 0
    for symbol in symbols:
        success = await collect_historical_data_for_symbol(symbol, days=90)
        if success:
            success_count += 1
        print()  # 空行分隔
    
    print("=" * 50)
    print(f"📈 数据收集完成: {success_count}/{len(symbols)} 个币种成功")
    
    # 检查收集后的数据情况
    print("\n🔍 检查收集后的数据情况...")
    dc = DataCollector()
    
    for symbol in symbols:
        market_data = dc.get_market_data(symbol, '1h', limit=1000)
        if not market_data.empty:
            start_date = market_data['timestamp'].min()
            end_date = market_data['timestamp'].max()
            data_span = end_date - start_date
            print(f"  {symbol}: {len(market_data)} 条记录, {data_span.days} 天")
        else:
            print(f"  {symbol}: 无数据")

def main():
    """主函数"""
    print("🎯 历史数据收集脚本")
    print("用于为策略参数优化提供充足的历史数据")
    print("=" * 50)
    
    # 运行异步数据收集
    try:
        asyncio.run(collect_data_for_all_symbols())
    except KeyboardInterrupt:
        print("\n🛑 用户中断数据收集")
    except Exception as e:
        print(f"❌ 数据收集失败: {e}")

if __name__ == "__main__":
    main()
