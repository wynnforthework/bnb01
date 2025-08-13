// 现货交易页面JavaScript
let socket;

// 初始化应用
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 现货交易页面开始初始化...');
    initializeSocket();
    loadInitialData();
    bindEvents();
    checkTradingStatus();
    
    // 延迟初始化币种管理，确保页面完全加载
    setTimeout(async () => {
        console.log('🔄 开始初始化币种管理...');
        await initializeSymbolManagement();
    }, 500);
    
    // 延迟加载合约数据，确保futures.js已加载
    setTimeout(() => {
        console.log('🔄 开始加载合约数据...');
        if (typeof loadFuturesInitialData === 'function') {
            loadFuturesInitialData();
        } else {
            console.log('⚠️ loadFuturesInitialData 函数未找到，尝试直接调用合约数据加载函数');
            // 如果futures.js函数不可用，尝试直接调用API
            loadFuturesDataDirectly();
        }
    }, 1500);
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

    // 策略管理按钮
    const showSymbolsBtn = document.getElementById('show-symbols');
    if (showSymbolsBtn) {
        showSymbolsBtn.addEventListener('click', function () {
            showStrategyPanel('symbols');
        });
    }

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
    
    // 币种管理按钮
    const showAllSymbolsBtn = document.getElementById('show-all-symbols');
    if (showAllSymbolsBtn) {
        showAllSymbolsBtn.addEventListener('click', function() {
            showAllSymbols();
        });
    }
    
    const showPopularSymbolsBtn = document.getElementById('show-popular-symbols');
    if (showPopularSymbolsBtn) {
        showPopularSymbolsBtn.addEventListener('click', function() {
            showPopularSymbols();
        });
    }
    
    const addCustomSymbolBtn = document.getElementById('add-custom-symbol');
    if (addCustomSymbolBtn) {
        addCustomSymbolBtn.addEventListener('click', function() {
            addCustomSymbol();
        });
    }
    
    const deleteCustomSymbolBtn = document.getElementById('delete-custom-symbol');
    if (deleteCustomSymbolBtn) {
        deleteCustomSymbolBtn.addEventListener('click', function() {
            deleteCustomSymbol();
        });
    }
}

// 加载初始数据
function loadInitialData() {
    loadAccountData();
    loadPortfolioData();
    loadTradesData();
    loadRiskMetrics();
    loadStrategiesList();
    loadStrategiesStatus();
    checkTradingStatus();
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


// 更新市场数据币种选择下拉框
function updateMarketDataSymbolSelect() {
    const symbolSelect = document.getElementById('symbol-select');
    if (!symbolSelect) return;

    // 清空现有选项
    symbolSelect.innerHTML = '';

    // 只添加已启用的币种
    if (availableSymbols && availableSymbols.length > 0) {
        availableSymbols.forEach(symbol => {
            const option = document.createElement('option');
            option.value = symbol;
            option.textContent = symbol.replace('USDT', '/USDT');
            symbolSelect.appendChild(option);
        });

        // 设置默认选择第一个
        if (availableSymbols.length > 0) {
            symbolSelect.value = availableSymbols[0];
        }
    } else {
        // 如果没有启用的币种，显示默认选项
        const defaultSymbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT'];
        defaultSymbols.forEach(symbol => {
            const option = document.createElement('option');
            option.value = symbol;
            option.textContent = symbol.replace('USDT', '/USDT');
            symbolSelect.appendChild(option);
        });
    }
}

// 更新数据收集币种选择下拉框
function updateDataCollectionSymbolSelect() {
    const collectSymbolSelect = document.getElementById('collect-symbol');
    if (!collectSymbolSelect) return;

    // 清空现有选项
    collectSymbolSelect.innerHTML = '';

    // 只添加已启用的币种
    if (availableSymbols && availableSymbols.length > 0) {
        availableSymbols.forEach(symbol => {
            const option = document.createElement('option');
            option.value = symbol;
            option.textContent = symbol.replace('USDT', '/USDT');
            collectSymbolSelect.appendChild(option);
        });

        // 设置默认选择第一个
        if (availableSymbols.length > 0) {
            collectSymbolSelect.value = availableSymbols[0];
        }
    } else {
        // 如果没有启用的币种，显示默认选项
        const defaultSymbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT'];
        defaultSymbols.forEach(symbol => {
            const option = document.createElement('option');
            option.value = symbol;
            option.textContent = symbol.replace('USDT', '/USDT');
            collectSymbolSelect.appendChild(option);
        });
    }
}


// 启动现货交易
async function startSpotTrading() {
    try {
        const response = await fetch('/api/spot/trading/start', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showSuccess(data.message);
            updateTradingStatus(true);
            
            // 更新策略数量显示
            if (data.enabled_count !== undefined && data.total_count !== undefined) {
                updateStrategyCountDisplay(data.enabled_count, data.total_count);
            }
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
        const response = await fetch('/api/spot/trading/stop', {
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
        const response = await fetch('/api/spot/trading/status');
        const data = await response.json();

        if (data.success) {
            updateTradingStatus(data.trading);
            
            // 更新策略数量显示
            if (data.enabled_count !== undefined && data.total_count !== undefined) {
                updateStrategyCountDisplay(data.enabled_count, data.total_count);
            }
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
    // 创建toast通知
    const toast = document.createElement('div');
    toast.className = 'alert alert-success alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

function showError(message) {
    console.error('Error:', message);
    // 创建toast通知
    const toast = document.createElement('div');
    toast.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
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
        <div class="columns">
            <div class="column">
                <div class="has-text-centered">
                    <h6 class="has-text-grey mb-2">总风险敞口</h6>
                    <h5 class="has-text-warning">${(riskData.total_exposure || 0).toFixed(2)}%</h5>
                </div>
            </div>
            <div class="column">
                <div class="has-text-centered">
                    <h6 class="has-text-grey mb-2">最大回撤</h6>
                    <h5 class="has-text-danger">${(riskData.max_drawdown || 0).toFixed(2)}%</h5>
                </div>
            </div>
            <div class="column">
                <div class="has-text-centered">
                    <h6 class="has-text-grey mb-2">夏普比率</h6>
                    <h5 class="has-text-info">${(riskData.sharpe_ratio || 0).toFixed(2)}</h5>
                </div>
            </div>
            <div class="column">
                <div class="has-text-centered">
                    <h6 class="has-text-grey mb-2">风险评级</h6>
                    <h5 class="has-text-success">${riskData.risk_level || '低'}</h5>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}


// 加载策略列表
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
    
    // 保存回测结果到全局变量
    const resultKey = `${symbol}_${strategyType}`;
    backtestResults[resultKey] = {
        result: result,
        strategyType: strategyType,
        symbol: symbol,
        timestamp: new Date().toISOString()
    };
    
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
    
    // 保存用户状态
    saveUserState();
    
    const html = `
        <div class="card">
            <div class="card-header">
                <h6 class="title is-6">${strategyName} - ${symbol} 回测结果</h6>
            </div>
            <div class="card-content">
                <div class="columns">
                    <div class="column is-6">
                        <h6 class="title is-6">收益指标</h6>
                        <table class="table is-fullwidth is-striped">
                            <tbody>
                                <tr>
                                    <td><strong>总收益率</strong></td>
                                    <td class="${result.total_return >= 0 ? 'has-text-success' : 'has-text-danger'}">
                                        ${(result.total_return * 100).toFixed(2)}%
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>年化收益率</strong></td>
                                    <td class="${result.annual_return >= 0 ? 'has-text-success' : 'has-text-danger'}">
                                        ${(result.annual_return * 100).toFixed(2)}%
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>最大回撤</strong></td>
                                    <td class="has-text-danger">
                                        ${(result.max_drawdown * 100).toFixed(2)}%
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>夏普比率</strong></td>
                                    <td class="${result.sharpe_ratio >= 0 ? 'has-text-success' : 'has-text-danger'}">
                                        ${result.sharpe_ratio.toFixed(2)}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="column is-6">
                        <h6 class="title is-6">交易统计</h6>
                        <table class="table is-fullwidth is-striped">
                            <tbody>
                                <tr>
                                    <td><strong>总交易次数</strong></td>
                                    <td>${result.total_trades}</td>
                                </tr>
                                <tr>
                                    <td><strong>胜率</strong></td>
                                    <td class="${result.win_rate >= 0.5 ? 'has-text-success' : 'has-text-danger'}">
                                        ${(result.win_rate * 100).toFixed(1)}%
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>平均交易收益</strong></td>
                                    <td class="${result.avg_trade_return >= 0 ? 'has-text-success' : 'has-text-danger'}">
                                        ${(result.avg_trade_return * 100).toFixed(2)}%
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>盈亏比</strong></td>
                                    <td class="${result.profit_factor >= 1 ? 'has-text-success' : 'has-text-danger'}">
                                        ${result.profit_factor.toFixed(2)}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h6 class="title is-6">最近交易记录</h6>
                    <div class="table-container" style="max-height: 200px; overflow-y: auto;">
                        <table class="table is-fullwidth is-striped is-narrow">
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
                                        <td class="${trade.action === 'BUY' ? 'has-text-success' : 'has-text-danger'}">
                                            <strong>${trade.action}</strong>
                                        </td>
                                        <td>$${trade.price.toFixed(2)}</td>
                                        <td>${trade.quantity.toFixed(6)}</td>
                                        <td class="${trade.profit >= 0 ? 'has-text-success' : 'has-text-danger'}">
                                            <strong>${trade.profit.toFixed(2)}</strong>
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
    const container = document.getElementById('backtest-results');
    
    let html = `
        <h6>策略比较结果 - ${symbol}</h6>
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>策略</th>
                        <th>总收益率</th>
                        <th>交易次数</th>
                        <th>胜率</th>
                        <th>最大回撤</th>
                        <th>夏普比率</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    results.forEach(result => {
        html += `
            <tr>
                <td>${result.strategy}</td>
                <td class="${result.total_return >= 0 ? 'text-success' : 'text-danger'}">${(result.total_return * 100).toFixed(2)}%</td>
                <td>${result.total_trades}</td>
                <td>${(result.win_rate * 100).toFixed(1)}%</td>
                <td class="text-danger">${(result.max_drawdown * 100).toFixed(2)}%</td>
                <td>${result.sharpe_ratio.toFixed(2)}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// ========== 新增的币种管理和策略控制功能 ==========

// 全局变量
let selectedSymbols = ['BTCUSDT', 'ETHUSDT']; // 默认选中的币种
let enabledStrategies = {}; // 启用的策略状态
let availableSymbols = []; // 当前可用的币种
let allAvailableSymbols = []; // 存储所有可用币种
let backtestResults = {}; // 存储回测结果

// 状态持久化函数
async function saveUserState() {
    try {
        const response = await fetch('/api/user/state', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                selected_symbols: selectedSymbols,
                enabled_strategies: enabledStrategies,
                backtest_results: backtestResults,
                strategy_backtest_data: window.strategyBacktestData || {}
            })
        });
        
        const data = await response.json();
        if (data.success) {
            console.log('用户状态保存成功');
        } else {
            console.error('保存用户状态失败:', data.message);
        }
    } catch (error) {
        console.error('保存用户状态失败:', error);
    }
}

async function loadUserState() {
    try {
        // 首先尝试从服务器加载用户状态
        const response = await fetch('/api/user/state');
        const data = await response.json();
        
        if (data.success) {
            const state = data.data;
            
            // 恢复选中的币种
            if (state.selected_symbols && state.selected_symbols.length > 0) {
                selectedSymbols = state.selected_symbols;
                console.log('从服务器恢复选中的币种:', selectedSymbols);
            } else {
                console.log('服务器没有币种数据，使用默认值:', selectedSymbols);
            }
            
            // 恢复启用的策略
            if (state.enabled_strategies && Object.keys(state.enabled_strategies).length > 0) {
                enabledStrategies = state.enabled_strategies;
                console.log('从服务器恢复启用的策略:', enabledStrategies);
            } else {
                console.log('服务器没有策略数据，使用默认值:', enabledStrategies);
            }
            
            // 恢复回测结果
            if (state.backtest_results && Object.keys(state.backtest_results).length > 0) {
                backtestResults = state.backtest_results;
                console.log('从服务器恢复回测结果:', Object.keys(backtestResults));
            } else {
                console.log('服务器没有回测结果，使用默认值:', backtestResults);
            }
            
            // 恢复策略回测数据
            if (state.strategy_backtest_data && Object.keys(state.strategy_backtest_data).length > 0) {
                window.strategyBacktestData = state.strategy_backtest_data;
                console.log('从服务器恢复策略回测数据:', Object.keys(window.strategyBacktestData));
            } else {
                console.log('服务器没有策略回测数据，使用默认值');
                window.strategyBacktestData = {};
            }
            
            console.log('用户状态恢复成功');
        } else {
            console.log('服务器加载用户状态失败，使用默认值');
        }
    } catch (error) {
        console.log('服务器连接失败，使用默认值:', error.message);
    }
    
    // 无论服务器是否成功，都确保有默认值
    if (!selectedSymbols || selectedSymbols.length === 0) {
        selectedSymbols = ['BTCUSDT', 'ETHUSDT'];
        console.log('设置默认币种:', selectedSymbols);
    }
    
    if (!enabledStrategies || Object.keys(enabledStrategies).length === 0) {
        // 设置一些默认启用的策略
        enabledStrategies = {
            'BTCUSDT_MA': true,
            'BTCUSDT_RSI': false,
            'BTCUSDT_ML': true,
            'BTCUSDT_Chanlun': false,
            'ETHUSDT_MA': false,
            'ETHUSDT_RSI': false,
            'ETHUSDT_ML': false,
            'ETHUSDT_Chanlun': false
        };
        console.log('设置默认策略状态:', enabledStrategies);
    }
    
    if (!backtestResults || Object.keys(backtestResults).length === 0) {
        backtestResults = {};
        console.log('设置默认回测结果:', backtestResults);
    }
    
    // 确保strategyBacktestData被初始化
    if (!window.strategyBacktestData) {
        window.strategyBacktestData = {};
        console.log('初始化strategyBacktestData');
    }
    
    // 更新显示
    updateSymbolsDisplay();
    updateStrategiesDisplay();
    
    // 恢复回测结果显示
    if (backtestResults && Object.keys(backtestResults).length > 0) {
        console.log('🔄 恢复回测结果显示...');
        const resultsContainer = document.getElementById('backtest-results');
        if (resultsContainer) {
            console.log('找到回测结果容器');
            // 显示最新的回测结果
            const latestResult = Object.values(backtestResults).sort((a, b) => 
                new Date(b.timestamp) - new Date(a.timestamp)
            )[0];
            
            if (latestResult) {
                console.log('调用displayBacktestResults...');
                displayBacktestResults(latestResult.result, latestResult.strategyType, latestResult.symbol);
            }
        }
    }
}

// 初始化币种管理
async function initializeSymbolManagement() {
    console.log('🔍 开始初始化币种管理...');
    try {
        // 首先加载用户状态（从本地存储或服务器）
        await loadUserState();
        console.log('✅ 加载用户状态完成');
        
        // 然后加载可用币种
        await loadAvailableSymbols();
        console.log('✅ 加载可用币种完成');
        
        // 加载策略状态
        await loadStrategiesStatus();
        console.log('✅ 加载策略状态完成');
        
        // 更新显示
        updateSymbolsDisplay();
        console.log('✅ 更新币种显示完成');
        updateStrategiesDisplay();
        console.log('✅ 更新策略显示完成');
        
        // 显示成功消息
        showSuccess('币种管理初始化完成');
    } catch (error) {
        console.error('❌ 币种管理初始化失败:', error);
        showError('币种管理初始化失败: ' + error.message);
    }
}

// 加载可用币种
async function loadAvailableSymbols() {
    console.log('🔄 正在加载可用币种...');
    try {
        // 首先尝试获取所有可用币种
        const response = await fetch('/api/spot/symbols/available');
        console.log('可用币种API响应状态:', response.status);
        const data = await response.json();
        console.log('可用币种API响应数据:', data);
        
        if (data.success) {
            allAvailableSymbols = data.symbols;
            console.log('✅ 所有可用币种已加载:', allAvailableSymbols.length, '个');
        }
        
        // 然后获取当前选择的币种
        const currentResponse = await fetch('/api/spot/symbols');
        console.log('当前币种API响应状态:', currentResponse.status);
        const currentData = await currentResponse.json();
        console.log('当前币种API响应数据:', currentData);
        
        if (currentData.success) {
            availableSymbols = currentData.symbols;
            console.log('✅ 当前币种已加载:', availableSymbols);
        } else {
            console.error('❌ 加载当前币种失败:', currentData.message);
            throw new Error(currentData.message);
        }
    } catch (error) {
        console.error('❌ 加载币种失败:', error);
        throw error;
    }
}

// 加载策略状态
async function loadStrategiesStatus() {
    console.log('🔄 正在加载策略状态...');
    try {
        const response = await fetch('/api/spot/strategies/status');
        console.log('策略状态API响应状态:', response.status);
        const data = await response.json();
        console.log('策略状态API响应数据:', data);
        if (data.success) {
            // 确保没有重复的币种
            const uniqueSymbols = [...new Set(data.symbols)];
            if (uniqueSymbols.length !== data.symbols.length) {
                console.warn('⚠️ API返回的币种中有重复，已自动去重');
                console.warn('原始币种:', data.symbols);
                console.warn('去重后币种:', uniqueSymbols);
            }
            
            selectedSymbols = uniqueSymbols;
            enabledStrategies = data.enabled_strategies;
            
            // 更新策略数量显示
            updateStrategyCountDisplay(data.enabled_count, data.total_count);
            
            console.log('✅ 策略状态已加载:', {selectedSymbols, enabledStrategies});
        } else {
            console.error('❌ 加载策略状态失败:', data.message);
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('❌ 加载策略状态失败:', error);
        throw error;
    }
}

// 更新币种显示
function updateSymbolsDisplay() {
    console.log('🔄 正在更新币种显示...');
    console.log('当前 availableSymbols:', availableSymbols);
    console.log('当前 selectedSymbols:', selectedSymbols);
    
    const container = document.getElementById('symbols-container');
    if (!container) {
        console.error('❌ 找不到币种容器元素');
        return;
    }
    
    console.log('可用币种:', availableSymbols);
    let html = '';
    availableSymbols.forEach(symbol => {
        const isSelected = selectedSymbols.includes(symbol);
        html += `
            <div class="col-md-3 col-sm-4 col-6 mb-2 symbol-item">
                <div class="form-check">
                    <input class="form-check-input symbol-checkbox" type="checkbox" 
                           value="${symbol}" id="symbol-${symbol}"
                           ${isSelected ? 'checked' : ''}>
                    <label class="form-check-label" for="symbol-${symbol}">
                        ${symbol}
                    </label>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    console.log('✅ 币种显示已更新，HTML长度:', html.length);
    console.log('生成的HTML:', html.substring(0, 200) + '...');
    updateSymbolCount();
    
    // 更新市场数据币种选择下拉框
    updateMarketDataSymbolSelect();
    
    // 更新数据收集币种选择下拉框
    updateDataCollectionSymbolSelect();
}

// 更新币种计数
function updateSymbolCount() {
    const countElement = document.getElementById('symbol-count');
    if (countElement) {
        countElement.textContent = availableSymbols.length;
    }
}

// 搜索币种
function filterSymbols() {
    const searchTerm = document.getElementById('symbol-search').value.toLowerCase();
    const symbolItems = document.querySelectorAll('.symbol-item');
    
    symbolItems.forEach(item => {
        const symbol = item.querySelector('label').textContent.toLowerCase();
        if (symbol.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// 显示所有币种
function showAllSymbols() {
    console.log('🔍 showAllSymbols 被调用');
    console.log('当前 allAvailableSymbols:', allAvailableSymbols);
    console.log('当前 availableSymbols:', availableSymbols);
    
    // 检查 allAvailableSymbols 是否已初始化
    if (!allAvailableSymbols || allAvailableSymbols.length === 0) {
        console.log('⚠️ allAvailableSymbols 尚未初始化，正在重新加载...');
        showError('币种数据尚未加载完成，请稍后再试');
        // 尝试重新初始化
        setTimeout(() => {
            initializeSymbolManagement();
        }, 100);
        return;
    }
    
    availableSymbols = [...allAvailableSymbols]; // 使用展开运算符创建副本
    console.log('更新后 availableSymbols:', availableSymbols);
    
    updateSymbolsDisplay();
    showSuccess('已显示所有可用币种');
}

// 显示热门币种
function showPopularSymbols() {
    console.log('🔍 showPopularSymbols 被调用');
    console.log('当前 allAvailableSymbols:', allAvailableSymbols);
    
    // 检查 allAvailableSymbols 是否已初始化
    if (!allAvailableSymbols || allAvailableSymbols.length === 0) {
        console.log('⚠️ allAvailableSymbols 尚未初始化，正在重新加载...');
        showError('币种数据尚未加载完成，请稍后再试');
        // 尝试重新初始化
        setTimeout(() => {
            initializeSymbolManagement();
        }, 100);
        return;
    }
    
    const popularSymbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT',
        'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT',
        'FILUSDT', 'XRPUSDT', 'MATICUSDT', 'SHIBUSDT'
    ];
    
    availableSymbols = popularSymbols.filter(symbol => 
        allAvailableSymbols.includes(symbol)
    );
    console.log('更新后 availableSymbols:', availableSymbols);
    
    updateSymbolsDisplay();
    showSuccess('已显示热门币种');
}

// 添加自定义币种
async function addCustomSymbol() {
    console.log('🔍 addCustomSymbol 被调用');
    const symbol = prompt('请输入币种代码 (例如: BTCUSDT):');
    if (symbol) {
        const upperSymbol = symbol.toUpperCase();
        console.log('用户输入的币种:', upperSymbol);
        
        if (upperSymbol.endsWith('USDT')) {
            // 检查 allAvailableSymbols 是否已初始化
            if (!allAvailableSymbols || allAvailableSymbols.length === 0) {
                console.log('⚠️ allAvailableSymbols 尚未初始化，正在重新加载...');
                showError('币种数据尚未加载完成，请稍后再试');
                return;
            }
            
            if (!availableSymbols.includes(upperSymbol)) {
                // 获取添加币种按钮
                const addBtn = document.getElementById('add-custom-symbol');
                const originalContent = addBtn.innerHTML;
                
                try {
                    // 显示加载状态
                    addBtn.disabled = true;
                    addBtn.innerHTML = `
                        <span class="icon">
                            <i class="fas fa-spinner fa-spin"></i>
                        </span>
                        <span>添加中...</span>
                    `;
                    
                    // 添加到当前显示的币种列表
                    availableSymbols.push(upperSymbol);
                    console.log('添加币种后 availableSymbols:', availableSymbols);
                    updateSymbolsDisplay();
                    
                    // 同时保存到后端
                    const response = await fetch('/api/spot/symbols', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({symbols: availableSymbols})
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        selectedSymbols = availableSymbols;
                        showSuccess(`已添加币种: ${upperSymbol}`);
                        // 重新加载策略状态
                        await loadStrategiesStatus();
                        updateStrategiesDisplay();
                    } else {
                        showError('保存币种失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('添加币种失败:', error);
                    showError('添加币种失败: ' + error.message);
                } finally {
                    // 恢复按钮状态
                    addBtn.disabled = false;
                    addBtn.innerHTML = originalContent;
                }
            } else {
                showError('该币种已存在');
            }
        } else {
            showError('币种格式错误，请使用 USDT 交易对');
        }
    }
}

// 删除自定义币种
async function deleteCustomSymbol() {
    console.log('🔍 deleteCustomSymbol 被调用');
    
    // 检查 allAvailableSymbols 是否已初始化
    if (!allAvailableSymbols || allAvailableSymbols.length === 0) {
        console.log('⚠️ allAvailableSymbols 尚未初始化，正在重新加载...');
        showError('币种数据尚未加载完成，请稍后再试');
        return;
    }
    
    // 获取当前选中的币种
    const selectedSymbolsToDelete = Array.from(document.querySelectorAll('.symbol-checkbox:checked'))
                                .map(checkbox => checkbox.value);
    
    if (selectedSymbolsToDelete.length === 0) {
        showError('请先选择要删除的币种');
        return;
    }
    
    // 确认删除
    const symbolList = selectedSymbolsToDelete.join(', ');
    const confirmed = confirm(`确定要删除以下币种吗？\n${symbolList}`);
    
    if (confirmed) {
        // 获取删除币种按钮
        const deleteBtn = document.getElementById('delete-custom-symbol');
        const originalContent = deleteBtn.innerHTML;
        
        try {
            // 显示加载状态
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = `
                <span class="icon">
                    <i class="fas fa-spinner fa-spin"></i>
                </span>
                <span>删除中...</span>
            `;
            
            // 从当前显示的币种列表中移除
            selectedSymbolsToDelete.forEach(symbol => {
                const index = availableSymbols.indexOf(symbol);
                if (index > -1) {
                    availableSymbols.splice(index, 1);
                }
            });
            
            console.log('删除币种后 availableSymbols:', availableSymbols);
            updateSymbolsDisplay();
            
            // 同时保存到后端
            const response = await fetch('/api/spot/symbols', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({symbols: availableSymbols})
            });
            
            const data = await response.json();
            if (data.success) {
                showSuccess(`已删除币种: ${symbolList}`);
                // 重新加载策略状态
                await loadStrategiesStatus();
                updateStrategiesDisplay();
            } else {
                showError('保存币种失败: ' + data.message);
            }
        } catch (error) {
            console.error('删除币种失败:', error);
            showError('删除币种失败: ' + error.message);
        } finally {
            // 恢复按钮状态
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = originalContent;
        }
    }
}

// 更新策略显示
function updateStrategiesDisplay() {
    const container = document.getElementById('strategies-container');
    if (!container) return;
    
    let html = '';
    let totalStrategies = 0;
    let enabledCount = 0;
    let totalReturn = 0;
    let totalWinRate = 0;
    let validStrategies = 0;
    
    selectedSymbols.forEach(symbol => {
        html += `
            <div class="mb-5">
                <h4 class="title is-4 has-text-primary pb-2 mb-4" style="border-bottom: 2px solid #3273dc;">
                    <i class="fas fa-coins mr-2"></i>${symbol}
                </h4>
        `;
        
        // 策略垂直排版
        ['MA', 'RSI', 'ML', 'Chanlun'].forEach((strategy, index) => {
            const key = `${symbol}_${strategy}`;
            const enabled = enabledStrategies[key] || false;
            // 优先使用全局回测数据，如果没有则尝试从用户状态恢复
            let backtestData = window.strategyBacktestData ? window.strategyBacktestData[key] : null;
            if (!backtestData && window.backtestResults && window.backtestResults[key]) {
                backtestData = window.backtestResults[key];
            }
            
            totalStrategies++;
            if (enabled) enabledCount++;
            
            // 计算统计数据
            if (backtestData) {
                totalReturn += backtestData.total_return || 0;
                totalWinRate += backtestData.win_rate || 0;
                validStrategies++;
            }
            
            const returnPercent = backtestData ? (backtestData.total_return * 100).toFixed(2) : '0.00';
            const winRatePercent = backtestData ? (backtestData.win_rate * 100).toFixed(1) : '0.0';
            const tradeCount = backtestData ? backtestData.total_trades : 0;
            const sharpeRatio = backtestData ? backtestData.sharpe_ratio.toFixed(2) : '0.00';
            
            const returnColor = returnPercent >= 0 ? 'has-text-success' : 'has-text-danger';
            const winRateColor = winRatePercent >= 50 ? 'has-text-success' : 'has-text-warning';
            
            html += `
                <div class="mb-4">
                    <div class="card ${enabled ? 'has-background-success-light' : 'has-background-light'} strategy-card">
                        <div class="card-header p-3" style="background-color: ${enabled ? '#f0f9ff' : '#f5f5f5'};">
                            <div class="level is-mobile mb-0">
                                <div class="level-left">
                                    <div class="level-item">
                                        <h6 class="title is-6 mb-0">
                                            <i class="fas fa-chart-line mr-2"></i>${strategy} 策略
                                        </h6>
                                    </div>
                                </div>
                                <div class="level-right">
                                    <div class="level-item">
                                        <label class="switch">
                                            <input type="checkbox" ${enabled ? 'checked' : ''} 
                                                   onchange="toggleStrategy('${key}', event)">
                                            <span class="slider round"></span>
                                        </label>
                                        <small class="ml-2 has-text-grey">${enabled ? '启用' : '禁用'}</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card-content p-4">
                            ${backtestData ? `
                                <!-- 回测结果水平排版 -->
                                <div class="columns is-multiline">
                                    <div class="column is-3">
                                        <div class="has-text-centered p-3" style="background-color: #f8f9fa; border-radius: 8px;">
                                            <div class="has-text-grey is-size-7">收益率</div>
                                            <div class="has-text-weight-bold is-size-4 ${returnColor}">${returnPercent}%</div>
                                        </div>
                                    </div>
                                    <div class="column is-3">
                                        <div class="has-text-centered p-3" style="background-color: #f8f9fa; border-radius: 8px;">
                                            <div class="has-text-grey is-size-7">胜率</div>
                                            <div class="has-text-weight-bold is-size-4 ${winRateColor}">${winRatePercent}%</div>
                                        </div>
                                    </div>
                                    <div class="column is-3">
                                        <div class="has-text-centered p-3" style="background-color: #f8f9fa; border-radius: 8px;">
                                            <div class="has-text-grey is-size-7">交易次数</div>
                                            <div class="has-text-weight-bold is-size-4">${tradeCount}</div>
                                        </div>
                                    </div>
                                    <div class="column is-3">
                                        <div class="has-text-centered p-3" style="background-color: #f8f9fa; border-radius: 8px;">
                                            <div class="has-text-grey is-size-7">夏普比率</div>
                                            <div class="has-text-weight-bold is-size-4">${sharpeRatio}</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="mt-4 has-text-centered">
                                    <button class="button is-info is-outlined" 
                                            onclick="event.stopPropagation(); viewDetailedBacktest('${symbol}', '${strategy}')">
                                        <i class="fas fa-chart-line mr-2"></i>查看详细回测
                                    </button>
                                </div>
                            ` : `
                                <div class="has-text-centered has-text-grey p-4">
                                    <i class="fas fa-clock is-size-1 mb-3"></i>
                                    <div class="is-size-5">等待回测</div>
                                    <small>该策略尚未进行回测分析</small>
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `</div>`;
    });
    
    container.innerHTML = html;
    
    // 更新统计信息
    updateStrategyStatistics(totalStrategies, enabledCount, totalReturn, totalWinRate, validStrategies);
}

function updateStrategyStatistics(total, enabled, totalReturn, totalWinRate, validStrategies) {
    const totalElement = document.getElementById('total-strategies-count');
    const enabledElement = document.getElementById('enabled-strategies-count');
    const avgReturnElement = document.getElementById('avg-return');
    const avgWinRateElement = document.getElementById('avg-win-rate');
    
    if (totalElement) totalElement.textContent = total;
    if (enabledElement) enabledElement.textContent = enabled;
    
    if (validStrategies > 0) {
        const avgReturn = (totalReturn / validStrategies * 100).toFixed(2);
        const avgWinRate = (totalWinRate / validStrategies * 100).toFixed(1);
        
        if (avgReturnElement) avgReturnElement.textContent = `${avgReturn}%`;
        if (avgWinRateElement) avgWinRateElement.textContent = `${avgWinRate}%`;
    } else {
        if (avgReturnElement) avgReturnElement.textContent = '0%';
        if (avgWinRateElement) avgReturnElement.textContent = '0%';
    }
}

// 更新策略数量显示
function updateStrategyCountDisplay(enabledCount, totalCount) {
    // 更新现货交易控制面板中的策略数量显示
    const spotStrategiesCountElement = document.getElementById('spot-strategies-count');
    if (spotStrategiesCountElement) {
        spotStrategiesCountElement.textContent = enabledCount;
    }
    
    // 更新策略统计面板中的数量显示
    const totalStrategiesCountElement = document.getElementById('total-strategies-count');
    const enabledStrategiesCountElement = document.getElementById('enabled-strategies-count');
    
    if (totalStrategiesCountElement) {
        totalStrategiesCountElement.textContent = totalCount;
    }
    if (enabledStrategiesCountElement) {
        enabledStrategiesCountElement.textContent = enabledCount;
    }
    
    console.log(`✅ 策略数量显示已更新: 启用 ${enabledCount}, 总计 ${totalCount}`);
}

async function viewDetailedBacktest(symbol, strategyType) {
    try {
        const response = await fetch(`/api/spot/strategies/backtest/${symbol}/${strategyType}`);
        const data = await response.json();
        
        if (data.success) {
            showDetailedBacktestModal(data.result);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('获取详细回测失败: ' + error.message);
    }
}

function showDetailedBacktestModal(backtestData) {
    const modalHtml = `
        <div class="modal" id="backtestModal">
            <div class="modal-background"></div>
            <div class="modal-card">
                <header class="modal-card-head">
                    <p class="modal-card-title">${backtestData.symbol} - ${backtestData.strategy} 详细回测结果</p>
                    <button class="delete" aria-label="close" onclick="closeBacktestModal()"></button>
                </header>
                <section class="modal-card-body">
                    <div class="columns">
                        <div class="column">
                            <h6 class="title is-6">收益指标</h6>
                            <table class="table is-fullwidth is-striped">
                                <tr><td>总收益率:</td><td class="${backtestData.total_return >= 0 ? 'has-text-success' : 'has-text-danger'}">${(backtestData.total_return * 100).toFixed(2)}%</td></tr>
                                <tr><td>夏普比率:</td><td>${backtestData.sharpe_ratio.toFixed(2)}</td></tr>
                                <tr><td>最大回撤:</td><td class="has-text-danger">${(backtestData.max_drawdown * 100).toFixed(2)}%</td></tr>
                            </table>
                        </div>
                        <div class="column">
                            <h6 class="title is-6">交易统计</h6>
                            <table class="table is-fullwidth is-striped">
                                <tr><td>总交易次数:</td><td>${backtestData.total_trades}</td></tr>
                                <tr><td>胜率:</td><td class="${backtestData.win_rate >= 0.5 ? 'has-text-success' : 'has-text-warning'}">${(backtestData.win_rate * 100).toFixed(1)}%</td></tr>
                                <tr><td>策略状态:</td><td><span class="tag is-success">已启用</span></td></tr>
                            </table>
                        </div>
                    </div>
                    ${backtestData.parameters ? `
                        <div class="mt-4">
                            <h6 class="title is-6">策略参数</h6>
                            <pre class="has-background-light p-2" style="border-radius: 4px;">${JSON.stringify(backtestData.parameters, null, 2)}</pre>
                        </div>
                    ` : ''}
                </section>
                <footer class="modal-card-foot">
                    <button class="button" onclick="closeBacktestModal()">关闭</button>
                </footer>
            </div>
        </div>
    `;
    
    // 移除现有模态框
    const existingModal = document.getElementById('backtestModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 显示模态框
    const modal = document.getElementById('backtestModal');
    modal.classList.add('is-active');
    
    // 添加背景点击关闭事件
    const modalBackground = modal.querySelector('.modal-background');
    if (modalBackground) {
        modalBackground.onclick = closeBacktestModal;
    }
}

// 关闭详细回测模态框
function closeBacktestModal() {
    const modal = document.getElementById('backtestModal');
    if (modal) {
        modal.classList.remove('is-active');
        // 延迟删除模态框元素
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 150);
    }
}

// 全选币种
function selectAllSymbols() {
    document.querySelectorAll('.symbol-checkbox').forEach(checkbox => {
        checkbox.checked = true;
    });
}

// 清空币种选择
function clearAllSymbols() {
    document.querySelectorAll('.symbol-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
}

// 保存币种选择
async function saveSymbolSelection() {
    const selected = Array.from(document.querySelectorAll('.symbol-checkbox:checked'))
                        .map(checkbox => checkbox.value);
    
    // 获取保存选择按钮
    const saveBtn = document.querySelector('button[onclick="saveSymbolSelection()"]');
    const originalContent = saveBtn.innerHTML;
    
    try {
        // 显示加载状态
        saveBtn.disabled = true;
        saveBtn.innerHTML = `
            <span class="icon">
                <i class="fas fa-spinner fa-spin"></i>
            </span>
            <span>保存中...</span>
        `;
        
        const response = await fetch('/api/spot/symbols', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbols: selected})
        });
        
        const data = await response.json();
        if (data.success) {
            selectedSymbols = selected;
            // 保存用户状态
            await saveUserState();
            showSuccess(data.message);
            await loadStrategiesStatus();
            updateStrategiesDisplay();
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('保存币种选择失败: ' + error.message);
    } finally {
        // 恢复按钮状态
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalContent;
    }
}

// 更新策略
async function updateStrategies() {
    if (selectedSymbols.length === 0) {
        showError('请先选择币种');
        return;
    }
    
    // 获取更新策略按钮
    const updateBtn = document.querySelector('button[onclick="updateStrategies()"]');
    const originalContent = updateBtn.innerHTML;
    
    try {
        // 显示加载状态
        updateBtn.disabled = true;
        updateBtn.innerHTML = `
            <span class="icon">
                <i class="fas fa-spinner fa-spin"></i>
            </span>
            <span>更新中...</span>
        `;
        
        showSuccess('正在更新策略，请稍候...');
        
        // 确保没有重复的币种
        const uniqueSymbols = [...new Set(selectedSymbols)];
        if (uniqueSymbols.length !== selectedSymbols.length) {
            console.warn('⚠️ 选中的币种中有重复，已自动去重');
            console.warn('原始币种:', selectedSymbols);
            console.warn('去重后币种:', uniqueSymbols);
        }
        
        const response = await fetch('/api/spot/strategies/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbols: uniqueSymbols})
        });
        
        const data = await response.json();
        if (data.success) {
            // 存储回测数据到全局变量
            window.strategyBacktestData = {};
            
            // 更新启用状态和回测数据
            data.results.forEach(symbolResult => {
                symbolResult.strategies.forEach(strategy => {
                    enabledStrategies[strategy.strategy_key] = strategy.enabled;
                    // 存储回测数据
                    window.strategyBacktestData[strategy.strategy_key] = {
                        total_return: strategy.total_return,
                        total_trades: strategy.total_trades,
                        win_rate: strategy.win_rate,
                        max_drawdown: strategy.max_drawdown,
                        sharpe_ratio: strategy.sharpe_ratio,
                        parameters: strategy.parameters
                    };
                });
            });
            
            // 保存用户状态，包括新的回测数据
            await saveUserState();
            
            updateStrategiesDisplay();
            showSuccess(data.message);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('更新策略失败: ' + error.message);
    } finally {
        // 恢复按钮状态
        updateBtn.disabled = false;
        updateBtn.innerHTML = originalContent;
    }
}

// 启用全部策略
async function enableAllStrategies() {
    // 获取启用全部按钮
    const enableBtn = document.querySelector('button[onclick="enableAllStrategies()"]');
    const originalContent = enableBtn.innerHTML;
    
    try {
        // 显示加载状态
        enableBtn.disabled = true;
        enableBtn.innerHTML = `
            <span class="icon">
                <i class="fas fa-spinner fa-spin"></i>
            </span>
            <span>启用中...</span>
        `;
        
        const response = await fetch('/api/spot/strategies/manage', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: 'enable_all'})
        });
        
        const data = await response.json();
        if (data.success) {
            selectedSymbols.forEach(symbol => {
                ['MA', 'RSI', 'ML', 'Chanlun'].forEach(strategy => {
                    enabledStrategies[`${symbol}_${strategy}`] = true;
                });
            });
            // 保存用户状态
            await saveUserState();
            updateStrategiesDisplay();
            showSuccess(data.message);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('启用策略失败: ' + error.message);
    } finally {
        // 恢复按钮状态
        enableBtn.disabled = false;
        enableBtn.innerHTML = originalContent;
    }
}

// 禁用全部策略
async function disableAllStrategies() {
    // 获取禁用全部按钮
    const disableBtn = document.querySelector('button[onclick="disableAllStrategies()"]');
    const originalContent = disableBtn.innerHTML;
    
    try {
        // 显示加载状态
        disableBtn.disabled = true;
        disableBtn.innerHTML = `
            <span class="icon">
                <i class="fas fa-spinner fa-spin"></i>
            </span>
            <span>禁用中...</span>
        `;
        
        const response = await fetch('/api/spot/strategies/manage', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: 'disable_all'})
        });
        
        const data = await response.json();
        if (data.success) {
            selectedSymbols.forEach(symbol => {
                ['MA', 'RSI', 'ML', 'Chanlun'].forEach(strategy => {
                    enabledStrategies[`${symbol}_${strategy}`] = false;
                });
            });
            // 保存用户状态
            await saveUserState();
            updateStrategiesDisplay();
            showSuccess(data.message);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('禁用策略失败: ' + error.message);
    } finally {
        // 恢复按钮状态
        disableBtn.disabled = false;
        disableBtn.innerHTML = originalContent;
    }
}

// 切换单个策略
async function toggleStrategy(strategyKey, event) {
    // 阻止事件冒泡，防止重复触发
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // 获取当前状态
    const currentState = enabledStrategies[strategyKey] || false;
    const newState = !currentState;
    
    // 获取对应的checkbox元素
    const checkbox = document.querySelector(`input[onchange="toggleStrategy('${strategyKey}', event)"]`);
    if (checkbox) {
        checkbox.disabled = true;
    }
    
    try {
        const response = await fetch('/api/spot/strategies/manage', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: 'toggle', 
                strategy_key: strategyKey,
                enabled: newState
            })
        });
        
        const data = await response.json();
        if (data.success) {
            enabledStrategies[strategyKey] = newState;
            // 保存用户状态
            await saveUserState();
            updateStrategiesDisplay();
            showSuccess(data.message);
        } else {
            // 如果失败，恢复原状态
            if (checkbox) {
                checkbox.checked = currentState;
            }
            showError(data.message);
        }
    } catch (error) {
        // 如果失败，恢复原状态
        if (checkbox) {
            checkbox.checked = currentState;
        }
        showError('切换策略失败: ' + error.message);
    } finally {
        // 重新启用checkbox
        if (checkbox) {
            checkbox.disabled = false;
        }
    }
}

// 修改现有的策略面板切换功能
function showStrategyPanel(panelType) {
    // 隐藏所有面板
    document.querySelectorAll('.strategy-panel').forEach(panel => {
        panel.style.display = 'none';
    });
    
    // 移除所有按钮的active类
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('btn-primary', 'btn-info', 'btn-success');
        btn.classList.add('btn-outline-primary', 'btn-outline-info', 'btn-outline-success');
    });
    
    // 显示选中的面板
    if (panelType === 'symbols') {
        document.getElementById('symbols-panel').style.display = 'block';
        document.getElementById('show-symbols').classList.remove('btn-outline-primary');
        document.getElementById('show-symbols').classList.add('btn-primary');
    } else if (panelType === 'strategies') {
        document.getElementById('strategies-panel').style.display = 'block';
        document.getElementById('show-strategies').classList.remove('btn-outline-info');
        document.getElementById('show-strategies').classList.add('btn-info');
    } else if (panelType === 'backtest') {
        document.getElementById('backtest-panel').style.display = 'block';
        document.getElementById('show-backtest').classList.remove('btn-outline-success');
        document.getElementById('show-backtest').classList.add('btn-success');
    }
}

// 直接加载合约数据的备用函数
async function loadFuturesDataDirectly() {
    console.log('🔄 直接加载合约数据...');
    
    try {
        // 加载合约持仓
        const positionsResponse = await fetch('/api/futures/positions');
        const positionsData = await positionsResponse.json();
        
        if (positionsData.success) {
            displayFuturesPositionsDirectly(positionsData.positions);
        } else {
            console.error('加载合约持仓失败:', positionsData.message);
        }
        
        // 加载合约交易历史
        const tradesResponse = await fetch('/api/futures/trades');
        const tradesData = await tradesResponse.json();
        
        if (tradesData.success) {
            displayFuturesTradesDirectly(tradesData.trades);
        } else {
            console.error('加载合约交易历史失败:', tradesData.message);
        }
        
    } catch (error) {
        console.error('直接加载合约数据失败:', error.message);
    }
}

// 直接显示合约持仓
function displayFuturesPositionsDirectly(positions) {
    const tbody = document.querySelector('#futures-positions-table tbody');
    if (!tbody) {
        console.error('未找到合约持仓表格');
        return;
    }
    
    if (positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="has-text-centered">暂无合约持仓</td></tr>';
        return;
    }
    
    let html = '';
    positions.forEach(position => {
        const pnlClass = position.unRealizedProfit >= 0 ? 'has-text-success' : 'has-text-danger';
        const pnlSign = position.unRealizedProfit >= 0 ? '+' : '';
        const sideClass = position.positionAmt > 0 ? 'has-text-success' : 'has-text-danger';
        const sideText = position.positionAmt > 0 ? '做多' : '做空';
        
        html += `
            <tr>
                <td>${position.symbol}</td>
                <td class="${sideClass}">${sideText}</td>
                <td>${Math.abs(position.positionAmt).toFixed(6)}</td>
                <td>$${position.entryPrice.toFixed(2)}</td>
                <td>$${position.markPrice.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}$${position.unRealizedProfit.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}${(position.percentage || 0).toFixed(2)}%</td>
                <td>$${position.isolatedMargin.toFixed(2)}</td>
                <td>${position.leverage}x</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 直接显示合约交易历史
function displayFuturesTradesDirectly(trades) {
    const tbody = document.querySelector('#futures-trades-table tbody');
    if (!tbody) {
        console.error('未找到合约交易历史表格');
        return;
    }
    
    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="has-text-centered">暂无合约交易记录</td></tr>';
        return;
    }
    
    let html = '';
    trades.forEach(trade => {
        const sideClass = trade.side === 'BUY' ? 'has-text-success' : 'has-text-danger';
        const pnlClass = trade.profit_loss >= 0 ? 'has-text-success' : 'has-text-danger';
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
                <td><span class="tag is-warning">合约</span></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

