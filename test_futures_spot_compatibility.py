#!/usr/bin/env python3
"""
测试合约交易与现货交易的币种和策略兼容性
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_futures_spot_compatibility():
    """测试合约交易与现货交易的兼容性"""
    print("🔍 测试合约交易与现货交易的兼容性")
    print("=" * 60)
    
    try:
        # 1. 加载配置
        print("1️⃣ 加载配置文件...")
        
        # 加载现货交易配置
        spot_config = {
            'symbols': [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT', 
                'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 
                'FILUSDT', 'XRPUSDT', 'MATICUSDT', 'SHIBUSDT', 'TRXUSDT', 'XLMUSDT',
                'BCHUSDT', 'ETCUSDT', 'NEARUSDT', 'FTMUSDT', 'ALGOUSDT', 'VETUSDT',
                'ICPUSDT', 'THETAUSDT', 'XMRUSDT', 'EOSUSDT', 'AAVEUSDT', 'SUSHIUSDT'
            ],
            'strategy_types': ['MA', 'RSI', 'ML', 'Chanlun']
        }
        
        # 加载合约交易配置
        with open('futures_config.json', 'r') as f:
            futures_config = json.load(f)
        
        print(f"✅ 现货交易币种数量: {len(spot_config['symbols'])}")
        print(f"✅ 现货交易策略类型: {', '.join(spot_config['strategy_types'])}")
        print(f"✅ 合约交易币种数量: {len(futures_config['symbols'])}")
        print(f"✅ 合约交易策略类型: {', '.join(futures_config['enabled_strategies'])}")
        
        # 2. 检查币种兼容性
        print("\n2️⃣ 检查币种兼容性...")
        spot_symbols = set(spot_config['symbols'])
        futures_symbols = set(futures_config['symbols'])
        
        common_symbols = spot_symbols.intersection(futures_symbols)
        spot_only = spot_symbols - futures_symbols
        futures_only = futures_symbols - spot_symbols
        
        print(f"✅ 共同支持的币种: {len(common_symbols)} 个")
        print(f"   {', '.join(sorted(common_symbols)[:10])}{'...' if len(common_symbols) > 10 else ''}")
        
        if spot_only:
            print(f"⚠️  仅现货支持的币种: {len(spot_only)} 个")
            print(f"   {', '.join(sorted(spot_only)[:5])}{'...' if len(spot_only) > 5 else ''}")
        
        if futures_only:
            print(f"⚠️  仅合约支持的币种: {len(futures_only)} 个")
            print(f"   {', '.join(sorted(futures_only)[:5])}{'...' if len(futures_only) > 5 else ''}")
        
        # 3. 检查策略兼容性
        print("\n3️⃣ 检查策略兼容性...")
        spot_strategies = set(spot_config['strategy_types'])
        futures_strategies = set(futures_config['enabled_strategies'])
        
        common_strategies = spot_strategies.intersection(futures_strategies)
        spot_only_strategies = spot_strategies - futures_strategies
        futures_only_strategies = futures_strategies - spot_strategies
        
        print(f"✅ 共同支持的策略: {', '.join(sorted(common_strategies))}")
        
        if spot_only_strategies:
            print(f"⚠️  仅现货支持的策略: {', '.join(sorted(spot_only_strategies))}")
        
        if futures_only_strategies:
            print(f"⚠️  仅合约支持的策略: {', '.join(sorted(futures_only_strategies))}")
        
        # 4. 测试交易引擎兼容性
        print("\n4️⃣ 测试交易引擎兼容性...")
        
        try:
            from backend.trading_engine import TradingEngine
            from backend.client_manager import client_manager
            
            # 测试现货交易引擎
            print("   测试现货交易引擎...")
            spot_engine = TradingEngine(trading_mode='SPOT')
            print(f"   ✅ 现货引擎策略数量: {len(spot_engine.strategies)}")
            
            # 测试合约交易引擎
            print("   测试合约交易引擎...")
            futures_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
            print(f"   ✅ 合约引擎策略数量: {len(futures_engine.strategies)}")
            
            # 检查策略类型
            spot_strategy_types = set()
            futures_strategy_types = set()
            
            for strategy_name in spot_engine.strategies.keys():
                if '_MA_' in strategy_name:
                    spot_strategy_types.add('MA')
                elif '_RSI_' in strategy_name:
                    spot_strategy_types.add('RSI')
                elif '_ML_' in strategy_name:
                    spot_strategy_types.add('ML')
                elif '_Chanlun_' in strategy_name:
                    spot_strategy_types.add('Chanlun')
            
            for strategy_name in futures_engine.strategies.keys():
                if '_MA_' in strategy_name:
                    futures_strategy_types.add('MA')
                elif '_RSI_' in strategy_name:
                    futures_strategy_types.add('RSI')
                elif '_ML_' in strategy_name:
                    futures_strategy_types.add('ML')
                elif '_Chanlun_' in strategy_name:
                    futures_strategy_types.add('Chanlun')
            
            print(f"   ✅ 现货引擎策略类型: {', '.join(sorted(spot_strategy_types))}")
            print(f"   ✅ 合约引擎策略类型: {', '.join(sorted(futures_strategy_types))}")
            
        except Exception as e:
            print(f"   ❌ 交易引擎测试失败: {e}")
        
        # 5. 总结
        print("\n5️⃣ 兼容性总结...")
        print("=" * 60)
        
        if len(common_symbols) == len(spot_symbols) and len(common_strategies) == len(spot_strategies):
            print("🎉 完全兼容！合约交易可以使用现货交易的所有币种和策略")
        elif len(common_symbols) > 0 and len(common_strategies) > 0:
            print("✅ 部分兼容！合约交易可以使用部分现货交易的币种和策略")
            print(f"   币种兼容度: {len(common_symbols)}/{len(spot_symbols)} ({len(common_symbols)/len(spot_symbols)*100:.1f}%)")
            print(f"   策略兼容度: {len(common_strategies)}/{len(spot_strategies)} ({len(common_strategies)/len(spot_strategies)*100:.1f}%)")
        else:
            print("❌ 不兼容！合约交易无法使用现货交易的币种和策略")
        
        print("\n💡 建议:")
        if spot_only:
            print(f"   - 考虑将 {len(spot_only)} 个现货专用币种添加到合约配置中")
        if spot_only_strategies:
            print(f"   - 考虑启用 {', '.join(spot_only_strategies)} 策略到合约交易中")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_futures_spot_compatibility()
