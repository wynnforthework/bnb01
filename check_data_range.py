#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中实际可用的数据范围
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.data_collector import DataCollector
from datetime import datetime, timedelta
import pandas as pd

def check_data_range():
    """检查数据库中实际可用的数据范围"""
    print("🔍 检查数据库中实际可用的数据范围...")
    
    dc = DataCollector()
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'MATICUSDT']
    
    for symbol in symbols:
        print(f"\n📊 {symbol}:")
        
        # 检查市场数据
        market_data = dc.get_market_data(symbol, '1h', limit=1000)
        print(f"  市场数据: {len(market_data)} 条记录")
        
        if not market_data.empty:
            start_date = market_data['timestamp'].min()
            end_date = market_data['timestamp'].max()
            print(f"  数据范围: {start_date} 到 {end_date}")
            print(f"  最新价格: {market_data.iloc[-1]['close']:.4f}")
            
            # 计算数据跨度
            data_span = end_date - start_date
            print(f"  数据跨度: {data_span.days} 天")
        else:
            print("  ⚠️  没有市场数据")
    
    print(f"\n💡 建议:")
    print(f"  1. 如果数据库中没有数据，需要先收集数据")
    print(f"  2. 如果有数据，请使用实际的数据范围进行回测")
    print(f"  3. 可以尝试使用最近30天的数据范围")

if __name__ == "__main__":
    check_data_range()
