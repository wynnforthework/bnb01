#!/usr/bin/env python3
"""
检查Binance当前有效的交易对并更新配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.client_manager import client_manager
import json

def check_valid_symbols():
    """检查当前有效的交易对"""
    print("🔍 检查Binance当前有效的交易对...")
    print("=" * 60)
    
    # 测试符号列表
    test_symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT',
        'DOGEUSDT', 'SOLUSDT', 'MATICUSDT', 'DOTUSDT', 
        'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 
        'ATOMUSDT', 'FILUSDT', 'XRPUSDT', 'TRXUSDT'
    ]
    
    valid_symbols = []
    invalid_symbols = []
    
    try:
        # 使用现货客户端测试（通常现货交易对更稳定）
        spot_client = client_manager.get_spot_client()
        
        print("📊 测试现货交易对...")
        for symbol in test_symbols:
            try:
                # 尝试获取K线数据来验证符号
                klines = spot_client.get_klines(symbol, '1h', 1)
                if klines is not None and not klines.empty:
                    valid_symbols.append(symbol)
                    print(f"✅ {symbol}: 有效")
                else:
                    invalid_symbols.append(symbol)
                    print(f"❌ {symbol}: 无效")
            except Exception as e:
                invalid_symbols.append(symbol)
                print(f"❌ {symbol}: 无效 - {e}")
        
        print("\n" + "=" * 60)
        print("🚀 测试合约交易对...")
        
        # 使用合约客户端测试
        futures_client = client_manager.get_futures_client()
        
        futures_valid = []
        futures_invalid = []
        
        for symbol in test_symbols:
            try:
                # 尝试获取合约K线数据
                klines = futures_client.get_klines(symbol, '1h', 1)
                if klines is not None and not klines.empty:
                    futures_valid.append(symbol)
                    print(f"✅ {symbol}: 合约有效")
                else:
                    futures_invalid.append(symbol)
                    print(f"❌ {symbol}: 合约无效")
            except Exception as e:
                futures_invalid.append(symbol)
                print(f"❌ {symbol}: 合约无效 - {e}")
        
        # 生成报告
        print("\n" + "=" * 60)
        print("📋 验证结果报告")
        print("=" * 60)
        
        print(f"\n现货有效交易对 ({len(valid_symbols)}个):")
        for symbol in valid_symbols:
            print(f"  - {symbol}")
        
        print(f"\n现货无效交易对 ({len(invalid_symbols)}个):")
        for symbol in invalid_symbols:
            print(f"  - {symbol}")
        
        print(f"\n合约有效交易对 ({len(futures_valid)}个):")
        for symbol in futures_valid:
            print(f"  - {symbol}")
        
        print(f"\n合约无效交易对 ({len(futures_invalid)}个):")
        for symbol in futures_invalid:
            print(f"  - {symbol}")
        
        # 更新配置文件
        update_config_files(valid_symbols, futures_valid)
        
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")

def update_config_files(spot_symbols, futures_symbols):
    """更新配置文件"""
    print("\n" + "=" * 60)
    print("🔧 更新配置文件...")
    print("=" * 60)
    
    # 更新config.py中的DEFAULT_SYMBOLS
    try:
        config_content = """import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Binance API配置
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    BINANCE_API_KEY_FUTURES = os.getenv('BINANCE_API_KEY_FUTURES', '')
    BINANCE_SECRET_KEY_FUTURES = os.getenv('BINANCE_SECRET_KEY_FUTURES', '')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading.db')
    
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # 交易配置 - 更新为有效的交易对
    DEFAULT_SYMBOLS = {spot_symbols}
    DEFAULT_TIMEFRAME = '1h'
    MAX_POSITION_SIZE = 0.1  # 最大仓位比例
    STOP_LOSS_PERCENT = 0.02  # 止损比例
    TAKE_PROFIT_PERCENT = 0.05  # 止盈比例
    
    # 风险管理
    MAX_DAILY_LOSS = 0.05  # 最大日损失比例
    MAX_DRAWDOWN = 0.15  # 最大回撤比例
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
"""
        
        # 格式化DEFAULT_SYMBOLS
        formatted_symbols = "[" + ", ".join([f"'{s}'" for s in spot_symbols]) + "]"
        config_content = config_content.replace("{spot_symbols}", formatted_symbols)
        
        with open('config/config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("✅ config/config.py 已更新")
        
    except Exception as e:
        print(f"❌ 更新config.py失败: {e}")
    
    # 更新futures_config.json
    try:
        futures_config = {
            "leverage": 10,
            "symbols": futures_symbols,
            "updated_at": "2025-08-08T13:30:00.000000"
        }
        
        with open('futures_config.json', 'w', encoding='utf-8') as f:
            json.dump(futures_config, f, indent=2, ensure_ascii=False)
        
        print("✅ futures_config.json 已更新")
        
    except Exception as e:
        print(f"❌ 更新futures_config.json失败: {e}")
    
    # 生成HTML选项更新建议
    print("\n📝 HTML模板更新建议:")
    print("在 templates/index.html 和 templates/futures.html 中:")
    print("将以下无效的选项移除:")
    
    all_test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 
                       'SOLUSDT', 'MATICUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 
                       'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'FILUSDT', 'XRPUSDT', 'TRXUSDT']
    
    invalid_for_html = [s for s in all_test_symbols if s not in spot_symbols]
    
    for symbol in invalid_for_html:
        print(f"  - <option value=\"{symbol}\">{symbol.replace('USDT', '/USDT')}</option>")
    
    print(f"\n保留以下有效的选项:")
    for symbol in spot_symbols:
        print(f"  - <option value=\"{symbol}\">{symbol.replace('USDT', '/USDT')}</option>")

if __name__ == "__main__":
    check_valid_symbols()
