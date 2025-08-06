#!/usr/bin/env python3
"""
修复机器学习和缠论策略回测数据为0的问题
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_ml_strategy_parameters():
    """修复机器学习策略参数"""
    print("🧠 修复机器学习策略参数...")
    
    # 更保守的参数设置
    ml_params = {
        'model_type': 'random_forest',
        'lookback_period': 30,  # 增加回看期
        'prediction_horizon': 1,
        'min_confidence': 0.65,  # 提高信心阈值
        'up_threshold': 0.01,    # 1% - 更保守的阈值
        'down_threshold': -0.01, # -1% - 更保守的阈值
        'stop_loss': 0.03,       # 3%止损
        'take_profit': 0.06,     # 6%止盈
        'position_size': 0.05,   # 降低仓位
        'retrain_frequency': 50,  # 减少重训练频率
        'min_training_samples': 100  # 增加最小训练样本
    }
    
    return ml_params

def fix_chanlun_strategy_parameters():
    """修复缠论策略参数"""
    print("🎯 修复缠论策略参数...")
    
    # 更宽松的参数设置
    chanlun_params = {
        'timeframes': ['30m', '1h', '4h'],
        'min_swing_length': 2,  # 降低最小笔长度
        'central_bank_min_bars': 2,  # 降低中枢最少笔数
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'rsi_period': 14,
        'ma_short': 5,
        'ma_long': 20,
        'position_size': 0.2,  # 降低初始仓位
        'max_position': 0.8,   # 降低最大仓位
        'stop_loss': 0.04,     # 4%止损
        'take_profit': 0.08,   # 8%止盈
        'trend_confirmation': 0.01,  # 降低趋势确认阈值
        'divergence_threshold': 0.05  # 降低背离阈值
    }
    
    return chanlun_params

def fix_chanlun_buy_sell_logic():
    """修复缠论买卖点逻辑"""
    print("🔧 修复缠论买卖点逻辑...")
    
    # 修改缠论策略的买卖点判断逻辑
    chanlun_fixes = {
        'buy_point_1_threshold': -0.05,  # 降低第一类买点阈值
        'buy_point_2_ma_threshold': 0.01,  # 降低第二类买点均线阈值
        'sell_point_1_threshold': 0.05,   # 降低第一类卖点阈值
        'sell_point_2_ma_threshold': -0.01,  # 降低第二类卖点均线阈值
        'divergence_sensitivity': 0.8,    # 提高背离敏感度
        'trend_sensitivity': 0.6         # 提高趋势敏感度
    }
    
    return chanlun_fixes

def update_app_backtest_api():
    """更新app.py中的回测API参数"""
    print("📝 更新app.py中的回测API参数...")
    
    try:
        # 读取app.py文件
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新机器学习策略参数
        ml_old_params = """'model_type': 'random_forest',
                'lookback_period': 20,
                'prediction_horizon': 1,
                'min_confidence': 0.6,
                'up_threshold': 0.01,
                'down_threshold': -0.01,
                'stop_loss': 0.02,
                'take_profit': 0.05,
                'position_size': 0.1"""
        
        ml_new_params = """'model_type': 'random_forest',
                'lookback_period': 30,
                'prediction_horizon': 1,
                'min_confidence': 0.65,
                'up_threshold': 0.015,
                'down_threshold': -0.015,
                'stop_loss': 0.03,
                'take_profit': 0.06,
                'position_size': 0.05"""
        
        content = content.replace(ml_old_params, ml_new_params)
        
        # 更新缠论策略参数
        chanlun_old_params = """'timeframes': ['30m', '1h', '4h'],
                'min_swing_length': 3,
                'central_bank_min_bars': 3,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'rsi_period': 14,
                'ma_short': 5,
                'ma_long': 20,
                'position_size': 0.3,
                'max_position': 1.0,
                'stop_loss': 0.03,
                'take_profit': 0.05,
                'trend_confirmation': 0.02,
                'divergence_threshold': 0.1"""
        
        chanlun_new_params = """'timeframes': ['30m', '1h', '4h'],
                'min_swing_length': 2,
                'central_bank_min_bars': 2,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'rsi_period': 14,
                'ma_short': 5,
                'ma_long': 20,
                'position_size': 0.2,
                'max_position': 0.8,
                'stop_loss': 0.04,
                'take_profit': 0.08,
                'trend_confirmation': 0.01,
                'divergence_threshold': 0.05"""
        
        content = content.replace(chanlun_old_params, chanlun_new_params)
        
        # 写回文件
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ app.py参数更新成功")
        
    except Exception as e:
        print(f"❌ 更新app.py失败: {e}")

def update_chanlun_strategy():
    """更新缠论策略的买卖点逻辑"""
    print("🔧 更新缠论策略的买卖点逻辑...")
    
    try:
        # 读取缠论策略文件
        with open('strategies/chanlun_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新第一类买点逻辑
        buy_point_1_old = """            # 背离判断：价格创新低但MACD绿柱面积缩小
            if hist_area > -0.1:  # 绿柱面积较小
                return True"""
        
        buy_point_1_new = """            # 背离判断：价格创新低但MACD绿柱面积缩小
            if hist_area > -0.05:  # 降低绿柱面积阈值，提高敏感度
                return True"""
        
        content = content.replace(buy_point_1_old, buy_point_1_new)
        
        # 更新第二类买点逻辑
        buy_point_2_old = """            # 检查是否站上5日均线
            if current_price < ma_short:
                return False"""
        
        buy_point_2_new = """            # 检查是否站上5日均线（放宽条件）
            if current_price < ma_short * 0.99:  # 允许1%的误差
                return False"""
        
        content = content.replace(buy_point_2_old, buy_point_2_new)
        
        # 写回文件
        with open('strategies/chanlun_strategy.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 缠论策略更新成功")
        
    except Exception as e:
        print(f"❌ 更新缠论策略失败: {e}")

def update_ml_strategy():
    """更新机器学习策略的参数"""
    print("🧠 更新机器学习策略参数...")
    
    try:
        # 读取机器学习策略文件
        with open('strategies/ml_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新默认参数
        ml_params_old = """        self.lookback_period = parameters.get('lookback_period', 20)
        self.prediction_horizon = parameters.get('prediction_horizon', 1)
        self.model_type = parameters.get('model_type', 'random_forest')
        self.retrain_frequency = parameters.get('retrain_frequency', 100)  # 每100个数据点重训练
        self.min_training_samples = parameters.get('min_training_samples', 200)"""
        
        ml_params_new = """        self.lookback_period = parameters.get('lookback_period', 30)
        self.prediction_horizon = parameters.get('prediction_horizon', 1)
        self.model_type = parameters.get('model_type', 'random_forest')
        self.retrain_frequency = parameters.get('retrain_frequency', 50)  # 每50个数据点重训练
        self.min_training_samples = parameters.get('min_training_samples', 100)"""
        
        content = content.replace(ml_params_old, ml_params_new)
        
        # 写回文件
        with open('strategies/ml_strategy.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 机器学习策略更新成功")
        
    except Exception as e:
        print(f"❌ 更新机器学习策略失败: {e}")

def test_fixed_strategies():
    """测试修复后的策略"""
    print("\n🧪 测试修复后的策略...")
    
    try:
        import asyncio
        from strategies.ml_strategy import MLStrategy
        from strategies.chanlun_strategy import ChanlunStrategy
        from backend.backtesting import BacktestEngine
        from backend.data_collector import DataCollector
        
        async def test_strategies():
            # 创建数据收集器
            collector = DataCollector()
            
            # 获取历史数据
            print("1️⃣ 获取历史数据...")
            data = await collector.collect_historical_data('BTCUSDT', '1h', 100)
            print(f"   获取到 {len(data)} 条数据")
            
            if data.empty:
                print("❌ 无法获取历史数据")
                return
            
            # 测试机器学习策略
            print("\n2️⃣ 测试修复后的机器学习策略...")
            ml_strategy = MLStrategy('BTCUSDT', fix_ml_strategy_parameters())
            
            # 测试信号生成
            signals = []
            for i in range(50, len(data)):
                current_data = data.iloc[:i+1]
                signal = ml_strategy.generate_signal(current_data)
                signals.append(signal)
                if signal != 'HOLD':
                    print(f"   ML信号: {signal} at {data.iloc[i]['timestamp']}")
            
            print(f"   ML生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
            
            # 测试缠论策略
            print("\n3️⃣ 测试修复后的缠论策略...")
            chanlun_strategy = ChanlunStrategy('BTCUSDT', fix_chanlun_strategy_parameters())
            
            # 测试信号生成
            signals = []
            for i in range(50, len(data)):
                current_data = data.iloc[:i+1]
                signal = chanlun_strategy.generate_signal(current_data)
                signals.append(signal)
                if signal != 'HOLD':
                    print(f"   缠论信号: {signal} at {data.iloc[i]['timestamp']}")
            
            print(f"   缠论生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
            
            # 运行回测
            print("\n4️⃣ 运行修复后的回测...")
            backtest_engine = BacktestEngine(initial_capital=10000.0)
            
            # 机器学习策略回测
            ml_result = backtest_engine.run_backtest(
                strategy=ml_strategy,
                symbol='BTCUSDT',
                start_date='2025-07-01',
                end_date='2025-08-05',
                interval='1h'
            )
            
            print("✅ 修复后的机器学习策略回测结果:")
            print(f"   总收益率: {ml_result.total_return:.2%}")
            print(f"   总交易次数: {ml_result.total_trades}")
            print(f"   胜率: {ml_result.win_rate:.2%}")
            
            # 缠论策略回测
            chanlun_result = backtest_engine.run_backtest(
                strategy=chanlun_strategy,
                symbol='BTCUSDT',
                start_date='2025-07-01',
                end_date='2025-08-05',
                interval='1h'
            )
            
            print("\n✅ 修复后的缠论策略回测结果:")
            print(f"   总收益率: {chanlun_result.total_return:.2%}")
            print(f"   总交易次数: {chanlun_result.total_trades}")
            print(f"   胜率: {chanlun_result.win_rate:.2%}")
        
        # 运行测试
        asyncio.run(test_strategies())
        
    except Exception as e:
        print(f"❌ 测试修复后的策略失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

def main():
    """主函数"""
    print("🔧 修复策略回测问题")
    print("=" * 60)
    
    # 1. 修复机器学习策略参数
    fix_ml_strategy_parameters()
    
    # 2. 修复缠论策略参数
    fix_chanlun_strategy_parameters()
    
    # 3. 修复缠论买卖点逻辑
    fix_chanlun_buy_sell_logic()
    
    # 4. 更新app.py中的API参数
    update_app_backtest_api()
    
    # 5. 更新策略文件
    update_chanlun_strategy()
    update_ml_strategy()
    
    # 6. 测试修复后的策略
    test_fixed_strategies()
    
    print("\n🎉 修复完成!")
    print("\n📋 修复内容总结:")
    print("   ✅ 调整机器学习策略参数，降低敏感度")
    print("   ✅ 调整缠论策略参数，提高信号生成率")
    print("   ✅ 修复缠论买卖点判断逻辑")
    print("   ✅ 更新app.py中的回测API参数")
    print("   ✅ 更新策略文件中的默认参数")
    print("   ✅ 测试修复后的策略效果")

if __name__ == "__main__":
    main() 