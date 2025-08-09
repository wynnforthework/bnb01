# 数据持久化问题修复总结

## 问题描述
用户反馈：当刷新页面后，策略控制里所有策略的启用状态都关闭了，已启用为0，平均收益率为0，平均胜率为0。策略里回测结果丢失了。

## 问题分析
经过代码分析，发现以下问题：

1. **数据存储不完整**：`window.strategyBacktestData` 只在 `updateStrategies()` 函数中被设置，但没有被保存到用户状态中
2. **数据恢复不完整**：`loadUserState()` 函数只恢复了 `backtestResults`，但没有恢复 `window.strategyBacktestData`
3. **数据同步不一致**：回测数据生成后，只保存到 `backtestResults`，没有同步到 `window.strategyBacktestData`

## 修复内容

### 1. 修复 `saveUserState()` 函数
- 添加了对 `window.strategyBacktestData` 的保存
- 确保所有回测数据都能被持久化

```javascript
body: JSON.stringify({
    selected_symbols: selectedSymbols,
    enabled_strategies: enabledStrategies,
    backtest_results: backtestResults,
    strategy_backtest_data: window.strategyBacktestData || {}  // 新增
})
```

### 2. 修复 `loadUserState()` 函数
- 添加了对 `strategy_backtest_data` 的恢复
- 确保 `window.strategyBacktestData` 被正确初始化

```javascript
// 恢复策略回测数据
if (state.strategy_backtest_data && Object.keys(state.strategy_backtest_data).length > 0) {
    window.strategyBacktestData = state.strategy_backtest_data;
    console.log('从服务器恢复策略回测数据:', Object.keys(window.strategyBacktestData));
} else {
    console.log('服务器没有策略回测数据，使用默认值');
    window.strategyBacktestData = {};
}
```

### 3. 修复 `displayBacktestResults()` 函数
- 确保回测数据同时保存到两个全局变量中
- 保证数据的一致性

```javascript
// 同时保存到strategyBacktestData中，用于策略显示
if (!window.strategyBacktestData) {
    window.strategyBacktestData = {};
}
window.strategyBacktestData[resultKey] = {
    total_return: result.total_return,
    total_trades: result.total_trades,
    win_rate: result.win_rate,
    max_drawdown: result.max_drawdown,
    sharpe_ratio: result.sharpe_ratio,
    parameters: result.parameters || {}
};
```

### 4. 增强数据持久化
- 在 `enableAllStrategies()` 和 `disableAllStrategies()` 函数中添加了 `saveUserState()` 调用
- 在 `updateStrategies()` 函数中添加了 `saveUserState()` 调用
- 确保所有策略状态变化都能被保存

### 5. 改进数据初始化
- 在 `loadUserState()` 函数中确保 `window.strategyBacktestData` 被正确初始化
- 防止未定义错误

## 修复后的数据流

### 数据保存流程
1. 用户操作（选择币种、切换策略、运行回测等）
2. 更新相应的全局变量
3. 调用 `saveUserState()` 保存到后端
4. 后端存储所有数据（包括 `strategy_backtest_data`）

### 数据恢复流程
1. 页面加载时调用 `loadUserState()`
2. 从后端恢复所有数据
3. 正确设置 `window.strategyBacktestData`
4. 调用 `updateStrategiesDisplay()` 显示策略和回测结果

## 测试验证

创建了 `test_data_persistence.html` 测试页面，包含：
- 币种选择和策略控制
- 回测功能（模拟数据）
- 调试信息显示
- 数据清除功能

## 预期效果

修复后，页面刷新时：
1. ✅ 选中的币种会被保持
2. ✅ 策略的启用/禁用状态会被保持
3. ✅ 回测结果（收益率、胜率等）会被保持
4. ✅ 策略统计信息会正确显示

## 注意事项

1. 需要确保后端 API `/api/user/state` 支持 `strategy_backtest_data` 字段
2. 如果后端不支持新字段，需要先更新后端代码
3. 建议在测试环境中验证修复效果

## 相关文件

- `static/js/app.js` - 主要修复文件
- `test_data_persistence.html` - 测试页面
- `DATA_PERSISTENCE_FIX_SUMMARY.md` - 本文档
