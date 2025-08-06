// 现货交易页面JavaScript
let socket;
let currentSymbol = 'BTCUSDT';

// 初始化应用
document.addEventListener('DOMContentLoaded', function () {
    initializeSocket();
    loadInitialData();
    bindEvents();
    checkTradingStatus();
});

// 初始化WebSocket连接
function initializeSocket() {
    socket = io();

    socket.on('connect', function () {
        console.log('现货交易WebSocket连接成功');
    });

    socket.on('portfolio_update', function (data) {
        updatePortfolioDisplay(data);
    });

    socket.on('trades_update', function (data) {
        updateTradesDisplay(data);
    });

    socket.on('disconnect', function () {
        console.log('现货交易WebSocket连接断开');
    });
}

// 绑定事件
function bindEvents() {
    // 现货交易控制按钮
    const startBtn = document.getElementById('start-spot-trading');
    if (startBtn) {
        startBtn.addEventListener('click', function () {
            startSpotTrading();
        });
    }

    const stopBtn = document.getElementById('stop-spot-trading');
    if (stopBtn) {
        stopBtn.addEventListener('click', function () {
            stopSpotTrading();
        });
    }

    const refreshBtn = document.getElementById('refresh-spot-data');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function () {
            loadInitialData();
        });
    }

    // 交易对选择
    const symbolSelect = document.getElementById('symbol-select');
    if (symbolSelect) {
        symbolSelect.addEventListener('change', function () {
            currentSymbol = this.value;
            loadMarketData(currentSymbol);
        });
    }

    // 策略管理按钮
    const showStrategiesBtn = document.getElementById('show-strategies');
    if (showStrategiesBtn) {
        showStrategiesBtn.addEventListener('click', function () {
            showStrategyPanel('strategies');
        });
    }

    const showBacktestBtn = document.getElementById('show-backtest');
    if (showBacktestBtn) {
        showBacktestBtn.addEventListener('click', function () {
            showStrategyPanel('backtest');
        });
    }

    const showMlBtn = document.getElementById('show-ml');
    if (showMlBtn) {
        showMlBtn.addEventListener('click', function () {
            showStrategyPanel('ml');
        });
    }

    // 回测表单提交
    const backtestForm = document.getElementById('backtest-form');
    if (backtestForm) {
        backtestForm.addEventListener('submit', function(e) {
            e.preventDefault();
            runBacktest();
        });
    }
    
    // 策略比较按钮
    const compareStrategiesBtn = document.getElementById('compare-strategies');
    if (compareStrategiesBtn) {
        compareStrategiesBtn.addEventListener('click', function() {
            compareStrategies();
        });
    }
}

// 加载初始数据
function loadInitialData() {
    loadAccountData();
    loadPortfolioData();
    loadTradesData();
    loadMarketData(currentSymbol);
    loadRiskMetrics();
    loadSystemStatus();
    loadStrategiesList();
}

// 加载账户数据
async function loadAccountData() {
    try {
        const response = await fetch('/api/account');
        const data = await response.json();

        if (data.success) {
            displayAccountBalances(data.balances);
        } else {
            console.error('加载账户数据失败:', data.message);
        }
    } catch (error) {
        console.error('加载账户数据失败:', error.message);
    }
}

// 显示账户余额
function displayAccountBalances(balances) {
    const container = document.getElementById('account-balances');
    if (!container) return;

    if (balances.length === 0) {
        container.innerHTML = '<p class="text-muted">暂无余额数据</p>';
        return;
    }

    // 过滤并排序余额
    const importantAssets = ['USDT', 'BTC', 'ETH', 'BNB'];
    const filteredBalances = balances
        .filter(balance => balance.total > 0.001)
        .sort((a, b) => {
            const aIndex = importantAssets.indexOf(a.asset);
            const bIndex = importantAssets.indexOf(b.asset);

            if (aIndex !== -1 && bIndex !== -1) {
                return aIndex - bIndex;
            } else if (aIndex !== -1) {
                return -1;
            } else if (bIndex !== -1) {
                return 1;
            } else {
                return b.total - a.total;
            }
        });

    let html = '<div class="row">';
    filteredBalances.slice(0, 6).forEach(balance => {
        html += `
            <div class="col-md-4 mb-2">
                <div class="d-flex justify-content-between">
                    <span class="fw-bold">${balance.asset}</span>
                    <span>${balance.total.toFixed(6)}</span>
                </div>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

// 加载投资组合数据
async function loadPortfolioData() {
    try {
        const response = await fetch('/api/portfolio');
        const data = await response.json();

        if (data.success) {
            displayPortfolioSummary(data.data);
        } else {
            console.error('加载投资组合失败:', data.message);
        }
    } catch (error) {
        console.error('加载投资组合失败:', error.message);
    }
}

// 显示投资组合概览
function displayPortfolioSummary(portfolio) {
    const container = document.getElementById('portfolio-summary');
    if (!container) return;

    const totalValue = portfolio.total_value || 0;
    const cashBalance = portfolio.cash_balance || 0;
    const positionsCount = portfolio.positions ? portfolio.positions.length : 0;

    const html = `
        <div class="row">
            <div class="col-4">
                <div class="text-center">
                    <h6 class="text-muted mb-1">总资产</h6>
                    <h4 class="text-primary">$${(totalValue + cashBalance).toFixed(2)}</h4>
                </div>
            </div>
            <div class="col-4">
                <div class="text-center">
                    <h6 class="text-muted mb-1">持仓数量</h6>
                    <h4 class="text-info">${positionsCount}</h4>
                </div>
            </div>
            <div class="col-4">
                <div class="text-center">
                    <h6 class="text-muted mb-1">现金余额</h6>
                    <h4 class="text-success">$${cashBalance.toFixed(2)}</h4>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // 更新持仓表格
    if (portfolio.positions) {
        displayPositions(portfolio.positions);
    }
}

// 显示持仓
function displayPositions(positions) {
    const tbody = document.querySelector('#positions-table tbody');
    if (!tbody) return;

    if (positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无持仓</td></tr>';
        return;
    }

    let html = '';
    positions.forEach(position => {
        const pnlClass = position.unrealized_pnl >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = position.unrealized_pnl >= 0 ? '+' : '';

        html += `
            <tr>
                <td>${position.symbol}</td>
                <td>${position.quantity.toFixed(6)}</td>
                <td>$${position.avg_price.toFixed(2)}</td>
                <td>$${position.current_price.toFixed(2)}</td>
                <td>$${position.market_value.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}$${position.unrealized_pnl.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}${position.pnl_percent.toFixed(2)}%</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// 加载交易历史
async function loadTradesData() {
    try {
        const response = await fetch('/api/trades');
        const data = await response.json();

        if (data.success) {
            displayTradesData(data.trades);
        } else {
            console.error('加载交易历史失败:', data.message);
        }
    } catch (error) {
        console.error('加载交易历史失败:', error.message);
    }
}

// 显示交易历史
function displayTradesData(trades) {
    const tbody = document.querySelector('#trades-table tbody');
    if (!tbody) return;

    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无交易记录</td></tr>';
        return;
    }

    let html = '';
    trades.slice(0, 20).forEach(trade => {
        const sideClass = trade.side === 'BUY' ? 'text-success' : 'text-danger';
        const pnlClass = trade.profit_loss >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = trade.profit_loss >= 0 ? '+' : '';

        html += `
            <tr>
                <td>${new Date(trade.timestamp).toLocaleString()}</td>
                <td>${trade.symbol}</td>
                <td class="${sideClass}">${trade.side}</td>
                <td>${trade.quantity.toFixed(6)}</td>
                <td>$${trade.price.toFixed(2)}</td>
                <td>${trade.strategy || 'N/A'}</td>
                <td class="${pnlClass}">${pnlSign}$${trade.profit_loss.toFixed(2)}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// 加载市场数据
async function loadMarketData(symbol) {
    try {
        const response = await fetch(`/api/market/${symbol}`);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            displayMarketChart(data.data, symbol);
        } else {
            console.error('加载市场数据失败:', data.message);
        }
    } catch (error) {
        console.error('加载市场数据失败:', error.message);
    }
}

// 显示市场图表
function displayMarketChart(marketData, symbol) {
    const chartContainer = document.getElementById('price-chart');
    if (!chartContainer) return;

    try {
        const traces = [{
            x: marketData.map(d => new Date(d.timestamp)),
            close: marketData.map(d => d.close),
            high: marketData.map(d => d.high),
            low: marketData.map(d => d.low),
            open: marketData.map(d => d.open),
            type: 'candlestick',
            name: symbol
        }];

        const layout = {
            title: `${symbol} 现货价格`,
            xaxis: { title: '时间' },
            yaxis: { title: '价格 (USDT)' },
            height: 400
        };

        Plotly.newPlot('price-chart', traces, layout);
    } catch (error) {
        console.error('显示图表失败:', error);
        chartContainer.innerHTML = '<p class="text-center text-muted">图表加载失败</p>';
    }
}

// 启动现货交易
async function startSpotTrading() {
    try {
        const response = await fetch('/api/trading/start', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showSuccess(data.message);
            updateTradingStatus(true);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('启动现货交易失败: ' + error.message);
    }
}

// 停止现货交易
async function stopSpotTrading() {
    try {
        const response = await fetch('/api/trading/stop', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showSuccess(data.message);
            updateTradingStatus(false);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('停止现货交易失败: ' + error.message);
    }
}

// 检查交易状态
async function checkTradingStatus() {
    try {
        const response = await fetch('/api/trading/status');
        const data = await response.json();

        if (data.success) {
            updateTradingStatus(data.is_running);
        }
    } catch (error) {
        console.error('检查交易状态失败:', error);
    }
}

// 更新交易状态显示
function updateTradingStatus(isRunning) {
    const statusElement = document.getElementById('spot-trading-status');
    const badgeElement = document.getElementById('spot-status-badge');

    if (statusElement) {
        if (isRunning) {
            statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> 运行中';
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle text-danger"></i> 未运行';
        }
    }

    if (badgeElement) {
        if (isRunning) {
            badgeElement.className = 'badge bg-success';
            badgeElement.textContent = '运行中';
        } else {
            badgeElement.className = 'badge bg-danger';
            badgeElement.textContent = '未运行';
        }
    }
}

// 更新投资组合显示
function updatePortfolioDisplay(data) {
    if (data) {
        displayPortfolioSummary(data);
    }
}

// 更新交易显示
function updateTradesDisplay(data) {
    if (data && data.length > 0) {
        displayTradesData(data);
    }
}

// 工具函数
function showSuccess(message) {
    console.log('Success:', message);
    // 这里可以添加toast通知
}

function showError(message) {
    console.error('Error:', message);
    // 这里可以添加toast通知
}

// 定期刷新数据
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadAccountData();
        loadPortfolioData();
        checkTradingStatus();
    }
}, 30000); // 每30秒刷新一次
// 策略面板切换
function showStrategyPanel(panelType) {
    // 隐藏所有面板
    const panels = ['strategies-panel', 'backtest-panel', 'ml-panel'];
    panels.forEach(panelId => {
        const panel = document.getElementById(panelId);
        if (panel) {
            panel.style.display = 'none';
        }
    });

    // 显示选中的面板
    const targetPanel = document.getElementById(panelType + '-panel');
    if (targetPanel) {
        targetPanel.style.display = 'block';
    }

    // 更新按钮状态
    const buttons = ['show-strategies', 'show-backtest', 'show-ml'];
    buttons.forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-primary');
        }
    });

    const activeBtn = document.getElementById('show-' + panelType);
    if (activeBtn) {
        activeBtn.classList.remove('btn-outline-primary');
        activeBtn.classList.add('btn-primary');
    }
}

// 加载风险管理数据
async function loadRiskMetrics() {
    const container = document.getElementById('risk-metrics');
    if (!container) return;

    try {
        const response = await fetch('/api/risk/portfolio');
        const data = await response.json();

        if (data.success) {
            displayRiskMetrics(data.data);
        } else {
            container.innerHTML = '<p class="text-muted">暂无风险数据</p>';
        }
    } catch (error) {
        console.error('加载风险数据失败:', error);
        container.innerHTML = '<p class="text-muted">加载风险数据失败</p>';
    }
}

// 显示风险管理数据
function displayRiskMetrics(riskData) {
    const container = document.getElementById('risk-metrics');
    if (!container) return;

    const html = `
        <div class="row">
            <div class="col-md-3">
                <div class="text-center">
                    <h6 class="text-muted mb-1">总风险敞口</h6>
                    <h5 class="text-warning">${(riskData.total_exposure || 0).toFixed(2)}%</h5>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h6 class="text-muted mb-1">最大回撤</h6>
                    <h5 class="text-danger">${(riskData.max_drawdown || 0).toFixed(2)}%</h5>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h6 class="text-muted mb-1">夏普比率</h6>
                    <h5 class="text-info">${(riskData.sharpe_ratio || 0).toFixed(2)}</h5>
                </div>
            </div>
            <div class="col-md-3">
                <div class="text-center">
                    <h6 class="text-muted mb-1">风险评级</h6>
                    <h5 class="text-success">${riskData.risk_level || '低'}</h5>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// 加载系统状态
async function loadSystemStatus() {
    const container = document.getElementById('system-status');
    if (!container) return;

    try {
        const response = await fetch('/api/system/status');
        const data = await response.json();

        if (data.success) {
            displaySystemStatus(data.data);
        } else {
            container.innerHTML = '<p class="text-muted">暂无系统状态</p>';
        }
    } catch (error) {
        console.error('加载系统状态失败:', error);
        container.innerHTML = '<p class="text-muted">加载系统状态失败</p>';
    }
}

// 显示系统状态
function displaySystemStatus(statusData) {
    const container = document.getElementById('system-status');
    if (!container) return;

    const html = `
        <div class="row">
            <div class="col-6">
                <div class="d-flex justify-content-between">
                    <span>API连接</span>
                    <span class="badge ${statusData.api_connected ? 'bg-success' : 'bg-danger'}">
                        ${statusData.api_connected ? '正常' : '断开'}
                    </span>
                </div>
            </div>
            <div class="col-6">
                <div class="d-flex justify-content-between">
                    <span>数据库</span>
                    <span class="badge ${statusData.database_connected ? 'bg-success' : 'bg-danger'}">
                        ${statusData.database_connected ? '正常' : '异常'}
                    </span>
                </div>
            </div>
            <div class="col-6 mt-2">
                <div class="d-flex justify-content-between">
                    <span>内存使用</span>
                    <span class="badge bg-info">${(statusData.memory_usage || 0).toFixed(1)}%</span>
                </div>
            </div>
            <div class="col-6 mt-2">
                <div class="d-flex justify-content-between">
                    <span>运行时间</span>
                    <span class="badge bg-secondary">${statusData.uptime || '0h'}</span>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}// 加载策略
列表
async function loadStrategiesList() {
    try {
        const response = await fetch('/api/strategies/list');
        const data = await response.json();

        if (data.success) {
            displayStrategiesList(data.data);
            updateStrategiesCount(data.data.length);
        } else {
            console.error('加载策略列表失败:', data.message);
        }
    } catch (error) {
        console.error('加载策略列表失败:', error.message);
    }
}

// 显示策略列表
function displayStrategiesList(strategies) {
    const tbody = document.querySelector('#strategies-table tbody');
    if (!tbody) return;

    if (strategies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无策略数据</td></tr>';
        return;
    }

    let html = '';
    strategies.forEach(strategy => {
        const statusClass = strategy.status === 'active' ? 'text-success' : 'text-secondary';
        const statusText = strategy.status === 'active' ? '运行中' : '已停止';
        const pnlClass = strategy.pnl >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = strategy.pnl >= 0 ? '+' : '';

        html += `
            <tr>
                <td>${strategy.name}</td>
                <td>${strategy.symbol}</td>
                <td>${strategy.type}</td>
                <td>${strategy.position.toFixed(6)}</td>
                <td>${strategy.entry_price > 0 ? strategy.entry_price.toFixed(2) : '-'}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary btn-sm" onclick="editStrategy('${strategy.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="deleteStrategy('${strategy.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// 更新策略数量显示
function updateStrategiesCount(count) {
    const countElement = document.getElementById('spot-strategies-count');
    if (countElement) {
        countElement.textContent = count;
    }
}

// 编辑策略（占位函数）
function editStrategy(strategyId) {
    console.log('编辑策略:', strategyId);
    // 这里可以添加编辑策略的逻辑
}

// 删除策略（占位函数）
function deleteStrategy(strategyId) {
    if (confirm('确定要删除这个策略吗？')) {
        console.log('删除策略:', strategyId);
        // 这里可以添加删除策略的逻辑
    }
}

// 运行回测
async function runBacktest() {
    const strategyType = document.getElementById('backtest-strategy').value;
    const symbol = document.getElementById('backtest-symbol').value;
    const startDate = document.getElementById('backtest-start').value;
    const endDate = document.getElementById('backtest-end').value;
    
    if (!strategyType || !symbol || !startDate || !endDate) {
        showError('请填写完整的回测参数');
        return;
    }
    
    const resultsContainer = document.getElementById('backtest-results');
    resultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>正在运行回测...</p></div>';
    
    try {
        const response = await fetch('/api/backtest/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                strategy_type: strategyType,
                symbol: symbol,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayBacktestResults(data.data, strategyType, symbol);
        } else {
            showError(data.message);
            resultsContainer.innerHTML = '<p class="text-danger">回测失败</p>';
        }
    } catch (error) {
        console.error('回测失败:', error);
        showError('回测请求失败');
        resultsContainer.innerHTML = '<p class="text-danger">回测失败</p>';
    }
}

// 显示回测结果
function displayBacktestResults(result, strategyType, symbol) {
    const resultsContainer = document.getElementById('backtest-results');
    
    const strategyNames = {
        'MA': '移动平均线策略',
        'RSI': 'RSI策略',
        'ML': '机器学习策略',
        'Chanlun': '缠论01策略'
    };
    
    const strategyName = strategyNames[strategyType] || strategyType;
    
    const html = `
        <div class="card">
            <div class="card-header">
                <h6>${strategyName} - ${symbol} 回测结果</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>收益指标</h6>
                        <table class="table table-sm">
                            <tr>
                                <td>总收益率</td>
                                <td class="${result.total_return >= 0 ? 'text-success' : 'text-danger'}">
                                    ${(result.total_return * 100).toFixed(2)}%
                                </td>
                            </tr>
                            <tr>
                                <td>年化收益率</td>
                                <td class="${result.annual_return >= 0 ? 'text-success' : 'text-danger'}">
                                    ${(result.annual_return * 100).toFixed(2)}%
                                </td>
                            </tr>
                            <tr>
                                <td>最大回撤</td>
                                <td class="text-danger">
                                    ${(result.max_drawdown * 100).toFixed(2)}%
                                </td>
                            </tr>
                            <tr>
                                <td>夏普比率</td>
                                <td class="${result.sharpe_ratio >= 0 ? 'text-success' : 'text-danger'}">
                                    ${result.sharpe_ratio.toFixed(2)}
                                </td>
                            </tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>交易统计</h6>
                        <table class="table table-sm">
                            <tr>
                                <td>总交易次数</td>
                                <td>${result.total_trades}</td>
                            </tr>
                            <tr>
                                <td>胜率</td>
                                <td class="${result.win_rate >= 0.5 ? 'text-success' : 'text-danger'}">
                                    ${(result.win_rate * 100).toFixed(1)}%
                                </td>
                            </tr>
                            <tr>
                                <td>平均交易收益</td>
                                <td class="${result.avg_trade_return >= 0 ? 'text-success' : 'text-danger'}">
                                    ${(result.avg_trade_return * 100).toFixed(2)}%
                                </td>
                            </tr>
                            <tr>
                                <td>盈亏比</td>
                                <td class="${result.profit_factor >= 1 ? 'text-success' : 'text-danger'}">
                                    ${result.profit_factor.toFixed(2)}
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <div class="mt-3">
                    <h6>最近交易记录</h6>
                    <div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>时间</th>
                                    <th>动作</th>
                                    <th>价格</th>
                                    <th>数量</th>
                                    <th>收益</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${result.trades.map(trade => `
                                    <tr>
                                        <td>${new Date(trade.timestamp).toLocaleString()}</td>
                                        <td class="${trade.action === 'BUY' ? 'text-success' : 'text-danger'}">
                                            ${trade.action}
                                        </td>
                                        <td>$${trade.price.toFixed(2)}</td>
                                        <td>${trade.quantity.toFixed(6)}</td>
                                        <td class="${trade.profit >= 0 ? 'text-success' : 'text-danger'}">
                                            ${trade.profit.toFixed(2)}
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
}

// 策略比较
async function compareStrategies() {
    const symbol = document.getElementById('backtest-symbol').value;
    const startDate = document.getElementById('backtest-start').value;
    const endDate = document.getElementById('backtest-end').value;
    
    if (!symbol || !startDate || !endDate) {
        showError('请填写完整的回测参数');
        return;
    }
    
    const strategies = ['MA', 'RSI', 'ML', 'Chanlun'];
    const results = [];
    
    const resultsContainer = document.getElementById('backtest-results');
    resultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>正在比较策略...</p></div>';
    
    try {
        for (const strategy of strategies) {
            try {
                const response = await fetch('/api/backtest/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        strategy_type: strategy,
                        symbol: symbol,
                        start_date: startDate,
                        end_date: endDate
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    results.push({
                        strategy: strategy,
                        ...data.data
                    });
                }
            } catch (error) {
                console.error(`策略 ${strategy} 回测失败:`, error);
            }
        }
        
        displayStrategyComparison(results, symbol);
        
    } catch (error) {
        console.error('策略比较失败:', error);
        showError('策略比较失败');
        resultsContainer.innerHTML = '<p class="text-danger">策略比较失败</p>';
    }
}

// 显示策略比较结果
function displayStrategyComparison(results, symbol) {
    const resultsContainer = document.getElementById('backtest-results');
    
    const strategyNames = {
        'MA': '移动平均线',
        'RSI': 'RSI策略',
        'ML': '机器学习',
        'Chanlun': '缠论01'
    };
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p class="text-danger">所有策略回测都失败了</p>';
        return;
    }
    
    // 按总收益率排序
    results.sort((a, b) => b.total_return - a.total_return);
    
    const html = `
        <div class="card">
            <div class="card-header">
                <h6>策略比较 - ${symbol}</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>策略</th>
                                <th>总收益率</th>
                                <th>年化收益率</th>
                                <th>最大回撤</th>
                                <th>夏普比率</th>
                                <th>胜率</th>
                                <th>交易次数</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${results.map(result => `
                                <tr>
                                    <td><strong>${strategyNames[result.strategy]}</strong></td>
                                    <td class="${result.total_return >= 0 ? 'text-success' : 'text-danger'}">
                                        ${(result.total_return * 100).toFixed(2)}%
                                    </td>
                                    <td class="${result.annual_return >= 0 ? 'text-success' : 'text-danger'}">
                                        ${(result.annual_return * 100).toFixed(2)}%
                                    </td>
                                    <td class="text-danger">
                                        ${(result.max_drawdown * 100).toFixed(2)}%
                                    </td>
                                    <td class="${result.sharpe_ratio >= 0 ? 'text-success' : 'text-danger'}">
                                        ${result.sharpe_ratio.toFixed(2)}
                                    </td>
                                    <td class="${result.win_rate >= 0.5 ? 'text-success' : 'text-danger'}">
                                        ${(result.win_rate * 100).toFixed(1)}%
                                    </td>
                                    <td>${result.total_trades}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <div class="mt-3">
                    <h6>最佳策略: ${strategyNames[results[0].strategy]}</h6>
                    <p class="text-muted">
                        总收益率: ${(results[0].total_return * 100).toFixed(2)}% | 
                        夏普比率: ${results[0].sharpe_ratio.toFixed(2)} | 
                        胜率: ${(results[0].win_rate * 100).toFixed(1)}%
                    </p>
                </div>
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
}