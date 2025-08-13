# 策略参数优化系统使用指南

## 📋 系统概述

本系统为您的交易策略提供自动化的参数优化功能，支持四种策略类型：
- **MA (移动平均策略)**
- **RSI (相对强弱指数策略)**
- **ML (机器学习策略)**
- **Chanlun (缠论策略)**

## 🚀 快速开始

### 1. 检查数据情况
```bash
python check_data_range.py
```
这个脚本会显示数据库中可用的数据范围和数量。

### 2. 收集更多历史数据（可选）
如果数据不足，可以运行：
```bash
python collect_more_data.py
```
这将收集最近90天的历史数据，为优化提供更充足的数据基础。

### 3. 运行策略参数优化
```bash
python strategy_optimizer.py
```
系统会提示您配置优化参数，然后开始自动优化过程。

### 4. 查看优化结果
```bash
python view_optimization_results.py
```
查看和分析优化结果，导出最佳参数配置。

## ⚙️ 配置说明

### 优化配置文件 (`optimization_config.json`)
```json
{
  "symbols": ["ETHUSDT"],
  "trading_mode": "SPOT",
  "start_date": "2025-08-06",
  "end_date": "2025-08-13",
  "max_iterations": 1000,
  "population_size": 50,
  "elite_size": 10,
  "mutation_rate": 0.1,
  "crossover_rate": 0.8,
  "test_interval": 5,
  "save_results": true,
  "results_file": "optimization_results.json",
  "database_file": "optimization_results.db"
}
```

### 参数说明
- **symbols**: 要优化的币种列表
- **trading_mode**: 交易模式 (SPOT/FUTURES)
- **start_date/end_date**: 回测时间范围
- **max_iterations**: 最大迭代次数
- **test_interval**: 测试间隔（秒）
- **mutation_rate**: 变异率（遗传算法参数）
- **crossover_rate**: 交叉率（遗传算法参数）

## 📊 策略参数范围

### MA策略参数
- `short_window`: 5-20
- `long_window`: 20-100
- `position_size`: [0.1, 0.5, 1.0, 2.0, 5.0]
- `stop_loss`: [0.01, 0.02, 0.03, 0.05]
- `take_profit`: [0.02, 0.03, 0.05, 0.08, 0.10]

### RSI策略参数
- `rsi_period`: 7-21
- `overbought`: 65-80
- `oversold`: 20-35
- `position_size`: [0.1, 0.5, 1.0, 2.0, 5.0]
- `stop_loss`: [0.01, 0.02, 0.03, 0.05]
- `take_profit`: [0.02, 0.03, 0.05, 0.08, 0.10]

### ML策略参数
- `lookback_period`: 10-50
- `prediction_horizon`: [1, 2, 3, 5]
- `model_type`: ['random_forest', 'gradient_boosting', 'logistic_regression']
- `position_size`: [0.1, 0.5, 1.0, 2.0, 5.0]
- `stop_loss`: [0.01, 0.02, 0.03, 0.05]
- `take_profit`: [0.02, 0.03, 0.05, 0.08, 0.10]

### Chanlun策略参数
- `min_swing_length`: 3-7
- `trend_confirmation`: [0.01, 0.02, 0.03, 0.05]
- `position_size`: [0.1, 0.5, 1.0, 2.0, 5.0]
- `stop_loss`: [0.01, 0.02, 0.03, 0.05]
- `take_profit`: [0.02, 0.03, 0.05, 0.08, 0.10]

## 🔄 优化算法

系统使用改进的遗传算法进行参数优化：

1. **随机初始化**: 生成初始参数种群
2. **回测评估**: 对每个参数组合进行回测
3. **适应度计算**: 基于总收益、夏普比率等指标计算适应度
4. **选择**: 保留表现最好的参数组合
5. **变异**: 对最佳参数进行随机变异
6. **迭代**: 重复上述过程直到达到最大迭代次数

## 📈 性能指标

系统会计算以下性能指标：
- **总收益率**: 策略的总收益百分比
- **夏普比率**: 风险调整后的收益指标
- **最大回撤**: 最大亏损幅度
- **胜率**: 盈利交易的比例
- **盈亏比**: 平均盈利与平均亏损的比值
- **交易次数**: 总交易数量

## 💾 结果保存

### 数据库存储
- `optimization_results.db`: SQLite数据库
- `optimization_results`: 所有测试结果
- `best_results`: 每个策略的最佳结果

### JSON文件
- `optimization_results.json`: 所有测试结果
- `best_strategy_parameters.json`: 最佳参数配置

## 🎯 使用建议

### 1. 数据准备
- 确保有足够的历史数据（建议至少30天）
- 使用实际可用的数据范围进行回测

### 2. 参数配置
- 根据市场情况调整参数范围
- 设置合理的迭代次数和测试间隔
- 考虑交易成本和滑点

### 3. 结果分析
- 关注多个性能指标，不要只看总收益
- 考虑策略的稳定性和风险
- 在实盘交易前进行充分验证

### 4. 持续优化
- 定期重新运行优化
- 根据市场变化调整参数范围
- 记录和分析优化结果

## 🛠️ 故障排除

### 常见问题

1. **数据不足**
   - 运行 `collect_more_data.py` 收集更多数据
   - 调整回测时间范围

2. **优化结果为零**
   - 检查数据质量
   - 调整参数范围
   - 增加回测时间

3. **策略创建失败**
   - 检查策略参数名称是否正确
   - 确保所有必需参数都已提供

4. **数据库错误**
   - 检查数据库文件权限
   - 删除损坏的数据库文件重新开始

## 📞 技术支持

如果遇到问题，请检查：
1. 日志文件中的错误信息
2. 数据库连接状态
3. 网络连接和API访问
4. 策略参数配置

---

**注意**: 本系统仅用于策略参数优化，实际交易时请谨慎使用，并充分测试策略的有效性。
