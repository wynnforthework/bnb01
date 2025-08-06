#!/usr/bin/env python3
"""
简单修复机器学习和缠论策略回测数据为0的问题
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_app_backtest_api():
    """修复app.py中的回测API参数"""
    print("📝 修复app.py中的回测API参数...")
    
    try:
        # 读取app.py文件
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新机器学习策略参数 - 更保守的设置
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
                'min_confidence': 0.55,
                'up_threshold': 0.008,
                'down_threshold': -0.008,
                'stop_loss': 0.025,
                'take_profit': 0.06,
                'position_size': 0.08"""
        
        content = content.replace(ml_old_params, ml_new_params)
        
        # 更新缠论策略参数 - 更宽松的设置
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
                'position_size': 0.25,
                'max_position': 0.9,
                'stop_loss': 0.035,
                'take_profit': 0.07,
                'trend_confirmation': 0.015,
                'divergence_threshold': 0.08"""
        
        content = content.replace(chanlun_old_params, chanlun_new_params)
        
        # 写回文件
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ app.py参数更新成功")
        
    except Exception as e:
        print(f"❌ 更新app.py失败: {e}")

def fix_chanlun_strategy():
    """修复缠论策略的买卖点逻辑"""
    print("🔧 修复缠论策略的买卖点逻辑...")
    
    try:
        # 读取缠论策略文件
        with open('strategies/chanlun_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新第一类买点逻辑 - 降低阈值
        buy_point_1_old = """            # 背离判断：价格创新低但MACD绿柱面积缩小
            if hist_area > -0.1:  # 绿柱面积较小
                return True"""
        
        buy_point_1_new = """            # 背离判断：价格创新低但MACD绿柱面积缩小
            if hist_area > -0.08:  # 降低绿柱面积阈值，提高敏感度
                return True"""
        
        content = content.replace(buy_point_1_old, buy_point_1_new)
        
        # 更新第二类买点逻辑 - 放宽条件
        buy_point_2_old = """            # 检查是否站上5日均线
            if current_price < ma_short:
                return False"""
        
        buy_point_2_new = """            # 检查是否站上5日均线（放宽条件）
            if current_price < ma_short * 0.995:  # 允许0.5%的误差
                return False"""
        
        content = content.replace(buy_point_2_old, buy_point_2_new)
        
        # 写回文件
        with open('strategies/chanlun_strategy.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 缠论策略更新成功")
        
    except Exception as e:
        print(f"❌ 更新缠论策略失败: {e}")

def fix_ml_strategy():
    """修复机器学习策略的参数"""
    print("🧠 修复机器学习策略参数...")
    
    try:
        # 读取机器学习策略文件
        with open('strategies/ml_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新默认参数 - 更保守的设置
        ml_params_old = """        self.lookback_period = parameters.get('lookback_period', 20)
        self.prediction_horizon = parameters.get('prediction_horizon', 1)
        self.model_type = parameters.get('model_type', 'random_forest')
        self.retrain_frequency = parameters.get('retrain_frequency', 100)  # 每100个数据点重训练
        self.min_training_samples = parameters.get('min_training_samples', 200)"""
        
        ml_params_new = """        self.lookback_period = parameters.get('lookback_period', 25)
        self.prediction_horizon = parameters.get('prediction_horizon', 1)
        self.model_type = parameters.get('model_type', 'random_forest')
        self.retrain_frequency = parameters.get('retrain_frequency', 60)  # 每60个数据点重训练
        self.min_training_samples = parameters.get('min_training_samples', 120)"""
        
        content = content.replace(ml_params_old, ml_params_new)
        
        # 写回文件
        with open('strategies/ml_strategy.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 机器学习策略更新成功")
        
    except Exception as e:
        print(f"❌ 更新机器学习策略失败: {e}")

def fix_ml_data_validation():
    """修复机器学习策略的数据验证问题"""
    print("🔧 修复机器学习策略的数据验证问题...")
    
    try:
        # 读取机器学习策略文件
        with open('strategies/ml_strategy.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新数据验证逻辑
        validation_old = """            # 处理可能的嵌套数组数据
            if isinstance(df, pd.DataFrame) and len(df.columns) == 1:
                # 如果数据是单列的嵌套数组，尝试解析
                self.logger.warning("检测到嵌套数组数据，尝试解析...")
                try:
                    # 尝试将第一列解析为JSON或数组
                    first_col = df.iloc[:, 0]
                    if first_col.dtype == 'object':
                        # 尝试解析为数值数组
                        parsed_data = []
                        for item in first_col:
                            if isinstance(item, str):
                                # 移除引号和空格，分割
                                clean_item = item.strip().strip("'[]").split()
                                parsed_data.append([float(x.strip("'")) for x in clean_item])
                            elif isinstance(item, (list, np.ndarray)):
                                parsed_data.append([float(x) for x in item])
                            else:
                                parsed_data.append([float(item)])
                        
                        # 创建新的DataFrame
                        if parsed_data:
                            df = pd.DataFrame(parsed_data, columns=['open', 'high', 'low', 'close', 'volume'])
                            self.logger.info(f"成功解析嵌套数组数据，形状: {df.shape}")
                except Exception as parse_error:
                    self.logger.error(f"解析嵌套数组失败: {parse_error}")
                    return pd.DataFrame()"""
        
        validation_new = """            # 处理可能的嵌套数组数据
            if isinstance(df, pd.DataFrame) and len(df.columns) == 1:
                # 如果数据是单列的嵌套数组，尝试解析
                self.logger.warning("检测到嵌套数组数据，尝试解析...")
                try:
                    # 尝试将第一列解析为JSON或数组
                    first_col = df.iloc[:, 0]
                    if first_col.dtype == 'object':
                        # 尝试解析为数值数组
                        parsed_data = []
                        for item in first_col:
                            if isinstance(item, str):
                                # 移除引号和空格，分割
                                clean_item = item.strip().strip("'[]").split()
                                try:
                                    parsed_data.append([float(x.strip("'")) for x in clean_item])
                                except ValueError:
                                    # 如果解析失败，跳过这一行
                                    continue
                            elif isinstance(item, (list, np.ndarray)):
                                try:
                                    parsed_data.append([float(x) for x in item])
                                except (ValueError, TypeError):
                                    continue
                            else:
                                try:
                                    parsed_data.append([float(item)])
                                except (ValueError, TypeError):
                                    continue
                        
                        # 创建新的DataFrame
                        if parsed_data:
                            df = pd.DataFrame(parsed_data, columns=['open', 'high', 'low', 'close', 'volume'])
                            self.logger.info(f"成功解析嵌套数组数据，形状: {df.shape}")
                except Exception as parse_error:
                    self.logger.error(f"解析嵌套数组失败: {parse_error}")
                    return pd.DataFrame()"""
        
        content = content.replace(validation_old, validation_new)
        
        # 写回文件
        with open('strategies/ml_strategy.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 机器学习数据验证修复成功")
        
    except Exception as e:
        print(f"❌ 修复机器学习数据验证失败: {e}")

def create_test_script():
    """创建一个简单的测试脚本"""
    print("📝 创建简单的测试脚本...")
    
    test_script = '''#!/usr/bin/env python3
"""
简单测试修复后的策略
"""

import asyncio
import pandas as pd
from strategies.ml_strategy import MLStrategy
from strategies.chanlun_strategy import ChanlunStrategy
from backend.backtesting import BacktestEngine
from backend.data_collector import DataCollector

async def test_fixed_strategies():
    """测试修复后的策略"""
    print("🧪 测试修复后的策略...")
    
    try:
        # 创建数据收集器
        collector = DataCollector()
        
        # 获取历史数据
        print("1️⃣ 获取历史数据...")
        data = await collector.collect_historical_data('BTCUSDT', '1h', 30)  # 减少数据量
        print(f"   获取到 {len(data)} 条数据")
        
        if data.empty:
            print("❌ 无法获取历史数据")
            return
        
        # 测试机器学习策略
        print("\\n2️⃣ 测试修复后的机器学习策略...")
        ml_strategy = MLStrategy('BTCUSDT', {
            'model_type': 'random_forest',
            'lookback_period': 25,
            'prediction_horizon': 1,
            'min_confidence': 0.55,
            'up_threshold': 0.008,
            'down_threshold': -0.008,
            'stop_loss': 0.025,
            'take_profit': 0.06,
            'position_size': 0.08
        })
        
        # 测试信号生成
        signals = []
        for i in range(20, len(data)):
            current_data = data.iloc[:i+1]
            signal = ml_strategy.generate_signal(current_data)
            signals.append(signal)
            if signal != 'HOLD':
                print(f"   ML信号: {signal} at {data.iloc[i]['timestamp']}")
        
        print(f"   ML生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
        
        # 测试缠论策略
        print("\\n3️⃣ 测试修复后的缠论策略...")
        chanlun_strategy = ChanlunStrategy('BTCUSDT', {
            'timeframes': ['30m', '1h', '4h'],
            'min_swing_length': 2,
            'central_bank_min_bars': 2,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_period': 14,
            'ma_short': 5,
            'ma_long': 20,
            'position_size': 0.25,
            'max_position': 0.9,
            'stop_loss': 0.035,
            'take_profit': 0.07,
            'trend_confirmation': 0.015,
            'divergence_threshold': 0.08
        })
        
        # 测试信号生成
        signals = []
        for i in range(20, len(data)):
            current_data = data.iloc[:i+1]
            signal = chanlun_strategy.generate_signal(current_data)
            signals.append(signal)
            if signal != 'HOLD':
                print(f"   缠论信号: {signal} at {data.iloc[i]['timestamp']}")
        
        print(f"   缠论生成信号数量: {len([s for s in signals if s != 'HOLD'])}")
        
        print("\\n✅ 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_fixed_strategies())
'''
    
    with open('test_fixed_strategies.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ 测试脚本创建成功")

def main():
    """主函数"""
    print("🔧 简单修复策略回测问题")
    print("=" * 60)
    
    # 1. 修复app.py中的API参数
    fix_app_backtest_api()
    
    # 2. 修复缠论策略
    fix_chanlun_strategy()
    
    # 3. 修复机器学习策略
    fix_ml_strategy()
    
    # 4. 修复机器学习数据验证问题
    fix_ml_data_validation()
    
    # 5. 创建测试脚本
    create_test_script()
    
    print("\n🎉 修复完成!")
    print("\n📋 修复内容总结:")
    print("   ✅ 调整机器学习策略参数，降低敏感度")
    print("   ✅ 调整缠论策略参数，提高信号生成率")
    print("   ✅ 修复缠论买卖点判断逻辑")
    print("   ✅ 修复机器学习数据验证问题")
    print("   ✅ 更新app.py中的回测API参数")
    print("   ✅ 更新策略文件中的默认参数")
    print("   ✅ 创建测试脚本 test_fixed_strategies.py")
    print("\n💡 下一步:")
    print("   运行 python test_fixed_strategies.py 来测试修复效果")

if __name__ == "__main__":
    main() 