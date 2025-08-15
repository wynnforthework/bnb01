#!/usr/bin/env python3
"""
诊断策略执行问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.trading_engine import TradingEngine
from backend.binance_client import BinanceClient
from backend.data_collector import DataCollector
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_strategy_execution():
    """诊断策略执行问题"""
    
    print("=== 策略执行诊断 ===\n")
    
    try:
        # 1. 检查交易引擎初始化
        print("1. 检查交易引擎初始化...")
        engine = TradingEngine(
            trading_mode='SPOT',
            selected_symbols=['BTCUSDT', 'ETHUSDT'],
            enabled_strategies=['MA', 'RSI']
        )
        
        print(f"✅ 交易引擎初始化成功")
        print(f"   交易模式: {engine.trading_mode}")
        print(f"   选择币种: {engine.selected_symbols}")
        print(f"   启用策略: {engine.enabled_strategies}")
        print(f"   策略数量: {len(engine.strategies)}")
        
        if engine.strategies:
            print("   策略列表:")
            for strategy_name, strategy in engine.strategies.items():
                print(f"     - {strategy_name}: {type(strategy).__name__}")
        else:
            print("   ❌ 没有创建任何策略")
            return
        
        # 2. 检查数据获取
        print(f"\n2. 检查数据获取...")
        data_collector = DataCollector()
        
        for symbol in engine.selected_symbols:
            print(f"   检查 {symbol} 数据...")
            
            # 从数据库获取数据
            db_data = data_collector.get_market_data(symbol, '1h', limit=100)
            if db_data is not None and not db_data.empty:
                print(f"     ✅ 数据库数据: {len(db_data)} 条记录")
                print(f"     最新价格: ${db_data['close'].iloc[-1]:.4f}")
            else:
                print(f"     ❌ 数据库无数据")
            
            # 从API获取数据
            try:
                api_data = engine.binance_client.get_klines(symbol, '1h', 100)
                if api_data is not None and not api_data.empty:
                    print(f"     ✅ API数据: {len(api_data)} 条记录")
                    print(f"     最新价格: ${api_data['close'].iloc[-1]:.4f}")
                else:
                    print(f"     ❌ API无数据")
            except Exception as e:
                print(f"     ❌ API获取失败: {e}")
        
        # 3. 检查策略信号生成
        print(f"\n3. 检查策略信号生成...")
        
        for strategy_name, strategy in engine.strategies.items():
            print(f"   测试 {strategy_name}...")
            
            try:
                # 获取市场数据
                data = engine._get_enhanced_market_data(strategy.symbol)
                
                if data is not None and not data.empty:
                    print(f"     ✅ 获取到 {len(data)} 条数据")
                    
                    # 生成信号
                    signal = strategy.generate_signal(data)
                    print(f"     ✅ 生成信号: {signal}")
                    
                    # 检查策略状态
                    print(f"     当前持仓: {strategy.position}")
                    print(f"     入场价格: {strategy.entry_price}")
                    
                else:
                    print(f"     ❌ 无法获取数据")
                    
            except Exception as e:
                print(f"     ❌ 策略执行失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 4. 检查风险检查
        print(f"\n4. 检查风险检查...")
        
        try:
            portfolio_value = engine.risk_manager._get_portfolio_value()
            print(f"   投资组合价值: ${portfolio_value:.2f}")
            
            # 测试仓位计算
            for strategy_name, strategy in engine.strategies.items():
                current_price = engine.binance_client.get_ticker_price(strategy.symbol)
                if current_price:
                    suggested_quantity = engine.risk_manager.calculate_position_size(
                        strategy.symbol, 1.0, current_price, portfolio_value
                    )
                    print(f"   {strategy.symbol} 建议仓位: {suggested_quantity:.6f}")
                    
                    # 检查风险限制
                    passed, message = engine.risk_manager.check_risk_limits(
                        strategy.symbol, suggested_quantity, current_price
                    )
                    print(f"   风险检查: {'通过' if passed else '失败'} - {message}")
                else:
                    print(f"   ❌ 无法获取 {strategy.symbol} 价格")
                    
        except Exception as e:
            print(f"   ❌ 风险检查失败: {e}")
        
        # 5. 检查交易循环
        print(f"\n5. 检查交易循环...")
        
        try:
            # 执行一次交易循环
            print("   执行一次交易循环...")
            engine._execute_trading_cycle()
            print("   ✅ 交易循环执行完成")
            
        except Exception as e:
            print(f"   ❌ 交易循环失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. 检查持仓管理
        print(f"\n6. 检查持仓管理...")
        
        try:
            analysis = engine.position_manager.get_position_analysis()
            if analysis:
                print(f"   ✅ 持仓分析成功")
                print(f"   投资组合总值: ${analysis['portfolio_value']:.2f}")
                print(f"   持仓数量: {len(analysis['positions'])}")
                print(f"   风险指标: {analysis['risk_metrics']}")
            else:
                print(f"   ❌ 持仓分析失败")
                
        except Exception as e:
            print(f"   ❌ 持仓管理失败: {e}")
        
        print(f"\n=== 诊断完成 ===")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()

def test_single_strategy():
    """测试单个策略"""
    
    print("\n=== 测试单个策略 ===\n")
    
    try:
        # 创建单个策略
        from strategies.ma_strategy import MovingAverageStrategy
        
        strategy = MovingAverageStrategy(
            symbol='BTCUSDT',
            parameters={
                'short_window': 5,
                'long_window': 20,
                'stop_loss': 0.02,
                'take_profit': 0.04,
                'position_size': 0.03
            }
        )
        
        print(f"✅ 策略创建成功: {type(strategy).__name__}")
        
        # 获取数据
        binance_client = BinanceClient(trading_mode='SPOT')
        data = binance_client.get_klines('BTCUSDT', '1h', 100)
        
        if data is not None and not data.empty:
            print(f"✅ 获取数据成功: {len(data)} 条记录")
            
            # 生成信号
            signal = strategy.generate_signal(data)
            print(f"✅ 生成信号: {signal}")
            
            # 计算仓位
            current_price = data['close'].iloc[-1]
            balance = 10000  # 模拟余额
            position_size = strategy.calculate_position_size(current_price, balance)
            print(f"✅ 计算仓位: {position_size:.6f}")
            
        else:
            print("❌ 无法获取数据")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_strategy_execution()
    test_single_strategy()
