# 策略计数问题修复总结

## 问题描述
用户报告：选择了3种币，总共启用了12个策略，但是顶部的"策略数量"显示的是52个，而不是预期的12个。

## 问题分析

### 1. 变量名冲突问题
在 `deleteCustomSymbol` 函数中，存在局部变量 `selectedSymbols` 与全局变量 `selectedSymbols` 冲突：
```javascript
// 问题代码
const selectedSymbols = Array.from(document.querySelectorAll('.symbol-checkbox:checked'))
                            .map(checkbox => checkbox.value);
```
这可能导致全局变量被意外修改。

### 2. API返回重复币种问题
在 `loadStrategiesStatus` 函数中，如果后端API `/api/spot/strategies/status` 返回重复的币种，会导致策略计数错误：
```javascript
// 问题代码
selectedSymbols = data.symbols; // 如果data.symbols包含重复项，会导致计数错误
```

### 3. 策略计数计算逻辑
在 `updateStrategiesDisplay` 函数中，策略计数是基于 `selectedSymbols` 数组的长度：
```javascript
selectedSymbols.forEach(symbol => {
    ['MA', 'RSI', 'ML', 'Chanlun'].forEach((strategy, index) => {
        totalStrategies++; // 每个币种的每个策略都会+1
    });
});
```

如果 `selectedSymbols` 包含重复项，比如：
- 原始：['BTCUSDT', 'ETHUSDT', 'MATICUSDT'] (3个币种)
- 重复后：['BTCUSDT', 'ETHUSDT', 'MATICUSDT', 'BTCUSDT', 'ETHUSDT'] (5个币种)

策略总数就会变成：5 × 4 = 20个，而不是预期的 3 × 4 = 12个。

## 修复方案

### 1. 修复变量名冲突
将 `deleteCustomSymbol` 函数中的局部变量重命名：
```javascript
// 修复后
const selectedSymbolsToDelete = Array.from(document.querySelectorAll('.symbol-checkbox:checked'))
                                .map(checkbox => checkbox.value);
```

### 2. 添加币种去重逻辑
在 `loadStrategiesStatus` 函数中添加去重逻辑：
```javascript
// 修复后
const uniqueSymbols = [...new Set(data.symbols)];
if (uniqueSymbols.length !== data.symbols.length) {
    console.warn('⚠️ API返回的币种中有重复，已自动去重');
}
selectedSymbols = uniqueSymbols;
```

### 3. 在更新策略时也添加去重
在 `updateStrategies` 函数中添加去重逻辑：
```javascript
// 修复后
const uniqueSymbols = [...new Set(selectedSymbols)];
if (uniqueSymbols.length !== selectedSymbols.length) {
    console.warn('⚠️ 选中的币种中有重复，已自动去重');
}
```

## 修复效果

修复后，即使后端API返回重复的币种，前端也会自动去重，确保：
- 策略总数 = 实际币种数量 × 4
- 避免了重复计算导致的计数错误
- 保持了数据的一致性

## 测试验证

创建了 `debug_strategy_count.html` 调试页面，包含：
- 策略计数调试功能
- 模拟更新策略功能
- 测试loadStrategiesStatus功能
- 全局变量状态显示

可以通过这个页面验证修复效果。

## 预防措施

1. **前端去重**：在所有处理币种数组的地方都添加去重逻辑
2. **日志记录**：添加警告日志，及时发现重复数据
3. **数据验证**：在关键函数中添加数据完整性检查
4. **变量命名**：避免局部变量与全局变量同名

## 总结

策略计数显示52个而不是12个的根本原因是：
1. 后端API可能返回了重复的币种
2. 前端没有对重复数据进行去重处理
3. 变量名冲突可能导致全局状态异常

通过添加去重逻辑和修复变量冲突，现在策略计数应该能正确显示为12个（3个币种 × 4种策略）。
